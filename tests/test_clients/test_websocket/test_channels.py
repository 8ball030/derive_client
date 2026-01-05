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
