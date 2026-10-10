"""Request ceilings read when this module is imported.

Malformed values raise immediately. They do not fall back to unlimited input,
an unlimited body, a missing timeout, or a disabled rate limit.
"""

import math
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MAX_QUERY_CHARS = 20_000
DEFAULT_MAX_SCHEMA_CHARS = 100_000
DEFAULT_MAX_QUESTION_CHARS = 4_000
DEFAULT_MAX_BODY_BYTES = 256 * 1024
DEFAULT_ANALYSIS_TIMEOUT_SECONDS = 30.0
DEFAULT_GENERATION_TIMEOUT_SECONDS = 45.0
DEFAULT_RATE_LIMIT_REQUESTS = 20
DEFAULT_RATE_LIMIT_WINDOW_SECONDS = 60.0
DEFAULT_RATE_LIMIT_MAX_KEYS = 10_000


def parse_positive_int(name: str, raw: Optional[str], default: int) -> int:
    """Return default when raw is missing or blank. Reject every other invalid value."""
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw.strip())
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a positive integer") from exc
    if value < 1:
        raise RuntimeError(f"{name} must be a positive integer")
    return value


def parse_positive_float(name: str, raw: Optional[str], default: float) -> float:
    """Return default when raw is missing or blank. Reject zero, negatives, and non-finite values."""
    if raw is None or raw.strip() == "":
        return default
    try:
        value = float(raw.strip())
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a positive number") from exc
    if not math.isfinite(value) or value <= 0:
        raise RuntimeError(f"{name} must be a positive number")
    return value


MAX_QUERY_CHARS = parse_positive_int(
    "MAX_QUERY_CHARS", os.environ.get("MAX_QUERY_CHARS"), DEFAULT_MAX_QUERY_CHARS
)
MAX_SCHEMA_CHARS = parse_positive_int(
    "MAX_SCHEMA_CHARS", os.environ.get("MAX_SCHEMA_CHARS"), DEFAULT_MAX_SCHEMA_CHARS
)
MAX_QUESTION_CHARS = parse_positive_int(
    "MAX_QUESTION_CHARS", os.environ.get("MAX_QUESTION_CHARS"), DEFAULT_MAX_QUESTION_CHARS
)
MAX_BODY_BYTES = parse_positive_int(
    "MAX_BODY_BYTES", os.environ.get("MAX_BODY_BYTES"), DEFAULT_MAX_BODY_BYTES
)
ANALYSIS_TIMEOUT_SECONDS = parse_positive_float(
    "ANALYSIS_TIMEOUT_SECONDS",
    os.environ.get("ANALYSIS_TIMEOUT_SECONDS"),
    DEFAULT_ANALYSIS_TIMEOUT_SECONDS,
)
GENERATION_TIMEOUT_SECONDS = parse_positive_float(
    "GENERATION_TIMEOUT_SECONDS",
    os.environ.get("GENERATION_TIMEOUT_SECONDS"),
    DEFAULT_GENERATION_TIMEOUT_SECONDS,
)
RATE_LIMIT_REQUESTS = parse_positive_int(
    "RATE_LIMIT_REQUESTS", os.environ.get("RATE_LIMIT_REQUESTS"), DEFAULT_RATE_LIMIT_REQUESTS
)
RATE_LIMIT_WINDOW_SECONDS = parse_positive_float(
    "RATE_LIMIT_WINDOW_SECONDS",
    os.environ.get("RATE_LIMIT_WINDOW_SECONDS"),
    DEFAULT_RATE_LIMIT_WINDOW_SECONDS,
)
RATE_LIMIT_MAX_KEYS = parse_positive_int(
    "RATE_LIMIT_MAX_KEYS", os.environ.get("RATE_LIMIT_MAX_KEYS"), DEFAULT_RATE_LIMIT_MAX_KEYS
)


def analysis_timeout_seconds() -> float:
    return ANALYSIS_TIMEOUT_SECONDS


def generation_timeout_seconds() -> float:
    return GENERATION_TIMEOUT_SECONDS
