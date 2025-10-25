import asyncio
import weakref

import aiohttp

from derive_client._clients.logger import logger
from derive_client.constants import PUBLIC_HEADERS


class AsyncHTTPSession:
    def __init__(self, request_timeout: float):
        self._request_timeout = request_timeout

        self._connector: aiohttp.TCPConnector | None = None
        self._aiohttp_session: aiohttp.ClientSession | None = None
        self._lock = asyncio.Lock()
        self._finalizer = weakref.finalize(self, self._finalize)

    async def open(self) -> None:
        """Explicit session creation."""

        if self._aiohttp_session and not self._aiohttp_session.closed:
            return

        async with self._lock:
            if self._aiohttp_session and not self._aiohttp_session.closed:
                return

            self._connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=10,
                keepalive_timeout=30,
                enable_cleanup_closed=True,
            )

            self._aiohttp_session = aiohttp.ClientSession(connector=self._connector)

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
                logger.exception("Error closing session")

        if connector and not connector.closed:
            try:
                await connector.close()
            except Exception:
                logger.exception("Error closing connector")

    async def _send_request(
        self,
        url: str,
        data: bytes,
        *,
        headers: dict | None = None,
        timeout: float | None = None,
    ):
        await self.open()

        headers = headers or PUBLIC_HEADERS
        total = timeout or self._request_timeout
        timeout = aiohttp.ClientTimeout(total=total)

        try:
            async with self._aiohttp_session.post(url, data=data, headers=headers, timeout=timeout) as response:
                response.raise_for_status()
                try:
                    return await response.content.read()
                except Exception as e:
                    raise ValueError(f"Failed to decode JSON from {url}: {e}") from e
        except aiohttp.ClientError as e:
            logger.error("HTTP request failed: %s -> %s", url, e)
            raise

    def _finalize(self):
        if self._aiohttp_session and not self._aiohttp_session.closed:
            msg = "%s was garbage collected with an open session. Session will be closed by process exit if needed."
            logger.debug(msg, self.__class__.__name__)

    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
