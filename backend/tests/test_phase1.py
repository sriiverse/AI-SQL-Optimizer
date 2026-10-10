"""Phase 1: analysis history reliability and provenance. Providers are mocked."""

import asyncio
import json
import sqlite3
import sys
from types import SimpleNamespace

from fastapi.testclient import TestClient

from history_storage import HistoryStorage
from main import app
from models import AnalysisResult, PlanNode

client = TestClient(app)

DEMO_QUERY = "SELECT * FROM users"


def _plan_json(node_type="Seq Scan", cost=10.0, rows=4):
    return json.dumps(
        {
            "execution_plan_summary": {
                "node_type": node_type,
                "cost": cost,
                "rows": rows,
                "relation_name": "users",
            },
            "suggestions": [],
            "optimized_query": "SELECT id FROM users",
            "explanation": "estimated only",
        }
    )


class _GeminiModel:
    def __init__(self, text=None, error=None):
        self._text = text
        self._error = error

    async def generate_content_async(self, prompt, request_options=None):
        if self._error is not None:
            raise self._error
        return SimpleNamespace(text=self._text)


class _GroqCompletions:
    def __init__(self, content):
        self._content = content

    async def create(self, **kwargs):
        message = SimpleNamespace(content=self._content)
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])


class _GroqClient:
    def __init__(self, api_key=None, timeout=None):
        self.chat = SimpleNamespace(completions=_GroqCompletions(_plan_json()))


def _install_fake_groq(monkeypatch):
    monkeypatch.setitem(sys.modules, "groq", SimpleNamespace(AsyncGroq=_GroqClient))
    monkeypatch.setenv("GROQ_API_KEY", "test-key")


def test_history_writer_reads_existing_plan_cost(tmp_path):
    storage = HistoryStorage(str(tmp_path / "history.db"))
    result = AnalysisResult(
        original_query="SELECT 1",
        execution_plan=PlanNode(node_type="Seq Scan", cost=12.5, rows=3, relation_name="t"),
        suggestions=[],
        optimized_query="SELECT 1",
        explanation="demo",
        analysis_source="demo",
        plan_origin="synthetic",
        database_connected=False,
        performance_measured=False,
    )

    assert not hasattr(result.execution_plan, "execution_cost")
    assert not hasattr(result.execution_plan, "execution_time_ms")

    storage.add_entry(result, dialect="postgresql")
    row = storage.get_history(limit=1)[0]
    assert row["original_cost"] == 12.5
    assert row["optimized_query"] == "SELECT 1"
    assert row["execution_time_ms"] is None
    assert row["optimized_cost"] is None
    assert row["cost_savings"] is None


def test_analyze_demo_succeeds_and_records_history(tmp_path, monkeypatch):
    monkeypatch.setattr("main.history_enabled", lambda: True)
    storage = HistoryStorage(str(tmp_path / "history.db"))
    monkeypatch.setattr("main.get_history_storage", lambda: storage)
    monkeypatch.setattr("main.get_model", lambda: None)

    response = client.post("/analyze", json={"query": DEMO_QUERY, "dialect": "postgresql"})

    assert response.status_code == 200
    data = response.json()
    assert data["original_query"] == DEMO_QUERY
    assert data["analysis_source"] == "demo"
    assert data["plan_origin"] == "synthetic"
    assert data["database_connected"] is False
    assert data["performance_measured"] is False
    assert len(data["suggestions"]) >= 1

    row = storage.get_history(limit=1)[0]
    assert row["original_cost"] == data["execution_plan"]["cost"]
    assert row["optimized_query"] == data["optimized_query"]
    assert row["execution_time_ms"] is None


def test_history_failure_still_returns_analysis(monkeypatch):
    monkeypatch.setattr("main.history_enabled", lambda: True)

    class _FailingStorage:
        def add_entry(self, *args, **kwargs):
            raise sqlite3.OperationalError("disk full simulated")

    monkeypatch.setattr("main.get_history_storage", lambda: _FailingStorage())
    monkeypatch.setattr("main.get_model", lambda: None)

    response = client.post("/analyze", json={"query": DEMO_QUERY, "dialect": "postgresql"})

    assert response.status_code == 200
    data = response.json()
    assert data["original_query"] == DEMO_QUERY
    assert data["analysis_source"] == "demo"
    assert "disk full simulated" not in response.text
    assert "OperationalError" not in response.text


