"""
E2E test for WebSocket reconnection logic.
"""

import threading
import time

import pytest

from derive_client.data_types.channel_models import Interval, TickerSlimInstrumentNameIntervalPublisherDataSchema

TIMEOUT = 30  # Increased timeout for reconnection
SUBSCRIPTION_OK = "ok"


def test_reconnection_after_forced_disconnect(client_admin_wallet):
    """
    Test that:
    1. We can subscribe and receive messages
    2. After forcing a disconnect, we automatically reconnect
    3. We automatically resubscribe and continue receiving messages
    """

    messages = []
    msg_event = threading.Event()
    disconnect_event = threading.Event()
    reconnect_event = threading.Event()

    def callback(result):
        messages.append(result)
        msg_event.set()

    def on_disconnect():
        disconnect_event.set()

    def on_reconnect():
        reconnect_event.set()

    # Get the underlying WebSocket session to add callbacks
    # (Assuming your client exposes the session, adjust if needed)
    ws_session = client_admin_wallet._ws_session
    ws_session._on_disconnect = on_disconnect
    ws_session._on_reconnect = on_reconnect

    # Step 1: Subscribe and verify initial message
    subscription_result = client_admin_wallet.public_channels.ticker_slim_interval_by_instrument_name(
        instrument_name="ETH-PERP",
        interval=Interval.field_1000,
        callback=callback,
    )

    assert subscription_result.status["ticker_slim.ETH-PERP.1000"] == SUBSCRIPTION_OK

    # Wait for first message
    received_first = msg_event.wait(timeout=TIMEOUT)
    assert received_first is True
    assert len(messages) == 1
    assert isinstance(messages[0], TickerSlimInstrumentNameIntervalPublisherDataSchema)

    first_message_count = len(messages)
    msg_event.clear()

    # Step 2: Force disconnect by closing the underlying WebSocket connection
    # This simulates a network issue or server restart
    if ws_session._ws:
        ws_session._ws.close()  # Force close the connection

    # Wait for disconnect to be detected
    disconnected = disconnect_event.wait(timeout=TIMEOUT)
    assert disconnected is True, "Disconnect was not detected"

    # Step 3: Wait for automatic reconnection
    reconnected = reconnect_event.wait(timeout=TIMEOUT)
    assert reconnected is True, "Reconnection did not occur"

    # Step 4: Verify we continue receiving messages after reconnection
    # Wait for a new message (proves resubscription worked)
    received_after_reconnect = msg_event.wait(timeout=TIMEOUT)
    assert received_after_reconnect is True, "No messages received after reconnection"
    assert len(messages) > first_message_count, "No new messages after reconnection"

    # Verify the new message is still the correct type
    assert isinstance(messages[-1], TickerSlimInstrumentNameIntervalPublisherDataSchema)

    print(f"✓ Received {len(messages)} total messages")
    print(f"✓ Messages before disconnect: {first_message_count}")
    print(f"✓ Messages after reconnect: {len(messages) - first_message_count}")


