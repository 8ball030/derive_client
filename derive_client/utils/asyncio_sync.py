import asyncio
import inspect
import threading
from concurrent.futures import TimeoutError as _TimeoutError
from typing import Any, Optional

_bg = {"loop": None, "thread": None, "started": False, "start_ev": threading.Event()}
_start_lock = threading.Lock()


def _start_bg_loop() -> None:
    if _bg["loop"] is not None and _bg["started"]:
        return
    with _start_lock:
        if _bg["loop"] is not None and _bg["started"]:
            return

        def _run() -> None:
            loop = asyncio.new_event_loop()
            _bg["loop"] = loop
            asyncio.set_event_loop(loop)
            _bg["start_ev"].set()
            _bg["started"] = True
            try:
                loop.run_forever()
            finally:
                try:
                    pending = asyncio.all_tasks(loop=loop)
                    for t in pending:
                        t.cancel()
                    loop.run_until_complete(loop.shutdown_asyncgens())
                finally:
                    loop.close()
                    _bg["loop"] = None
                    _bg["started"] = False
                    _bg["start_ev"].clear()

        t = threading.Thread(target=_run, name="bg-async-loop", daemon=True)
        t.start()
        _bg["thread"] = t
        _bg["start_ev"].wait(timeout=5)
        if not _bg["started"]:
            raise RuntimeError("Failed to start background loop")


def run_coroutine_sync(coro: object, timeout: Optional[float] = None) -> Any:
    """Run coroutine on the single background loop and block until result."""

    _start_bg_loop()
    loop = _bg["loop"]

    if inspect.iscoroutine(coro):
        fut = asyncio.run_coroutine_threadsafe(coro, loop)
    else:

        async def _await_it():
            return await coro

        fut = asyncio.run_coroutine_threadsafe(_await_it(), loop)

    try:
        return fut.result(timeout)
    except _TimeoutError:
        fut.cancel()
        raise
