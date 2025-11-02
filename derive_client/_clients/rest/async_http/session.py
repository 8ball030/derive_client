import asyncio
import contextvars
import weakref
from logging import Logger

import aiohttp

# Context-local timeout (task-scoped) used to temporarily override session timeout.
_request_timeout_override: contextvars.ContextVar[float | None] = contextvars.ContextVar(
    '_request_timeout_override', default=None
)


class AsyncHTTPSession:
    def __init__(self, request_timeout: float, logger: Logger):
        self._request_timeout = request_timeout
        self._logger = logger

        self._connector: aiohttp.TCPConnector | None = None
        self._aiohttp_session: aiohttp.ClientSession | None = None
        self._lock = asyncio.Lock()
        self._finalizer = weakref.finalize(self, self._finalize)

    async def open(self) -> aiohttp.ClientSession:
        """Explicit session creation."""

        if self._aiohttp_session and not self._aiohttp_session.closed:
            return self._aiohttp_session

        async with self._lock:
            if self._aiohttp_session and not self._aiohttp_session.closed:
                return self._aiohttp_session

            self._connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=10,
                keepalive_timeout=30,
                enable_cleanup_closed=True,
            )

            self._aiohttp_session = aiohttp.ClientSession(connector=self._connector)
            return self._aiohttp_session

    async def close(self):
        """Explicit cleanup"""

        async with self._lock:
            session = self._aiohttp_session
            connector = self._connector
            self._aiohttp_session = None
            self._connector = None

        if session and not session.closed:
            try:
                await session.close()
            except Exception:
                self._logger.exception("Error closing session")

        if connector and not connector.closed:
            try:
                await connector.close()
            except Exception:
                self._logger.exception("Error closing connector")

    async def _send_request(
        self,
        url: str,
        data: bytes,
        *,
        headers: dict | None = None,
    ) -> bytes:
        session = await self.open()

        total = _request_timeout_override.get() or self._request_timeout

        timeout = aiohttp.ClientTimeout(total=total)

        try:
            async with session.post(url, data=data, headers=headers, timeout=timeout) as response:
                response.raise_for_status()
                try:
                    return await response.read()
                except Exception as e:
                    raise ValueError(f"Failed to read response from {url}: {e}") from e
        except aiohttp.ClientError as e:
            self._logger.error("HTTP request failed: %s -> %s", url, e)
            raise

    def _finalize(self):
        if self._aiohttp_session and not self._aiohttp_session.closed:
            msg = "%s was garbage collected with an open session. Session will be closed by process exit if needed."
            self._logger.debug(msg, self.__class__.__name__)

    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
