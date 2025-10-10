from __future__ import annotations

from web3 import AsyncWeb3

from derive_client._clients.rest.async_http.api import PrivateAPI, PublicAPI
from derive_client._clients.rest.async_http.session import AsyncHTTPSession
from derive_client._clients.utils import AuthContext
from derive_client.constants import CONFIGS
from derive_client.data_types import Address, Environment


class AsyncHTTPClient:
    """Asynchronous HTTP client"""

    def __init__(self, wallet: Address, session_key: str, env: Environment):
        config = CONFIGS[env]
        w3 = AsyncWeb3(AsyncWeb3.HTTPProvider(config.rpc_endpoint))
        account = w3.eth.account.from_key(session_key)

        auth = AuthContext(
            w3=w3,
            wallet=wallet,
            account=account,
        )

        self._session = AsyncHTTPSession()

        self.public = PublicAPI(session=self._session, config=config)
        self.private = PrivateAPI(session=self._session, config=config, auth=auth)

    async def __aenter__(self):
        await self._session.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.close()

    async def open(self):
        await self._session.open()

    async def close(self):
        await self._session.close()
