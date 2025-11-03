"""CLI commands for Market Making Protocol (MMP) interactions."""

from __future__ import annotations

from decimal import Decimal

import rich_click as click

from ._utils import struct_to_series, structs_to_dataframe


@click.group("mmp")
@click.pass_context
def mmp(ctx):
    """Market maker protection configuration."""


@mmp.command("get-config")
@click.argument(
    "currency",
    default=None,
    help="Currency to get the config for. If not provided, returns all configs for the subaccount.",
)
@click.pass_context
def get_config(ctx, currency: str | None):
    """Get the current mmp config for a subaccount (optionally filtered by currency).

    Examples:
        drv mmp get-config
        drv mmp get-config BTC
    """

    client = ctx.obj["client"]
    subaccount = client.active_subaccount
    mmp_config = subaccount.mmp.get_config(currency=currency)

    print("\n=== Market Maker Protection Config ===")
    print(structs_to_dataframe(mmp_config))


@mmp.command("set-config")
@click.argument(
    "currency",
    required=True,
    help="Currency of this mmp config.",
)
@click.option(
    "--mmp-frozen-time",
    "-f",
    type=int,
    required=True,
    help="Time interval in ms setting how long the subaccount is frozen after an mmp trigger, if 0 then a manual reset would be required via private/reset_mmp",  # noqa: E501
)
@click.option(
    "--mmp-interval",
    "-i",
    type=int,
    required=True,
    help="Time interval in ms over which the limits are monotored, if 0 then mmp is disabled.",
)
@click.option(
    "--mmp-amount-limit",
    "-a",
    type=Decimal,
    default=Decimal("0"),
    help="Maximum total order amount that can be traded within the mmp_interval across all instruments of the provided currency.",  # noqa: E501
)
@click.option(
    "--mmp-delta-limit",
    "-d",
    type=Decimal,
    default=Decimal("0"),
    help="Maximum total delta that can be traded within the mmp_interval across all instruments of the provided currency.",  # noqa: E501
)
@click.pass_context
def set_config(
    ctx,
    currency: str,
    mmp_frozen_time: int,
    mmp_interval: int,
    mmp_amount_limit: Decimal,
    mmp_delta_limit: Decimal,
):
    """Set the mmp config for the subaccount and currency.

    Examples:
        drv mmp set-config BTC -f 0 -i 10000
        drv mmp set-config BTC --mmp-frozen-time 0 --mmp-interval 10000
    """

    client = ctx.obj["client"]
    subaccount = client.active_subaccount
    mmp_config = subaccount.mmp.set_config(
        currency=currency,
        mmp_frozen_time=mmp_frozen_time,
        mmp_interval=mmp_interval,
        mmp_amount_limit=mmp_amount_limit,
        mmp_delta_limit=mmp_delta_limit,
    )

    print("\n=== Updated Market Maker Protection Config ===")
    print(struct_to_series(mmp_config).to_string(index=True))


@mmp.command("reset")
@click.argument(
    "currency",
    default=None,
    help="Currency to reset the mmp for. If not provided, resets all configs for the subaccount.",
)
@click.pass_context
def reset(ctx, currency: str | None):
    """Resets (unfreezes) the mmp state for a subaccount (optionally filtered by currency)."""

    client = ctx.obj["client"]
    subaccount = client.active_subaccount
    result = subaccount.mmp.reset(currency=currency)

    print(f"\n=== Market Maker Protection Reset for subaccount {subaccount.id} ===")
    print(f"MMP reset result: {result.value}")
