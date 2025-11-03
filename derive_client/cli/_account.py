"""CLI commands related to wallet."""

from __future__ import annotations

import rich_click as click

from ._columns import COLLATERAL_COLUMNS, ORDER_COLUMNS, POSITION_COLUMNS, SUBACCOUNT_COLUMNS
from ._utils import explode_struct_column, struct_to_series, structs_to_dataframe


@click.group("account")
@click.pass_context
def account(ctx):
    """Account details."""


@account.command("get")
@click.pass_context
def get(ctx):
    """Account details."""

    client = ctx.obj["client"]
    account = client.account.get()
    series = struct_to_series(account)

    print("\n=== Account Info ===")
    print(series.drop("fee_info"))

    print("\n=== Fee Info ===")
    print(struct_to_series(series.fee_info).to_string(index=True))


@account.command("portfolios")
@click.pass_context
def portfolios(ctx):
    """Get all portfolios of a wallet."""

    client = ctx.obj["client"]
    portfolios = client.account.get_all_portfolios()

    df = structs_to_dataframe(portfolios)

    print("\n=== Portfolio Info ===")
    print(df[SUBACCOUNT_COLUMNS])

    print("\n=== Collaterals Info ===")
    collaterals_df = explode_struct_column(df, "subaccount_id", "collaterals")
    print(collaterals_df[COLLATERAL_COLUMNS])

    print("\n=== Positions Info ===")
    if df.positions.map(bool).any():
        positions_df = explode_struct_column(df, "subaccount_id", "positions")
        print(positions_df[POSITION_COLUMNS])
    else:
        print("No open positions")

    print("\n=== Open Orders Info ===")
    if df.open_orders.map(bool).any():
        orders_df = explode_struct_column(df, "subaccount_id", "open_orders")
        print(orders_df[ORDER_COLUMNS])
    else:
        print("No open orders")
