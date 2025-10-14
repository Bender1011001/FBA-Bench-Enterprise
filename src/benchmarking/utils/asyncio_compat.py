from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any, TypeVar

T = TypeVar("T")


def ensure_event_loop() -> asyncio.AbstractEventLoop:
    """
    Ensure and return an event loop for the current thread.

    Behavior:
    - If a running loop exists (async context), return it.
    - Else attempt to get the default loop (may raise on Python 3.12+).
    - If unavailable, create a new loop and set it as the current loop.

    Notes:
    - Python 3.12 on Windows may not create a default event loop in MainThread for sync contexts,
      which causes constructs like asyncio.Future() to fail with
      "There is no current event loop in thread 'MainThread'".
    - This helper ensures a loop is present in both sync and async contexts.
    """
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        # Not in a running loop; try to get the default loop or create a new one.
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        else:
            if loop is None:  # Defensive; some environments may return None
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        return loop


def create_future() -> asyncio.Future[Any]:
    """
    Create a Future bound to a valid event loop.

    Safe to call in synchronous test/runtime code across Python versions and OSes.
    """
    return ensure_event_loop().create_future()


def ensure_task(coro: Coroutine[Any, Any, T]) -> asyncio.Task[T]:
    """
    Schedule a coroutine as a Task on a valid event loop.

    - If a loop is running, schedules on the running loop.
    - If not, ensures a loop exists and schedules the task.
    """
    return ensure_event_loop().create_task(coro)
