from __future__ import annotations

import asyncio
import contextlib
from logging import Logger
from typing import AsyncGenerator

from pydantic import validate_call
from web3 import AsyncWeb3

from derive_client._bridge.async_client import AsyncBridgeClient
from derive_client._clients.rest.async_http.account import LightAccount
from derive_client._clients.rest.async_http.api import AsyncPrivateAPI, AsyncPublicAPI
from derive_client._clients.rest.async_http.markets import MarketOperations
from derive_client._clients.rest.async_http.mmp import MMPOperations
from derive_client._clients.rest.async_http.orders import OrderOperations
from derive_client._clients.rest.async_http.positions import PositionOperations
from derive_client._clients.rest.async_http.rfq import RFQOperations
from derive_client._clients.rest.async_http.session import AsyncHTTPSession, _request_timeout_override
from derive_client._clients.rest.async_http.subaccount import Subaccount
from derive_client._clients.rest.async_http.transactions import TransactionOperations
from derive_client._clients.utils import AuthContext
from derive_client.constants import CONFIGS
from derive_client.data_types import Address, Environment
from derive_client.exceptions import BridgePrimarySignerRequiredError, NotConnectedError
from derive_client.utils.logger import get_logger


class AsyncHTTPClient:
    """Asynchronous HTTP client"""

    @validate_call(config=dict(arbitrary_types_allowed=True))
    def __init__(
        self,
        *,
        wallet: Address,
        session_key: str,
        subaccount_id: int,
        env: Environment,
        logger: Logger | None = None,
        request_timeout: float = 10.0,
    ):
        config = CONFIGS[env]
        w3 = AsyncWeb3(AsyncWeb3.HTTPProvider(config.rpc_endpoint))
        account = w3.eth.account.from_key(session_key)

        auth = AuthContext(
            w3=w3,
            wallet=wallet,
            account=account,
            config=config,
        )

        self._env = env
        self._auth = auth
        self._config = config
        self._subaccount_id = subaccount_id

        self._session = AsyncHTTPSession(request_timeout=request_timeout)
        self._logger = logger if logger is not None else get_logger()

        self._public_api = AsyncPublicAPI(session=self._session, config=config)
        self._private_api = AsyncPrivateAPI(session=self._session, config=config, auth=auth)

        self._markets = MarketOperations(public_api=self._public_api)

        self._light_account: LightAccount | None = None
        self._subaccounts: dict[int, Subaccount] = {}

        self._bridge_client: AsyncBridgeClient | None = None

    async def connect(self, initialize_bridge: bool = True) -> None:
        """
        Connect to Derive and validate credentials.

        Args:
            initialize_bridge: If True, attempt to initialize bridge client (requires owner signer)
        """

        await self._session.open()

        self._light_account = await LightAccount.from_api(
            auth=self._auth,
            config=self._config,
            logger=self._logger,
            public_api=self._public_api,
            private_api=self._private_api,
        )

        await self.markets.fetch_instruments(expired=False)
        self._logger.debug(f"Cached {len(self.markets.cached_active_instruments)} instruments")

        if initialize_bridge and self._env is Environment.PROD:
            try:
                self._bridge_client = AsyncBridgeClient(
                    env=self._env,
                    account=self._auth.account,
                    wallet=self._auth.wallet,
                    logger=self._logger,
                )
                await self._bridge_client.connect()
            except BridgePrimarySignerRequiredError:
                self._logger.info("Bridge unavailable: requires signer to be the LightAccount owner.")
        elif initialize_bridge:
            self._logger.debug("Bridge module unavailable in non-prod environment.")

        subaccount_ids = self._light_account._state.subaccount_ids
        if self._subaccount_id not in subaccount_ids:
            self._logger.warning(
                f"Subaccount {self._subaccount_id} does not exist for wallet {self._light_account.address}. "
                f"Available subaccounts: {subaccount_ids}"
            )
            return

        subaccount = await self._instantiate_subaccount(self._subaccount_id)
        self._subaccounts[subaccount.id] = subaccount

    async def disconnect(self) -> None:
        """Close the underlying session and clear cached state. Idempotent."""

        await self._session.close()
        self._light_account = None
        self._subaccounts.clear()
        self.markets._active_instrument_cache.clear()

    async def _instantiate_subaccount(self, subaccount_id: int) -> Subaccount:
        return await Subaccount.from_api(
            subaccount_id=subaccount_id,
            auth=self._auth,
            config=self._config,
            logger=self._logger,
            markets=self._markets,
            public_api=self._public_api,
            private_api=self._private_api,
        )

    @property
    def account(self) -> LightAccount:
        if self._light_account is None:
            raise NotConnectedError("AsyncHTTPClient.account accessed before connect(); call connect() first.")
        return self._light_account

    @property
    def active_subaccount(self) -> Subaccount:
        if (subaccount := self._subaccounts.get(self._subaccount_id)) is None:
            raise NotConnectedError("No active subaccount. Call connect() first and ensure subaccount exists.")
        return subaccount

    @property
    def bridge(self) -> AsyncBridgeClient:
        if not self._bridge_client:
            msg = "Bridge unavailable: call connect() and ensure session key is the LightAccount owner."
            raise NotConnectedError(msg)
        return self._bridge_client

    async def fetch_subaccount(self, subaccount_id: int) -> Subaccount:
        """Fetch a subaccount from API and cache it."""
        self._subaccounts[subaccount_id] = await self._instantiate_subaccount(subaccount_id)
        return self._subaccounts[subaccount_id]

    async def fetch_subaccounts(self) -> list[Subaccount]:
        """Fetch subaccounts from API and cache them."""
        account_subaccounts = await self.account.get_subaccounts()
        return sorted(await asyncio.gather(*(self.fetch_subaccount(sid) for sid in account_subaccounts.subaccount_ids)))

    @property
    def cached_subaccounts(self) -> list[Subaccount]:
        return sorted(self._subaccounts.values())

    @property
    def markets(self) -> MarketOperations:
        return self._markets

    @property
    def transactions(self) -> TransactionOperations:
        return self.active_subaccount.transactions

    @property
    def orders(self) -> OrderOperations:
        return self.active_subaccount.orders

    @property
    def positions(self) -> PositionOperations:
        return self.active_subaccount.positions

    @property
    def rfq(self) -> RFQOperations:
        return self.active_subaccount.rfq

    @property
    def mmp(self) -> MMPOperations:
        return self.active_subaccount.mmp

    @contextlib.asynccontextmanager
    async def timeout(self, seconds: float) -> AsyncGenerator[None, None]:
        """Temporarily overwrite client's AsyncHTTPSession's request_timeout."""

        token = _request_timeout_override.set(float(seconds))
        try:
            yield
        finally:
            _request_timeout_override.reset(token)

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
