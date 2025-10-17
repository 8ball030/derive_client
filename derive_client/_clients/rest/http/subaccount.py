"""Subaccount operations."""

from __future__ import annotations

from logging import Logger

from derive_action_signing import ModuleData, SignedAction

from derive_client._clients.rest.http.api import PrivateAPI, PublicAPI
from derive_client._clients.rest.http.markets import MarketOperations
from derive_client._clients.rest.http.orders import OrderOperations
from derive_client._clients.rest.http.positions import PositionOperations
from derive_client._clients.rest.http.transactions import TransactionOperations
from derive_client._clients.utils import AuthContext, NonceGenerator
from derive_client.constants import EnvConfig
from derive_client.data.generated.models import (
    MarginType,
    PrivateGetSubaccountParamsSchema,
    PrivateGetSubaccountResultSchema,
)
from derive_client.data_types import Address


class Subaccount:
    """Subaccount operations."""

    def __init__(
        self,
        subaccount_id: int,
        auth: AuthContext,
        config: EnvConfig,
        logger: Logger,
        markets: MarketOperations,
        public_api: PublicAPI,
        private_api: PrivateAPI,
        nonce_generator: NonceGenerator,
        _state: PrivateGetSubaccountResultSchema | None = None,
    ):
        """
        Initialize subaccount (internal use - use from_api() instead).

        Args:
            subaccount_id: Unique identifier for this subaccount
            auth: Authentication context for signing operations
            config: Environment configuration
            markets: Market operations interface
            public_api: Public API interface
            private_api: Private API interface for authenticated requests
            nonce_generator: Generator for unique nonces
            _state: Initial state (internal use only)
        """
        self._id = subaccount_id
        self._auth = auth
        self._config = config
        self._markets = markets
        self._logger = logger
        self._public_api = public_api
        self._private_api = private_api
        self._nonce_generator = nonce_generator

        self._transactions = TransactionOperations(self)
        self._orders = OrderOperations(self)
        self._positions = PositionOperations(self)

        self._latest_state: PrivateGetSubaccountResultSchema | None = _state

    @classmethod
    def from_api(
        cls,
        subaccount_id: int,
        auth: AuthContext,
        config: EnvConfig,
        logger: Logger,
        markets: MarketOperations,
        public_api: PublicAPI,
        private_api: PrivateAPI,
        nonce_generator: NonceGenerator,
    ) -> Subaccount:
        """
        Validate subaccount by fetching its state from the API.

        This performs a network call to verify the subaccount exists and
        caches immutable properties like margin_type and currency.

        Args:
            subaccount_id: Unique identifier for this subaccount
            auth: Authentication context for signing operations
            config: Environment configuration
            markets: Market operations interface
            public_api: Public API interface
            private_api: Private API interface for authenticated requests
            nonce_generator: Generator for unique nonces

        Returns:
            Initialized Subaccount instance

        Raises:
            APIError: If subaccount does not exist or API call fails
        """
        params = PrivateGetSubaccountParamsSchema(subaccount_id=subaccount_id)
        response = private_api.get_subaccount(params)
        state = response.result
        logger.debug(f"Subaccount validated: {state.subaccount_id}")

        return cls(
            subaccount_id=subaccount_id,
            auth=auth,
            config=config,
            logger=logger,
            markets=markets,
            public_api=public_api,
            private_api=private_api,
            nonce_generator=nonce_generator,
            _state=state,
        )

    def refresh(self) -> Subaccount:
        """Refresh mutable state from API."""
        params = PrivateGetSubaccountParamsSchema(subaccount_id=self.id)
        response = self._private_api.get_subaccount(params)
        self._latest_state = response.result
        return self

    @property
    def state(self) -> PrivateGetSubaccountResultSchema:
        """Current mutable state (positions, orders, collateral, etc)."""
        if not self._latest_state:
            raise RuntimeError(
                "Subaccount state not loaded. Use Subaccount.from_api() to create "
                "instances or call refresh() to load state."
            )
        return self._latest_state

    @property
    def margin_type(self) -> MarginType:
        return self.state.margin_type

    @property
    def currency(self) -> str:
        return self.state.currency

    @property
    def id(self) -> int:
        return self._id

    @property
    def markets(self) -> MarketOperations:
        return self._markets

    @property
    def transactions(self) -> TransactionOperations:
        return self._transactions

    @property
    def orders(self) -> OrderOperations:
        return self._orders

    @property
    def positions(self) -> PositionOperations:
        return self._positions

    def sign_action(
        self,
        nonce: int | None,
        module_address: Address,
        module_data: ModuleData,
        signature_expiry_sec: int,
    ) -> SignedAction:
        nonce = nonce if nonce is not None else self._nonce_generator.next()
        return self._auth.sign_action(
            nonce=nonce,
            module_address=module_address,
            module_data=module_data,
            signature_expiry_sec=signature_expiry_sec,
            subaccount_id=self.id,
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}({self.id}) object at {hex(id(self))}>"
