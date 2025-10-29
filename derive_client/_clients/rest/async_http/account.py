"""Account management operations."""

from __future__ import annotations

from decimal import Decimal
from logging import Logger
from typing import Optional

from derive_action_signing.module_data import DepositModuleData

from derive_client._clients.rest.async_http.api import AsyncPrivateAPI, AsyncPublicAPI
from derive_client._clients.utils import AuthContext
from derive_client.constants import CURRENCY_DECIMALS, Currency, EnvConfig
from derive_client.data.generated.models import (
    MarginType,
    PrivateCreateSubaccountParamsSchema,
    PrivateCreateSubaccountResultSchema,
    PrivateEditSessionKeyParamsSchema,
    PrivateEditSessionKeyResultSchema,
    PrivateGetAccountParamsSchema,
    PrivateGetAccountResultSchema,
    PrivateGetAllPortfoliosParamsSchema,
    PrivateGetSubaccountResultSchema,
    PrivateGetSubaccountsParamsSchema,
    PrivateGetSubaccountsResultSchema,
    PrivateRegisterScopedSessionKeyParamsSchema,
    PrivateRegisterScopedSessionKeyResultSchema,
    PrivateSessionKeysParamsSchema,
    PrivateSessionKeysResultSchema,
    PublicBuildRegisterSessionKeyTxResultSchema,
    PublicDeregisterSessionKeyResultSchema,
    PublicRegisterSessionKeyResultSchema,
    Scope,
)
from derive_client.data_types import Address


