"""Tests for the `order` command group."""

import pytest

from derive_client.cli import cli as drv


@pytest.mark.parametrize(
    "args",
    [
        ("ETH-PERP", "buy", "-a", "0.1", "-p", "100"),
        ("ETH-PERP", "buy", "--amount", "0.1", "--price", "100"),
    ],
)
def test_order_create(runner, args):
    """Test: `drv order create`"""

    result = runner.invoke(drv, ["order", "create", *args])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"


def test_order_get(runner):
    """Test: `drv order get`"""

    order_res = runner.invoke(drv, ["order", "create", "ETH-USDC", "buy", "-a", "10", "-p", "0.99"])
    assert order_res.exit_code == 0, f"Order creation failed with output:\n{order_res.output}"
    order_id = [f for f in order_res.output.split("\n") if "order_id" in f].pop().split()[-1]

    result = runner.invoke(drv, ["order", "get", order_id])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"


def test_order_list_open(runner):
    """Test: `drv order list-open`"""

    result = runner.invoke(drv, ["order", "list-open"])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"


@pytest.mark.skip(reason="Requires order_id of an active order.")
def test_order_cancel(runner):
    """Test: `drv order cancel`"""

    order_res = runner.invoke(drv, ["order", "create", "ETH-USDC", "buy", "-a", "10", "-p", "0.99"])
    assert order_res.exit_code == 0, f"Order creation failed with output:\n{order_res.output}"
    order_id = [f for f in order_res.output.split("\n") if "order_id" in f].pop().split()[-1]
    result = runner.invoke(drv, ["order", "cancel", order_id])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"


def test_order_cancel_all(runner):
    """Test: `drv order cancel-all`"""

    result = runner.invoke(drv, ["order", "cancel-all"])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"
