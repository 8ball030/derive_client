import asyncio
import functools
import time
from http import HTTPStatus
from logging import Logger
from typing import Callable, ParamSpec, Sequence, TypeVar

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError as ReqConnectionError
from requests.exceptions import ConnectTimeout, ReadTimeout, RequestException
from urllib3.util.retry import Retry

from derive_client.utils.logger import get_logger

P = ParamSpec('P')
T = TypeVar('T')

RETRY_STATUS_CODES = {HTTPStatus.REQUEST_TIMEOUT, HTTPStatus.TOO_MANY_REQUESTS} | set(range(500, 600))

RETRY_EXCEPTIONS = (
    ReadTimeout,
    ConnectTimeout,
    ReqConnectionError,
)


def exp_backoff_retry(
    func: Callable[..., T] | None = None,
    *,
    attempts: int = 3,
    initial_delay: float = 1.0,
    exceptions=(Exception,),
) -> T:
    if func is None:
        return lambda f: exp_backoff_retry(f, attempts=attempts, initial_delay=initial_delay, exceptions=exceptions)

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        delay = initial_delay
        for attempt in range(attempts):
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                if attempt == attempts - 1:
                    raise e
                await asyncio.sleep(delay)
                delay *= 2

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
    **kwargs: P.kwargs,
) -> T:
    retries = 0
    start_time = time.time()
    while True:
        try:
            result = func(**kwargs)
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


def is_retryable(e: RequestException) -> bool:
    status = getattr(e.response, "status_code", None)
    if status in RETRY_STATUS_CODES:
        return True
    return bool(isinstance(e, RETRY_EXCEPTIONS))
