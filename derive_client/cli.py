"""
Cli module in order to allow interaction.
"""

import math
import os
from pathlib import Path
from textwrap import dedent

import pandas as pd
import rich_click as click
from dotenv import load_dotenv
from rich import print
from rich.table import Table

from derive_client.analyser import PortfolioAnalyser
from derive_client.data_types import (
    ChainID,
    CollateralAsset,
    Currency,
    Environment,
    InstrumentType,
    OrderSide,
    OrderStatus,
    OrderType,
    PreparedBridgeTx,
    SubaccountType,
    TxStatus,
    UnderlyingCurrency,
)
from derive_client.derive import DeriveClient
from derive_client.utils import from_base_units, get_logger

click.rich_click.USE_RICH_MARKUP = True
pd.set_option("display.precision", 2)


def fmt_sig_up_to(x: float, sig: int = 4) -> str:
    """Format x to up to `sig` significant digits, preserving all necessary decimals."""

    if x == 0:
        return "0"

    order = math.floor(math.log10(abs(x)))
    decimals = max(sig - order - 1, 0)
    formatted = f"{x:.{decimals}f}"
    return formatted.rstrip("0").rstrip(".")


def rich_prepared_tx(prepared_tx: PreparedBridgeTx):
    table = Table(title="Prepared Bridge Transaction", show_header=False, box=None)
    if prepared_tx.amount > 0:
        human_amount = from_base_units(amount=prepared_tx.amount, currency=prepared_tx.currency)
        table.add_row("Amount", f"{human_amount} {prepared_tx.currency.name} (base units: {prepared_tx.amount})")
    if prepared_tx.fee_in_token > 0:
        fee_human = from_base_units(prepared_tx.fee_in_token, prepared_tx.currency)
        table.add_row(
            "Estimated fee (token)",
            f"{fmt_sig_up_to(fee_human)} {prepared_tx.currency.name} (base units: {prepared_tx.fee_in_token})",
        )
    if prepared_tx.value and prepared_tx.value > 0:
        human_value = prepared_tx.value / 1e18
        table.add_row("Value", f"{human_value} ETH (base units: {prepared_tx.value})")
    if prepared_tx.fee_value > 0:
        human_fee_value = fmt_sig_up_to(prepared_tx.fee_value / 1e9)
        table.add_row("Estimated fee (native)", f"{human_fee_value} gwei (base units: {prepared_tx.fee_value})")

    # table.add_row("Value", f"{fmt_sig_up_to(prepared_tx.value / 1e18)} ETH (base units: {prepared_tx.value})")
    table.add_row("Source chain", prepared_tx.source_chain.name)
    table.add_row("Target chain", prepared_tx.target_chain.name)
    table.add_row("Bridge type", prepared_tx.bridge_type.name)
    table.add_row("Tx hash", prepared_tx.tx_hash)
    table.add_row("Gas limit", str(prepared_tx.gas))
    table.add_row("Max fee/gas", f"{fmt_sig_up_to(prepared_tx.max_fee_per_gas / 1e9)} gwei")
    table.add_row("Max total fee", f"{fmt_sig_up_to(prepared_tx.max_total_fee / 1e9)} gwei")

    return table


def set_logger(ctx, level):
    """Set the logger."""
    if not hasattr(ctx, "logger"):
        ctx.logger = get_logger()
        ctx.logger.setLevel(level)
    return ctx.logger


def set_client(ctx, env, subaccount_id, derive_sc_wallet, signer_key_path):
    """Set the client."""
    # we use dotenv to load the env vars from DIRECTORY where the cli tool is executed
    _path = os.getcwd()
    env_path = os.path.join(_path, ".env")
    load_dotenv(dotenv_path=env_path)
    if not hasattr(ctx, "client"):
        if signer_key_path:
            private_key = Path(signer_key_path).read_text().strip()
        else:
            private_key = os.environ.get("ETH_PRIVATE_KEY")
        if not private_key:
            raise ValueError("Private key not found. Please provide a valid private key.")

        auth = {
            "private_key": private_key,
            "logger": ctx.logger,
            "verbose": ctx.logger.level == "DEBUG",
        }
        env = Environment(env) if isinstance(env, Environment) else Environment[env.upper()]

        if not derive_sc_wallet and subaccount_id is None:
            msg = dedent(
                """
                Please provide either a wallet or a subaccount_id in the .env file at {env_path}"
                Wallet is the address of the account to use, subaccount_id is the subaccount to use"
                Subaccount_id is the subaccount to use"
                You must provide the `DERIVE_SC_WALLET" flag.
                """
            )
            raise ValueError(msg)
        ctx.client = DeriveClient(**auth, env=env, subaccount_id=subaccount_id, wallet=derive_sc_wallet)

    if ctx.logger.level == "DEBUG":
        print(f"Client created for environment `{ctx.client.env.value}`")
    return ctx.client


