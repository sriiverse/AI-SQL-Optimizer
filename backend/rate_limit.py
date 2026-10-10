"""Process-local sliding window for the analysis and generation routes.

This limiter is not shared across workers or machines. A deployment with more
than one process has a separate budget in each process. There is no trusted
proxy configuration in this project, so the key is the direct client address.
X-Forwarded-For is ignored.
"""

import time
from collections import deque

from starlette.responses import JSONResponse

from safety_config import (
    RATE_LIMIT_MAX_KEYS,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
)

LIMITED_PATHS = {"/analyze", "/generate-sql"}


class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: float, max_keys: int, clock=None):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self.clock = clock or time.monotonic
        self._events = {}
        self._last_seen = {}

    def reset(self) -> None:
        self._events.clear()
        self._last_seen.clear()

    def allow(self, key: str) -> bool:
        now = self.clock()
        self._drop_expired(now)
        events = self._events.get(key)
        if events is None:
            if len(self._events) >= self.max_keys:
                self._evict_oldest()
            events = deque()
            self._events[key] = events
        if len(events) >= self.max_requests:
            self._last_seen[key] = now
            return False
        events.append(now)
        self._last_seen[key] = now
        return True

    def _drop_expired(self, now: float) -> None:
        cutoff = now - self.window_seconds
        empty = []
        for key, events in self._events.items():
            while events and events[0] <= cutoff:
                events.popleft()
            if not events:
                empty.append(key)
        for key in empty:
            self._events.pop(key, None)
            self._last_seen.pop(key, None)

    def _evict_oldest(self) -> None:
        if not self._last_seen:
            return
        oldest = min(self._last_seen, key=self._last_seen.get)
        self._events.pop(oldest, None)
        self._last_seen.pop(oldest, None)


limiter = SlidingWindowLimiter(
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
    RATE_LIMIT_MAX_KEYS,
)


def direct_client_ip(scope) -> str:
    client = scope.get("client")
    if not client or not client[0]:
        return "unknown"
    return str(client[0])


class RateLimitMiddleware:
    def __init__(self, app, limiter: SlidingWindowLimiter):
        self.app = app
        self.limiter = limiter

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        if scope.get("method") != "POST" or scope.get("path") not in LIMITED_PATHS:
            await self.app(scope, receive, send)
            return
        if not self.limiter.allow(direct_client_ip(scope)):
            response = JSONResponse(
                {"detail": "Rate limit exceeded. Try again later."},
                status_code=429,
            )
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)
