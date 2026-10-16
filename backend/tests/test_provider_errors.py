"""Provider failures stay out of responses and logs. Credentials here are synthetic."""

import asyncio
import logging
from types import SimpleNamespace

import pytest

from fastapi.testclient import TestClient

from analyze import analyze_query_with_gemini
from generator import generate_sql_with_gemini
from main import app

client = TestClient(app)

FAKE_GEMINI_KEY = "AIzaSYFAKEKEYFORTESTONLY000000"
FAKE_PROJECT = "projects/999001"
FAKE_GROQ_KEY = "gsk_FAKEGROQKEY999"
GEMINI_LEAK = (
    "403 CONSUMER_SUSPENDED Permission denied for consumer "
    f"{FAKE_PROJECT}. "
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest"
    f"?key={FAKE_GEMINI_KEY}"
)
GROQ_LEAK = f"401 invalid api key {FAKE_GROQ_KEY}"

ANALYZE = {
    "query": "SELECT * FROM orders WHERE YEAR(order_date) = 2025 AND customer_id = 1042",
    "dialect": "postgresql",
}
GENERATE = {
    "schema_def": "CREATE TABLE orders (id INT, customer_id INT, order_date TEXT)",
    "question": "orders for customer 1042 in 2025",
    "dialect": "postgresql",
}
AUTH = {"Authorization": "Bearer server-secret"}


class _ProviderError(Exception):
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code


class _Model:
    def __init__(self, error):
        self.error = error

    async def generate_content_async(self, prompt, request_options=None):
        raise self.error


def _hidden(text: str):
    assert FAKE_GEMINI_KEY not in text
    assert FAKE_PROJECT not in text
    assert "CONSUMER_SUSPENDED" not in text
    assert FAKE_GROQ_KEY not in text
    assert "generativelanguage.googleapis.com" not in text
    assert "Authorization" not in text


def _install_failing_groq(monkeypatch, error):
    class _Completions:
        async def create(self, **kwargs):
            raise error

    class _Groq:
        def __init__(self, api_key=None, timeout=None):
            self.chat = SimpleNamespace(completions=_Completions())

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setitem(__import__("sys").modules, "groq", SimpleNamespace(AsyncGroq=_Groq))


def _allow_provider(monkeypatch, model):
    monkeypatch.setattr("main.provider_access_token", lambda: "server-secret")
    monkeypatch.setattr("main.get_model", lambda: model)


def test_gemini_403_is_absent_from_the_analysis_response_and_logs(caplog):
    caplog.set_level(logging.WARNING)
    model = _Model(_ProviderError(GEMINI_LEAK, 403))

    result = asyncio.run(analyze_query_with_gemini("SELECT 1", "postgresql", model))

    assert result.analysis_source == "error"
    assert result.explanation == "AI analysis failed."
    assert result.optimized_query == "ERROR"
    assert result.performance_measured is False
    _hidden(result.model_dump_json())
    _hidden(caplog.text)


def test_analyze_and_generate_endpoints_hide_a_gemini_403(monkeypatch, caplog):
    caplog.set_level(logging.WARNING)
    _allow_provider(monkeypatch, _Model(_ProviderError(GEMINI_LEAK, 403)))

    analyzed = client.post("/analyze", json=ANALYZE, headers=AUTH)
    generated = client.post("/generate-sql", json=GENERATE, headers=AUTH)

    assert analyzed.status_code == 502
    assert generated.status_code == 502
    assert analyzed.json() == {"detail": "AI analysis failed."}
    assert generated.json() == {"detail": "AI generation failed."}
    _hidden(analyzed.text)
    _hidden(generated.text)
    _hidden(caplog.text)
    assert "Analysis Report" not in analyzed.text


def test_groq_fallback_errors_are_sanitized_for_analysis_and_generation(monkeypatch, caplog):
    caplog.set_level(logging.WARNING)
    _install_failing_groq(monkeypatch, _ProviderError(GROQ_LEAK, 401))
    model = _Model(_ProviderError("429 quota exceeded " + GEMINI_LEAK, 429))

    analyzed = asyncio.run(analyze_query_with_gemini("SELECT 1", "postgresql", model))
    generated = asyncio.run(
        generate_sql_with_gemini("CREATE TABLE users (id INT)", "list users", "postgresql", model)
    )

    assert analyzed.analysis_source == "error"
    assert generated.analysis_source == "error"
    assert "fallback provider returned an error" in analyzed.explanation
    assert "fallback provider returned an error" in generated.explanation
    _hidden(analyzed.model_dump_json())
    _hidden(generated.model_dump_json())
    _hidden(caplog.text)


def test_non_allowlisted_provider_text_is_replaced_at_the_endpoint(monkeypatch):
    async def analyze(*args, **kwargs):
        from analyze import _analysis_error

        return _analysis_error("SELECT 1", GEMINI_LEAK)

    async def generate(*args, **kwargs):
        from generator import _generation_error

        return _generation_error(GROQ_LEAK)

    _allow_provider(monkeypatch, object())
    monkeypatch.setattr("main.analyze_query_with_gemini", analyze)
    monkeypatch.setattr("main.generate_sql_with_gemini", generate)

    analyzed = client.post("/analyze", json=ANALYZE, headers=AUTH)
    generated = client.post("/generate-sql", json=GENERATE, headers=AUTH)

    assert analyzed.status_code == 502
    assert generated.status_code == 502
    assert analyzed.json()["detail"] == "AI analysis failed."
    assert generated.json()["detail"] == "AI generation failed."
    _hidden(analyzed.text)
    _hidden(generated.text)


