"""CLI commands for market queries."""

from __future__ import annotations

import pandas as pd
import rich_click as click

from derive_client.data_types import InstrumentType

from ._columns import CURRENCY_COLUMNS, INSTRUMENT_COLUMNS
from ._utils import struct_to_series, structs_to_dataframe


@click.group("market")
@click.pass_context
def market(ctx):
    """Query market data: currencies, instruments, tickers."""


@market.command("currency")
@click.argument("currency", required=False)
@click.option("--all", "-a", is_flag=True, help="Get all currencies")
@click.pass_context
def currency(ctx, currency, all):
    """Get currency details.

    Examples:
        drv market currency USDC
        drv market currency --all
    """

    client = ctx.obj["client"]

    complex_cols = [
        "asset_cap_and_supply_per_manager",
        "managers",
        "protocol_asset_addresses",
        "pm2_collateral_discounts",
    ]

    if all:
        currencies = client.markets.get_all_currencies()
        df = structs_to_dataframe(currencies)

        print("\n=== Currencies Info ===")
        print(df[CURRENCY_COLUMNS])

    elif currency:
        result = client.markets.get_currency(currency=currency)
        series = struct_to_series(result)

        print("\n=== Currency Info ===")
        print(series.drop(complex_cols).to_string(index=True))
        print("\n=== Managers ===")
        print(structs_to_dataframe(series.managers))
        print("\n=== Protocol Asset Addresses ===")
        print(struct_to_series(series.protocol_asset_addresses).to_string(index=True))
        print("\n=== Portfolio Manager Collateral Discounts ===")
        print(structs_to_dataframe(series.pm2_collateral_discounts))

    else:
        click.echo("Error: Provide a currency or use --all")
        ctx.exit(1)


@market.command("instrument")
@click.argument("instrument_name", required=False)
@click.option(
    "--currency",
    "-c",
    help="Currency for bulk ticker query (requires --type)",
)
@click.option(
    "--type",
    "-t",
    type=click.Choice([x.name for x in InstrumentType]),
    help="Instrument type for bulk query",
)
@click.option(
    "--expired",
    default=False,
    help="Include expired instruments (default: active only)",
)
@click.pass_context
def instrument(ctx, instrument_name, currency, type, expired):
    """Get instrument details.

    Examples:
        drv market instrument BTC-USDC
        drv market instrument BTC-PERP
        drv market instrument --currency BTC --type option
    """

    client = ctx.obj["client"]

    if instrument_name and (currency or type):
        click.echo("Error: Cannot specify instrument name with --currency or --type")
        ctx.exit(1)

    if (currency or type) and not (currency and type):
        click.echo("Error: --currency and --type must be used together")
        ctx.exit(1)

    if not instrument_name and not (currency and type):
        click.echo("Error: Provide either instrument name or --currency and --type")
        click.echo("Run 'drv market instrument --help' for examples")
        ctx.exit(1)

    complex_cols = ["erc20_details", "perp_details", "option_details"]

    if instrument_name:
        instrument = client.markets.get_instrument(instrument_name=instrument_name)
        series = struct_to_series(instrument)

        print("\n=== Instrument Info ===")
        print(series.drop(complex_cols).to_string(index=True))

        if series.erc20_details is not None:
            print("\n=== ERC20 Details ===")
            print(struct_to_series(series.erc20_details).to_string(index=True))
        if series.perp_details is not None:
            print("\n=== Perp Details ===")
            print(struct_to_series(series.perp_details).to_string(index=True))
        if series.option_details is not None:
            print("\n=== Option Details ===")
            print(struct_to_series(series.option_details).to_string(index=True))

    else:
        instrument_type = InstrumentType[type]
        instruments = client.markets.get_instruments(
            currency=currency,
            expired=expired,
            instrument_type=instrument_type,
        )
        df = structs_to_dataframe(instruments)

        print("\n=== Instruments Info ===")
        print(df[INSTRUMENT_COLUMNS])


@market.command("ticker")
@click.argument("instrument_name", required=False)
@click.option(
    "--currency",
    "-c",
    help="Currency for bulk ticker query (requires --type)",
)
@click.option(
    "--type",
    "-t",
    type=click.Choice([x.name for x in InstrumentType]),
    help="Instrument type for bulk query",
)
@click.option(
    "--expired",
    default=False,
    help="Include expired instruments (default: active only)",
)
@click.pass_context
def ticker(ctx, instrument_name, currency, type, expired):
    """Get ticker details.

    Examples:
        drv market ticker BTC-PERP
        drv market ticker --currency BTC --type option
    """

    client = ctx.obj["client"]

    if instrument_name and (currency or type):
        click.echo("Error: Cannot specify instrument name with --currency or --type")
        ctx.exit(1)

    if (currency or type) and not (currency and type):
        click.echo("Error: --currency and --type must be used together")
        ctx.exit(1)

    if not instrument_name and not (currency and type):
        click.echo("Error: Provide either instrument name or --currency and --type")
        click.echo("Run 'drv market ticker --help' for examples")
        ctx.exit(1)

    complex_cols = ["open_interest", "stats", "erc20_details", "perp_details", "option_details"]

    if instrument_name:
        ticker = client.markets.get_ticker(instrument_name=instrument_name)
        series = struct_to_series(ticker)

        print("\n=== Ticker Info ===")
        print(series.drop(complex_cols).to_string(index=True))

        if series.erc20_details is not None:
            print("\n=== ERC20 Details ===")
            print(struct_to_series(series.erc20_details).to_string(index=True))
        if series.perp_details is not None:
            print("\n=== Perp Details ===")
            print(struct_to_series(series.perp_details).to_string(index=True))
        if series.option_details is not None:
            print("\n=== Option Details ===")
            print(struct_to_series(series.option_details).to_string(index=True))

        print("\n=== Open Interest ===")
        items = series["open_interest"].items()
        print(pd.DataFrame({k: struct_to_series(v2) for k, v in items for v2 in v}))

        print("\n=== Stats ===")
        print(struct_to_series(series.stats).to_string(index=True))

    else:
        instrument_type = InstrumentType[type]
        click.echo(f"⚠ Fetching all {type} tickers for {currency} (this may take a while)...")
        tickers = client.markets.get_all_tickers(
            currency=currency,
            expired=expired,
            instrument_type=instrument_type,
        )
        df = structs_to_dataframe(tickers)

        print("\n=== Tickers Info ===")
        print(df)
