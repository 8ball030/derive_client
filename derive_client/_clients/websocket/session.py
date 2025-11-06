from __future__ import annotations

import json
import uuid
import weakref
from logging import Logger

import requests
from requests.adapters import HTTPAdapter, Retry

from websockets.sync.client import ClientConnection, connect


class WebsocketSession:
    """HTTP session."""

    def __init__(self,
                 logger: Logger,
                 ws_address: str
                 ):
        self._logger = logger

        self._ws_session: ClientConnection | None = None
        self._finalizer = weakref.finalize(self, self._finalize)
        self._ws_address = ws_address

    def open(self) -> ClientConnection:
        """Lazy session creation"""

        if self._ws_session is not None:
            return self._ws_session

        session = connect(self._ws_address)
        self._ws_session = session
        return self._ws_session

    def close(self):
        """Explicit cleanup"""

        if self._ws_session is None:
            return

        self._ws_session.close()
        self._ws_session = None

    def _send_request(
        self,
        url: str,
        data: bytes,
    ) -> bool:
        session = self.open()
        id = str(uuid.uuid4())

        try:
            session.send(json.dumps({
                "id": id,
                "method": "url",
                "params": data,
            }).encode('utf-8'),)
            return True
        except requests.RequestException as e:
            self._logger.error("Websocket request failed: %s -> %s", url, e)
            return False


    def _finalize(self):
        if self._ws_session:
            msg = "%s was garbage collected without explicit close(); closing session automatically"
            self._logger.debug(msg, self.__class__.__name__)
            try:
                self._ws_session.close()
            except Exception:
                self._logger.exception("Error closing session in finalizer")
            self._ws_session = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

