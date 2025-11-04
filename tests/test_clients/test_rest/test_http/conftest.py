import time

import pytest

from derive_client._clients.rest.http.client import HTTPClient
from derive_client.data_types import Environment
from derive_client.data_types.generated_models import Direction, OrderStatus
from derive_client.data_types.utils import D
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


@pytest.fixture(scope="session")
def client_owner_wallet_with_position(client_admin_wallet: HTTPClient):
    """
    Client connected to a wallet where the session key is registered as admin.
    This wallet is NOT owned by the session key, so only admin-level operations are allowed.
    """
    client_admin_wallet.orders.cancel_all()

    market_instrument = "ETH-PERP"

    def close_positions(client: HTTPClient):
        open_positions = [f for f in client.positions.list() if f.amount != 0]
        for position in open_positions:
            price = client.markets.get_ticker(instrument_name=position.instrument_name).index_price
            direction = Direction.buy if position.amount > 0 else Direction.sell
            client.orders.create(
                instrument_name=position.instrument_name,
                amount=abs(position.amount),
                direction=direction,
                limit_price=price,
            )

    subaccount_id = 137626
    client = HTTPClient(
        wallet=OWNER_TEST_WALLET,
        session_key=SESSION_KEY_PRIVATE_KEY,
        subaccount_id=subaccount_id,
        env=Environment.TEST,
    )
    close_positions(client)

    # Open a position
    price = client.markets.get_ticker(instrument_name=market_instrument).index_price
    order = client.orders.create(
        instrument_name=market_instrument,
        amount=D(0.1),
        direction=Direction.buy,
        limit_price=price * D("1.05"),
        signature_expiry_sec=int(time.time() + 302),
    )

    attempts = 10

    while True:
        maker_order = client.orders.get(order_id=order.order_id)
        if order.order_status != OrderStatus.open:
            break
        time.sleep(1)
        attempts -= 1
        if attempts == 0:
            # we now submit a new order to help fill the position
            breakpoint()
            taker_order = client_admin_wallet.orders.create(
                instrument_name=market_instrument, amount=D(0.1), direction=Direction.sell, limit_price=price
            )
            time.sleep(1)
            client_admin_wallet.orders.list(status=OrderStatus.open)
            original_order = client.orders.get(order_id=order.order_id)
            time.sleep(1)
            assert original_order.order_status != OrderStatus.open, "Failed to fill position in time"
            assert taker_order.order_status != OrderStatus.open, "Failed to fill position in time"
            assert maker_order.order_status != OrderStatus.open, "Failed to fill position in time"

    positions = client.positions.list()

    assert len(positions) == 1, f"Expected exactly one open position, found: {positions}"

    client.connect()
    yield client
    client.orders.cancel_all()
    client.rfq.cancel_batch_rfqs()
    client.rfq.cancel_batch_quotes()
    client.disconnect()