class LightAccount:
    """LightAccount smart contract wallet operations."""

    def __init__(
        self,
        *,
        auth: AuthContext,
        config: EnvConfig,
        logger: Logger,
        public_api: AsyncPublicAPI,
        private_api: AsyncPrivateAPI,
        _state: PrivateGetAccountResultSchema | None = None,
    ):
        """
        Initialize LightAccount (internal use - use from_api() instead).

        Args:
            auth: Authentication context for signing operations
            config: Environment configuration
            public_api: Public API interface
            private_api: Private API interface for authenticated requests
            _state: Initial state (internal use only)
        """
        self._auth = auth
        self._config = config
        self._logger = logger
        self._public_api = public_api
        self._private_api = private_api
        self._state = _state

    @classmethod
    async def from_api(
        cls,
        *,
        auth: AuthContext,
        config: EnvConfig,
        logger: Logger,
        public_api: AsyncPublicAPI,
        private_api: AsyncPrivateAPI,
    ) -> LightAccount:
        """
        Validate LightAccount by fetching its state from the API.

        This performs a network call to verify the wallet exists and that
        the provided session key is registered and valid.

        Args:
            auth: Authentication context for signing operations
            config: Environment configuration
            public_api: Public API interface
            private_api: Private API interface for authenticated requests

        Returns:
            Initialized LightAccount instance

        Raises:
            APIError: If wallet does not exist
        """

        params = PrivateGetAccountParamsSchema(wallet=auth.wallet)
        response = await private_api.get_account(params)
        state = response.result
        logger.debug(f"LightAccount validated: {state.wallet}")

        # Check if the current signer is in the list of valid session keys
        session_keys_params = PrivateSessionKeysParamsSchema(wallet=auth.wallet)
        session_keys_response = await private_api.session_keys(session_keys_params)

        valid_signers = {key.public_session_key: key for key in session_keys_response.result.public_session_keys}
        if auth.account.address not in valid_signers:
            logger.warning(f"Session key {auth.account.address} is not registered for wallet {auth.wallet}")
        else:
            logger.debug(f"Session key validated: {auth.account.address}")

        return cls(
            auth=auth,
            config=config,
            logger=logger,
            public_api=public_api,
            private_api=private_api,
            _state=state,
        )

    @property
    def address(self) -> Address:
        """LightAccount wallet address."""
        return self._auth.wallet

    async def build_register_session_key_tx(
        self,
        *,
        expiry_sec: int,
        public_session_key: str,
        gas: Optional[int] = None,
        nonce: Optional[int] = None,
    ) -> PublicBuildRegisterSessionKeyTxResultSchema:
        """
        NOT SUPPORTED PROGRAMMATICALLY: registering a session key (paymaster flow)
        cannot be executed from this client.

        Options:
        - Use the Derive frontend (recommended) so the paymaster pays gas.
        - To register programmatically, use an owner-signed, EOA-paid flow:
            client.owner.build_register_session_key_tx(...)
        """
        raise NotImplementedError(
            "Programmatic paymaster registration is not supported. "
            "Use the Derive frontend (paymaster) or client.owner.build_register_session_key_tx(...) "
            "for an owner-signed, EOA-paid registration."
        )

    async def register_session_key(
        self,
        *,
        expiry_sec: int,
        label: str,
        public_session_key: str,
        signed_raw_tx: str,
    ) -> PublicRegisterSessionKeyResultSchema:
        """
        NOT SUPPORTED PROGRAMMATICALLY: registering a session key (paymaster flow)
        cannot be executed from this client.

        Options:
        - Use the Derive frontend (recommended) so the paymaster pays gas.
        - To register programmatically, use an owner-signed, EOA-paid flow:
            client.owner.register_session_key_via_eoa(...)
        """
        raise NotImplementedError(
            "Programmatic paymaster registration is not supported. "
            "Use the Derive frontend (paymaster) or client.owner.register_session_key_via_eoa(...) "
            "for an owner-signed, EOA-paid registration."
        )

    async def deregister_session_key(
        self,
        *,
        public_session_key: str,
        signed_raw_tx: str,
    ) -> PublicDeregisterSessionKeyResultSchema:
        """
        NOT SUPPORTED PROGRAMMATICALLY: deregistering a session key (paymaster flow)
        cannot be executed from this client.

        Options:
        - Use the Derive frontend to deregister so paymaster handles flow.
        - To deregister programmatically, use an owner-signed, EOA-paid flow:
            client.owner.deregister_session_key_via_eoa(...)
        """
        raise NotImplementedError(
            "Programmatic paymaster deregistration is not supported. "
            "Use the Derive frontend or client.owner.deregister_session_key_via_eoa(...)."
            "for an owner-signed, EOA-paid registration."
        )

    async def register_scoped_session_key(
        self,
        *,
        expiry_sec: int,
        public_session_key: str,
        ip_whitelist: Optional[list[str]] = None,
        label: Optional[str] = None,
        scope: Scope = 'read_only',
        signed_raw_tx: Optional[str] = None,
    ) -> PrivateRegisterScopedSessionKeyResultSchema:
        params = PrivateRegisterScopedSessionKeyParamsSchema(
            wallet=self._auth.wallet,
            expiry_sec=expiry_sec,
            public_session_key=public_session_key,
            ip_whitelist=ip_whitelist,
            label=label,
            scope=scope,
            signed_raw_tx=signed_raw_tx,
        )
        response = await self._private_api.register_scoped_session_key(params)
        return response.result

    async def session_keys(self) -> PrivateSessionKeysResultSchema:
        params = PrivateSessionKeysParamsSchema(wallet=self.address)
        response = await self._private_api.session_keys(params)
        return response.result

    async def edit_session_key(
        self,
        *,
        public_session_key: str,
        disable: bool = False,
        ip_whitelist: Optional[list[str]] = None,
        label: Optional[str] = None,
    ) -> PrivateEditSessionKeyResultSchema:
        params = PrivateEditSessionKeyParamsSchema(
            wallet=self.address,
            public_session_key=public_session_key,
            disable=disable,
            ip_whitelist=ip_whitelist,
            label=label,
        )
        response = await self._private_api.edit_session_key(params)
        return response.result

    async def get_all_portfolios(self) -> list[PrivateGetSubaccountResultSchema]:
        params = PrivateGetAllPortfoliosParamsSchema(wallet=self.address)
        response = await self._private_api.get_all_portfolios(params)
        return response.result

    async def create_subaccount(
        self,
        *,
        amount: Decimal = Decimal("0"),
        asset_name: str = "USDC",
        margin_type: MarginType = MarginType.SM,
        nonce: Optional[int] = None,
        signature_expiry_sec: Optional[int] = None,
        currency: Optional[str] = None,
    ) -> PrivateCreateSubaccountResultSchema:
        """Create subaccount."""

        # Current implementation only supports the exact invariants below.
        # If callers pass any other values, fail fast with NotImplementedError
        # so we can change the API later without breaking callers.
        if amount != Decimal("0"):
            raise NotImplementedError("Only amount == 0 is supported at present.")
        if asset_name != "USDC":
            raise NotImplementedError('Only asset_name == "USDC" is supported at present.')
        if margin_type != MarginType.SM:
            raise NotImplementedError("Only margin_type == MarginType.SM is supported at present.")
        if currency is not None:
            raise NotImplementedError("Only currency == None is supported for SM subaccounts at present.")

        if margin_type == MarginType.SM and currency is not None:
            raise ValueError("base_currency must not be provided for standard-margin (SM) subaccounts.")

        nonce = nonce if nonce is not None else self._auth.nonce_generator.next()
        subaccount_id = 0  # must be zero for new account creation
        module_address = self._config.contracts.DEPOSIT_MODULE

        decimals = CURRENCY_DECIMALS[Currency(asset_name)]
        manager_address = self._config.contracts.STANDARD_RISK_MANAGER
        asset = self._config.contracts.CASH_ASSET

        module_data = DepositModuleData(
            amount=str(amount),
            asset=asset,
            manager=manager_address,
            decimals=decimals,
            asset_name=asset_name,
        )

        signed_action = self._auth.sign_action(
            nonce=nonce,
            module_address=module_address,
            module_data=module_data,
            signature_expiry_sec=signature_expiry_sec,
            subaccount_id=subaccount_id,
        )

        params = PrivateCreateSubaccountParamsSchema(
            amount=amount,
            asset_name=asset_name,
            margin_type=margin_type,
            nonce=signed_action.nonce,
            signature=signed_action.signature,
            signature_expiry_sec=signed_action.signature_expiry_sec,
            signer=signed_action.signer,
            wallet=self.address,
        )
        response = await self._private_api.create_subaccount(params)
        return response.result

    async def get_subaccounts(self) -> PrivateGetSubaccountsResultSchema:
        params = PrivateGetSubaccountsParamsSchema(wallet=self.address)
        response = await self._private_api.get_subaccounts(params)
        return response.result

    async def get(self) -> PrivateGetAccountResultSchema:
        params = PrivateGetAccountParamsSchema(wallet=self.address)
        response = await self._private_api.get_account(params)
        return response.result

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}({self.address}) object at {hex(id(self))}>"
