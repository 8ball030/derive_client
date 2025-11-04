"""Tests for Orders module."""

from derive_client.data_types.generated_models import (
    TradeResponseSchema,
    TradeSettledPublicResponseSchema,
)


def test_trades_public_list(client_admin_wallet):
    trades = client_admin_wallet.trades.list_public()
    assert isinstance(trades, list)
    assert all(isinstance(t, TradeSettledPublicResponseSchema) for t in trades)


def test_trades_private_list(client_admin_wallet):
    trades = client_admin_wallet.trades.list_private()
    assert isinstance(trades, list)
    assert all(isinstance(t, TradeResponseSchema) for t in trades)
