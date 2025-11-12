"""Collateral management operations."""

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
    PrivateGetCollateralsParamsSchema,
    PrivateGetCollateralsResultSchema,
    PrivateGetMarginParamsSchema,
    PrivateGetMarginResultSchema,
    PrivateWithdrawParamsSchema,
    PrivateWithdrawResultSchema,
    SimulatedCollateralSchema,
    SimulatedPositionSchema,
)

if TYPE_CHECKING:
    from .subaccount import Subaccount


class CollateralOperations:
    """Collateral management operations."""

    def __init__(self, *, subaccount: Subaccount):
        """
        Initialize collateral operations.

        Args:
            subaccount: Subaccount instance providing access to auth, config, and APIs
        """
        self._subaccount = subaccount

    def get(self) -> PrivateGetCollateralsResultSchema:
        """Get collaterals of a subaccount."""

        subaccount_id = self._subaccount.id
        params = PrivateGetCollateralsParamsSchema(subaccount_id=subaccount_id)
        response = self._subaccount._private_api.get_collaterals(params)
        return response.result

    def get_margin(
        self,
        simulated_collateral_changes: Optional[list[SimulatedCollateralSchema]] = None,
        simulated_position_changes: Optional[list[SimulatedPositionSchema]] = None,
    ) -> PrivateGetMarginResultSchema:
        """
        Calculates margin for a given subaccount and (optionally) a simulated state change.

        Does not take into account open orders margin requirements.
        """

        subaccount_id = self._subaccount.id
        params = PrivateGetMarginParamsSchema(
            subaccount_id=subaccount_id,
            simulated_collateral_changes=simulated_collateral_changes,
            simulated_position_changes=simulated_position_changes,
        )
        response = self._subaccount._private_api.get_margin(params)
        return response.result

    def deposit_to_subaccount(
        self,
        *,
        amount: Decimal,
        asset_name: str,
        subaccount_id: Optional[int] = None,
        nonce: Optional[int] = None,
        signature_expiry_sec: Optional[int] = None,
        is_atomic_signing: bool = False,
    ) -> PrivateDepositResultSchema:
        """Deposit an asset to a subaccount from the LightAccount wallet."""

        subaccount_id = self._subaccount.id if subaccount_id is None else subaccount_id
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
            msg = f"Expected exactly one manager for {(self._subaccount.margin_type, self._subaccount.currency)}, found {managers}"  # noqa: E501
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
        subaccount_id: Optional[int] = None,
        nonce: Optional[int] = None,
        signature_expiry_sec: Optional[int] = None,
        is_atomic_signing: bool = False,
    ) -> PrivateWithdrawResultSchema:
        """Withdraw an asset from a subaccount to the LightAccount wallet."""

        subaccount_id = self._subaccount.id if subaccount_id is None else subaccount_id
        module_address = self._subaccount._config.contracts.WITHDRAWAL_MODULE

        currency = self._subaccount.markets.get_currency(currency=asset_name)
        if (asset := currency.protocol_asset_addresses.spot) is None:
            raise ValueError(f"asset '{asset_name}' has no spot address, found: {currency}")

        decimals = CURRENCY_DECIMALS[Currency[asset_name]]

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
