from __future__ import annotations

from logging import Logger

from web3 import Web3

from derive_client._clients.rest.http.account import LightAccount
from derive_client._clients.rest.http.api import PrivateAPI, PublicAPI
from derive_client._clients.rest.http.markets import MarketOperations
from derive_client._clients.rest.http.orders import OrderOperations
from derive_client._clients.rest.http.positions import PositionOperations
from derive_client._clients.rest.http.session import HTTPSession
from derive_client._clients.rest.http.subaccount import Subaccount
from derive_client._clients.rest.http.transactions import TransactionOperations
from derive_client._clients.utils import AuthContext, NonceGenerator
from derive_client.constants import CONFIGS
from derive_client.data_types import Address, Environment
from derive_client.utils.logger import get_logger


class NotConnectedError(RuntimeError):
    """Raised when the client hasn't connected (call connect())."""


class HTTPClient:
    """Synchronous HTTP client"""

    def __init__(
        self,
        wallet: Address,
        session_key: str,
        subaccount_id: int,
        env: Environment,
        logger: Logger | None = None,
    ):
        config = CONFIGS[env]
        w3 = Web3(Web3.HTTPProvider(config.rpc_endpoint))
        account = w3.eth.account.from_key(session_key)

        auth = AuthContext(
            w3=w3,
            wallet=wallet,
            account=account,
            config=config,
        )

        self._auth = auth
        self._config = config
        self._subaccount_id = subaccount_id

        self._session = HTTPSession()
        self._logger = logger if logger is not None else get_logger()
        self._nonce_generator = NonceGenerator()

        self._public_api = PublicAPI(session=self._session, config=config)
        self._private_api = PrivateAPI(session=self._session, config=config, auth=auth)

        self._markets = MarketOperations(public_api=self._public_api)

        self._account: LightAccount | None = None
        self._subaccounts: dict[int, Subaccount] = {}

    def connect(self) -> None:
        """
        Connect to Derive and validate credentials.

        Performs API calls to:
        - Verify the wallet exists
        - Validate the session key is registered
        - Verify the subaccount exists

        Raises:
            APIError: If wallet/subaccount don't exist or session key is invalid
        """

        self._light_account = LightAccount.from_api(
            auth=self._auth,
            config=self._config,
            logger=self._logger,
            public_api=self._public_api,
            private_api=self._private_api,
            nonce_generator=self._nonce_generator,
        )

        subaccount_ids = self._light_account._state.subaccount_ids
        if self._subaccount_id not in subaccount_ids:
            self._logger.warning(
                f"Subaccount {self._subaccount_id} does not exist for wallet {self.wallet}. "
                f"Available subaccounts: {subaccount_ids}"
            )
            return

        subaccount = self._instantiate_subaccount(self._subaccount_id)
        self._subaccounts[subaccount.id] = subaccount

    def _instantiate_subaccount(self, subaccount_id: int) -> Subaccount:
        return Subaccount.from_api(
            subaccount_id=subaccount_id,
            auth=self._auth,
            config=self._config,
            logger=self._logger,
            markets=self._markets,
            public_api=self._public_api,
            private_api=self._private_api,
            nonce_generator=self._nonce_generator,
        )

    @property
    def account(self) -> LightAccount:
        if self._light_account is None:
            raise NotConnectedError("HTTPClient.account accessed before connect(); call connect() first.")
        return self._light_account

    @property
    def active_subaccount(self) -> Subaccount:
        if (subaccount := self._subaccounts.get(self._subaccount_id)) is None:
            raise NotConnectedError("No active subaccount. Call connect() first and ensure subaccount exists.")
        return subaccount

    def fetch_subaccount(self, subaccount_id: int) -> Subaccount:
        """Fetch a subaccount from API and cache it."""
        self._subaccounts[subaccount_id] = self._instantiate_subaccount(subaccount_id)
        return self._subaccounts[subaccount_id]

    def fetch_subaccounts(self) -> list[Subaccount]:
        """Fetch subaccounts from API and cache them."""
        account_subaccounts = self.account.get_subaccounts()
        return [self.fetch_subaccount(sid) for sid in account_subaccounts.subaccount_ids]

    @property
    def cached_subaccounts(self) -> list[Subaccount]:
        return list(self._subaccounts.values())

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
    def wallet(self) -> Address:
        return self._auth.wallet

    @property
    def signer(self) -> Address:
        return self._auth.signer

    def get_nonce(self) -> int:
        return self._nonce_generator.next()

    def __enter__(self):
        self._session.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.__exit__(exc_type, exc_val, exc_tb)

    def open(self) -> None:
        self._session.open()

    def close(self) -> None:
        self._session.close()
