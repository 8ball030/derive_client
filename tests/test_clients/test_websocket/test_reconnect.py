"""
E2E test for WebSocket reconnection logic.
"""

import asyncio
import time

import pytest

from derive_client import WebSocketClient
from derive_client.data_types.channel_models import Interval, TickerSlimInstrumentNameIntervalPublisherDataSchema

TIMEOUT = 30
SUBSCRIPTION_OK = "ok"
ALREADY_SUBSCRIBED = "already subscribed"


@pytest.mark.asyncio
async def test_reconnection_after_forced_disconnect(client_admin_wallet: WebSocketClient):
    """
    Test that:
    1. We can subscribe and receive messages
    2. After forcing a disconnect, we automatically reconnect
    3. We re-authenticate and resubscribe
    4. We continue receiving messages
    """

    messages = []
    msg_event = asyncio.Event()
    disconnect_event = asyncio.Event()
    reconnect_event = asyncio.Event()
    reauth_event = asyncio.Event()

    def callback(result):
        messages.append(result)
        msg_event.set()

    # Hook into client's session callbacks
    ws_session = client_admin_wallet._session
    original_disconnect = client_admin_wallet._handle_disconnect
    original_reconnect = client_admin_wallet._handle_reconnect
    original_reauth = client_admin_wallet._handle_before_resubscribe

    async def on_disconnect():
        disconnect_event.set()
        if original_disconnect:
            original_disconnect()

    async def on_reconnect():
        reconnect_event.set()
        if original_reconnect:
            original_reconnect()

    async def on_reauth():
        reauth_event.set()
        if original_reauth:
            await original_reauth()

    ws_session._on_disconnect = on_disconnect
    ws_session._on_reconnect = on_reconnect
    ws_session._on_before_resubscribe = on_reauth

    # Step 1: Subscribe and verify initial message
    subscription_result = await client_admin_wallet.public_channels.ticker_slim_interval_by_instrument_name(
        instrument_name="ETH-PERP",
        interval=Interval.field_1000,
        callback=callback,
    )

    assert subscription_result.status["ticker_slim.ETH-PERP.1000"] in [SUBSCRIPTION_OK, ALREADY_SUBSCRIBED]

    # Wait for first message
    await asyncio.sleep(TIMEOUT)
    assert msg_event.is_set() is True
    assert len(messages) >= 1
    assert isinstance(messages[0], TickerSlimInstrumentNameIntervalPublisherDataSchema)

    first_message_count = len(messages)

    # Step 2: Force disconnect
    if ws_session._ws:
        await ws_session._ws.close()
    msg_event.clear()

    # Wait for disconnect to be detected

    await asyncio.sleep(TIMEOUT)
    assert disconnect_event.is_set() is True, "Disconnect was not detected"

    # Step 3: Wait for reconnection
    assert reconnect_event.is_set() is True, "Reconnection did not occur"

    # Step 4: Verify re-authentication happened
    assert reauth_event.is_set() is True, "Re-authentication did not occur"

    # Step 5: Verify we continue receiving messages after reconnection
    assert msg_event.is_set() is True, "No messages received after reconnection"
    assert len(messages) > first_message_count, "No new messages after reconnection"

    # Verify the new message is still the correct type
    assert isinstance(messages[-1], TickerSlimInstrumentNameIntervalPublisherDataSchema)

    print(f"✓ Received {len(messages)} total messages")
    print(f"✓ Messages before disconnect: {first_message_count}")
    print(f"✓ Messages after reconnect: {len(messages) - first_message_count}")


@pytest.mark.asyncio
async def test_reconnection_with_multiple_channels(client_admin_wallet):
    """
    Test that all subscribed channels are properly resubscribed after reconnection.
    """

    eth_messages = []
    btc_messages = []
    eth_event = asyncio.Event()
    btc_event = asyncio.Event()
    reconnect_event = asyncio.Event()

    def eth_callback(result):
        eth_messages.append(result)
        eth_event.set()

    def btc_callback(result):
        btc_messages.append(result)
        btc_event.set()

    ws_session = client_admin_wallet._session
    original_reconnect = ws_session._on_reconnect

    def on_reconnect():
        reconnect_event.set()
        if original_reconnect:
            original_reconnect()

    ws_session._on_reconnect = on_reconnect

    # Subscribe to two different channels
    await client_admin_wallet.public_channels.ticker_slim_interval_by_instrument_name(
        instrument_name="ETH-PERP",
        interval=Interval.field_1000,
        callback=eth_callback,
    )

    await client_admin_wallet.public_channels.ticker_slim_interval_by_instrument_name(
        instrument_name="BTC-PERP",
        interval=Interval.field_1000,
        callback=btc_callback,
    )

    # Wait for initial messages from both
    await asyncio.sleep(TIMEOUT)
    eth_received = eth_event.wait()
    btc_received = btc_event.wait()
    assert eth_received and btc_received

    eth_count_before = len(eth_messages)
    btc_count_before = len(btc_messages)

    # Force disconnect
    if ws_session._ws:
        await ws_session._ws.close()

    eth_event.clear()
    btc_event.clear()
    # Wait for reconnection
    await asyncio.sleep(TIMEOUT)
    reconnected = await reconnect_event.wait()
    assert reconnected is True

    # Verify BOTH channels receive messages after reconnect
    await asyncio.sleep(TIMEOUT)
    eth_after = await eth_event.wait()
    btc_after = await btc_event.wait()

    assert eth_after is True, "ETH channel not working after reconnect"
    assert btc_after is True, "BTC channel not working after reconnect"
    assert len(eth_messages) > eth_count_before
    assert len(btc_messages) > btc_count_before

    print(f"✓ ETH: {eth_count_before} → {len(eth_messages)} messages")
    print(f"✓ BTC: {btc_count_before} → {len(btc_messages)} messages")


@pytest.mark.stress
@pytest.mark.asyncio
async def test_multiple_reconnections(client_admin_wallet):
    """
    Stress test: Force multiple disconnects and verify we handle them all.
    """

    messages = []
    reconnect_count = [0]

    def callback(result):
        messages.append(result)

    ws_session = client_admin_wallet._session
    original_reconnect = ws_session._on_reconnect

    def on_reconnect():
        reconnect_count[0] += 1
        if original_reconnect:
            original_reconnect()

    ws_session._on_reconnect = on_reconnect

    # Subscribe
    await client_admin_wallet.public_channels.ticker_slim_interval_by_instrument_name(
        instrument_name="ETH-PERP",
        interval=Interval.field_1000,
        callback=callback,
    )

    await asyncio.sleep(2)  # Get some initial messages
    initial_count = len(messages)

    # Force 3 disconnects
    for i in range(3):
        if ws_session._ws:
            await ws_session._ws.close()
        await asyncio.sleep(8)  # Wait for reconnection + reauth

    # Verify we reconnected all 3 times
    assert reconnect_count[0] == 3, f"Expected 3 reconnects, got {reconnect_count[0]}"

    # Verify we're still receiving messages
    await asyncio.sleep(5)
    final_count = len(messages)
    assert final_count > initial_count, "No messages received after multiple reconnects"

    print(f"✓ Survived {reconnect_count[0]} reconnections")
    print(f"✓ Total messages: {final_count}")
