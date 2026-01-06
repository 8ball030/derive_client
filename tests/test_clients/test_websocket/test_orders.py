"""Tests for Orders module."""

from decimal import Decimal

from derive_client.data_types.generated_models import (
    Direction,
    OrderResponseSchema,
    OrderType,
    PrivateCancelByInstrumentResultSchema,
    PrivateCancelByLabelResultSchema,
    PrivateCancelByNonceResultSchema,
    PrivateCancelResultSchema,
    PrivateReplaceResultSchema,
    Result,
)
from tests.conftest import assert_api_calls


def _create_order(
    client,
    amount=Decimal("0.10"),
    instrument_name: str = "ETH-PERP",
    direction=Direction.buy,
    limit_price=Decimal("200.00"),
) -> OrderResponseSchema:
    max_fee = Decimal("1000")
    order_type = OrderType.limit
    label = "test_order"

    order = client.orders.create(
        amount=amount,
        direction=direction,
        instrument_name=instrument_name,
        limit_price=limit_price,
        max_fee=max_fee,
        order_type=order_type,
        label=label,
    )
    return order


def test_orders_create(client_admin_wallet):
    with assert_api_calls(client_admin_wallet, expected=1):
        order = _create_order(client_admin_wallet)
    assert isinstance(order, OrderResponseSchema)


def test_orders_get(client_admin_wallet):
    order = _create_order(client_admin_wallet)
    order_id = order.order_id
    order = client_admin_wallet.orders.get(order_id=order_id)
    assert isinstance(order, OrderResponseSchema)


def test_orders_list(client_admin_wallet):
    orders = client_admin_wallet.orders.list()
    assert isinstance(orders, list)
    assert all(isinstance(o, OrderResponseSchema) for o in orders)


def test_orders_list_open(client_admin_wallet):
    open_orders = client_admin_wallet.orders.list_open()
    assert isinstance(open_orders, list)
    assert all(isinstance(o, OrderResponseSchema) for o in open_orders)


def test_orders_cancel(client_admin_wallet):
    order = _create_order(client_admin_wallet)
    order_id = order.order_id
    cancelled = client_admin_wallet.orders.cancel(
        instrument_name=order.instrument_name,
        order_id=order_id,
    )
    assert isinstance(cancelled, PrivateCancelResultSchema)


def test_orders_cancel_by_label(client_admin_wallet):
    order = _create_order(client_admin_wallet)
    cancelled_by_label = client_admin_wallet.orders.cancel_by_label(label=order.label)
    assert isinstance(cancelled_by_label, PrivateCancelByLabelResultSchema)


def test_orders_cancel_by_nonce(client_admin_wallet):
    order = _create_order(client_admin_wallet)
    cancelled_by_label = client_admin_wallet.orders.cancel_by_nonce(
        instrument_name=order.instrument_name,
        nonce=order.nonce,
    )
    assert isinstance(cancelled_by_label, PrivateCancelByNonceResultSchema)


def test_orders_cancel_by_instrument(client_admin_wallet):
    order = _create_order(client_admin_wallet)
    cancelled_by_label = client_admin_wallet.orders.cancel_by_instrument(instrument_name=order.instrument_name)
    assert isinstance(cancelled_by_label, PrivateCancelByInstrumentResultSchema)


def test_orders_cancel_all(client_admin_wallet):
    cancelled_all = client_admin_wallet.orders.cancel_all()
    assert isinstance(cancelled_all, Result)


def test_orders_replace(client_admin_wallet):
    order = _create_order(client_admin_wallet)
    order_id = order.order_id
    with assert_api_calls(client_admin_wallet, expected=1):
        replace = client_admin_wallet.orders.replace(
            amount=order.amount,
            direction=order.direction,
            instrument_name=order.instrument_name,
            limit_price=order.limit_price,
            max_fee=order.max_fee,
            order_id_to_cancel=order_id,
        )
    assert isinstance(replace, PrivateReplaceResultSchema)