def test_gemini_analyze_provenance(monkeypatch):
    monkeypatch.setattr("main.get_model", lambda: object())

    async def fake_analyze(query, dialect, model):
        from analyze import analyze_query_with_gemini

        return await analyze_query_with_gemini(
            query,
            dialect,
            _GeminiModel(text=_plan_json()),
        )

    monkeypatch.setattr("main.analyze_query_with_gemini", fake_analyze)

    response = client.post("/analyze", json={"query": "SELECT id FROM users", "dialect": "postgresql"})
    assert response.status_code == 200
    data = response.json()
    assert data["analysis_source"] == "gemini"
    assert data["plan_origin"] == "synthetic"
    assert data["database_connected"] is False
    assert data["performance_measured"] is False


def test_groq_analyze_provenance(monkeypatch):
    _install_fake_groq(monkeypatch)

    async def run():
        from analyze import analyze_query_with_gemini

        return await analyze_query_with_gemini(
            "SELECT id FROM users",
            "postgresql",
            _GeminiModel(error=RuntimeError("429 quota exceeded")),
        )

    result = asyncio.run(run())
    assert result.analysis_source == "groq"
    assert result.plan_origin == "synthetic"
    assert result.database_connected is False
    assert result.performance_measured is False
    assert "429" not in result.explanation


def test_provider_error_does_not_leak_exception_text():
    secret = "provider-internal-detail-should-stay-in-logs"

    async def run():
        from analyze import analyze_query_with_gemini

        return await analyze_query_with_gemini(
            "SELECT 1",
            "postgresql",
            _GeminiModel(error=RuntimeError(secret)),
        )

    result = asyncio.run(run())
    assert result.analysis_source == "error"
    assert result.plan_origin == "none"
    assert result.database_connected is False
    assert result.performance_measured is False
    assert secret not in result.explanation


def test_generate_demo_provenance(monkeypatch):
    monkeypatch.setattr("main.get_model", lambda: None)
    response = client.post(
        "/generate-sql",
        json={
            "schema_def": "CREATE TABLE users (id INT)",
            "question": "Show me all active users",
            "dialect": "postgresql",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"]
    assert data["analysis_source"] == "demo"
    assert data["plan_origin"] == "none"
    assert data["database_connected"] is False
    assert data["performance_measured"] is False


def test_gemini_and_groq_generate_provenance(monkeypatch):
    async def gemini():
        from generator import generate_sql_with_gemini

        model = _GeminiModel(text="SQL: SELECT id FROM users\nExplanation: gemini path")
        return await generate_sql_with_gemini("CREATE TABLE users (id INT)", "list ids", "postgresql", model)

    gemini_result = asyncio.run(gemini())
    assert gemini_result.analysis_source == "gemini"
    assert gemini_result.plan_origin == "none"
    assert "SELECT id FROM users" in gemini_result.query
    assert gemini_result.database_connected is False
    assert gemini_result.performance_measured is False

    _install_fake_groq(monkeypatch)

    class GroqSql(_GroqClient):
        def __init__(self, api_key=None, timeout=None):
            self.chat = SimpleNamespace(
                completions=_GroqCompletions("SQL: SELECT id FROM users\nExplanation: groq path")
            )

    monkeypatch.setitem(sys.modules, "groq", SimpleNamespace(AsyncGroq=GroqSql))

    async def groq():
        from generator import generate_sql_with_gemini

        return await generate_sql_with_gemini(
            "CREATE TABLE users (id INT)",
            "list ids",
            "postgresql",
            _GeminiModel(error=RuntimeError("429 quota exceeded")),
        )

    groq_result = asyncio.run(groq())
    assert groq_result.analysis_source == "groq"
    assert groq_result.plan_origin == "none"
    assert "SELECT id FROM users" in groq_result.query
    assert groq_result.database_connected is False
    assert groq_result.performance_measured is False


def test_unparsed_model_text_falls_back_to_labeled_demo():
    async def run():
        from generator import generate_sql_with_gemini

        model = _GeminiModel(text="I need more information before I can answer.")
        return await generate_sql_with_gemini("CREATE TABLE users (id INT)", "list users", "postgresql", model)

    result = asyncio.run(run())
    assert result.analysis_source == "demo"
    assert result.plan_origin == "none"
    assert "[Demo Mode" in result.explanation
