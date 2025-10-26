"""Tests for Transactions module."""

from decimal import Decimal

import pytest

from derive_client.data.generated.models import (
    PrivateDepositResultSchema,
    PrivateWithdrawResultSchema,
    PublicGetTransactionResultSchema,
)


@pytest.mark.asyncio
async def test_transactions_get(client_admin_wallet):
    transaction_id = "f589e847-c7a5-40c4-82d5-2d8cec9c93da"
    transaction = await client_admin_wallet.transactions.get(transaction_id=transaction_id)
    assert isinstance(transaction, PublicGetTransactionResultSchema)


@pytest.mark.asyncio
async def test_transactions_deposit_to_subaccount(client_admin_wallet):
    amount = Decimal("0.10")
    asset_name = "USDC"
    deposit = await client_admin_wallet.transactions.deposit_to_subaccount(amount=amount, asset_name=asset_name)
    assert isinstance(deposit, PrivateDepositResultSchema)


@pytest.mark.asyncio
async def test_transactions_withdraw_from_subaccount(client_admin_wallet):
    amount = Decimal("0.10")
    asset_name = "USDC"
    withdrawal = await client_admin_wallet.transactions.withdraw_from_subaccount(amount=amount, asset_name=asset_name)
    assert isinstance(withdrawal, PrivateWithdrawResultSchema)
