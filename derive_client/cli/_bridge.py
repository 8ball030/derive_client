"""CLI commands for bridging operations."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Type, TypeVar

import rich_click as click
from rich import print

from derive_client._clients.rest.http.client import BridgeClient, HTTPClient
from derive_client.data_types import (
    ChainID,
    Currency,
    TxStatus,
)

from ._utils import rich_prepared_tx

E = TypeVar("E", bound=Enum)


class EnumChoice(click.Choice):
    """Click choice type that converts to enum."""

    def __init__(self, enum_type: Type[E], case_sensitive: bool = False):
        self.enum_type = enum_type
        super().__init__([e.name for e in enum_type], case_sensitive=case_sensitive)

    def convert(self, value, param, ctx):
        name = super().convert(value, param, ctx)
        return self.enum_type[name]


@click.group("bridge")
@click.pass_context
def bridge(ctx):
    """Bridge assets to/from Derive (ETH, ERC-20, DRV)."""


@bridge.command("deposit")
@click.option(
    "--chain-id",
    "-c",
    type=EnumChoice(ChainID),
    required=True,
    help="The chain ID to bridge FROM.",
)
@click.option(
    "--currency",
    "-t",
    type=EnumChoice(Currency),
    required=True,
    help="The token symbol (e.g. weETH) to bridge.",
)
@click.option(
    "--amount",
    "-a",
    type=Decimal,
    required=True,
    help="The amount to deposit in decimal units of the selected token (converted to base units internally).",
)
@click.pass_context
def deposit(ctx, chain_id: ChainID, currency: Currency, amount: Decimal):
    """
    Deposit funds via the socket superbridge to a Derive funding account.

    Example:
        $ cli bridge deposit --chain-id 8453 --currency weETH --amount 0.001
    """

    client: HTTPClient = ctx.obj["client"]
    bridge: BridgeClient = client.bridge

    prepared_tx = bridge.prepare_deposit_tx(chain_id=chain_id, currency=currency, amount=amount)

    print(rich_prepared_tx(prepared_tx))
    if not click.confirm("Do you want to submit this transaction?", default=False):
        print("[yellow]Aborted by user.[/yellow]")
        return

    tx_result = bridge.submit_tx(prepared_tx=prepared_tx)
    bridge_tx_result = bridge.poll_tx_progress(tx_result=tx_result)

    match bridge_tx_result.status:
        case TxStatus.SUCCESS:
            print(f"[bold green]Bridging {currency.name} from {chain_id.name} to DERIVE successful![/bold green]")
        case TxStatus.FAILED:
            print(f"[bold red]Bridging {currency.name} from {chain_id.name} to DERIVE failed.[/bold red]")
        case TxStatus.PENDING:
            print(f"[yellow]Bridging {currency.name} from {chain_id.name} to DERIVE is pending...[/yellow]")
        case _:
            raise click.ClickException(f"Exception attempting to deposit:\n{bridge_tx_result}")


@bridge.command("gas")
@click.option(
    "--amount",
    required=True,
    type=Decimal,
)
@click.option(
    "--chain-id",
    type=EnumChoice(ChainID),
    default=ChainID.ETH,
    show_default=True,
    required=True,
)
@click.pass_context
def gas(ctx, amount: Decimal, chain_id: ChainID):
    """Deposit gas (native token) for bridging."""
    click.echo(f"Deposit gas: chain={chain_id} amount={amount}")

    """
    Deposit gas (native token) for bridging via the standard bridge to the owner's EOA.

    Example:
        $ cli bridge gas --amount 0.001 --chain-id ETH
    """

    client: HTTPClient = ctx.obj["client"]
    bridge: BridgeClient = client.bridge

    currency = Currency.ETH

    prepared_tx = bridge.prepare_gas_deposit_tx(amount=amount, chain_id=chain_id)

    print(rich_prepared_tx(prepared_tx))
    if not click.confirm("Do you want to submit this transaction?", default=False):
        print("[yellow]Aborted by user.[/yellow]")
        return

    tx_result = bridge.submit_tx(prepared_tx=prepared_tx)
    bridge_tx_result = bridge.poll_tx_progress(tx_result=tx_result)

    match bridge_tx_result.status:
        case TxStatus.SUCCESS:
            print(f"[bold green]Bridging {currency.name} from {chain_id.name} to DERIVE successful![/bold green]")
        case TxStatus.FAILED:
            print(f"[bold red]Bridging {currency.name} from {chain_id.name} to DERIVE failed.[/bold red]")
        case TxStatus.PENDING:
            print(f"[yellow]Bridging {currency.name} from {chain_id.name} to DERIVE is pending...[/yellow]")
        case _:
            raise click.ClickException(f"Exception attempting to deposit:\n{bridge_tx_result}")


@bridge.command("withdraw")
@click.option(
    "--chain-id",
    "-c",
    type=click.Choice([c.name for c in ChainID]),
    required=True,
    help="The chain ID to bridge FROM.",
)
@click.option(
    "--currency",
    "-t",
    type=click.Choice([c.name for c in Currency]),
    required=True,
    help="The token symbol (e.g. weETH) to bridge.",
)
@click.option(
    "--amount",
    "-a",
    type=Decimal,
    required=True,
    help="The amount to withdraw in human units of the selected token (converted to base units internally).",
)
@click.pass_context
def withdraw(ctx, chain_id: ChainID, currency: Currency, amount: Decimal):
    """
    Withdraw funds from Derive funding account via the Withdraw Wrapper contract.

    Example:
        $ cli bridge withdraw --chain-id BASE --currency weETH --amount 0.001
    """

    client: HTTPClient = ctx.obj["client"]
    bridge: BridgeClient = client.bridge

    prepared_tx = bridge.prepare_withdrawal_tx(chain_id=chain_id, currency=currency, amount=amount)

    print(rich_prepared_tx(prepared_tx))
    if not click.confirm("Do you want to submit this transaction?", default=False):
        print("[yellow]Aborted by user.[/yellow]")
        return

    tx_result = bridge.submit_tx(prepared_tx=prepared_tx)
    bridge_tx_result = bridge.poll_tx_progress(tx_result=tx_result)

    match bridge_tx_result.status:
        case TxStatus.SUCCESS:
            print(f"[bold green]Bridging {currency.name} from DERIVE to {chain_id.name} successful![/bold green]")
        case TxStatus.FAILED:
            print(f"[bold red]Bridging {currency.name} from DERIVE to {chain_id.name} failed.[/bold red]")
        case TxStatus.PENDING:
            print(f"[yellow]Bridging {currency.name} from DERIVE to {chain_id.name} is pending...[/yellow]")
        case _:
            raise click.ClickException(f"Exception attempting to withdraw:\n{bridge_tx_result}")