@click.group("Derive Client")
@click.option(
    "--log-level",
    "-l",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    help="Logging level.",
)
@click.option(
    "--env",
    "-e",
    type=click.Choice([e.value for e in Environment]),
    default=Environment.PROD.value,
    help="Environment to use (test or prod).",
)
@click.option(
    "--subaccount-id",
    "-s",
    type=int,
    default=None,
    help="Subaccount ID to use. If not provided, the client will use the wallet address.",
)
@click.option("--derive-sc-wallet", "-w", type=str, help="Wallet address to use.")
@click.option(
    "--signer-key-path",
    "-k",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to the file containing the private key for the signer.",
)
@click.pass_context
def cli(ctx, log_level, env, subaccount_id, derive_sc_wallet, signer_key_path):
    """Derive v2 client command line interface."""
    ctx.ensure_object(dict)
    ctx.obj["logger"] = set_logger(ctx, log_level)
    ctx.obj["client"] = set_client(ctx, env, subaccount_id, derive_sc_wallet, signer_key_path)


@cli.group("bridge")
def bridge():
    """Interact with bridging functions."""


@bridge.command("deposit")
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
    type=float,
    required=True,
    help="The amount to deposit in human units of the selected token (converted to base units internally).",
)
@click.pass_context
def deposit(ctx, chain_id, currency, amount):
    """
    Deposit funds via the socket superbridge to a Derive funding account.

    Example:
        $ cli bridge deposit --chain-id 8453 --currency weETH --amount 0.001
    """

    chain_id = ChainID[chain_id]
    currency = Currency[currency]

    client: DeriveClient = ctx.obj["client"]

    prepared_tx = client.prepare_deposit_to_derive(chain_id=chain_id, currency=currency, human_amount=amount)

    print(rich_prepared_tx(prepared_tx))
    if not click.confirm("Do you want to submit this transaction?", default=False):
        print("[yellow]Aborted by user.[/yellow]")
        return

    tx_result = client.submit_bridge_tx(prepared_tx=prepared_tx)
    bridge_tx_result = client.poll_bridge_progress(tx_result=tx_result)

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
    type=float,
    required=True,
    help="The amount to withdraw in human units of the selected token (converted to base units internally).",
)
@click.pass_context
def withdraw(ctx, chain_id, currency, amount):
    """
    Withdraw funds from Derive funding account via the Withdraw Wrapper contract.

    Example:
        $ cli bridge withdraw --chain-id BASE --currency weETH --amount 0.001
    """

    chain_id = ChainID[chain_id]
    currency = Currency[currency]

    client: DeriveClient = ctx.obj["client"]

    prepared_tx = client.prepare_withdrawal_from_derive(chain_id=chain_id, currency=currency, human_amount=amount)

    print(rich_prepared_tx(prepared_tx))
    if not click.confirm("Do you want to submit this transaction?", default=False):
        print("[yellow]Aborted by user.[/yellow]")
        return

    tx_result = client.submit_bridge_tx(prepared_tx=prepared_tx)
    bridge_tx_result = client.poll_bridge_progress(tx_result=tx_result)

    match bridge_tx_result.status:
        case TxStatus.SUCCESS:
            print(f"[bold green]Bridging {currency.name} from DERIVE to {chain_id.name} successful![/bold green]")
        case TxStatus.FAILED:
            print(f"[bold red]Bridging {currency.name} from DERIVE to {chain_id.name} failed.[/bold red]")
        case TxStatus.PENDING:
            print(f"[yellow]Bridging {currency.name} from DERIVE to {chain_id.name} is pending...[/yellow]")
        case _:
            raise click.ClickException(f"Exception attempting to withdraw:\n{bridge_tx_result}")


@cli.group("instruments")
def instruments():
    """Interact with markets."""


@cli.group("tickers")
def tickers():
    """Interact with tickers."""


@cli.group("subaccounts")
def subaccounts():
    """Interact with subaccounts."""


@cli.group("orders")
def orders():
    """Interact with orders."""


