import threading

import msgspec

from derive_client.data_types.channel_models import (
    Depth,
    Group,
    InstrumentType,
    Interval,
    OrderbookInstrumentNameGroupDepthPublisherDataSchema,
    TickerSlimInstrumentNameIntervalPublisherDataSchema,
    TxStatus2,
)

TIMEOUT = 5
SUBSCRIPTION_OK = "ok"


def noop(result: msgspec.Struct) -> None:
    """No-op passed as callback when a notification within TIMEOUT seconds is not guaranteed."""

    return None


## Public channels
def test_public_auctions_watch(client_admin_wallet):
    subscription_result = client_admin_wallet.public_channels.auctions_watch(
        callback=noop,
    )

    assert subscription_result.status["auctions.watch"] == SUBSCRIPTION_OK


def test_public_margin_watch(client_admin_wallet):
    subscription_result = client_admin_wallet.public_channels.margin_watch(
        callback=noop,
    )

    assert subscription_result.status["margin.watch"] == SUBSCRIPTION_OK


def test_public_orderbook_group_depth_by_instrument_name(client_admin_wallet):
    got = {}
    msg_event = threading.Event()

    def callback(result):
        got['data'] = result
        msg_event.set()

    subscription_result = client_admin_wallet.public_channels.orderbook_group_depth_by_instrument_name(
        instrument_name="ETH-PERP",
        group=Group.field_1,
        depth=Depth.field_1,
        callback=callback,
    )

    received = msg_event.wait(timeout=TIMEOUT)

    assert subscription_result.status["orderbook.ETH-PERP.1.1"] == SUBSCRIPTION_OK
    assert received is True
    assert isinstance(got["data"], OrderbookInstrumentNameGroupDepthPublisherDataSchema)


def test_public_spot_feed_by_currency(client_admin_wallet):
    subscription_result = client_admin_wallet.public_channels.spot_feed_by_currency(
        currency="ETH",
        callback=noop,
    )

    assert subscription_result.status["spot_feed.ETH"] == SUBSCRIPTION_OK


def test_public_ticker_slim_interval_by_instrument_name(client_admin_wallet):
    got = {}
    msg_event = threading.Event()

    def callback(result):
        got['data'] = result
        msg_event.set()

    subscription_result = client_admin_wallet.public_channels.ticker_slim_interval_by_instrument_name(
        instrument_name="ETH-PERP",
        interval=Interval.field_1000,
        callback=callback,
    )

    received = msg_event.wait(timeout=TIMEOUT)

    assert subscription_result.status["ticker_slim.ETH-PERP.1000"] == SUBSCRIPTION_OK
    assert received is True
    assert isinstance(got["data"], TickerSlimInstrumentNameIntervalPublisherDataSchema)


def test_public_trades_by_instrument_name(client_admin_wallet):
    subscription_result = client_admin_wallet.public_channels.trades_by_instrument_name(
        instrument_name="ETH-PERP",
        callback=noop,
    )

    assert subscription_result.status["trades.ETH-PERP"] == SUBSCRIPTION_OK


def test_public_trades_by_instrument_type(client_admin_wallet):
    subscription_result = client_admin_wallet.public_channels.trades_by_instrument_type(
        instrument_type=InstrumentType.erc20,
        currency="ETH",
        callback=noop,
    )

    assert subscription_result.status["trades.erc20.ETH"] == SUBSCRIPTION_OK


def test_public_trades_tx_status_by_instrument_type(client_admin_wallet):
    subscription_result = client_admin_wallet.public_channels.trades_tx_status_by_instrument_type(
        instrument_type=InstrumentType.option,
        currency="ETH",
        tx_status=TxStatus2.settled,
        callback=noop,
    )

    assert subscription_result.status["trades.option.ETH.settled"] == SUBSCRIPTION_OK


## Private channels
def test_private_balances_by_subaccount_id(client_admin_wallet):
    subaccount_id = client_admin_wallet.active_subaccount.id
    subscription_result = client_admin_wallet.private_channels.balances_by_subaccount_id(
        subaccount_id=subaccount_id,
        callback=noop,
    )

    assert subscription_result.status[f"{subaccount_id}.balances"] == SUBSCRIPTION_OK


def test_private_best_quotes_by_subaccount_id(client_admin_wallet):
    subaccount_id = client_admin_wallet.active_subaccount.id
    subscription_result = client_admin_wallet.private_channels.best_quotes_by_subaccount_id(
        subaccount_id=subaccount_id,
        callback=noop,
    )

    assert subscription_result.status[f"{subaccount_id}.best.quotes"] == SUBSCRIPTION_OK


def test_private_orders_by_subaccount_id(client_admin_wallet):
    subaccount_id = client_admin_wallet.active_subaccount.id
    subscription_result = client_admin_wallet.private_channels.orders_by_subaccount_id(
        subaccount_id=subaccount_id,
        callback=noop,
    )

    assert subscription_result.status[f"{subaccount_id}.orders"] == SUBSCRIPTION_OK


def test_private_quotes_by_subaccount_id(client_admin_wallet):
    subaccount_id = client_admin_wallet.active_subaccount.id
    subscription_result = client_admin_wallet.private_channels.quotes_by_subaccount_id(
        subaccount_id=subaccount_id,
        callback=noop,
    )

    assert subscription_result.status[f"{subaccount_id}.quotes"] == SUBSCRIPTION_OK


def test_private_trades_by_subaccount_id(client_admin_wallet):
    subaccount_id = client_admin_wallet.active_subaccount.id
    subscription_result = client_admin_wallet.private_channels.trades_by_subaccount_id(
        subaccount_id=subaccount_id,
        callback=noop,
    )

    assert subscription_result.status[f"{subaccount_id}.trades"] == SUBSCRIPTION_OK


def test_private_trades_tx_status_by_subaccount_id(client_admin_wallet):
    subaccount_id = client_admin_wallet.active_subaccount.id
    tx_status = TxStatus2.settled
    subscription_result = client_admin_wallet.private_channels.trades_tx_status_by_subaccount_id(
        subaccount_id=subaccount_id,
        tx_status=TxStatus2.settled,
        callback=noop,
    )

    assert subscription_result.status[f"{subaccount_id}.trades.{tx_status.name}"] == SUBSCRIPTION_OK


def test_private_rfqs_by_wallet(client_admin_wallet):
    wallet = client_admin_wallet.account.address
    subscription_result = client_admin_wallet.private_channels.rfqs_by_wallet(
        wallet=wallet,
        callback=noop,
    )

    assert subscription_result.status[f"{wallet}.rfqs"] == SUBSCRIPTION_OK
