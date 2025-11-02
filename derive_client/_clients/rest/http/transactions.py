"""Transaction operations."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from derive_action_signing import DepositModuleData, WithdrawModuleData

from derive_client.config import CURRENCY_DECIMALS
from derive_client.data_types import Currency
from derive_client.data_types.generated_models import (
    MarginType,
    PrivateDepositParamsSchema,
    PrivateDepositResultSchema,
    PrivateWithdrawParamsSchema,
    PrivateWithdrawResultSchema,
    PublicGetTransactionParamsSchema,
    PublicGetTransactionResultSchema,
)

if TYPE_CHECKING:
    from .subaccount import Subaccount


class TransactionOperations:
    """High-level transaction operations."""

    def __init__(self, *, subaccount: Subaccount):
        """
        Initialize order operations.

        Args:
            subaccount: Subaccount instance providing access to auth, config, and APIs
        """
        self._subaccount = subaccount

    def get(self, *, transaction_id: str) -> PublicGetTransactionResultSchema:
        """Get a transaction by its transaction id."""

        params = PublicGetTransactionParamsSchema(transaction_id=transaction_id)
        response = self._subaccount._public_api.get_transaction(params)
        return response.result

    def deposit_to_subaccount(
        self,
        *,
        amount: Decimal,
        asset_name: str,
        nonce: Optional[int] = None,
        signature_expiry_sec: Optional[int] = None,
        is_atomic_signing: bool = False,
    ) -> PrivateDepositResultSchema:
        """Deposit from LightAccount smart contract wallet into subaccount."""

        subaccount_id = self._subaccount.id
        module_address = self._subaccount._config.contracts.DEPOSIT_MODULE

        currency = self._subaccount.markets.get_currency(currency=asset_name)
        if (asset := currency.protocol_asset_addresses.spot) is None:
            raise ValueError(f"asset '{asset_name}' has no spot address, found: {currency}")

        managers = []
        for manager in currency.managers:
            if manager.margin_type == self._subaccount.margin_type == MarginType.SM:
                managers.append(manager)
            if manager.margin_type is self._subaccount.margin_type and manager.currency == self._subaccount.currency:
                managers.append(manager)

        if len(managers) != 1:
            msg = f"Expected exactly one manager for {(self._subaccount.margin_type, self._subaccount.currency)}, found {managers}"
            raise ValueError(msg)

        manager_address = managers[0].address
        decimals = CURRENCY_DECIMALS[Currency[currency.currency]]

        module_data = DepositModuleData(
            amount=amount,
            asset=asset,
            manager=manager_address,
            decimals=decimals,
            asset_name=asset_name,
        )

        signed_action = self._subaccount.sign_action(
            nonce=nonce,
            module_address=module_address,
            module_data=module_data,
            signature_expiry_sec=signature_expiry_sec,
        )

        params = PrivateDepositParamsSchema(
            amount=amount,
            asset_name=asset_name,
            nonce=signed_action.nonce,
            signature=signed_action.signature,
            signature_expiry_sec=signed_action.signature_expiry_sec,
            signer=signed_action.signer,
            subaccount_id=subaccount_id,
            is_atomic_signing=is_atomic_signing,
        )
        response = self._subaccount._private_api.deposit(params)
        return response.result

    def withdraw_from_subaccount(
        self,
        *,
        amount: Decimal,
        asset_name: str,
        nonce: Optional[int] = None,
        signature_expiry_sec: Optional[int] = None,
        is_atomic_signing: bool = False,
    ) -> PrivateWithdrawResultSchema:
        """Deposit from subaccount into LightAccount smart contract wallet."""

        subaccount_id = self._subaccount.id
        module_address = self._subaccount._config.contracts.WITHDRAWAL_MODULE

        currency = self._subaccount.markets.get_currency(currency=asset_name)
        if (asset := currency.protocol_asset_addresses.spot) is None:
            raise ValueError(f"asset '{asset_name}' has no spot address, found: {currency}")

        decimals = CURRENCY_DECIMALS[Currency[currency.currency]]

        module_data = WithdrawModuleData(
            amount=amount,
            asset=asset,
            decimals=decimals,
            asset_name=asset_name,
        )

        signed_action = self._subaccount.sign_action(
            nonce=nonce,
            module_address=module_address,
            module_data=module_data,
            signature_expiry_sec=signature_expiry_sec,
        )

        params = PrivateWithdrawParamsSchema(
            amount=amount,
            asset_name=asset_name,
            nonce=signed_action.nonce,
            signature=signed_action.signature,
            signature_expiry_sec=signed_action.signature_expiry_sec,
            signer=signed_action.signer,
            subaccount_id=subaccount_id,
            is_atomic_signing=is_atomic_signing,
        )
        response = self._subaccount._private_api.withdraw(params)
        return response.result
