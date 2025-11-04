"""Tests for Orders module."""

from decimal import Decimal

from derive_client._clients.rest.http.client import HTTPClient
from derive_client.data_types.generated_models import (
    Direction,
    OrderResponseSchema,
    OrderType,
    PrivateCancelByInstrumentResultSchema,
    PrivateCancelByLabelResultSchema,
    PrivateCancelByNonceResultSchema,
    PrivateCancelResultSchema,
    PrivateGetOpenOrdersResultSchema,
    PrivateGetOrderResultSchema,
    PrivateGetOrdersResultSchema,
    PrivateOrderResultSchema,
    PrivateReplaceResultSchema,
    Result,
    TradeResponseSchema,
    TradeSettledPublicResponseSchema,
)
from tests.conftest import assert_api_calls


def test_trades_public_list(client_admin_wallet):
    trades = client_admin_wallet.trades.list_public()
    assert isinstance(trades, list)
    assert all(isinstance(t, TradeSettledPublicResponseSchema) for t in trades)

def test_trades_private_list(client_admin_wallet):
    trades = client_admin_wallet.trades.list_private()
    assert isinstance(trades, list)
    assert all(isinstance(t, TradeResponseSchema) for t in trades)

