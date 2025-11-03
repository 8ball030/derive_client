"""Tests for the `position` command group."""

import pytest

from derive_client.cli import cli as drv


def test_position_list(runner):
    """Test: `drv position list`"""

    result = runner.invoke(drv, ["position", "list"])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"


@pytest.mark.skip(reason="Complex end-to-end test that mutates subaccount state.")
def test_position_transfer(runner):
    """Test: `drv position transfer`"""

    result = runner.invoke(drv, ["position", "transfer", "ETH-PERP", "0.01", "137627"])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"
