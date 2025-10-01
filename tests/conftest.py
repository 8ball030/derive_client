"""
Conftest for derive tests
"""

import time
from unittest.mock import MagicMock

import pytest

from derive_client.clients import AsyncClient
from derive_client.data_types import Environment
from derive_client.derive import DeriveClient
from derive_client.exceptions import DeriveJSONRPCException
from derive_client.utils import get_logger

OWNER_TEST_WALLET = "0xA419f70C696a4b449a4A24F92e955D91482d44e9"  # SESSION_KEY_PRIVATE_KEY owns this
TEST_WALLET = "0x8772185a1516f0d61fC1c2524926BfC69F95d698"
# this SESSION_KEY_PRIVATE_KEY is not the owner of the wallet
TEST_PRIVATE_KEY = "0x2ae8be44db8a590d20bffbe3b6872df9b569147d3bf6801a35a28281a4816bbd"


def freeze_time(derive_client):
    ts = 1705439697008
    nonce = 17054396970088651
    expiration = 1705439703008
    derive_client.get_nonce_and_signature_expiry = MagicMock(return_value=(ts, nonce, expiration))
    return derive_client


@pytest.fixture
def derive_client():
    derive_client = DeriveClient(
        wallet=TEST_WALLET, private_key=TEST_PRIVATE_KEY, env=Environment.TEST, logger=get_logger()
    )
    yield derive_client
    while True:
        try:
            derive_client.cancel_all()
            derive_client.cancel_batch_rfqs()
            break
        except DeriveJSONRPCException as e:
            if "Retry after" in e.data:
                wait_ms = int(e.data.split(" ")[2])
                time.sleep(wait_ms / 1000)
                continue
            raise e


@pytest.fixture
async def derive_async_client():
    derive_client = AsyncClient(
        wallet=TEST_WALLET, private_key=TEST_PRIVATE_KEY, env=Environment.TEST, logger=get_logger()
    )
    yield derive_client
    await derive_client.cancel_all()
