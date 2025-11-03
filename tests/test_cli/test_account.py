"""Tests for the `account` command group."""

from derive_client.cli import cli as drv


def test_account_get(runner):
    """Test: derive account get"""

    result = runner.invoke(drv, ["account", "get"])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"


def test_account_portfolios(runner):
    """Test: derive account portfolios"""

    result = runner.invoke(drv, ["account", "portfolios"])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"
