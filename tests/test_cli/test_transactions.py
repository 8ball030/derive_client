"""Tests for the `transaction` command group."""

from derive_client.cli import cli as drv


def test_transaction_get(runner):
    """Test: `drv transaction get`"""

    result = runner.invoke(drv, ["transaction", "get", "514aea9b-c86b-49e5-ba89-620b38477cdd"])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"
