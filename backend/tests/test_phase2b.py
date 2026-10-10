"""Phase 2B: input limits, provider deadlines, and per-IP rate limiting."""

import asyncio
import sys
import time
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from analyze import analyze_query_with_gemini
from body_limit import BodySizeLimitMiddleware
from generator import generate_sql_with_gemini
from main import app
from rate_limit import SlidingWindowLimiter
from safety_config import (
    MAX_BODY_BYTES,
    MAX_QUERY_CHARS,
    MAX_QUESTION_CHARS,
    MAX_SCHEMA_CHARS,
    RATE_LIMIT_REQUESTS,
    parse_positive_float,
    parse_positive_int,
)

client = TestClient(app)

MARKER = "secret-marker-should-not-echo"


def _scope(method="POST", path="/analyze", headers=None, client_addr=("203.0.113.8", 4000)):
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": headers or [],
        "client": client_addr,
        "server": ("test", 80),
    }


def _invoke(app, scope, messages):
    sent = []
    pending = list(messages)

    async def receive():
        if pending:
            return pending.pop(0)
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    asyncio.run(app(scope, receive, send))
    return sent


def _status(sent):
    for message in sent:
        if message["type"] == "http.response.start":
            return message["status"]
    return None


def _install_provider_spy(monkeypatch, target):
    calls = []

    async def fake(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("provider should not be called")

    monkeypatch.setattr(target, fake)
    monkeypatch.setattr("main.get_model", lambda: object())
    return calls


def test_malformed_limits_are_rejected():
    with pytest.raises(RuntimeError, match="MAX_QUERY_CHARS"):
        parse_positive_int("MAX_QUERY_CHARS", "abc", 20_000)
    with pytest.raises(RuntimeError, match="MAX_QUERY_CHARS"):
        parse_positive_int("MAX_QUERY_CHARS", "0", 20_000)
    with pytest.raises(RuntimeError, match="MAX_QUERY_CHARS"):
        parse_positive_int("MAX_QUERY_CHARS", "-3", 20_000)
    assert parse_positive_int("MAX_QUERY_CHARS", None, 20_000) == 20_000
    assert parse_positive_int("MAX_QUERY_CHARS", " 40 ", 20_000) == 40
    with pytest.raises(RuntimeError, match="ANALYSIS_TIMEOUT_SECONDS"):
        parse_positive_float("ANALYSIS_TIMEOUT_SECONDS", "inf", 30)
    with pytest.raises(RuntimeError, match="ANALYSIS_TIMEOUT_SECONDS"):
        parse_positive_float("ANALYSIS_TIMEOUT_SECONDS", "0", 30)
    assert parse_positive_float("ANALYSIS_TIMEOUT_SECONDS", "", 30) == 30


def test_oversized_query_schema_question_and_context_are_rejected(monkeypatch):
    analyze_calls = _install_provider_spy(monkeypatch, "main.analyze_query_with_gemini")
    monkeypatch.setattr(
        "main.analyze_query_demo",
        lambda query: (_ for _ in ()).throw(AssertionError("demo analyze called")),
    )
    generate_calls = []

    async def fake_generate(*args, **kwargs):
        generate_calls.append(args)
        raise AssertionError("provider should not be called")

    monkeypatch.setattr("main.generate_sql_with_gemini", fake_generate)
    monkeypatch.setattr(
        "main.generate_sql_demo",
        lambda schema, question: (_ for _ in ()).throw(AssertionError("demo generate called")),
    )

    query = client.post(
        "/analyze",
        json={"query": MARKER + ("q" * MAX_QUERY_CHARS), "dialect": "postgresql"},
    )
    assert query.status_code == 422
    assert "Query exceeds the maximum length" in query.text
    assert MARKER not in query.text

    context = client.post(
        "/analyze",
        json={
            "query": "SELECT 1",
            "schema_context": MARKER + ("s" * MAX_SCHEMA_CHARS),
            "dialect": "postgresql",
        },
    )
    assert context.status_code == 422
    assert "Schema exceeds the maximum length" in context.text
    assert MARKER not in context.text

    schema = client.post(
        "/generate-sql",
        json={
            "schema_def": MARKER + ("s" * MAX_SCHEMA_CHARS),
            "question": "list users",
            "dialect": "mysql",
        },
    )
    assert schema.status_code == 422
    assert "Schema exceeds the maximum length" in schema.text
    assert MARKER not in schema.text

    question = client.post(
        "/generate-sql",
        json={
            "schema_def": "CREATE TABLE users (id INT)",
            "question": MARKER + ("n" * MAX_QUESTION_CHARS),
            "dialect": "sqlite",
        },
    )
    assert question.status_code == 422
    assert "Question exceeds the maximum length" in question.text
    assert MARKER not in question.text
    assert analyze_calls == []
    assert generate_calls == []


def test_query_at_the_character_ceiling_is_accepted(monkeypatch):
    monkeypatch.setattr("main.get_model", lambda: None)
    response = client.post(
        "/analyze",
        json={"query": "x" * MAX_QUERY_CHARS, "dialect": "postgresql"},
    )
    assert response.status_code == 200
    assert response.json()["analysis_source"] == "demo"


def test_supported_dialects_remain_accepted_and_unknown_dialects_are_rejected(monkeypatch):
    calls = _install_provider_spy(monkeypatch, "main.analyze_query_with_gemini")
    rejected = client.post(
        "/analyze",
        json={"query": "SELECT 1", "dialect": "oracle"},
    )
    assert rejected.status_code == 422
    assert "postgresql, mysql, sqlite, mongodb" in rejected.text
    assert calls == []

    monkeypatch.setattr("main.get_model", lambda: None)
    for dialect in ("postgresql", "PostgreSQL", "mysql", "sqlite", "mongodb"):
        response = client.post(
            "/analyze",
            json={"query": "SELECT 1", "dialect": dialect},
        )
        assert response.status_code == 200, dialect
        assert response.json()["analysis_source"] == "demo"


def test_oversized_declared_body_is_413_without_reading_or_calling_provider(monkeypatch):
    calls = _install_provider_spy(monkeypatch, "main.analyze_query_with_gemini")
    body = (MARKER + ("x" * MAX_BODY_BYTES)).encode()
    response = client.post(
        "/analyze",
        content=body,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413
    assert response.json() == {"detail": "Request body is too large."}
    assert MARKER not in response.text
    assert calls == []

    entered = False

    async def inner(scope, receive, send):
        nonlocal entered
        entered = True
        await receive()

    middleware = BodySizeLimitMiddleware(inner, max_bytes=16)
    sent = _invoke(
        middleware,
        _scope(headers=[(b"content-length", b"100")]),
        [],
    )
    assert entered is False
    assert _status(sent) == 413


def test_chunked_body_over_limit_does_not_reach_the_app_and_small_chunks_are_replayed():
    entered = False

    async def blocked(scope, receive, send):
        nonlocal entered
        entered = True

    blocked_sent = _invoke(
        BodySizeLimitMiddleware(blocked, max_bytes=16),
        _scope(),
        [{"type": "http.request", "body": b"x" * 50, "more_body": False}],
    )
    assert entered is False
    assert _status(blocked_sent) == 413

    seen = []

    async def replayed(scope, receive, send):
        while True:
            message = await receive()
            if message["type"] != "http.request":
                break
            seen.append(message.get("body", b""))
            if not message.get("more_body", False):
                break
        await JSONResponse({"ok": True})(scope, receive, send)

    replay_sent = _invoke(
        BodySizeLimitMiddleware(replayed, max_bytes=16),
        _scope(),
        [
            {"type": "http.request", "body": b"abc", "more_body": True},
            {"type": "http.request", "body": b"def", "more_body": False},
        ],
    )
    assert b"".join(seen) == b"abcdef"
    assert _status(replay_sent) == 200

    passed = []

    async def declared(scope, receive, send):
        message = await receive()
        passed.append(message.get("body"))
        await JSONResponse({"ok": True})(scope, receive, send)

    declared_sent = _invoke(
        BodySizeLimitMiddleware(declared, max_bytes=16),
        _scope(headers=[(b"content-length", b"3")]),
        [{"type": "http.request", "body": b"abc", "more_body": False}],
    )
    assert passed == [b"abc"]
    assert _status(declared_sent) == 200


def test_invalid_content_length_is_rejected():
    entered = False

    async def inner(scope, receive, send):
        nonlocal entered
        entered = True

    sent = _invoke(
        BodySizeLimitMiddleware(inner, max_bytes=16),
        _scope(headers=[(b"content-length", b"nope")]),
        [],
    )
    assert entered is False
    assert _status(sent) == 400


def test_analysis_timeout_returns_a_controlled_error_without_fallback(monkeypatch):
    monkeypatch.setattr("analyze.analysis_timeout_seconds", lambda: 0.05)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    groq_calls = []

    class _Groq:
        def __init__(self, api_key=None, timeout=None):
            groq_calls.append(timeout)

    monkeypatch.setitem(sys.modules, "groq", SimpleNamespace(AsyncGroq=_Groq))
    seen = {}

    class HangingModel:
        async def generate_content_async(self, prompt, request_options=None):
            seen["options"] = request_options
            await asyncio.sleep(5)

    started = time.monotonic()
    result = asyncio.run(
        analyze_query_with_gemini("SELECT 1", "postgresql", HangingModel())
    )
    elapsed = time.monotonic() - started

    assert elapsed < 2
    assert seen["options"] == {"timeout": 0.05}
    assert groq_calls == []
    assert result.analysis_source == "error"
    assert result.plan_origin == "none"
    assert result.explanation == "AI analysis timed out."
    assert "test-key" not in result.explanation
    assert "Traceback" not in result.explanation


def test_generation_timeout_returns_a_controlled_error(monkeypatch):
    monkeypatch.setattr("generator.generation_timeout_seconds", lambda: 0.05)

    class HangingModel:
        async def generate_content_async(self, prompt, request_options=None):
            await asyncio.sleep(5)

    started = time.monotonic()
    result = asyncio.run(
        generate_sql_with_gemini(
            "CREATE TABLE users (id INT)",
            "list users",
            "postgresql",
            HangingModel(),
        )
    )
    assert time.monotonic() - started < 2
    assert result.analysis_source == "error"
    assert result.query == "ERROR"
    assert result.explanation == "AI generation timed out."
    assert "Traceback" not in result.explanation


def test_quota_fallback_is_one_groq_attempt_and_its_timeout_does_not_retry(monkeypatch):
    monkeypatch.setattr("analyze.analysis_timeout_seconds", lambda: 0.05)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    creates = {"n": 0}

    class _Completions:
        async def create(self, **kwargs):
            creates["n"] += 1
            await asyncio.sleep(5)

    class _Groq:
        def __init__(self, api_key=None, timeout=None):
            self.chat = SimpleNamespace(completions=_Completions())

    monkeypatch.setitem(sys.modules, "groq", SimpleNamespace(AsyncGroq=_Groq))

    class QuotaModel:
        async def generate_content_async(self, prompt, request_options=None):
            raise RuntimeError("429 quota exceeded")

    started = time.monotonic()
    result = asyncio.run(
        analyze_query_with_gemini("SELECT 1", "postgresql", QuotaModel())
    )
    assert time.monotonic() - started < 2
    assert creates["n"] == 1
    assert result.explanation == "AI analysis timed out."
    assert "429" not in result.explanation

    creates["n"] = 0

    class _FailingCompletions:
        async def create(self, **kwargs):
            creates["n"] += 1
            raise RuntimeError("429 quota from fallback")

    class _FailingGroq:
        def __init__(self, api_key=None, timeout=None):
            self.chat = SimpleNamespace(completions=_FailingCompletions())

    monkeypatch.setitem(sys.modules, "groq", SimpleNamespace(AsyncGroq=_FailingGroq))
    failed = asyncio.run(
        analyze_query_with_gemini("SELECT 1", "postgresql", QuotaModel())
    )
    assert creates["n"] == 1
    assert failed.analysis_source == "error"
    assert "429" not in failed.explanation
    assert "quota from fallback" not in failed.explanation


def test_rate_limit_boundary_ignores_forwarded_for_and_skips_health(monkeypatch):
    calls = []

    async def fake(query, dialect, model):
        calls.append(query)
        from analyze import analyze_query_demo

        return analyze_query_demo(query)

    monkeypatch.setattr("main.get_model", lambda: object())
    monkeypatch.setattr("main.analyze_query_with_gemini", fake)

    for index in range(RATE_LIMIT_REQUESTS):
        response = client.post(
            "/analyze",
            json={"query": "SELECT 1", "dialect": "postgresql"},
            headers={"X-Forwarded-For": f"198.51.100.{index}"},
        )
        assert response.status_code == 200

    blocked = client.post(
        "/analyze",
        json={"query": MARKER, "dialect": "postgresql"},
        headers={"X-Forwarded-For": "203.0.113.50"},
    )
    assert blocked.status_code == 429
    assert blocked.json() == {"detail": "Rate limit exceeded. Try again later."}
    assert MARKER not in blocked.text
    assert len(calls) == RATE_LIMIT_REQUESTS

    for _ in range(RATE_LIMIT_REQUESTS + 5):
        assert client.get("/health").status_code == 200
        assert client.get("/ping").status_code == 200


def test_limiter_window_keys_and_distinct_addresses_do_not_wait():
    now = [0.0]
    window = SlidingWindowLimiter(1, 60, 10, clock=lambda: now[0])
    assert window.allow("10.0.0.1") is True
    assert window.allow("10.0.0.1") is False
    now[0] = 59.0
    assert window.allow("10.0.0.1") is False
    now[0] = 60.0
    assert window.allow("10.0.0.1") is True

    separate = SlidingWindowLimiter(2, 60, 10, clock=lambda: 0.0)
    assert separate.allow("10.0.0.1") is True
    assert separate.allow("10.0.0.2") is True
    assert separate.allow("10.0.0.1") is True
    assert separate.allow("10.0.0.1") is False
    assert separate.allow("10.0.0.2") is True

    bounded = SlidingWindowLimiter(2, 60, 10, clock=lambda: 0.0)
    assert bounded.allow("a") is True
    assert bounded.allow("a") is True
    for _ in range(100):
        assert bounded.allow("a") is False
    assert len(bounded._events["a"]) == 2

    evicting = SlidingWindowLimiter(5, 60, 2, clock=lambda: 0.0)
    assert evicting.allow("a") is True
    assert evicting.allow("b") is True
    assert evicting.allow("c") is True
    assert len(evicting._events) == 2
    assert "a" not in evicting._events
    assert "c" in evicting._events
