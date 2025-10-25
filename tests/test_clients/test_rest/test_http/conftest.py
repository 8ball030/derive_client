import time
from contextlib import contextmanager
from unittest.mock import patch

import pytest

from derive_client._clients.rest.http.client import HTTPClient
from derive_client.data_types import Environment


@pytest.fixture(autouse=True)
def slow_down_every_test(request):
    time.sleep(1)


OWNER_TEST_WALLET = "0xA419f70C696a4b449a4A24F92e955D91482d44e9"
ADMIN_TEST_WALLET = "0x8772185a1516f0d61fC1c2524926BfC69F95d698"
SESSION_KEY_PRIVATE_KEY = "0x2ae8be44db8a590d20bffbe3b6872df9b569147d3bf6801a35a28281a4816bbd"


@contextmanager
def assert_api_calls(client, expected: int):
    with patch.object(client._session, "_send_request", wraps=client._session._send_request) as api_requests:
        before = api_requests.call_count
        yield
        after = api_requests.call_count
    actual = after - before
    if actual != expected:
        raise AssertionError(f"Expected {expected} HTTP calls, got {actual}. (before={before}, after={after})")


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
