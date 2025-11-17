"""Subaccount operations."""

from __future__ import annotations

import functools
from logging import Logger
from typing import Optional

from derive_action_signing import ModuleData, SignedAction

from derive_client._clients.rest.http.api import PrivateAPI, PublicAPI
from derive_client._clients.rest.http.collateral import CollateralOperations
from derive_client._clients.rest.http.markets import MarketOperations
from derive_client._clients.rest.http.mmp import MMPOperations
from derive_client._clients.rest.http.orders import OrderOperations
from derive_client._clients.rest.http.positions import PositionOperations
from derive_client._clients.rest.http.rfq import RFQOperations
from derive_client._clients.rest.http.trades import TradeOperations
from derive_client._clients.rest.http.transactions import TransactionOperations
from derive_client._clients.utils import AuthContext
from derive_client.data_types import ChecksumAddress, EnvConfig
from derive_client.data_types.generated_models import (
    MarginType,
    PrivateGetSubaccountParamsSchema,
    PrivateGetSubaccountResultSchema,
)


@functools.total_ordering
class Subaccount:
    """Subaccount operations."""

    def __init__(
        self,
        *,
        subaccount_id: int,
        auth: AuthContext,
        config: EnvConfig,
        logger: Logger,
        markets: MarketOperations,
        transactions: TransactionOperations,
        public_api: PublicAPI,
        private_api: PrivateAPI,
        _state: PrivateGetSubaccountResultSchema | None = None,
    ):
        """
        Initialize subaccount (internal use - use from_api() instead).

        Args:
            subaccount_id: Unique identifier for this subaccount
            auth: Authentication context for signing operations
            config: Environment configuration
            markets: Market operations interface
            transactions: Transaction operations interface
            public_api: Public API interface
            private_api: Private API interface for authenticated requests
            _state: Initial state (internal use only)
        """

        self._id = subaccount_id
        self._auth = auth
        self._config = config
        self._logger = logger
        self._public_api = public_api
        self._private_api = private_api

        self._markets = markets
        self._transactions = transactions

        self._collateral = CollateralOperations(subaccount=self)
        self._orders = OrderOperations(subaccount=self)
        self._trades = TradeOperations(subaccount=self)
        self._positions = PositionOperations(subaccount=self)
        self._rfq = RFQOperations(subaccount=self)
        self._mmp = MMPOperations(subaccount=self)

        self._state: PrivateGetSubaccountResultSchema | None = _state

    @classmethod
    def from_api(
        cls,
        *,
        subaccount_id: int,
        auth: AuthContext,
        config: EnvConfig,
        logger: Logger,
        markets: MarketOperations,
        transactions: TransactionOperations,
        public_api: PublicAPI,
        private_api: PrivateAPI,
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
            transactions: Transaction operations interface
            public_api: Public API interface
            private_api: Private API interface for authenticated requests

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
            transactions=transactions,
            public_api=public_api,
            private_api=private_api,
            _state=state,
        )

    def refresh(self) -> Subaccount:
        """Refresh mutable state from API."""

        params = PrivateGetSubaccountParamsSchema(subaccount_id=self.id)
        response = self._private_api.get_subaccount(params)
        self._state = response.result
        return self

    @property
    def state(self) -> PrivateGetSubaccountResultSchema:
        """Current mutable state (positions, orders, collateral, etc)."""

        if not self._state:
            raise RuntimeError(
                "Subaccount state not loaded. Use Subaccount.from_api() to create "
                "instances or call refresh() to load state."
            )
        return self._state

    @property
    def margin_type(self) -> MarginType:
        """Margin type of subaccount (PM (Portfolio Margin), PM2 (Portfolio Margin 2), or SM (Standard Margin))"""

        return self.state.margin_type

    @property
    def currency(self) -> str:
        """Currency of subaccount."""

        return self.state.currency

    @property
    def id(self) -> int:
        """Subaccount ID."""

        return self._id

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

        return self._collateral

    @property
    def orders(self) -> OrderOperations:
        """Place and manage orders."""

        return self._orders

    @property
    def positions(self) -> PositionOperations:
        """View and manage positions."""

        return self._positions

    @property
    def rfq(self) -> RFQOperations:
        """Request for quote operations."""

        return self._rfq

    @property
    def trades(self) -> TradeOperations:
        """View trade history."""

        return self._trades

    @property
    def mmp(self) -> MMPOperations:
        """Market maker protection settings."""

        return self._mmp

    def sign_action(
        self,
        *,
        module_address: ChecksumAddress,
        module_data: ModuleData,
        signature_expiry_sec: Optional[int] = None,
        nonce: Optional[int] | None = None,
    ) -> SignedAction:
        return self._auth.sign_action(
            nonce=nonce,
            module_address=module_address,
            module_data=module_data,
            signature_expiry_sec=signature_expiry_sec,
            subaccount_id=self.id,
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}({self.id}) object at {hex(id(self))}>"

    def __lt__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.id < other.id