@cli.group("collateral")
def collateral():
    """Interact with collateral."""


@cli.group("positions")
def positions():
    """Interact with positions."""


@cli.group("mmp")
def mmp():
    """Interact with market making parameters."""


@mmp.command("fetch")
@click.option(
    "--underlying-currency",
    "-u",
    type=click.Choice([f.value for f in UnderlyingCurrency]),
    default=UnderlyingCurrency.ETH.value,
)
@click.option(
    "--subaccount-id",
    "-s",
    type=int,
    required=True,
)
@click.pass_context
def fetch_mmp(ctx, underlying_currency, subaccount_id):
    """Fetch market making parameters."""
    client = ctx.obj["client"]
    mmp = client.get_mmp_config(subaccount_id=subaccount_id, currency=UnderlyingCurrency(underlying_currency))
    print(mmp)


@mmp.command("set")
@click.option(
    "--underlying-currency",
    "-u",
    type=click.Choice([f.value for f in UnderlyingCurrency]),
    default=UnderlyingCurrency.ETH.value,
)
@click.option(
    "--subaccount-id",
    "-s",
    type=int,
    required=True,
)
@click.option(
    "--frozen-time",
    "-f",
    type=int,
    required=True,
    help="Time interval in ms setting how long the subaccount is frozen after an mmp trigger, "
    + "if 0 then a manual reset would be required via private/reset_mmp",
    default=10000,
)
@click.option(
    "--interval",
    "-i",
    type=int,
    required=True,
    help="Time interval in ms over which the limits are monotored, if 0 then mmp is disabled",
    default=10000,
)
@click.option(
    "--amount-limit",
    "-a",
    type=float,
    help="Maximum total order amount that can be traded within the mmp_interval across all "
    + "instruments of the provided currency. The amounts are not netted, so a filled bid "
    + "of 1 and a filled ask of 2 would count as 3.",
    default=5,
)
@click.option(
    "--delta-limit",
    "-d",
    type=float,
    help="Maximum total delta that can be traded within the mmp_interval across all instruments "
    + "of the provided currency. This quantity is netted, so a filled order with +1 delta and "
    + "a filled order with -2 delta would count as 3",
    default=2,
)
@click.pass_context
def set_mmp(
    ctx,
    underlying_currency,
    subaccount_id,
    frozen_time,
    interval,
    amount_limit,
    delta_limit,
):
    """Set market making parameters."""
    client = ctx.obj["client"]
    mmp = client.set_mmp_config(
        subaccount_id=subaccount_id,
        currency=UnderlyingCurrency(underlying_currency),
        mmp_frozen_time=frozen_time,
        mmp_interval=interval,
        mmp_amount_limit=amount_limit,
        mmp_delta_limit=delta_limit,
    )
    print(mmp)


@positions.command("fetch")
@click.pass_context
def fetch_positions(ctx):
    """Fetch positions."""
    print("Fetching positions")
    client = ctx.obj["client"]
    positions = client.get_positions()
    print(positions)


@collateral.command("fetch")
@click.pass_context
def fetch_collateral(ctx):
    """Fetch collateral."""
    print("Fetching collateral")
    client = ctx.obj["client"]
    collateral = client.get_collaterals()
    print(collateral)


@instruments.command("fetch")
@click.pass_context
@click.option(
    "--instrument-type",
    "-i",
    type=click.Choice([f.value for f in InstrumentType]),
    default=InstrumentType.PERP.value,
)
@click.option(
    "--currency",
    "-c",
    type=click.Choice([f.value for f in UnderlyingCurrency]),
    default=UnderlyingCurrency.ETH.value,
)
def fetch_instruments(ctx, instrument_type, currency):
    """Fetch markets."""
    client = ctx.obj["client"]
    markets = client.fetch_instruments(
        instrument_type=InstrumentType(instrument_type),
        currency=UnderlyingCurrency(currency),
    )
    print(markets)


@tickers.command("fetch")
@click.pass_context
@click.argument(
    "instrument_name",
    type=str,
)
def fetch_tickers(ctx, instrument_name):
    """Fetch tickers."""
    client = ctx.obj["client"]
    ticker = client.fetch_ticker(instrument_name=instrument_name)
    print(ticker)


