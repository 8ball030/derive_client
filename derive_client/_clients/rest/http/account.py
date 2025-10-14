"""Account management operations."""

from decimal import Decimal
from typing import Optional

from derive_action_signing.module_data import DepositModuleData

from derive_client.constants import CURRENCY_DECIMALS, INT64_MAX, Currency
from derive_client.data.generated.models import (
    MarginType,
    PrivateCreateSubaccountParamsSchema,
    PrivateCreateSubaccountResultSchema,
    PrivateEditSessionKeyParamsSchema,
    PrivateEditSessionKeyResultSchema,
    PrivateGetAccountParamsSchema,
    PrivateGetAccountResultSchema,
    PrivateGetAllPortfoliosParamsSchema,
    PrivateGetSubaccountParamsSchema,
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


class AccountOperations:
    """High-level account management operations."""

    def __init__(self, client):
        """
        Initialize account operations.

        Args:
            client: HTTPClient instance providing access to public/private APIs
        """
        self._client = client

    def build_register_session_key_tx(
        self,
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

    def register_session_key(
        self,
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

    def deregister_session_key(
        self,
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

    def register_scoped_session_key(
        self,
        expiry_sec: int,
        public_session_key: str,
        ip_whitelist: Optional[list[str]] = None,
        label: Optional[str] = None,
        scope: Scope = 'read_only',
        signed_raw_tx: Optional[str] = None,
    ) -> PrivateRegisterScopedSessionKeyResultSchema:
        params = PrivateRegisterScopedSessionKeyParamsSchema(
            wallet=self._client.wallet,
            expiry_sec=expiry_sec,
            public_session_key=public_session_key,
            ip_whitelist=ip_whitelist,
            label=label,
            scope=scope,
            signed_raw_tx=signed_raw_tx,
        )
        response = self._client.private.register_scoped_session_key(params)
        return response.result

    def session_keys(self) -> PrivateSessionKeysResultSchema:
        params = PrivateSessionKeysParamsSchema(wallet=self._client.wallet)
        response = self._client.private.session_keys(params)
        return response.result

    def edit_session_key(
        self,
        public_session_key: str,
        disable: bool = False,
        ip_whitelist: Optional[list[str]] = None,
        label: Optional[str] = None,
    ) -> PrivateEditSessionKeyResultSchema:
        params = PrivateEditSessionKeyParamsSchema(
            wallet=self._client.wallet,
            public_session_key=public_session_key,
            disable=disable,
            ip_whitelist=ip_whitelist,
            label=label,
        )
        response = self._client.private.edit_session_key(params)
        return response.result

    def get_all_portfolios(self) -> list[PrivateGetSubaccountResultSchema]:
        params = PrivateGetAllPortfoliosParamsSchema(wallet=self._client.wallet)
        response = self._client.private.get_all_portfolios(params)
        return response.result

    def create_subaccount(
        self,
        amount: Decimal = Decimal("0"),
        asset_name: str = "USDC",
        margin_type: MarginType = MarginType.SM,
        nonce: Optional[int] = None,
        signature_expiry_sec: int = INT64_MAX,
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

        subaccount_id = 0  # must be zero for new account creation
        module_address = self._client._config.contracts.DEPOSIT_MODULE

        decimals = CURRENCY_DECIMALS[Currency(asset_name)]
        manager_address = self._client._config.contracts.STANDARD_RISK_MANAGER
        asset = self._client._config.contracts.CASH_ASSET

        module_data = DepositModuleData(
            amount=str(amount),
            asset=asset,
            manager=manager_address,
            decimals=decimals,
            asset_name=asset_name,
        )

        signed_action = self._client._sign_action(
            nonce=nonce,
            module_address=module_address,
            module_data=module_data,
            signature_expiry_sec=signature_expiry_sec,
            subaccount_id=subaccount_id,
        )

        signer = signed_action.signer
        signature = signed_action.signature
        nonce = signed_action.nonce

        params = PrivateCreateSubaccountParamsSchema(
            amount=amount,
            asset_name=asset_name,
            margin_type=margin_type,
            nonce=nonce,
            signature=signature,
            signature_expiry_sec=signature_expiry_sec,
            signer=signer,
            wallet=self._client.wallet,
        )
        response = self._client.private.create_subaccount(params)
        return response.result

    def get_subaccount(self) -> PrivateGetSubaccountResultSchema:
        params = PrivateGetSubaccountParamsSchema(subaccount_id=self._client.subaccount_id)
        response = self._client.private.get_subaccount(params)
        return response.result

    def get_subaccounts(self) -> PrivateGetSubaccountsResultSchema:
        params = PrivateGetSubaccountsParamsSchema(wallet=self._client.wallet)
        response = self._client.private.get_subaccounts(params)
        return response.result

    def get(self) -> PrivateGetAccountResultSchema:
        params = PrivateGetAccountParamsSchema(wallet=self._client.wallet)
        response = self._client.private.get_account(params)
        return response.result
