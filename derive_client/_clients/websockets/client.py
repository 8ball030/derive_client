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

from derive_client._clients.rest.http.account import LightAccount
from derive_client._clients.rest.http.collateral import CollateralOperations
from derive_client._clients.rest.http.markets import MarketOperations
from derive_client._clients.rest.http.mmp import MMPOperations
from derive_client._clients.rest.http.orders import OrderOperations
from derive_client._clients.rest.http.positions import PositionOperations
from derive_client._clients.rest.http.rfq import RFQOperations
from derive_client._clients.rest.http.subaccount import Subaccount
from derive_client._clients.rest.http.trades import TradeOperations
from derive_client._clients.rest.http.transactions import TransactionOperations
from derive_client._clients.utils import AuthContext, load_client_config
from derive_client._clients.websockets.api import PrivateAPI, PublicAPI
from derive_client._clients.websockets.session import WebSocketSession
from derive_client.config import CONFIGS
from derive_client.data_types import ChecksumAddress, Environment
from derive_client.utils.logger import get_logger


class WebSocketClient:
    """Synchronous WebSocket client for real-time data and operations."""

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
            reconnect=True,
            on_disconnect=self._handle_disconnect,
            on_reconnect=self._handle_reconnect,
            on_before_resubscribe=self._handle_before_resubscribe,  # Re-authentication hook
        )

        self._public_api = PublicAPI(session=self._session)
        self._private_api = PrivateAPI(session=self._session)

        self._markets = MarketOperations(public_api=self._public_api, logger=self._logger)
        self._transactions = TransactionOperations(public_api=self._public_api, logger=self._logger)

        self._light_account: LightAccount | None = None
        self._subaccounts: dict[int, Subaccount] = {}

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
        """Connect to Derive via WebSocket and validate credentials."""
        self._session.open()
        self._authenticate()
        self._initialize_account_and_markets()

    def _authenticate(self) -> None:
        """Perform WebSocket authentication."""
        from derive_client.data_types.generated_models import PublicLoginParamsSchema

        params = PublicLoginParamsSchema(**self._auth.sign_ws_login())
        subaccount_ids = self._public_api.rpc.login(params=params)
        self._logger.debug(f"WebSocket login returned subaccount ids: {subaccount_ids}")

        # Validate subaccount
        if self._subaccount_id not in subaccount_ids:
            self._logger.warning(
                f"Subaccount {self._subaccount_id} does not exist for wallet {self._light_account.address}. "
                f"Available subaccounts: {subaccount_ids}"
            )

    def _initialize_account_and_markets(self) -> None:
        """Initialize account and fetch market data."""
        self._light_account = self._instantiate_account()
        self._markets.fetch_all_instruments(expired=False)

        if self._subaccount_id in self._light_account.state.subaccount_ids:
            subaccount = self._instantiate_subaccount(self._subaccount_id)
            self._subaccounts[subaccount.id] = subaccount

    def _handle_disconnect(self) -> None:
        """Called when WebSocket disconnects."""
        self._logger.warning("WebSocket client detected disconnect")

    def _handle_reconnect(self) -> None:
        """Called after WebSocket reconnects (before resubscribe)."""
        self._logger.info("WebSocket client reconnected")

    def _handle_before_resubscribe(self) -> None:
        """Called before resubscribing - perform re-authentication here."""
        self._logger.info("Re-authenticating after reconnection")
        self._authenticate()
        self._logger.info("Re-authentication successful")

    def disconnect(self) -> None:
        """Close WebSocket connection and clear cached state. Idempotent."""

        self._session.close()
        self._light_account = None
        self._subaccounts.clear()
        self._markets._erc20_instruments_cache.clear()
        self._markets._perp_instruments_cache.clear()
        self._markets._option_instruments_cache.clear()

    def _instantiate_account(self) -> LightAccount:
        """Instantiate account using WebSocket API."""
        return LightAccount.from_api(
            auth=self._auth,
            config=self._config,
            logger=self._logger,
            public_api=self._public_api,
            private_api=self._private_api,
        )

    def _instantiate_subaccount(self, subaccount_id: int) -> Subaccount:
        """Instantiate subaccount using WebSocket API."""
        return Subaccount.from_api(
            subaccount_id=subaccount_id,
            auth=self._auth,
            config=self._config,
            logger=self._logger,
            markets=self._markets,
            transactions=self._transactions,
            public_api=self._public_api,
            private_api=self._private_api,
        )

    @property
    def account(self) -> LightAccount:
        """Get the LightAccount instance."""

        if self._light_account is None:
            self._light_account = self._instantiate_account()
        return self._light_account

    @property
    def active_subaccount(self) -> Subaccount:
        """Get the currently active subaccount."""

        if (subaccount := self._subaccounts.get(self._subaccount_id)) is None:
            subaccount = self.fetch_subaccount(subaccount_id=self._subaccount_id)
        return subaccount

    def fetch_subaccount(self, subaccount_id: int) -> Subaccount:
        """Fetch a subaccount from API and cache it."""

        self._subaccounts[subaccount_id] = self._instantiate_subaccount(subaccount_id)
        return self._subaccounts[subaccount_id]

    def fetch_subaccounts(self) -> list[Subaccount]:
        """Fetch subaccounts from API and cache them."""

        account_subaccounts = self.account.get_subaccounts()
        return sorted(self.fetch_subaccount(sid) for sid in account_subaccounts.subaccount_ids)

    @property
    def cached_subaccounts(self) -> list[Subaccount]:
        """Get all cached subaccounts."""

        return sorted(self._subaccounts.values())

    @property
    def markets(self) -> MarketOperations:
        """Access market data and instruments."""

        return self._markets

    @property
    def transactions(self) -> TransactionOperations:
        """Query transaction status and details."""

        return self._transactions

    @property
    def collateral(self) -> CollateralOperations:
        """Manage collateral and margin."""

        return self.active_subaccount.collateral

    @property
    def orders(self) -> OrderOperations:
        """Place and manage orders."""

        return self.active_subaccount.orders

    @property
    def positions(self) -> PositionOperations:
        """View and manage positions."""

        return self.active_subaccount.positions

    @property
    def rfq(self) -> RFQOperations:
        """Request for quote operations."""

        return self.active_subaccount.rfq

    @property
    def trades(self) -> TradeOperations:
        """View trade history."""

        return self.active_subaccount.trades

    @property
    def mmp(self) -> MMPOperations:
        """Market maker protection settings."""

        return self.active_subaccount.mmp

    @property
    def public_channels(self):
        """Access public channel subscriptions."""
        return self._public_api.channels

    @property
    def private_channels(self):
        """Access private channel subscriptions."""
        return self._private_api.channels

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
