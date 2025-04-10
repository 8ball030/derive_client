"""
Conftest for derive tests
"""

from unittest.mock import MagicMock

import pytest

from derive_client.async_client import DeriveAsyncClient
from derive_client.derive import DeriveClient
from derive_client.enums import Environment
from derive_client.utils import get_logger

TEST_WALLET = "0x8772185a1516f0d61fC1c2524926BfC69F95d698"
TEST_PRIVATE_KEY = "0x2ae8be44db8a590d20bffbe3b6872df9b569147d3bf6801a35a28281a4816bbd"
SUBACCOUNT_ID = 30769


def freeze_time(derive_client):
    ts = 1705439697008
    nonce = 17054396970088651
    expiration = 1705439703008
    derive_client.get_nonce_and_signature_expiry = MagicMock(return_value=(ts, nonce, expiration))
    return derive_client


@pytest.fixture
def derive_client():
    derive_client = DeriveClient(
        private_key=TEST_PRIVATE_KEY, wallet=TEST_WALLET, env=Environment.TEST, logger=get_logger()
    )
    derive_client.subaccount_id = SUBACCOUNT_ID
    yield derive_client
    derive_client.cancel_all()


@pytest.fixture
def derive_client_2():
    derive_client = DeriveClient(
        wallet=TEST_WALLET, private_key=TEST_PRIVATE_KEY, env=Environment.TEST, logger=get_logger()
    )
    derive_client.subaccount_id = derive_client.fetch_subaccounts()[-1]['id']
    yield derive_client
    derive_client.cancel_all()


@pytest.fixture
async def derive_async_client():
    derive_client = DeriveAsyncClient(
        wallet=TEST_WALLET, private_key=TEST_PRIVATE_KEY, env=Environment.TEST, logger=get_logger()
    )
    derive_client.subaccount_id = SUBACCOUNT_ID
    yield derive_client
    await derive_client.cancel_all()
