"""CLI commands for transactions."""

from __future__ import annotations

from decimal import Decimal

import rich_click as click

from ._utils import struct_to_series


@click.group("collateral")
@click.pass_context
def collateral(ctx):
    """Manage collateral and margin."""


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
