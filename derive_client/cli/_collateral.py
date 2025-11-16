"""CLI commands for transactions."""

from __future__ import annotations

from decimal import Decimal

import rich_click as click

from ._utils import struct_to_series, structs_to_dataframe


@click.group("collateral")
@click.pass_context
def collateral(ctx):
    """Manage collateral and margin."""


@collateral.command("get")
@click.pass_context
def get(ctx):
    """Get subaccount collaterals."""

    client = ctx.obj["client"]
    subaccount = client.active_subaccount
    collateral = subaccount.collateral.get()

    print(f"\n=== Collaterals of subaccount {subaccount.id} ===")
    print(structs_to_dataframe(collateral.collaterals))


@collateral.command("get-margin")
@click.pass_context
def get_margin(ctx):
    """Calculates margin for a given subaccount.

    Does not take into account open orders margin requirements.
    """

    client = ctx.obj["client"]
    subaccount = client.active_subaccount
    margin = subaccount.collateral.get_margin()

    print(f"\n=== Margin of subaccount {subaccount.id} ===")
    print(struct_to_series(margin).to_string(index=True))


@collateral.command("deposit-to-subaccount")
@click.argument(
    "amount",
    type=Decimal,
    required=True,
)
@click.argument(
    "asset_name",
    required=True,
)
@click.pass_context
def deposit_to_subaccount(ctx, amount: Decimal, asset_name: str):
    """Deposit an asset to your subaccount."""

    client = ctx.obj["client"]
    subaccount = client.active_subaccount
    deposit = subaccount.collateral.deposit_to_subaccount(
        amount=amount,
        asset_name=asset_name,
    )

    print(f"\n=== Deposit to subaccount {subaccount.id} ===")
    print(struct_to_series(deposit).to_string(index=True))


@collateral.command("withdraw-from-subaccount")
@click.argument(
    "amount",
    type=Decimal,
    required=True,
)
@click.argument(
    "asset_name",
    required=True,
)
@click.pass_context
def withdraw_from_subaccount(ctx, amount: Decimal, asset_name: str):
    """Withdraw an asset to your lightaccount wallet."""

    client = ctx.obj["client"]
    subaccount = client.active_subaccount
    withdrawal = subaccount.collateral.withdraw_from_subaccount(
        amount=amount,
        asset_name=asset_name,
    )

    print(f"\n=== Withdrawal from subaccount {subaccount.id} ===")
    print(struct_to_series(withdrawal).to_string(index=True))
