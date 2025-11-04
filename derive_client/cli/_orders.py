"""CLI commands for orders."""

from __future__ import annotations

from decimal import Decimal

import rich_click as click

from derive_client._clients.rest.http.client import HTTPClient
from derive_client.data_types import Direction, OrderType

from ._columns import ORDER_COLUMNS
from ._utils import struct_to_series, structs_to_dataframe


@click.group("order")
@click.pass_context
def order(ctx):
    """Create, view, list, and cancel orders."""


@order.command("create")
@click.argument(
    "instrument_name",
    required=True,
)
@click.argument(
    "direction",
    required=True,
    type=click.Choice([i.value for i in Direction]),
)
@click.argument(
    "order_type",
    required=True,
    type=click.Choice([i.value for i in OrderType]),
    default=OrderType.limit,
)
@click.argument(
    "reduce_only",
    required=True,
    type=bool,
    default=False,
)
@click.option(
    "--amount",
    "-a",
    required=True,
    type=Decimal,
)
@click.option(
    "--price",
    "-p",
    "limit_price",
    required=True,
    type=Decimal,
)
@click.pass_context
def create(
    ctx,
    instrument_name: str,
    amount: Decimal,
    limit_price: Decimal,
    direction: str,
    order_type: str,
    reduce_only: bool,
):
    """Create a new order.

    Examples:
        drv order create ETH-PERP buy -a 0.1 -p 2000
    """

    client: HTTPClient = ctx.obj["client"]
    subaccount = client.active_subaccount
    order = subaccount.orders.create(
        amount=amount,
        direction=Direction(direction),
        instrument_name=instrument_name,
        limit_price=limit_price,
        order_type=OrderType(order_type),
        reduce_only=reduce_only,
    )

    print("\n=== Order ===")
    print(struct_to_series(order)[ORDER_COLUMNS].to_string(index=True))


@order.command("get")
@click.argument(
    "order_id",
    required=True,
)
@click.pass_context
def get(ctx, order_id: str):
    """Get state of an order by order id.

    Examples:
        drv order get 02379d44-020a-41a1-bcc1-4509344f1796
    """

    client = ctx.obj["client"]
    subaccount = client.active_subaccount
    order = subaccount.orders.get(order_id=order_id)

    print("\n=== Order ===")
    print(struct_to_series(order).to_string(index=True))


@order.command("list-open")
@click.pass_context
def list_open(ctx):
    """List all open orders of a subacccount.

    Examples:
        drv order list-open
    """

    client: HTTPClient = ctx.obj["client"]
    subaccount = client.active_subaccount
    open_orders = subaccount.orders.list_open()

    print(f"\n=== Open Orders for subaccount {client.active_subaccount.id} ===")
    if open_orders:
        print(structs_to_dataframe(open_orders)[ORDER_COLUMNS])
    else:
        print("No open orders")


@order.command("cancel")
@click.argument(
    "order_id",
    required=True,
)
@click.argument(
    "instrument_name",
    required=True,
)
@click.pass_context
def cancel(ctx, order_id: str, instrument_name: str):
    """Cancel a single order.

    Examples:
        drv order cancel 793b58f0-1b83-41cc-8e85-3ec3b35c3c50 ETH-PERP
    """

    client = ctx.obj["client"]
    subaccount = client.active_subaccount
    cancelled_order = subaccount.orders.cancel(order_id=order_id, instrument_name=instrument_name)

    print("\n=== Cancelled Order ===")
    print(struct_to_series(cancelled_order).to_string(index=True))


@order.command("cancel-all")
@click.pass_context
def cancel_all(ctx):
    """Cancel all orders.

    Examples:
        drv order cancel-all
    """

    client = ctx.obj["client"]
    subaccount = client.active_subaccount
    result = subaccount.orders.cancel_all()

    print(f"All orders cancelled: {result.value}")
