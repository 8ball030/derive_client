import time

import pytest

from derive_client._clients.rest.http.client import HTTPClient
from derive_client.data_types import Environment
from tests.conftest import ADMIN_TEST_WALLET, OWNER_TEST_WALLET, SESSION_KEY_PRIVATE_KEY


@pytest.fixture(autouse=True)
def slow_down_every_test(request):
    time.sleep(1)


@pytest.fixture(scope="session")
def client_owner_wallet():
    """
    Client connected to a wallet where the session key is the owner.
    Full authority over the wallet is available, allowing owner-level operations.
    """
    subaccount_id = 137626
    client = HTTPClient(
        wallet=OWNER_TEST_WALLET,
        session_key=SESSION_KEY_PRIVATE_KEY,
        subaccount_id=subaccount_id,
        env=Environment.TEST,
    )
    client.connect()
    yield client
    client.orders.cancel_all()
    client.rfq.cancel_batch_rfqs()
    client.rfq.cancel_batch_quotes()
    client.disconnect()


@pytest.fixture(scope="session")
def client_admin_wallet():
    """
    Client connected to a wallet where the session key is registered as admin.
    This wallet is NOT owned by the session key, so only admin-level operations are allowed.
    """
    subaccount_id = 31049
    client = HTTPClient(
        wallet=ADMIN_TEST_WALLET,
        session_key=SESSION_KEY_PRIVATE_KEY,
        subaccount_id=subaccount_id,
        env=Environment.TEST,
    )
    client.connect()
    yield client
    client.orders.cancel_all()
    client.rfq.cancel_batch_rfqs()
    client.rfq.cancel_batch_quotes()
    client.disconnect()
