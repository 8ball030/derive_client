from __future__ import annotations

from web3 import Web3

from derive_client._clients.rest.http.account import AccountOperations
from derive_client._clients.rest.http.api import PrivateAPI, PublicAPI
from derive_client._clients.rest.http.session import HTTPSession
from derive_client._clients.utils import AuthContext
from derive_client.constants import CONFIGS
from derive_client.data_types import Address, Environment


class HTTPClient:
    """Synchronous HTTP client"""

    def __init__(self, wallet: Address, session_key: str, env: Environment):
        config = CONFIGS[env]
        w3 = Web3(Web3.HTTPProvider(config.rpc_endpoint))
        account = w3.eth.account.from_key(session_key)

        auth = AuthContext(
            w3=w3,
            wallet=wallet,
            account=account,
        )

        self._auth = auth
        self._session = HTTPSession()

        self.public = PublicAPI(session=self._session, config=config)
        self.private = PrivateAPI(session=self._session, config=config, auth=auth)

        self.account = AccountOperations(self)

    @property
    def wallet(self) -> Address:
        return self._auth.wallet

    def __enter__(self):
        self._session.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.__exit__(exc_type, exc_val, exc_tb)

    def open(self):
        self._session.open()

    def close(self):
        self._session.close()
