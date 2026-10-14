"""Keep history, the agent, and paid providers off unless a test overrides them."""

import pytest


@pytest.fixture(autouse=True)
def _history_and_agent_default_off(monkeypatch):
    # Override the feature functions. Do not change os.environ after import.
    monkeypatch.setattr("main.history_enabled", lambda: False)
    monkeypatch.setattr("main.agent_enabled", lambda: False)
    monkeypatch.setattr("main.provider_access_token", lambda: None)


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    from rate_limit import limiter

    limiter.reset()
    yield
    limiter.reset()
