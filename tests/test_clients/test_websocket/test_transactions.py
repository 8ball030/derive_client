"""Tests for Transactions module."""

import pytest

from derive_client.data_types.generated_models import (
    PublicGetTransactionResultSchema,
)


@pytest.mark.asyncio
async def test_transactions_get(client_admin_wallet):
    transaction_id = "f589e847-c7a5-40c4-82d5-2d8cec9c93da"
    transaction = await client_admin_wallet.transactions.get(transaction_id=transaction_id)
    assert isinstance(transaction, PublicGetTransactionResultSchema)
