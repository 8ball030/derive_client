"""Tests for the `collateral` command group."""

from derive_client.cli import cli as drv


def test_collateral_get(runner):
    """Test: `drv collateral get`"""

    result = runner.invoke(drv, ["collateral", "get"])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"


def test_collateral_get_margin(runner):
    """Test: `drv collateral get-margin`"""

    result = runner.invoke(drv, ["collateral", "get-margin"])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"


def test_collateral_deposit_to_subaccount(runner):
    """Test: `drv collateral deposit-to-subaccount`"""

    result = runner.invoke(drv, ["collateral", "deposit-to-subaccount", "0.1", "USDC"])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"


def test_collateral_withdraw_from_subaccount(runner):
    """Test: `drv collateral withdraw-from-subaccount`"""

    result = runner.invoke(drv, ["collateral", "withdraw-from-subaccount", "0.1", "USDC"])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"
