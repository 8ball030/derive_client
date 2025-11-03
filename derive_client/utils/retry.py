import asyncio
import functools
import time
from logging import Logger
from typing import Awaitable, Callable, Optional, ParamSpec, Sequence, TypeVar, overload

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from derive_client.utils.logger import get_logger

P = ParamSpec('P')
T = TypeVar('T')


@overload
def exp_backoff_retry(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]: ...


@overload
def exp_backoff_retry(
    *,
    attempts: int = ...,
    initial_delay: float = ...,
    exceptions: tuple[type[BaseException], ...] = ...,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]: ...


@overload
def exp_backoff_retry(
    func: Callable[P, Awaitable[T]],
    *,
    attempts: int = ...,
    initial_delay: float = ...,
    exceptions: tuple[type[BaseException], ...] = ...,
) -> Callable[P, Awaitable[T]]: ...


def exp_backoff_retry(
    func: Optional[Callable[P, Awaitable[T]]] = None,
    *,
    attempts: int = 3,
    initial_delay: float = 1.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[P, Awaitable[T]] | Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    if func is None:

        def _decorator(f: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
            return exp_backoff_retry(f, attempts=attempts, initial_delay=initial_delay, exceptions=exceptions)

        return _decorator

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        delay = initial_delay
        for attempt in range(attempts):
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                if attempt == attempts - 1:
                    raise e
                await asyncio.sleep(delay)
                delay *= 2

        raise RuntimeError("Should never reach here")

    return wrapper


@functools.lru_cache
def get_retry_session(
    total_retries: int = 5,
    backoff_factor: float = 1.0,
    status_forcelist: Sequence[int] = (429, 500, 502, 503, 504),
    allowed_methods: Sequence[str] = (
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "HEAD",
        "OPTIONS",
    ),
    raise_on_status: bool = False,
    logger: Logger | None = None,
) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=total_retries,
        read=total_retries,
        connect=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=list(status_forcelist),
        allowed_methods=list(allowed_methods),
        respect_retry_after_header=True,
        raise_on_status=raise_on_status,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    logger = logger or get_logger()

    def log_response(r, *args, **kwargs):
        logger.info(f"Response {r.request.method} {r.url} (status {r.status_code})")

    session.hooks["response"] = [log_response]
    return session


def wait_until(
    func: Callable[P, T],
    condition: Callable[[T], bool],
    timeout: float = 60.0,
    poll_interval=1.0,
    retry_exceptions: type[Exception] | tuple[type[Exception], ...] = (ConnectionError, TimeoutError),
    max_retries: int = 3,
    timeout_message: str = "",
    *args: P.args,
    **kwargs: P.kwargs,
) -> T:
    retries = 0
    start_time = time.time()
    while True:
        try:
            result = func(*args, **kwargs)
        except retry_exceptions:
            retries += 1
            if retries >= max_retries:
                raise
            poll_interval *= 2
            result = None
        if result is not None and condition(result):
            return result
        if time.time() - start_time > timeout:
            msg = f"Timed out after {timeout}s waiting for condition on {func.__name__} {timeout_message}"
            raise TimeoutError(msg)
        time.sleep(poll_interval)