def test_authorization_failure_stays_enforced(monkeypatch):
    called = []

    async def analyze(*args, **kwargs):
        called.append("analyze")
        raise AssertionError("provider called")

    monkeypatch.setattr("main.provider_access_token", lambda: "server-secret")
    monkeypatch.setattr("main.get_model", lambda: _Model(_ProviderError(GEMINI_LEAK, 403)))
    monkeypatch.setattr("main.analyze_query_with_gemini", analyze)

    response = client.post("/analyze", json=ANALYZE)

    assert response.status_code == 403
    assert response.json() == {"detail": "Paid provider access is not authorized."}
    assert called == []
    _hidden(response.text)


def test_demo_mode_still_skips_the_provider(monkeypatch):
    monkeypatch.setattr("main.provider_access_token", lambda: None)
    monkeypatch.setattr(
        "main.get_model",
        lambda: (_ for _ in ()).throw(AssertionError("model loaded")),
    )

    response = client.post("/analyze", json={"query": "SELECT * FROM users", "dialect": "postgresql"})

    assert response.status_code == 200
    assert response.json()["analysis_source"] == "demo"
    _hidden(response.text)


class _TextModel:
    def __init__(self, text):
        self.text = text

    async def generate_content_async(self, prompt, request_options=None):
        return SimpleNamespace(text=self.text)


def test_unlabeled_provider_body_is_not_a_successful_query(caplog):
    caplog.set_level(logging.WARNING)
    body = (
        f"403 CONSUMER_SUSPENDED for {FAKE_PROJECT} key={FAKE_GEMINI_KEY}\n"
        "SELECT * FROM orders WHERE customer_id = 1042;"
    )
    result = asyncio.run(
        generate_sql_with_gemini(
            "CREATE TABLE orders (id INT)",
            "orders for customer 1042",
            "postgresql",
            _TextModel(body),
        )
    )

    assert result.analysis_source == "error"
    assert result.query == "ERROR"
    assert result.explanation == "The model response could not be read."
    _hidden(result.model_dump_json())
    assert body not in result.query
    assert body not in result.explanation


def test_unlabeled_provider_body_is_a_generation_502(monkeypatch):
    body = (
        f"The provider returned {FAKE_PROJECT} and key={FAKE_GEMINI_KEY}. "
        "SELECT * FROM orders WHERE YEAR(order_date) = 2025;"
    )
    _allow_provider(monkeypatch, _TextModel(body))

    response = client.post("/generate-sql", json=GENERATE, headers=AUTH)

    assert response.status_code == 502
    assert response.json() == {"detail": "The model response could not be read."}
    _hidden(response.text)
    assert body not in response.text


def test_prose_around_sql_without_the_response_format_fails():
    body = (
        f"I could not finish because of {FAKE_PROJECT} ({FAKE_GEMINI_KEY}). "
        "Here is a guess: SELECT id FROM orders"
    )
    result = asyncio.run(
        generate_sql_with_gemini(
            "CREATE TABLE orders (id INT)",
            "list ids",
            "postgresql",
            _TextModel(body),
        )
    )
    assert result.analysis_source == "error"
    assert result.explanation == "The model response could not be read."
    _hidden(result.model_dump_json())
    assert body not in result.model_dump_json()


TRAILING = f"key={FAKE_GEMINI_KEY} {FAKE_PROJECT}"
LABELED_WITH_TRAILING_QUERY = (
    "SQL: SELECT id FROM users\n"
    f"{TRAILING}\n"
    "Explanation: Returns users.\n"
)
LABELED_WITH_TRAILING_EXPLANATION = (
    "SQL: SELECT id FROM users\n"
    "Explanation: Returns users.\n"
    f"{TRAILING}\n"
)
FENCED_WITH_TRAILING_LINE = (
    "```sql\n"
    "SELECT id FROM users\n"
    f"{TRAILING}\n"
    "```\n"
)
MULTILINE_SQL = """SQL: WITH recent AS (
    SELECT id, region
    FROM users
    WHERE active = true
)
SELECT id
FROM recent
ORDER BY id
Explanation: Returns recent active users by region.
"""
MULTILINE_FENCE = """```sql
WITH recent AS (
    SELECT id, region
    FROM users
    WHERE active = true
)
SELECT id
FROM recent
ORDER BY id
```
"""


def _assert_unreadable(result, logged=""):
    assert result.analysis_source == "error"
    assert result.plan_origin == "none"
    assert result.query == "ERROR"
    assert result.explanation == "The model response could not be read."
    dumped = result.model_dump_json()
    _hidden(dumped)
    assert TRAILING not in dumped
    _hidden(logged)
    assert TRAILING not in logged