@collateral.command("transfer")
@click.pass_context
@click.option(
    "--amount",
    "-a",
    type=float,
    required=True,
)
@click.option(
    "--to",
    "-t",
    type=int,
    required=True,
    help="Subaccount ID to transfer to",
)
@click.option(
    "--asset",
    "-s",
    type=click.Choice([f.value for f in CollateralAsset]),
    default=CollateralAsset.USDC.value,
)
def transfer_collateral(ctx, amount, to, asset):
    """Transfer collateral."""
    client: DeriveClient = ctx.obj["client"]
    result = client.transfer_collateral(amount=amount, to=to, asset=CollateralAsset(asset))

    print(result)


@subaccounts.command("all")
@click.pass_context
def fetch_subaccounts(ctx):
    """Fetch subaccounts."""
    print("Fetching subaccounts")
    client: DeriveClient = ctx.obj["client"]
    subaccounts = client.fetch_subaccounts()
    print(subaccounts)


@subaccounts.command("fetch")
@click.argument(
    "subaccount_id",
    type=int,
)
@click.option(
    "--underlying-currency",
    "-u",
    type=click.Choice([f.value for f in UnderlyingCurrency]),
    default=UnderlyingCurrency.ETH.value,
)
@click.option(
    "--columns",
    "-c",
    type=str,
    default=None,
)
@click.pass_context
def fetch_subaccount(ctx, subaccount_id, underlying_currency, columns):
    """Fetch subaccount."""
    print("Fetching subaccount")
    print(f"Subaccount ID: {subaccount_id}")
    print(f"Underlying currency: {underlying_currency}")
    client: DeriveClient = ctx.obj["client"]
    subaccount = client.fetch_subaccount(subaccount_id=subaccount_id)
    analyser = PortfolioAnalyser(subaccount)
    print("Positions")
    analyser.print_positions(underlying_currency=underlying_currency, columns=columns)
    print("Total Greeks")
    print(analyser.get_total_greeks(underlying_currency))
    print("Subaccount values")
    print(f"Portfolio Value: ${analyser.get_subaccount_value():.2f}")


@subaccounts.command("create")
@click.pass_context
@click.option(
    "--underlying-currency",
    "-u",
    type=click.Choice([f.value for f in UnderlyingCurrency]),
    default=UnderlyingCurrency.ETH.value,
)
@click.option(
    "--subaccount-type",
    "-s",
    type=click.Choice([f.value for f in SubaccountType]),
    default=SubaccountType.PORTFOLIO.value,
)
@click.option(
    "--collateral-asset",
    "-c",
    type=click.Choice([f.value for f in CollateralAsset]),
    default=CollateralAsset.USDC.value,
)
@click.option(
    "--amount",
    "-a",
    type=float,
    default=0,
)
def create_subaccount(ctx, collateral_asset, underlying_currency, subaccount_type, amount):
    """Create subaccount."""
    underlying_currency = UnderlyingCurrency(underlying_currency)
    subaccount_type = SubaccountType(subaccount_type)
    collateral_asset = CollateralAsset(collateral_asset)
    print(f"Creating subaccount with collateral asset {collateral_asset} and underlying currency {underlying_currency}")
    client: DeriveClient = ctx.obj["client"]
    subaccount_id = client.create_subaccount(
        amount=int(amount * 1e6),
        subaccount_type=subaccount_type,
        collateral_asset=collateral_asset,
        underlying_currency=underlying_currency,
    )
    print(subaccount_id)