def test_reconnection_with_multiple_channels(client_admin_wallet):
    """
    Test that all subscribed channels are properly resubscribed after reconnection.
    """

    eth_messages = []
    btc_messages = []
    eth_event = threading.Event()
    btc_event = threading.Event()
    reconnect_event = threading.Event()

    def eth_callback(result):
        eth_messages.append(result)
        eth_event.set()

    def btc_callback(result):
        btc_messages.append(result)
        btc_event.set()

    def on_reconnect():
        reconnect_event.set()

    ws_session = client_admin_wallet._ws_session
    ws_session._on_reconnect = on_reconnect

    # Subscribe to two different channels
    eth_sub = client_admin_wallet.public_channels.ticker_slim_interval_by_instrument_name(
        instrument_name="ETH-PERP",
        interval=Interval.field_1000,
        callback=eth_callback,
    )

    btc_sub = client_admin_wallet.public_channels.ticker_slim_interval_by_instrument_name(
        instrument_name="BTC-PERP",
        interval=Interval.field_1000,
        callback=btc_callback,
    )

    assert eth_sub.status["ticker_slim.ETH-PERP.1000"] == SUBSCRIPTION_OK
    assert btc_sub.status["ticker_slim.BTC-PERP.1000"] == SUBSCRIPTION_OK

    # Wait for initial messages from both
    eth_received = eth_event.wait(timeout=TIMEOUT)
    btc_received = btc_event.wait(timeout=TIMEOUT)
    assert eth_received and btc_received

    eth_count_before = len(eth_messages)
    btc_count_before = len(btc_messages)
    eth_event.clear()
    btc_event.clear()

    # Force disconnect
    if ws_session._ws:
        ws_session._ws.close()

    # Wait for reconnection
    reconnected = reconnect_event.wait(timeout=TIMEOUT)
    assert reconnected is True

    # Verify BOTH channels receive messages after reconnect
    eth_after = eth_event.wait(timeout=TIMEOUT)
    btc_after = btc_event.wait(timeout=TIMEOUT)

    assert eth_after is True, "ETH channel not working after reconnect"
    assert btc_after is True, "BTC channel not working after reconnect"
    assert len(eth_messages) > eth_count_before
    assert len(btc_messages) > btc_count_before

    print(f"✓ ETH: {eth_count_before} → {len(eth_messages)} messages")
    print(f"✓ BTC: {btc_count_before} → {len(btc_messages)} messages")


def test_reconnection_backoff_timing(client_admin_wallet):
    """
    Test that reconnection uses exponential backoff.
    This test is more observational - we just verify reconnection happens
    within reasonable time bounds.
    """

    disconnect_times = []
    reconnect_times = []

    def on_disconnect():
        disconnect_times.append(time.time())

    def on_reconnect():
        reconnect_times.append(time.time())

    ws_session = client_admin_wallet._ws_session
    ws_session._on_disconnect = on_disconnect
    ws_session._on_reconnect = on_reconnect

    # Force disconnect
    if ws_session._ws:
        ws_session._ws.close()

    # Wait for reconnection
    time.sleep(10)  # Give it time to reconnect

    assert len(disconnect_times) > 0, "No disconnect detected"
    assert len(reconnect_times) > 0, "No reconnection occurred"

    # Verify reconnection happened within reasonable time
    # (with 1s initial delay and backoff, should reconnect within a few seconds)
    reconnect_duration = reconnect_times[0] - disconnect_times[0]
    assert reconnect_duration < 10.0, f"Reconnection took too long: {reconnect_duration}s"
    assert reconnect_duration >= 1.0, f"Reconnection too fast (no backoff?): {reconnect_duration}s"

    print(f"✓ Reconnected in {reconnect_duration:.2f}s")


@pytest.mark.stress
def test_multiple_reconnections(client_admin_wallet):
    """
    Stress test: Force multiple disconnects and verify we handle them all.
    """

    messages = []
    reconnect_count = [0]

    def callback(result):
        messages.append(result)

    def on_reconnect():
        reconnect_count[0] += 1

    ws_session = client_admin_wallet._ws_session
    ws_session._on_reconnect = on_reconnect

    # Subscribe
    client_admin_wallet.public_channels.ticker_slim_interval_by_instrument_name(
        instrument_name="ETH-PERP",
        interval=Interval.field_1000,
        callback=callback,
    )

    time.sleep(2)  # Get some initial messages
    initial_count = len(messages)

    # Force 3 disconnects
    for i in range(3):
        if ws_session._ws:
            ws_session._ws.close()
        time.sleep(5)  # Wait for reconnection

    # Verify we reconnected all 3 times
    assert reconnect_count[0] == 3, f"Expected 3 reconnects, got {reconnect_count[0]}"

    # Verify we're still receiving messages
    time.sleep(3)
    final_count = len(messages)
    assert final_count > initial_count, "No messages received after multiple reconnects"

    print(f"✓ Survived {reconnect_count[0]} reconnections")
    print(f"✓ Total messages: {final_count}")
