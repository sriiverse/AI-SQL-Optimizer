"""Reject oversized HTTP bodies before the application reads them.

A declared Content-Length above the ceiling is rejected without reading.
Every other body is counted from the bytes actually received. A declared
length at or below the ceiling does not skip that count. Accepted bodies are
replayed unchanged.
"""

from starlette.datastructures import Headers
from starlette.responses import JSONResponse

_BODY_METHODS = {"POST", "PUT", "PATCH"}


def _reject(scope, receive, send, status_code: int, detail: str):
    response = JSONResponse({"detail": detail}, status_code=status_code)
    return response(scope, receive, send)


class BodySizeLimitMiddleware:
    def __init__(self, app, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("method") not in _BODY_METHODS:
            await self.app(scope, receive, send)
            return

        raw_length = Headers(scope=scope).get("content-length")
        if raw_length is not None:
            try:
                length = int(raw_length)
            except ValueError:
                await _reject(scope, receive, send, 400, "Invalid Content-Length.")
                return
            if length < 0:
                await _reject(scope, receive, send, 400, "Invalid Content-Length.")
                return
            if length > self.max_bytes:
                # Do not call receive. The application and providers never see this body.
                await _reject(scope, receive, send, 413, "Request body is too large.")
                return

        chunks = []
        total = 0
        while True:
            message = await receive()
            if message["type"] != "http.request":
                chunks.append(message)
                break
            body = message.get("body", b"") or b""
            total += len(body)
            if total > self.max_bytes:
                await _reject(scope, receive, send, 413, "Request body is too large.")
                return
            chunks.append(message)
            if not message.get("more_body", False):
                break

        index = 0

        async def replay():
            nonlocal index
            if index < len(chunks):
                message = chunks[index]
                index += 1
                return message
            return {"type": "http.request", "body": b"", "more_body": False}

        await self.app(scope, replay, send)
