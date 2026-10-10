"""Phase 2A: history and agent are off unless explicitly enabled."""

import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import history_storage
from history_storage import HistoryStorage
from main import app, flag_is_enabled
from models import AnalysisResult, PlanNode
from socket_manager import manager

client = TestClient(app)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_QUERY = "SELECT secret_col FROM payroll"


def _sample_result() -> AnalysisResult:
    return AnalysisResult(
        original_query=DEMO_QUERY,
        execution_plan=PlanNode(
            node_type="Seq Scan", cost=4.0, rows=1, relation_name="payroll"
        ),
        suggestions=[],
        optimized_query="SELECT id FROM payroll",
        explanation="estimated only",
        analysis_source="demo",
        plan_origin="synthetic",
        database_connected=False,
        performance_measured=False,
    )


def test_flag_parser_defaults_off():
    assert flag_is_enabled(None) is False
    assert flag_is_enabled("") is False
    assert flag_is_enabled("false") is False
    assert flag_is_enabled("0") is False
    assert flag_is_enabled("true") is True
    assert flag_is_enabled("YES") is True


def test_history_is_disabled_by_default(tmp_path, monkeypatch):
    monkeypatch.setattr("main.get_model", lambda: None)
    db_path = tmp_path / "query_history.db"

    def open_database():
        HistoryStorage(str(db_path))
        raise AssertionError("history database opened")

    monkeypatch.setattr("main.get_history_storage", open_database)

    response = client.post(
        "/analyze", json={"query": DEMO_QUERY, "dialect": "postgresql"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["original_query"] == DEMO_QUERY
    assert data["analysis_source"] == "demo"
    assert data["plan_origin"] == "synthetic"
    assert data["database_connected"] is False
    assert data["performance_measured"] is False
    assert history_storage._history_storage is None
    assert not db_path.exists()

    history = client.get("/history")
    assert history.status_code == 404
    assert history.json() == {"detail": "History is disabled"}
    assert DEMO_QUERY not in history.text
    assert "history" not in history.json()
    assert not db_path.exists()


def test_disabled_history_does_not_return_existing_rows(tmp_path, monkeypatch):
    storage = HistoryStorage(str(tmp_path / "history.db"))
    storage.add_entry(_sample_result(), dialect="postgresql")
    monkeypatch.setattr("main.get_history_storage", lambda: storage)

    response = client.get("/history")

    assert response.status_code == 404
    assert response.json() == {"detail": "History is disabled"}
    assert "secret_col" not in response.text
    assert storage.get_history(limit=1)[0]["query"] == DEMO_QUERY


def test_enabled_history_uses_temporary_storage(tmp_path, monkeypatch):
    monkeypatch.setattr("main.history_enabled", lambda: True)
    storage = HistoryStorage(str(tmp_path / "history.db"))
    monkeypatch.setattr("main.get_history_storage", lambda: storage)
    monkeypatch.setattr("main.get_model", lambda: None)

    response = client.post(
        "/analyze", json={"query": DEMO_QUERY, "dialect": "postgresql"}
    )

    assert response.status_code == 200
    row = storage.get_history(limit=1)[0]
    assert row["query"] == DEMO_QUERY
    assert row["optimized_query"] == response.json()["optimized_query"]
    assert row["execution_time_ms"] is None

    history = client.get("/history")
    assert history.status_code == 200
    assert history.json()["history"][0]["query"] == DEMO_QUERY


def test_agent_websocket_is_refused_when_disabled():
    with pytest.raises(WebSocketDisconnect) as refused:
        with client.websocket_connect("/ws/agent/alice") as websocket:
            websocket.receive_text()

    assert refused.value.code == 1008
    assert refused.value.reason == "Agent is disabled"
    assert "alice" not in manager.active_connections


def test_agent_execute_does_not_deliver_query_when_disabled(capsys, caplog):
    sent = []

    class FakeSocket:
        async def send_text(self, payload):
            sent.append(payload)

    manager.active_connections["alice"] = FakeSocket()
    try:
        with caplog.at_level(logging.DEBUG):
            response = client.post(
                "/agent/execute",
                json={"client_id": "alice", "query": DEMO_QUERY},
            )
        captured = capsys.readouterr()
    finally:
        manager.active_connections.pop("alice", None)

    assert response.status_code == 404
    assert response.json() == {"detail": "Agent is disabled"}
    assert DEMO_QUERY not in response.text
    assert DEMO_QUERY not in captured.out
    assert DEMO_QUERY not in captured.err
    assert DEMO_QUERY not in caplog.text
    assert sent == []


def test_agent_execution_result_rejected_when_disabled(capsys, caplog):
    with caplog.at_level(logging.DEBUG):
        response = client.post(
            "/agent/execution-result",
            params={"client_id": "alice"},
            json={
                "status": "success",
                "execution_time_ms": 12.5,
                "note": DEMO_QUERY,
            },
        )
    captured = capsys.readouterr()

    assert response.status_code == 404
    assert response.json() == {"detail": "Agent is disabled"}
    assert DEMO_QUERY not in response.text
    assert DEMO_QUERY not in captured.out
    assert DEMO_QUERY not in captured.err
    assert DEMO_QUERY not in caplog.text


def test_enabled_agent_connects_delivers_and_disconnects(monkeypatch):
    monkeypatch.setattr("main.agent_enabled", lambda: True)

    with client.websocket_connect("/ws/agent/alice") as websocket:
        assert "alice" in manager.active_connections
        response = client.post(
            "/agent/execute",
            json={"client_id": "alice", "query": "SELECT 1"},
        )
        assert response.status_code == 200
        assert websocket.receive_json() == {"type": "EXECUTE", "query": "SELECT 1"}

        acknowledged = client.post(
            "/agent/execution-result",
            params={"client_id": "alice"},
            json={"status": "success", "execution_time_ms": 1.0, "note": "timer"},
        )
        assert acknowledged.status_code == 200
        assert acknowledged.json()["status"] == "success"

    assert "alice" not in manager.active_connections


def test_cli_and_pro_modal_do_not_claim_real_execution():
    cli_source = (REPO_ROOT / "cli" / "index.js").read_text()
    modal_source = (
        REPO_ROOT / "frontend" / "src" / "components" / "ProConnectionModal.tsx"
    ).read_text()
    combined = cli_source + "\n" + modal_source

    for claim in (
        "queryforge login",
        "queryforge connect",
        "True EXPLAIN",
        "never leave your laptop",
        "Executed on local database",
        "real timing measurement",
        "Connected securely",
        "Tunnel established",
        "Authenticates your local machine",
        "postgresql://user:pass",
    ):
        assert claim not in combined

    assert "Simulated timer only. This agent did not connect to a database or execute the query." in cli_source
    assert "does not connect to a database" in cli_source
    assert "No login command is implemented" in cli_source
    assert "does not connect to a database" in modal_source
    assert "does not run EXPLAIN" in modal_source
    assert "No login command is implemented" in modal_source
    assert "does not accept a database password" in modal_source
