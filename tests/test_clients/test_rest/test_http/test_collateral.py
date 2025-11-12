"""Tests for Collateral module."""

from decimal import Decimal

from derive_client.data_types.generated_models import (
    PrivateDepositResultSchema,
    PrivateGetCollateralsResultSchema,
    PrivateWithdrawResultSchema,
)


def test_collateral_get(client_admin_wallet):
    deposit = client_admin_wallet.collateral.get()
    assert isinstance(deposit, PrivateGetCollateralsResultSchema)


def test_collateral_deposit_to_subaccount(client_admin_wallet):
    amount = Decimal("0.10")
    asset_name = "USDC"
    deposit = client_admin_wallet.collateral.deposit_to_subaccount(amount=amount, asset_name=asset_name)
    assert isinstance(deposit, PrivateDepositResultSchema)


def test_collateral_withdraw_from_subaccount(client_admin_wallet):
    amount = Decimal("0.10")
    asset_name = "USDC"
    withdrawal = client_admin_wallet.collateral.withdraw_from_subaccount(amount=amount, asset_name=asset_name)
    assert isinstance(withdrawal, PrivateWithdrawResultSchema)
