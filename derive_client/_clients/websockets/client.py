"""
Synchronous WebSocket client for Derive.
"""

from __future__ import annotations

import contextlib
from logging import Logger
from pathlib import Path
from typing import Any, Callable, Generator

from derive_client._clients.websockets.channels import PrivateChannels, PublicChannels
from pydantic import ConfigDict, validate_call
from web3 import Web3

from derive_client._clients.utils import AuthContext, load_client_config
from derive_client._clients.websockets.session import WebSocketSession
from derive_client.config import CONFIGS
from derive_client.data_types import ChecksumAddress, Environment
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
            url=config.ws_endpoint,
            request_timeout=request_timeout,
            logger=self._logger,
        )

        # API facades - pass session for subscribe/unsubscribe
        self._public_channels = PublicChannels(session=self._session)
        self._private_channels = PrivateChannels(session=self._session)

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

    def disconnect(self) -> None:
        """Close WebSocket connection and clear subscriptions. Idempotent."""
        self._session.close()

    @property
    def public(self) -> PublicChannels:
        """Access public channel subscriptions."""
        return self._public_channels

    @property
    def private(self) -> PrivateChannels:
        """Access private channel subscriptions."""
        return self._private_channels

    def subscribe(
        self,
        channel: str,
        handler: Callable[[Any], None],
    ) -> None:
        """
        Subscribe to a channel with a handler.

        Low-level API - prefer using `client.public.*` or `client.private.*`

        Args:
            channel: Full channel name (e.g., "BTC-PERP.trades")
            handler: Callback function to handle messages
        """
        self._session.subscribe(channel, handler)

    def unsubscribe(
        self,
        channel: str,
        handler: Callable[[Any], None] | None = None,
    ) -> None:
        """
        Unsubscribe from a channel.

        Low-level API - prefer using channel return values.

        Args:
            channel: Channel name
            handler: Specific handler to remove (or None for all)
        """
        self._session.unsubscribe(channel, handler)

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
