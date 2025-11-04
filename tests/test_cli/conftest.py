"""Shared fixtures for CLI tests."""

import time
from pathlib import Path

import pytest
from click.testing import CliRunner

from derive_client.cli import cli as drv
from tests.conftest import OWNER_TEST_WALLET, SESSION_KEY_PRIVATE_KEY

DOT_ENV_CONTENT = f"""
DERIVE_SESSION_KEY={SESSION_KEY_PRIVATE_KEY}
DERIVE_WALLET={OWNER_TEST_WALLET}
DERIVE_SUBACCOUNT_ID=137626
DERIVE_ENV=TEST
"""


@pytest.fixture(autouse=True)
def slow_down_every_test():
    """Rate limit API calls in CLI tests."""

    time.sleep(1)


@pytest.fixture(scope="session")
def runner():
    """Create a Click CliRunner and run tests inside an isolated filesystem."""

    runner = CliRunner()

    with runner.isolated_filesystem() as tmp_dir:
        env_path = Path(tmp_dir) / ".env"
        env_path.write_text(DOT_ENV_CONTENT)
        yield runner

    runner.invoke(drv, ["order", "cancel-all"])
