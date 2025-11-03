"""Tests for the `transaction` command group."""

from derive_client.cli import cli as drv


def test_transaction_get(runner):
    """Test: `drv transaction get`"""

    result = runner.invoke(drv, ["transaction", "get", "514aea9b-c86b-49e5-ba89-620b38477cdd"])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"


def test_transaction_deposit_to_subaccount(runner):
    """Test: `drv transaction deposit-to-subaccount`"""

    result = runner.invoke(drv, ["transaction", "deposit-to-subaccount", "0.1", "USDC"])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"


def test_transaction_withdraw_from_subaccount(runner):
    """Test: `drv transaction withdraw-from-subaccount`"""

    result = runner.invoke(drv, ["transaction", "withdraw-from-subaccount", "0.1", "USDC"])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"
