from __future__ import annotations

from derive_action_signing.signed_action import SignedAction
from web3 import Web3

from derive_client._clients.rest.http.account import AccountOperations
from derive_client._clients.rest.http.api import PrivateAPI, PublicAPI
from derive_client._clients.rest.http.funding import FundingOperations
from derive_client._clients.rest.http.markets import MarketOperations
from derive_client._clients.rest.http.orders import OrderOperations
from derive_client._clients.rest.http.session import HTTPSession
from derive_client._clients.utils import AuthContext, NonceGenerator
from derive_client.constants import CONFIGS
from derive_client.data_types import Address, Environment


class HTTPClient:
    """Synchronous HTTP client"""

    def __init__(self, wallet: Address, session_key: str, subaccount_id: int, env: Environment):
        config = CONFIGS[env]
        w3 = Web3(Web3.HTTPProvider(config.rpc_endpoint))
        account = w3.eth.account.from_key(session_key)

        auth = AuthContext(
            w3=w3,
            wallet=wallet,
            account=account,
        )

        self._auth = auth
        self._config = config
        self._subaccount_id = subaccount_id

        self._session = HTTPSession()
        self._nonce_generator = NonceGenerator()

        self.public = PublicAPI(session=self._session, config=config)
        self.private = PrivateAPI(session=self._session, config=config, auth=auth)

        self.account = AccountOperations(self)
        self.markets = MarketOperations(self)
        self.funding = FundingOperations(self)
        self.orders = OrderOperations(self)

    @property
    def wallet(self) -> Address:
        return self._auth.wallet

    @property
    def subaccount_id(self) -> int:
        return self._subaccount_id

    @property
    def signer(self) -> Address:
        return self._auth.account.address

    def get_nonce(self) -> int:
        return self._nonce_generator.next()

    def _sign_action(
        self,
        nonce: int | None,
        module_address: Address,
        module_data,
        signature_expiry_sec: int,
    ) -> SignedAction:
        nonce = nonce if nonce is not None else self.get_nonce()
        action = SignedAction(
            subaccount_id=self.subaccount_id,
            owner=self.wallet,
            signer=self.signer,
            signature_expiry_sec=signature_expiry_sec,
            nonce=nonce,
            module_address=module_address,
            module_data=module_data,
            DOMAIN_SEPARATOR=self._config.DOMAIN_SEPARATOR,
            ACTION_TYPEHASH=self._config.ACTION_TYPEHASH,
        )
        action.sign(self._auth.account.key)
        return action

    def __enter__(self):
        self._session.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.__exit__(exc_type, exc_val, exc_tb)

    def open(self):
        self._session.open()

    def close(self):
        self._session.close()
