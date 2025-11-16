import time

import pytest

from derive_client._clients.rest.http.client import HTTPClient
from derive_client.data_types import Environment
from derive_client.data_types.generated_models import Direction, OrderType
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
def client_owner_wallet_with_position(client_owner_wallet: HTTPClient):
    """
    Client connected to a wallet where the session key is registered as admin.
    This wallet is NOT owned by the session key, so only admin-level operations are allowed.
    """

    maker_client = HTTPClient(
        wallet=ADMIN_TEST_WALLET,
        session_key=SESSION_KEY_PRIVATE_KEY,
        env=Environment.TEST,
        subaccount_id=31049,
    )
    maker_client.connect()
    maker_client.orders.cancel_all()
    client_owner_wallet.orders.cancel_all()
    market_perp_instrument = "ETH-PERP"

    current_positions = client_owner_wallet.positions.list(is_open=True)

    if market_perp_instrument not in [p.instrument_name for p in current_positions]:
        # we check if liqudity exists for us to take else we use the maker role
        ticker = maker_client.markets.get_ticker(instrument_name=market_perp_instrument)
        bid_diff = (D(ticker.best_bid_price) - D(ticker.index_price)) / D(ticker.index_price)
        ask_diff = (D(ticker.index_price) - D(ticker.best_ask_price)) / D(ticker.index_price)
        if bid_diff < D("0.05") or ask_diff < D("0.05"):
            # we know that we are unable to take liquidity, so we provide it
            maker_client.orders.create(
                instrument_name=market_perp_instrument,
                amount=D("0.1"),
                limit_price=D(ticker.index_price),
                direction=Direction.buy,
                order_type=OrderType.limit,
            )
            client_owner_wallet.orders.create(
                instrument_name=market_perp_instrument,
                amount=D("0.1"),
                limit_price=D(ticker.index_price),
                direction=Direction.sell,
                order_type=OrderType.market,
            )

        # we check the index, and ensure that there is less than 5% between the index and the mid price

    # we now check that we have an options position as well.
    current_positions = client_owner_wallet.positions.list(is_open=True)
    # TODO: ensuer that the option positions are created.

    assert market_perp_instrument in [p.instrument_name for p in client_owner_wallet.positions.list(is_open=True)]
    yield client_owner_wallet
    client_owner_wallet.orders.cancel_all()
    client_owner_wallet.rfq.cancel_batch_rfqs()
    client_owner_wallet.rfq.cancel_batch_quotes()
    client_owner_wallet.disconnect()
    close_instrument_position_with_taker_if_needed(
        taker_client=client_owner_wallet, maker_client=maker_client, instrument_name=market_perp_instrument
    )


def close_instrument_position_with_taker_if_needed(
    taker_client: HTTPClient, maker_client: HTTPClient, instrument_name: str
):
    """Close the instrument position with the taker if necessary."""
    taker_client.fetch_subaccounts()
    for subaccount in taker_client.cached_subaccounts:
        open_positions = subaccount.positions.list(is_open=True)
        for position in open_positions:
            if position.instrument_name != instrument_name:
                continue
            ticker = taker_client.markets.get_ticker(instrument_name=instrument_name)
            direction = Direction.sell if position.amount > 0 else Direction.buy
            # check if would be able to fill against the existing book.
            bid_diff = (D(ticker.best_bid_price) - D(ticker.index_price)) / D(ticker.index_price)
            ask_diff = (D(ticker.index_price) - D(ticker.best_ask_price)) / D(ticker.index_price)
            if (direction == Direction.sell and bid_diff >= D("0.05")) or (
                direction == Direction.buy and ask_diff >= D("0.05")
            ):
                # we know that we are able to take liquidity
                subaccount.orders.create(
                    instrument_name=instrument_name,
                    amount=abs(position.amount),
                    direction=direction,
                    order_type=OrderType.market,
                    limit_price=D(ticker.index_price) * D("1.05" if direction == Direction.buy else "0.95"),
                )
            else:
                # we need to use the maker to close the position
                opposite_direction = Direction.sell if direction == Direction.buy else Direction.buy
                maker_client.orders.create(
                    instrument_name=instrument_name,
                    amount=abs(position.amount),
                    direction=opposite_direction,
                    order_type=OrderType.limit,
                    limit_price=D(ticker.index_price),
                )
                subaccount.orders.create(
                    instrument_name=instrument_name,
                    amount=abs(position.amount),
                    direction=direction,
                    order_type=OrderType.market,
                    limit_price=D(ticker.index_price) * D("1.05" if direction == Direction.buy else "0.95"),
                )
