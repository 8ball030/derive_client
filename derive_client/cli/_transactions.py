"""CLI commands for transactions."""

from __future__ import annotations

import rich_click as click


@click.group("transaction")
@click.pass_context
def transaction(ctx):
    """Query transaction status and details."""


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

    print("\n=== Transaction ===")
    print(f"Status: {transaction.status.name}")
    print(f"Tx Hash: {transaction.transaction_hash}")
    if transaction.error_log:
        print(f"\nError: {transaction.error_log}")
