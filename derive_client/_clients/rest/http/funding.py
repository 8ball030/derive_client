"""Subaccount funding operations."""

from decimal import Decimal
from typing import Optional

from derive_action_signing.module_data import DepositModuleData, WithdrawModuleData

from derive_client.constants import CURRENCY_DECIMALS, INT64_MAX
from derive_client.data.generated.models import (
    PrivateDepositParamsSchema,
    PrivateDepositResultSchema,
    PrivateWithdrawParamsSchema,
    PrivateWithdrawResultSchema,
)
from derive_client.data_types import Currency


class FundingOperations:
    """High-level funding operations."""

    def __init__(self, client):
        """
        Initialize funding operations.

        Args:
            client: HTTPClient instance providing access to public/private APIs
        """
        self._client = client

    def deposit(
        self,
        amount: Decimal,
        asset_name: str,
        nonce: Optional[int] = None,
        signature_expiry_sec: int = INT64_MAX,
        is_atomic_signing: bool = False,
    ) -> PrivateDepositResultSchema:
        """Deposit from LightAccount smart contract wallet into subaccount."""

        subaccount_id = self._client.subaccount_id
        module_address = self._client._config.contracts.DEPOSIT_MODULE

        currency = self._client.markets.get_currency(asset_name)
        subaccount = self._client.account.get_subaccount()

        underlying_address = currency.protocol_asset_addresses.spot

        managers = []
        for manager in currency.managers:
            if manager.margin_type is subaccount.margin_type and manager.currency == subaccount.currency:
                managers.append(manager)

        if len(managers) != 1:
            msg = f"Expected exactly one manager for {(subaccount.margin_type, subaccount.currency)}, found {managers}"
            raise ValueError(msg)

        manager_address = managers[0].address
        decimals = CURRENCY_DECIMALS[Currency[currency.currency]]

        module_data = DepositModuleData(
            amount=str(amount),
            asset=underlying_address,
            manager=manager_address,
            decimals=decimals,
            asset_name=asset_name,
        )

        signed_action = self._client._sign_action(
            nonce=nonce,
            module_address=module_address,
            module_data=module_data,
            signature_expiry_sec=signature_expiry_sec,
        )

        signer = signed_action.signer
        signature = signed_action.signature
        nonce = signed_action.nonce

        params = PrivateDepositParamsSchema(
            amount=amount,
            asset_name=asset_name,
            nonce=nonce,
            signature=signature,
            signature_expiry_sec=signature_expiry_sec,
            signer=signer,
            subaccount_id=subaccount_id,
            is_atomic_signing=is_atomic_signing,
        )
        response = self._client.private.deposit(params)
        return response.result

    def withdraw(
        self,
        amount: Decimal,
        asset_name: str,
        nonce: Optional[int] = None,
        signature_expiry_sec: int = INT64_MAX,
        is_atomic_signing: bool = False,
    ) -> PrivateWithdrawResultSchema:
        """Deposit from subaccount inot LightAccount smart contract wallet."""

        subaccount_id = self._client.subaccount_id
        module_address = self._client._config.contracts.WITHDRAWAL_MODULE

        currency = self._client.markets.get_currency(asset_name)

        underlying_address = currency.protocol_asset_addresses.spot
        decimals = CURRENCY_DECIMALS[Currency[currency.currency]]

        module_data = WithdrawModuleData(
            amount=str(amount),
            asset=underlying_address,
            decimals=decimals,
            asset_name=asset_name,
        )

        signed_action = self._client._sign_action(
            nonce=nonce,
            module_address=module_address,
            module_data=module_data,
            signature_expiry_sec=signature_expiry_sec,
        )

        signer = signed_action.signer
        signature = signed_action.signature
        nonce = signed_action.nonce

        params = PrivateWithdrawParamsSchema(
            amount=amount,
            asset_name=asset_name,
            nonce=nonce,
            signature=signature,
            signature_expiry_sec=signature_expiry_sec,
            signer=signer,
            subaccount_id=subaccount_id,
            is_atomic_signing=is_atomic_signing,
        )
        response = self._client.private.withdraw(params)
        return response.result
