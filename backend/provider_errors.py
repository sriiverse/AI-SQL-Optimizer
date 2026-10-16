"""Provider failures stay out of API responses and process logs."""

import logging

_KNOWN_EXCEPTION_NAMES = frozenset({
    "Exception",
    "RuntimeError",
    "ValueError",
    "TypeError",
    "KeyError",
    "TimeoutError",
    "JSONDecodeError",
    "HTTPException",
    "RequestException",
    "WebSocketException",
    "PermissionDenied",
    "Forbidden",
    "ResourceExhausted",
    "GoogleAPICallError",
    "GoogleAPIError",
    "ClientError",
    "APIError",
    "APIConnectionError",
    "APIStatusError",
    "APITimeoutError",
    "RateLimitError",
    "AuthenticationError",
    "BadRequestError",
    "InternalServerError",
})


def _safe_exception_name(exc: BaseException) -> str:
    """Only ordinary exception types are logged. A class name is not trusted."""
    name = type(exc).__name__
    if name in _KNOWN_EXCEPTION_NAMES:
        return name
    return "Exception"

SAFE_ANALYSIS_MESSAGES = frozenset({
    "AI analysis timed out.",
    "AI analysis failed.",
    "AI analysis failed after the fallback provider returned an error.",
    "AI analysis failed because the primary provider was unavailable and no fallback provider is configured.",
    "The model response could not be read.",
})

SAFE_GENERATION_MESSAGES = frozenset({
    "AI generation timed out.",
    "AI generation failed.",
    "AI generation failed after the fallback provider returned an error.",
    "AI generation failed because the primary provider was unavailable and no fallback provider is configured.",
    "The model response could not be read.",
})


def _status_code(exc: BaseException):
    for name in ("code", "status_code"):
        value = getattr(exc, name, None)
        if isinstance(value, int):
            return value
    return None


def is_quota_error(exc: BaseException) -> bool:
    """True for a rate-limit response. The provider message is not logged."""
    if _status_code(exc) == 429:
        return True
    message = str(exc).lower()
    return "429" in message or "quota" in message or "resource_exhausted" in message


def log_provider_failure(logger: logging.Logger, event: str, exc: BaseException) -> None:
    """Record a generic type and status only. Never the exception text or class name."""
    code = _status_code(exc)
    label = _safe_exception_name(exc)
    if code is None:
        logger.warning("%s (%s)", event, label)
        return
    logger.warning("%s (%s status=%s)", event, label, code)


def public_provider_detail(explanation: str, allowed: frozenset, fallback: str) -> str:
    if explanation in allowed:
        return explanation
    return fallback
