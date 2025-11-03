from __future__ import annotations

import weakref
from logging import Logger

import requests
from requests.adapters import HTTPAdapter, Retry


class HTTPSession:
    """HTTP session."""

    def __init__(self, request_timeout: float, logger: Logger):
        self._request_timeout = request_timeout
        self._logger = logger

        self._requests_session: requests.Session | None = None
        self._finalizer = weakref.finalize(self, self._finalize)

    def open(self) -> requests.Session:
        """Lazy session creation"""

        if self._requests_session is not None:
            return self._requests_session

        session = requests.Session()

        retry = Retry(
            total=3,
            backoff_factor=0.2,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET", "HEAD", "OPTIONS"]),
        )

        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=retry,
            pool_block=False,
        )

        session.mount("https://", adapter)
        session.mount("http://", adapter)

        self._requests_session = session
        return self._requests_session

    def close(self):
        """Explicit cleanup"""

        if self._requests_session is None:
            return

        self._requests_session.close()
        self._requests_session = None

    def _send_request(
        self,
        url: str,
        data: bytes,
        *,
        headers: dict | None = None,
    ) -> bytes:
        session = self.open()

        timeout = self._request_timeout

        try:
            response = session.post(url, data=data, headers=headers, timeout=timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            self._logger.error("HTTP request failed: %s -> %s", url, e)
            raise

        return response.content

    def _finalize(self):
        if self._requests_session:
            msg = "%s was garbage collected without explicit close(); closing session automatically"
            self._logger.debug(msg, self.__class__.__name__)
            try:
                self._requests_session.close()
            except Exception:
                self._logger.exception("Error closing session in finalizer")
            self._requests_session = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
