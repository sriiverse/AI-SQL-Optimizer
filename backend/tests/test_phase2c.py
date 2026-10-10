"""Phase 2C: missing plan numbers stay unavailable and are not stored as measurements."""

import asyncio
import json
import sys
from types import SimpleNamespace

from fastapi.testclient import TestClient

from analyze import analyze_query_with_gemini
from history_storage import HistoryStorage
from main import app

client = TestClient(app)


class _Model:
    def __init__(self, text=None, error=None):
        self._text = text
        self._error = error

    async def generate_content_async(self, prompt, request_options=None):
        if self._error is not None:
            raise self._error
        return SimpleNamespace(text=self._text)


def _payload(**overrides):
    body = {
        "execution_plan_summary": {
            "node_type": "Seq Scan",
            "cost": 12.5,
            "rows": 4,
            "relation_name": "users",
        },
        "suggestions": [
            {
                "title": "Narrow the select list",
                "description": "A model note, not a measurement.",
                "impact": "High",
                "sql_snippet": "SELECT id FROM users",
            }
        ],
        "optimized_query": "SELECT id FROM users",
        "explanation": "estimated only",
    }
    body.update(overrides)
    return json.dumps(body)


def _run(text=None, error=None, query="SELECT * FROM users"):
    return asyncio.run(
        analyze_query_with_gemini(query, "postgresql", _Model(text=text, error=error))
    )


def test_groq_estimate_without_cost_keeps_groq_provenance(monkeypatch):
    payload = _payload(execution_plan_summary={"node_type": "Index Scan"})

    class _Completions:
        async def create(self, **kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=payload))]
            )

    class _Groq:
        def __init__(self, api_key=None, timeout=None):
            self.chat = SimpleNamespace(completions=_Completions())

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "groq", SimpleNamespace(AsyncGroq=_Groq))
    result = _run(error=RuntimeError("429 quota exceeded"))
    assert result.analysis_source == "groq"
    assert result.plan_origin == "synthetic"
    assert result.execution_plan.cost is None
    assert result.execution_plan.rows is None
    assert result.database_connected is False
    assert result.performance_measured is False
    assert "429" not in result.explanation


def test_missing_plan_cost_is_not_replaced_with_100():
    result = _run(_payload(execution_plan_summary={"node_type": "Seq Scan", "rows": 4}))
    assert result.execution_plan.cost is None
    assert result.execution_plan.cost != 100.0
    assert result.execution_plan.rows == 4
    assert result.plan_origin == "synthetic"
    assert result.analysis_source == "gemini"
    assert result.database_connected is False
    assert result.performance_measured is False
    assert result.optimized_query == "SELECT id FROM users"


def test_invalid_plan_cost_and_rows_stay_unset():
    summary = {"node_type": "Seq Scan", "cost": "not-a-number", "rows": "many", "relation_name": "users"}
    result = _run(_payload(execution_plan_summary=summary))
    assert result.execution_plan.cost is None
    assert result.execution_plan.rows is None

    for invalid_cost in (True, "NaN", "Infinity", "", "  ", "not-a-number"):
        summary = {"cost": invalid_cost, "rows": 3}
        parsed = _run(_payload(execution_plan_summary=summary))
        assert parsed.execution_plan.cost is None
        assert parsed.execution_plan.rows == 3

    zero_rows = _run(_payload(execution_plan_summary={"cost": 2, "rows": 0}))
    assert zero_rows.execution_plan.cost == 2
    assert zero_rows.execution_plan.rows == 0

    negative = _run(_payload(execution_plan_summary={"rows": -5, "cost": 1}))
    assert negative.execution_plan.rows is None


def test_incomplete_plan_still_returns_the_suggestion_and_query():
    result = _run(
        json.dumps(
            {
                "suggestions": "not-a-list",
                "optimized_query": "SELECT id FROM users",
                "explanation": "partial reply",
            }
        )
    )
    assert result.analysis_source == "gemini"
    assert result.plan_origin == "synthetic"
    assert result.execution_plan.cost is None
    assert result.execution_plan.rows is None
    assert result.execution_plan.node_type is None
    assert result.suggestions == []
    assert result.optimized_query == "SELECT id FROM users"
    assert result.explanation == "partial reply"
    assert result.database_connected is False
    assert result.performance_measured is False


def test_malformed_provider_output_is_an_error_without_fabricated_metrics():
    for text in ("this is not json", "[1, 2, 3]", ""):
        result = _run(text)
        assert result.analysis_source == "error"
        assert result.plan_origin == "none"
        assert result.execution_plan.cost is None
        assert result.execution_plan.rows is None
        assert result.database_connected is False
        assert result.performance_measured is False
        assert result.explanation == "The model response could not be read."
        assert "100.0" not in result.explanation


def test_demo_and_error_paths_do_not_invent_plan_metrics(tmp_path, monkeypatch):
    monkeypatch.setattr("main.history_enabled", lambda: True)
    monkeypatch.setattr("main.get_model", lambda: None)
    storage = HistoryStorage(str(tmp_path / "history.db"))
    monkeypatch.setattr("main.get_history_storage", lambda: storage)

    response = client.post(
        "/analyze",
        json={"query": "SELECT * FROM users", "dialect": "postgresql"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["analysis_source"] == "demo"
    assert data["plan_origin"] == "synthetic"
    assert data["database_connected"] is False
    assert data["performance_measured"] is False
    assert data["execution_plan"]["cost"] is None
    assert data["execution_plan"]["rows"] is None
    assert data["execution_plan"]["cost"] != 100.0
    assert "Sequential Scan" not in data["explanation"]

    row = storage.get_history(limit=1)[0]
    assert row["original_cost"] is None
    assert row["execution_time_ms"] is None
    assert row["optimized_query"] == data["optimized_query"]
    assert row["cost_savings"] is None

    failed = _run(error=RuntimeError("provider-secret-detail"))
    assert failed.analysis_source == "error"
    assert failed.plan_origin == "none"
    assert failed.execution_plan.cost is None
    assert "provider-secret-detail" not in failed.explanation


def test_supplied_estimate_is_stored_without_a_measured_runtime(tmp_path):
    from models import AnalysisResult, PlanNode

    storage = HistoryStorage(str(tmp_path / "history.db"))
    result = _run(_payload())
    assert result.execution_plan.cost == 12.5
    assert result.plan_origin == "synthetic"
    assert result.analysis_source == "gemini"
    storage.add_entry(result, dialect="postgresql")
    row = storage.get_history(limit=1)[0]
    assert row["original_cost"] == 12.5
    assert row["execution_time_ms"] is None

    engine_shaped = AnalysisResult(
        original_query="SELECT 1",
        execution_plan=PlanNode(node_type="Seq Scan", cost=9, rows=1),
        suggestions=[],
        explanation="should not be stored as measured",
        analysis_source="gemini",
        plan_origin="engine",
        database_connected=False,
        performance_measured=False,
    )
    storage.add_entry(engine_shaped, dialect="postgresql")
    stored = [item for item in storage.get_history(limit=10) if item["query"] == "SELECT 1"][0]
    assert stored["original_cost"] is None
    assert stored["execution_time_ms"] is None