@orders.command("fetch")
@click.pass_context
@click.option(
    "--instrument-name",
    "-i",
    type=str,
    default=None,
)
@click.option(
    "--label",
    "-l",
    type=str,
    default=None,
)
@click.option(
    "--page",
    "-p",
    type=int,
    default=1,
)
@click.option(
    "--page-size",
    "-s",
    type=int,
    default=100,
)
@click.option(
    "--status",
    "-s",
    type=click.Choice([f.value for f in OrderStatus]),
    default=None,
)
@click.option(
    "--regex",
    "-r",
    type=str,
    default=None,
)
def fetch_orders(ctx, instrument_name, label, page, page_size, status, regex):
    """Fetch orders."""
    print("Fetching orders")
    client: DeriveClient = ctx.obj["client"]
    orders = client.fetch_orders(
        instrument_name=instrument_name,
        label=label,
        page=page,
        page_size=page_size,
        status=status,
    )
    # apply the regex if exists to filter the orders
    if regex:
        orders = [o for o in orders if regex in o["instrument_name"]]
    df = pd.DataFrame.from_records(orders)
    print(orders[0])
    instrument_names = df["instrument_name"].unique()
    print(f"Found {len(instrument_names)} instruments")
    print(instrument_names)
    # print the orders
    # perform some analysis
    df["amount"] = pd.to_numeric(df["amount"])
    df["filled_amount"] = pd.to_numeric(df["filled_amount"])
    df["limit_price"] = pd.to_numeric(df["limit_price"])

    buys = df[df["direction"] == "buy"]
    sells = df[df["direction"] == "sell"]
    print("Buys")
    print(buys)
    print("Sells")
    print(sells)

    print("Average buy cost")
    # we determine by the average price of the buys by the amount
    df["cost"] = buys["limit_price"] * buys["amount"]
    print(df["cost"].sum())
    amount = buys["amount"].sum()
    print(amount)
    buy_total_cost = df["cost"].sum()
    print(f"Price per unit: {buy_total_cost / amount}")
    print(buy_total_cost / amount)
    print("Average sell cost")
    # we determine by the average price of the buys by the amount
    df["cost"] = sells["limit_price"] * sells["amount"]
    print(df["cost"].sum())
    amount = sells["amount"].sum()
    print(amount)
    sell_total_cost = df["cost"].sum()
    print(f"Price per unit: {sell_total_cost / amount}")
    print(sell_total_cost / amount)


@orders.command("cancel")
@click.pass_context
@click.option(
    "--order-id",
    "-o",
    type=str,
)
@click.option(
    "--instrument-name",
    "-i",
    type=str,
)
def cancel_order(ctx, order_id, instrument_name):
    """Cancel order."""
    print("Cancelling order")
    client: DeriveClient = ctx.obj["client"]
    result = client.cancel(order_id=order_id, instrument_name=instrument_name)
    print(result)


@orders.command("cancel_all")
@click.pass_context
def cancel_all_orders(ctx):
    """Cancel all orders."""
    print("Cancelling all orders")
    client: DeriveClient = ctx.obj["client"]
    result = client.cancel_all()
    print(result)


@orders.command("create")
@click.pass_context
@click.option(
    "--instrument-name",
    "-i",
    type=str,
    required=True,
)
@click.option(
    "--side",
    "-s",
    type=click.Choice([i.value for i in OrderSide]),
    required=True,
)
@click.option(
    "--price",
    "-p",
    type=float,
    required=True,
)
@click.option(
    "--amount",
    "-a",
    type=float,
    required=True,
)
@click.option(
    "--order-type",
    "-t",
    type=click.Choice([i.value for i in OrderType]),
    default="limit",
)
@click.option(
    "--instrument-type",
    "-it",
    type=click.Choice([i.value for i in InstrumentType]),
    default="PERP",
)
def create_order(ctx, instrument_name, side, price, amount, order_type, instrument_type):
    """Create order."""
    print("Creating order")
    client: DeriveClient = ctx.obj["client"]
    result = client.create_order(
        instrument_name=instrument_name,
        side=OrderSide(side),
        price=price,
        amount=amount,
        order_type=OrderType(order_type),
        instrument_type=InstrumentType(instrument_type),
    )
    print(result)


@positions.command("transfer")
@click.pass_context
@click.option(
    "--instrument-name",
    "-i",
    type=str,
    required=True,
    help="Name of the instrument to transfer",
)
@click.option(
    "--amount",
    "-a",
    type=float,
    required=True,
    help="Amount to transfer (absolute value)",
)
@click.option(
    "--limit-price",
    "-p",
    type=float,
    required=True,
    help="Limit price for the transfer",
)
@click.option(
    "--from-subaccount",
    "-f",
    type=int,
    required=True,
    help="Subaccount ID to transfer from",
)
@click.option(
    "--to-subaccount",
    "-t",
    type=int,
    required=True,
    help="Subaccount ID to transfer to",
)
@click.option(
    "--position-amount",
    type=float,
    default=None,
    help="Original position amount (if not provided, will be fetched)",
)
def transfer_position(ctx, instrument_name, amount, limit_price, from_subaccount, to_subaccount, position_amount):
    """Transfer a single position between subaccounts."""
    client: DeriveClient = ctx.obj["client"]
    result = client.transfer_position(
        instrument_name=instrument_name,
        amount=amount,
        limit_price=limit_price,
        from_subaccount_id=from_subaccount,
        to_subaccount_id=to_subaccount,
        position_amount=position_amount,
    )
    print(result)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
