"""Tests for the `mmp` command group."""

import pytest

from derive_client.cli import cli as drv


def test_reset(runner):
    """Test: `drv mmp reset`"""

    result = runner.invoke(drv, ["mmp", "reset"])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"


@pytest.mark.parametrize(
    "args",
    [
        (),
        ("BTC",),
    ],
)
def test_get_config(runner, args):
    """Test: `drv mmp get-config`"""

    result = runner.invoke(drv, ["mmp", "get-config", *args])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"


@pytest.mark.parametrize(
    "args",
    [
        ("BTC", "-f", "0", "-i", "10000"),
        ("BTC", "--mmp-frozen-time", "0", "--mmp-interval", "10000"),
    ],
)
def test_set_config(runner, args):
    """Test: `drv mmp set-config`"""

    result = runner.invoke(drv, ["mmp", "set-config", *args])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"
