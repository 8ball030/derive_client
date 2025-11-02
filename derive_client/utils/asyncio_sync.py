import asyncio
import inspect
import threading
from collections.abc import Awaitable, Coroutine
from concurrent.futures import TimeoutError as _TimeoutError
from typing import TypeVar

T = TypeVar('T')


class _BackgroundLoop:
    """Manages a singleton background event loop in a daemon thread."""

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._started: bool = False
        self._start_event = threading.Event()
        self._start_lock = threading.Lock()

    def start(self) -> None:
        """Start the background loop if not already running."""
        if self._loop is not None and self._started:
            return

        with self._start_lock:
            if self._loop is not None and self._started:
                return

            def _run() -> None:
                loop = asyncio.new_event_loop()
                self._loop = loop
                asyncio.set_event_loop(loop)
                self._start_event.set()
                self._started = True
                try:
                    loop.run_forever()
                finally:
                    try:
                        pending = asyncio.all_tasks(loop=loop)
                        for task in pending:
                            task.cancel()
                        loop.run_until_complete(loop.shutdown_asyncgens())
                    finally:
                        loop.close()
                        self._loop = None
                        self._started = False
                        self._start_event.clear()

            thread = threading.Thread(target=_run, name="bg-async-loop", daemon=True)
            thread.start()
            self._thread = thread

            if not self._start_event.wait(timeout=5):
                raise RuntimeError("Failed to start background loop within 5 seconds")

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """Get the background event loop, starting it if necessary."""
        self.start()
        if self._loop is None:
            raise RuntimeError("Background loop failed to start")
        return self._loop


# Singleton instance
_bg_loop = _BackgroundLoop()


def run_coroutine_sync(coro: Coroutine[None, None, T] | Awaitable[T], timeout: float | None = None) -> T:
    """
    Run a coroutine on the background event loop and block until result.

    Args:
        coro: A coroutine or awaitable to execute
        timeout: Optional timeout in seconds

    Returns:
        The result of the coroutine

    Raises:
        TimeoutError: If the operation times out
    """
    loop = _bg_loop.loop

    if inspect.iscoroutine(coro):
        future = asyncio.run_coroutine_threadsafe(coro, loop)
    else:
        # Handle other awaitables
        async def _await_it() -> T:
            return await coro

        future = asyncio.run_coroutine_threadsafe(_await_it(), loop)

    try:
        return future.result(timeout)
    except _TimeoutError:
        future.cancel()
        raise
