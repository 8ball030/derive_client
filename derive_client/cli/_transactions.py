"""CLI commands for transactions."""

from __future__ import annotations

from decimal import Decimal

import pandas as pd
import rich_click as click

from ._utils import struct_to_series


@click.group("transaction")
@click.pass_context
def transaction(ctx):
    """Move funds between wallet and subaccount."""


@transaction.command("get")
@click.argument(
    "transaction_id",
    required=True,
)
@click.pass_context
def get(ctx, transaction_id: str):
    """Used for getting a transaction by its transaction id."""

    client = ctx.obj["client"]
    subaccount = client.active_subaccount
    transaction = subaccount.transactions.get(transaction_id=transaction_id)

    tx_data = dict(
        subaccount_id=transaction.data.subaccount_id,
        status=transaction.status.name,
        asset_name=transaction.data.asset_name,
        amount=transaction.data.data.amount,
    )
    series = pd.Series(tx_data)

    print("\n=== Transaction ===")
    print(series.to_string(index=True))
    if transaction.error_log:
        print(f"\nError: {transaction.error_log.error}")


@transaction.command("deposit-to-subaccount")
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
    """Deposit an asset to a subaccount."""

    client = ctx.obj["client"]
    subaccount = client.active_subaccount
    deposit = subaccount.transactions.deposit_to_subaccount(
        amount=amount,
        asset_name=asset_name,
    )

    print(f"\n=== Deposit to subaccount {subaccount.id} ===")
    print(struct_to_series(deposit).to_string(index=True))


@transaction.command("withdraw-from-subaccount")
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
    """Withdraw an asset to wallet."""

    client = ctx.obj["client"]
    subaccount = client.active_subaccount
    withdrawal = subaccount.transactions.withdraw_from_subaccount(
        amount=amount,
        asset_name=asset_name,
    )

    print(f"\n=== Withdrawal from subaccount {subaccount.id} ===")
    print(struct_to_series(withdrawal).to_string(index=True))
