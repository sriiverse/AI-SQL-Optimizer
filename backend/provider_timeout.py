"""Deadline for one asynchronous provider attempt."""

import asyncio


class ProviderTimeout(Exception):
    """The provider attempt exceeded its deadline. This is not a quota error."""


async def await_provider(awaitable, timeout_seconds: float):
    """Wait for one attempt. Cancellation stops the attempt; it does not retry it."""
    try:
        return await asyncio.wait_for(awaitable, timeout=timeout_seconds)
    except asyncio.TimeoutError as exc:
        raise ProviderTimeout() from exc
