"""Utility functions for the CLI."""

from __future__ import annotations

import math
from decimal import Decimal
from enum import Enum

import msgspec
import pandas as pd
from rich.table import Table

from derive_client._clients.utils import StructT
from derive_client.data_types import PreparedBridgeTx
from derive_client.utils import from_base_units


def fmt_sig_up_to(x: float, sig: int = 4) -> str:
    """Format x to up to `sig` significant digits, preserving all necessary decimals."""

    if x == 0:
        return "0"

    order = math.floor(math.log10(abs(x)))
    decimals = max(sig - order - 1, 0)
    formatted = f"{x:.{decimals}f}"
    return formatted.rstrip("0").rstrip(".")


def rich_prepared_tx(prepared_tx: PreparedBridgeTx):
    """Return a rich Table summarizing a prepared bridge transaction for CLI display."""

    table = Table(title="Prepared Bridge Transaction", show_header=False, box=None)
    if prepared_tx.amount > 0:
        human_amount = from_base_units(amount=prepared_tx.amount, currency=prepared_tx.currency)
        table.add_row("Amount", f"{human_amount} {prepared_tx.currency.name} (base units: {prepared_tx.amount})")
    if prepared_tx.fee_in_token > 0:
        fee_human = from_base_units(prepared_tx.fee_in_token, prepared_tx.currency)
        table.add_row(
            "Estimated fee (token)",
            f"{fee_human} {prepared_tx.currency.name} (base units: {prepared_tx.fee_in_token})",
        )
    if prepared_tx.value and prepared_tx.value > 0:
        human_value = prepared_tx.value / 1e18
        table.add_row("Value", f"{human_value} ETH (base units: {prepared_tx.value})")
    if prepared_tx.fee_value > 0:
        human_fee_value = fmt_sig_up_to(prepared_tx.fee_value / 1e9)
        table.add_row("Estimated fee (native)", f"{human_fee_value} gwei (base units: {prepared_tx.fee_value})")

    table.add_row("Source chain", prepared_tx.source_chain.name)
    table.add_row("Target chain", prepared_tx.target_chain.name)
    table.add_row("Bridge type", prepared_tx.bridge_type.name)
    table.add_row("Tx hash", prepared_tx.tx_hash)
    table.add_row("Gas limit", str(prepared_tx.gas))
    table.add_row("Max fee/gas", f"{fmt_sig_up_to(prepared_tx.max_fee_per_gas / 1e9)} gwei")
    table.add_row("Max total fee", f"{fmt_sig_up_to(prepared_tx.max_total_fee / 1e9)} gwei")

    return table


def _quantize_safe(value: Decimal | None, quant=Decimal("0.0001")):
    if value is None:
        return value
    return value.quantize(quant)


def _check_enum_or_list(value):
    if isinstance(value, Enum):
        return True
    elif isinstance(value, list):
        return all(isinstance(y, Enum) for y in value)
    return False


def _convert_enum_value(value: Enum | list[Enum] | None):
    if isinstance(value, Enum):
        return value.value
    elif isinstance(value, list):
        return [item.value for item in value]
    return value


def struct_to_series(struct: msgspec.Struct) -> pd.Series:
    """Convert a msgspec.Struct to a formatted pandas Series.

    Automatically handles:
    - Decimal quantization
    - Enum conversion (single values and lists)
    """

    series = pd.Series(msgspec.structs.asdict(struct))

    decimal_mask = series.map(lambda x: isinstance(x, Decimal))
    series[decimal_mask] = series[decimal_mask].map(_quantize_safe)

    enum_mask = series.map(lambda x: _check_enum_or_list(x))
    series[enum_mask] = series[enum_mask].apply(_convert_enum_value)

    return series


def structs_to_dataframe(structs: list[StructT]) -> pd.DataFrame:
    """Convert a list of msgspec.Structs to a formatted pandas DataFrame.

    Automatically handles:
    - Decimal quantization
    - Enum conversion (single values and lists)
    """

    return pd.DataFrame(struct_to_series(s) for s in structs)


def explode_struct_column(df: pd.DataFrame, id_col: str, struct_col: str) -> pd.DataFrame:
    """Explode a column containing list of Structs into a flat DataFrame.

    Args:
        df: DataFrame containing nested Structs
        id_col: Column to preserve as identifier
        struct_col: Column containing list of Structs to explode

    Returns:
        Flattened DataFrame with quantized decimals and converted enums
    """

    df_copy = df[[id_col, struct_col]].copy()
    df_copy[struct_col] = df_copy[struct_col].map(lambda items: [struct_to_series(x) for x in items])

    exploded = df_copy.explode(struct_col, ignore_index=True)
    expanded_structs = exploded[struct_col].apply(lambda x: x if isinstance(x, pd.Series) else pd.Series())

    return pd.concat([exploded.drop(columns=[struct_col]), expanded_structs], axis=1)
