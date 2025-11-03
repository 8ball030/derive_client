"""Tests for the `market` command group."""

import pytest

from derive_client.cli import cli as drv


@pytest.mark.parametrize(
    "args",
    [
        ("--all",),
        ("USDC",),
    ],
)
def test_market_currency(runner, args):
    """Test: `drv market currency`"""

    result = runner.invoke(drv, ["market", "currency", *args])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"


@pytest.mark.parametrize(
    "args",
    [
        ("ETH-USDC",),
        ("ETH-PERP",),
        ("--currency", "ETH", "--type", "option"),
    ],
)
def test_market_instrument(runner, args):
    """Test: `drv market instrument`"""

    result = runner.invoke(drv, ["market", "instrument", *args])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"


@pytest.mark.parametrize(
    "args",
    [
        ("BTC-PERP",),
    ],
)
def test_market_ticker(runner, args):
    """Test: `drv market ticker`"""

    result = runner.invoke(drv, ["market", "ticker", *args])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"
