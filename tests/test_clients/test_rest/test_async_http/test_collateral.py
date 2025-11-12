"""Tests for Collateral module."""

from decimal import Decimal

import pytest

from derive_client.data_types.generated_models import (
    PrivateDepositResultSchema,
    PrivateWithdrawResultSchema,
)


@pytest.mark.asyncio
async def test_transactions_deposit_to_subaccount(client_admin_wallet):
    amount = Decimal("0.10")
    asset_name = "USDC"
    deposit = await client_admin_wallet.collateral.deposit_to_subaccount(amount=amount, asset_name=asset_name)
    assert isinstance(deposit, PrivateDepositResultSchema)


@pytest.mark.asyncio
async def test_transactions_withdraw_from_subaccount(client_admin_wallet):
    amount = Decimal("0.10")
    asset_name = "USDC"
    withdrawal = await client_admin_wallet.collateral.withdraw_from_subaccount(amount=amount, asset_name=asset_name)
    assert isinstance(withdrawal, PrivateWithdrawResultSchema)
