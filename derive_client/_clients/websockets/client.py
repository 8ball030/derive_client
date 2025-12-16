"""
Synchronous WebSocket client for Derive.
"""

from __future__ import annotations

import contextlib
from logging import Logger
from pathlib import Path
from typing import Generator

from pydantic import ConfigDict, validate_call
from web3 import Web3

from derive_client._clients.utils import AuthContext, load_client_config
from derive_client._clients.websockets.api import PrivateAPI, PublicAPI
from derive_client._clients.websockets.session import WebSocketSession
from derive_client.config import CONFIGS
from derive_client.data_types import ChecksumAddress, Environment
from derive_client.data_types.generated_models import PublicLoginParamsSchema
from derive_client.utils.logger import get_logger


class WebSocketClient:
    """Synchronous WebSocket client for real-time data streams."""

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        *,
        wallet: ChecksumAddress | str,
        session_key: str,
        subaccount_id: int,
        env: Environment,
        logger: Logger | None = None,
        request_timeout: float = 10.0,
    ):
        config = CONFIGS[env]
        w3 = Web3(Web3.HTTPProvider(config.rpc_endpoint))
        account = w3.eth.account.from_key(session_key)

        auth = AuthContext(
            w3=w3,
            wallet=ChecksumAddress(wallet),
            account=account,
            config=config,
        )

        self._env = env
        self._auth = auth
        self._config = config
        self._subaccount_id = subaccount_id

        self._logger = logger if logger is not None else get_logger()
        self._session = WebSocketSession(
            url=config.ws_address,
            request_timeout=request_timeout,
            logger=self._logger,
        )

        self._public_api = PublicAPI(session=self._session)
        self._private_api = PrivateAPI(session=self._session)

    @classmethod
    def from_env(
        cls,
        session_key_path: Path | None = None,
        env_file: Path | None = None,
    ) -> WebSocketClient:
        """Create WebSocketClient from environment configuration."""

        config = load_client_config(session_key_path=session_key_path, env_file=env_file)
        return cls(**config.model_dump())

    def connect(self) -> None:
        """Establish WebSocket connection."""
        self._session.open()
        params = PublicLoginParamsSchema(**self._auth.sign_ws_login())
        subaccount_ids = self._public_api.rpc.login(params=params)
        self._logger.debug(f"Websocket login returned subaccount ids: {subaccount_ids}")

    def disconnect(self) -> None:
        """Close WebSocket connection and clear subscriptions. Idempotent."""
        self._session.close()

    def unsubscribe(self, channels: list[str] | str) -> None:
        """Unsubscribe from a channel.

        Args:
            channels: Single channel name or list of channel names
        """
        self._session.unsubscribe(channels)

    @contextlib.contextmanager
    def timeout(self, seconds: float) -> Generator[None, None, None]:
        """Temporarily override request timeout for RPC calls."""

        prev = self._session._request_timeout
        try:
            self._session._request_timeout = float(seconds)
            yield
        finally:
            self._session._request_timeout = prev

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