@pytest.mark.parametrize(
    "body",
    [LABELED_WITH_TRAILING_QUERY, LABELED_WITH_TRAILING_EXPLANATION, FENCED_WITH_TRAILING_LINE],
)
def test_trailing_provider_text_is_not_a_successful_query(body, caplog):
    caplog.set_level(logging.DEBUG)
    result = asyncio.run(
        generate_sql_with_gemini(
            "CREATE TABLE users (id INT)",
            "list ids",
            "postgresql",
            _TextModel(body),
        )
    )
    _assert_unreadable(result, caplog.text)
    assert body not in result.model_dump_json()


@pytest.mark.parametrize(
    "body",
    [LABELED_WITH_TRAILING_QUERY, LABELED_WITH_TRAILING_EXPLANATION, FENCED_WITH_TRAILING_LINE],
)
def test_trailing_provider_text_is_a_generation_502(body, monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    _allow_provider(monkeypatch, _TextModel(body))

    response = client.post("/generate-sql", json=GENERATE, headers=AUTH)

    assert response.status_code == 502
    assert response.json() == {"detail": "The model response could not be read."}
    _hidden(response.text)
    _hidden(caplog.text)
    assert TRAILING not in response.text
    assert TRAILING not in caplog.text
    assert body not in response.text


def test_multiline_labeled_and_fenced_sql_still_succeeds():
    labeled = asyncio.run(
        generate_sql_with_gemini(
            "CREATE TABLE users (id INT, region TEXT, active BOOLEAN)",
            "recent users",
            "postgresql",
            _TextModel(MULTILINE_SQL),
        )
    )
    assert labeled.analysis_source == "gemini"
    assert "WITH recent AS (" in labeled.query
    assert "SELECT id, region" in labeled.query
    assert "FROM recent" in labeled.query
    assert labeled.explanation == "Returns recent active users by region."

    fenced = asyncio.run(
        generate_sql_with_gemini(
            "CREATE TABLE users (id INT, region TEXT, active BOOLEAN)",
            "recent users",
            "postgresql",
            _TextModel(MULTILINE_FENCE),
        )
    )
    assert fenced.analysis_source == "gemini"
    assert "WITH recent AS (" in fenced.query
    assert "ORDER BY id" in fenced.query
    assert fenced.explanation == "Generated based on your question and schema."


def test_agent_frame_and_result_note_are_not_logged(monkeypatch, caplog, capsys):
    monkeypatch.setattr("main.agent_enabled", lambda: True)
    secret = f"{FAKE_GEMINI_KEY} {FAKE_PROJECT}"
    frame = (
        '{"type":"EXECUTION_RESULT","note":"'
        + secret
        + '","execution_time_ms":1}'
    )
    with caplog.at_level(logging.DEBUG):
        with client.websocket_connect("/ws/agent/alice") as websocket:
            websocket.send_text(frame)
            acknowledged = client.post(
                "/agent/execution-result",
                params={"client_id": "alice"},
                json={"status": "success", "execution_time_ms": 1.0, "note": secret},
            )
            websocket.close()
    captured = capsys.readouterr()

    assert acknowledged.status_code == 200
    assert "Agent frame received" in caplog.text
    assert "Execution result received" in caplog.text
    assert secret not in caplog.text
    assert secret not in captured.out
    assert secret not in captured.err
    assert secret not in acknowledged.text


def test_labeled_sql_response_still_succeeds():
    text = "SQL: SELECT id FROM users WHERE active = true\nExplanation: Returns active users."
    result = asyncio.run(
        generate_sql_with_gemini(
            "CREATE TABLE users (id INT, active BOOLEAN)",
            "active users",
            "postgresql",
            _TextModel(text),
        )
    )
    assert result.analysis_source == "gemini"
    assert result.query.strip() == "SELECT id FROM users WHERE active = true"
    assert result.explanation == "Returns active users."


def test_exception_name_and_cause_are_not_logged(caplog):
    caplog.set_level(logging.WARNING)
    secret_name = FAKE_GEMINI_KEY
    cause = _ProviderError(GEMINI_LEAK, 403)
    try:
        raise type(secret_name, (Exception,), {})("wrapper") from cause
    except Exception as exc:
        chained = exc

    result = asyncio.run(analyze_query_with_gemini("SELECT 1", "postgresql", _Model(chained)))

    assert result.analysis_source == "error"
    assert result.explanation == "AI analysis failed."
    _hidden(result.model_dump_json())
    _hidden(caplog.text)
    assert secret_name not in caplog.text
    assert "Exception" in caplog.text


def test_startup_failure_does_not_print_the_exception(monkeypatch, capsys):
    from main import lifespan

    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-startup-value")
    monkeypatch.setattr("main._gemini_model", None)

    def fail(api_key=None):
        raise RuntimeError(GEMINI_LEAK)

    monkeypatch.setattr("main.genai.configure", fail)

    async def enter():
        async with lifespan(app):
            return None

    asyncio.run(enter())
    printed = capsys.readouterr().out
    assert "failed to initialize" in printed
    _hidden(printed)

