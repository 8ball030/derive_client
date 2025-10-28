import time

import pytest
import pytest_asyncio

from derive_client._clients.rest.async_http.client import AsyncHTTPClient
from derive_client.data_types import Environment
from tests.conftest import ADMIN_TEST_WALLET, OWNER_TEST_WALLET, SESSION_KEY_PRIVATE_KEY


@pytest.fixture(autouse=True)
def slow_down_every_test(request):
    time.sleep(1)


@pytest_asyncio.fixture(scope="session")
async def client_owner_wallet():
    """
    Client connected to a wallet where the session key is the owner.
    Full authority over the wallet is available, allowing owner-level operations.
    """
    subaccount_id = 137626
    client = AsyncHTTPClient(
        wallet=OWNER_TEST_WALLET,
        session_key=SESSION_KEY_PRIVATE_KEY,
        subaccount_id=subaccount_id,
        env=Environment.TEST,
    )
    await client.connect()
    yield client
    await client.orders.cancel_all()
    await client.rfq.cancel_batch_rfqs()
    await client.rfq.cancel_batch_quotes()
    await client.disconnect()


@pytest_asyncio.fixture(scope="session")
async def client_admin_wallet():
    """
    Client connected to a wallet where the session key is registered as admin.
    This wallet is NOT owned by the session key, so only admin-level operations are allowed.
    """
    subaccount_id = 31049
    client = AsyncHTTPClient(
        wallet=ADMIN_TEST_WALLET,
        session_key=SESSION_KEY_PRIVATE_KEY,
        subaccount_id=subaccount_id,
        env=Environment.TEST,
    )
    await client.connect()
    yield client
    await client.orders.cancel_all()
    await client.rfq.cancel_batch_rfqs()
    await client.rfq.cancel_batch_quotes()
    await client.disconnect()
