"""CLI commands for positions."""

from __future__ import annotations

from decimal import Decimal

import pandas as pd
import rich_click as click

from ._columns import OPEN_POSITION_COLUMNS, TRADE_COLUMNS
from ._utils import struct_to_series, structs_to_dataframe


@click.group("position")
@click.pass_context
def position(ctx):
    """Inspect and transfer positions across subaccounts."""


@position.command("list")
@click.pass_context
def list(ctx):
    """List active positions of a subaccount."""

    client = ctx.obj["client"]
    subaccount = client.active_subaccount
    positions = subaccount.positions.list()
    df = structs_to_dataframe(positions)

    print(f"\n=== Active Positions of subaccount {subaccount.id} ===")
    if not df.empty:
        print(df[OPEN_POSITION_COLUMNS])
    else:
        print("No open positions")


@position.command("transfer")
@click.argument(
    "instrument_name",
    required=True,
)
@click.argument(
    "amount",
    required=True,
    type=Decimal,
)
@click.argument(
    "to_subaccount",
    required=True,
    type=int,
)
@click.pass_context
def transfer(ctx, instrument_name: str, amount: Decimal, to_subaccount: int):
    """Transfers a positions from one subaccount to another, owned by the same wallet.

    Examples:
        drv position transfer BTC-PERP 0.1 123456
        drv position transfer -- ETH-PERP -0.1 123456
    """

    client = ctx.obj["client"]
    subaccount = client.active_subaccount
    transfer = subaccount.positions.transfer(
        instrument_name=instrument_name,
        amount=amount,
        to_subaccount=to_subaccount,
    )
    series = struct_to_series(transfer)
    trades = pd.DataFrame([struct_to_series(series.maker_trade), struct_to_series(series.taker_trade)])

    print(f"\n=== Transfer Position from subaccount {subaccount.id} to {to_subaccount} ===")
    print(trades[TRADE_COLUMNS])
