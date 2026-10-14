"""Paid provider calls stay closed unless the server token is presented."""

from fastapi.testclient import TestClient

from main import app, read_provider_access_token

client = TestClient(app)

ANALYZE = {"query": "SELECT * FROM users", "dialect": "postgresql"}
GENERATE = {
    "schema_def": "CREATE TABLE users (id INT)",
    "question": "list users",
    "dialect": "postgresql",
}


def _close_providers(monkeypatch):
    calls = []

    async def analyze(*args, **kwargs):
        calls.append(("analyze", args))
        raise AssertionError("analyze provider called")

    async def generate(*args, **kwargs):
        calls.append(("generate", args))
        raise AssertionError("generate provider called")

    monkeypatch.setattr("main.get_model", lambda: object())
    monkeypatch.setattr("main.analyze_query_with_gemini", analyze)
    monkeypatch.setattr("main.generate_sql_with_gemini", generate)
    return calls


def test_missing_or_blank_server_token_is_closed(monkeypatch):
    monkeypatch.delenv("PROVIDER_ACCESS_TOKEN", raising=False)
    assert read_provider_access_token() is None
    monkeypatch.setenv("PROVIDER_ACCESS_TOKEN", "   ")
    assert read_provider_access_token() is None
    monkeypatch.setenv("PROVIDER_ACCESS_TOKEN", "server-secret")
    assert read_provider_access_token() == "server-secret"


def test_disabled_paid_access_does_not_call_providers_even_when_a_model_exists(monkeypatch):
    calls = _close_providers(monkeypatch)
    monkeypatch.setattr("main.provider_access_token", lambda: None)

    analyzed = client.post("/analyze", json=ANALYZE)
    generated = client.post("/generate-sql", json=GENERATE)

    assert analyzed.status_code == 200
    assert analyzed.json()["analysis_source"] == "demo"
    assert generated.status_code == 200
    assert generated.json()["analysis_source"] == "demo"
    assert calls == []


def test_missing_or_wrong_token_does_not_call_providers(monkeypatch):
    calls = _close_providers(monkeypatch)
    monkeypatch.setattr("main.provider_access_token", lambda: "server-secret")

    missing = client.post("/analyze", json=ANALYZE)
    wrong = client.post(
        "/generate-sql",
        json=GENERATE,
        headers={"Authorization": "Bearer other-secret"},
    )
    forwarded = client.post(
        "/analyze",
        json=ANALYZE,
        headers={"X-Forwarded-For": "203.0.113.8", "X-API-Key": "server-secret"},
    )
    query_token = client.post("/analyze?access_token=server-secret", json=ANALYZE)

    for response in (missing, wrong, forwarded, query_token):
        assert response.status_code == 403
        assert response.json() == {"detail": "Paid provider access is not authorized."}
    assert calls == []


def test_matching_bearer_token_reaches_the_mocked_provider(monkeypatch):
    calls = []

    async def analyze(query, dialect, model):
        calls.append(("analyze", query, dialect))
        from analyze import analyze_query_demo

        return analyze_query_demo(query)

    async def generate(schema_def, question, dialect, model):
        calls.append(("generate", question, dialect))
        from generator import generate_sql_demo

        return generate_sql_demo(schema_def, question)

    monkeypatch.setattr("main.provider_access_token", lambda: "server-secret")
    monkeypatch.setattr("main.get_model", lambda: object())
    monkeypatch.setattr("main.analyze_query_with_gemini", analyze)
    monkeypatch.setattr("main.generate_sql_with_gemini", generate)
    headers = {"Authorization": "Bearer server-secret"}

    analyzed = client.post("/analyze", json=ANALYZE, headers=headers)
    generated = client.post("/generate-sql", json=GENERATE, headers=headers)

    assert analyzed.status_code == 200
    assert generated.status_code == 200
    assert calls == [
        ("analyze", "SELECT * FROM users", "postgresql"),
        ("generate", "list users", "postgresql"),
    ]


def test_authorized_request_without_a_model_stays_on_the_demo_path(monkeypatch):
    calls = []

    async def analyze(*args, **kwargs):
        calls.append(args)
        raise AssertionError("analyze provider called")

    monkeypatch.setattr("main.provider_access_token", lambda: "server-secret")
    monkeypatch.setattr("main.get_model", lambda: None)
    monkeypatch.setattr("main.analyze_query_with_gemini", analyze)

    response = client.post(
        "/analyze",
        json=ANALYZE,
        headers={"Authorization": "Bearer server-secret"},
    )
    assert response.status_code == 200
    assert response.json()["analysis_source"] == "demo"
    assert calls == []
