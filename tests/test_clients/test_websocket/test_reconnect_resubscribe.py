"""
Offline tests for reconnection: a reconnect must restore subscriptions.

Run against a local server, since the failures need a re-auth that fails,
reconnects that overlap, and a venue that refuses channels. The fake venue
only notifies connections that actually subscribed, so a session that
reconnects without resubscribing goes silent, as it does live.
"""

import asyncio
import json
from collections import Counter
from contextlib import asynccontextmanager

import pytest
from websockets.asyncio.server import serve

from derive_client._clients.websockets.session import WebSocketSession

CHANNEL = "test.channel"
OTHER = "other.channel"
# Live re-auth is a round trip over TLS; on loopback the race has no window.
LOGIN_DELAY = 1.0
REQUEST_TIMEOUT = 2.0


class FakeVenue:
    """Answers any RPC, records subscriptions, and can refuse or drop."""

    def __init__(self, login_delay: float = 0.0) -> None:
        self.seen: Counter = Counter()
        self.login_delay = login_delay
        # Set to "timeout", "error" or "drop" to break the next resubscribe.
        self.fault: str | None = None
        # Channel -> the reason the venue reports for refusing it.
        self.refuse: dict[str, str] = {}
        # Channels that make the venue reject the whole request they arrive
        # in, the way a deprecated channel name does live.
        self.poison: set[str] = set()
        # "both", "status" or "subscriptions": which half of the ack to send.
        self.ack = "both"
        self._subscriptions: dict = {}

    async def handler(self, websocket) -> None:
        self.seen["connections"] += 1
        self._subscriptions[websocket] = set()
        try:
            async for raw in websocket:
                message = json.loads(raw)
                method = message.get("method")
                self.seen[f"rpc:{method}"] += 1

                if method == "subscribe" and self.fault:
                    if await self._break(websocket, message):
                        return
                    continue

                if method == "public/login" and self.login_delay:
                    await asyncio.sleep(self.login_delay)

                reply = {"jsonrpc": "2.0", "id": message["id"], "result": {}}
                if method == "subscribe":
                    asked = message.get("params", {}).get("channels", [])
                    if self.poison.intersection(asked):
                        reply = {
                            "jsonrpc": "2.0",
                            "id": message["id"],
                            "error": {"code": -32602, "message": "Invalid params"},
                        }
                    else:
                        reply["result"] = self._subscribe(websocket, asked)
                await websocket.send(json.dumps(reply))
        except Exception:  # dropping clients is what this fixture is for
            pass
        finally:
            self._subscriptions.pop(websocket, None)

    def _subscribe(self, websocket, asked) -> dict:
        status = {}
        for channel in asked:
            if channel in self.refuse:
                status[channel] = self.refuse[channel]
                continue
            self._subscriptions[websocket].add(channel)
            status[channel] = "ok"

        result: dict = {}
        if self.ack in ("both", "status"):
            result["status"] = status
        if self.ack in ("both", "subscriptions"):
            result["current_subscriptions"] = sorted(self._subscriptions[websocket])
        return result

    async def _break(self, websocket, message) -> bool:
        """Apply the armed fault. True when the connection is gone."""

        if self.fault == "timeout":
            return False  # never answer
        if self.fault == "error":
            error = {"code": -32000, "message": "not authenticated"}
            await websocket.send(json.dumps({"jsonrpc": "2.0", "id": message["id"], "error": error}))
            return False
        self.fault = None  # "drop": only the first resubscribe dies
        websocket.transport.abort()
        return True

    async def publish(self, channel: str) -> int:
        """Notify subscribers of the channel, as the venue would."""
        delivered = 0
        for websocket, channels in list(self._subscriptions.items()):
            if channel not in channels:
                continue
            try:
                await websocket.send(
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "method": "subscription",
                            "params": {"channel": channel, "data": {"tick": 1}},
                        }
                    )
                )
                delivered += 1
            except Exception:
                pass
        return delivered

    async def drop_all(self) -> None:
        """Kill sockets without a close frame, as a network failure does."""
        for websocket in list(self._subscriptions):
            try:
                websocket.transport.abort()
            except Exception:
                await websocket.close(code=1006)
            self._subscriptions.pop(websocket, None)


@asynccontextmanager
async def _settled(venue, port, received, on_before_resubscribe=None, channels=(CHANNEL,)):
    """A session subscribed and proven to be delivering.

    Closed in a `finally`: conftest shares one event loop, so a leaked session
    keeps retrying a dead port for the whole run.
    """

    session = WebSocketSession(
        url=f"ws://127.0.0.1:{port}",
        request_timeout=REQUEST_TIMEOUT,
        reconnect_delay=0.2,
        on_before_resubscribe=on_before_resubscribe,
    )
    try:
        await session.open()

        async def on_message(_data):
            received.append(_data)

        for channel in channels:
            await session.subscribe(channel, on_message, notification_type=dict)

        assert await venue.publish(channels[0]) == 1
        await asyncio.sleep(0.3)
        assert received, "the channel was not delivering before the disconnect"
        received.clear()
        yield session
    finally:
        await session.close()


async def _assert_delivers(venue, received, message: str, channel: str = CHANNEL) -> None:
    received.clear()
    assert await venue.publish(channel) == 1, message
    await asyncio.sleep(0.3)
    assert received, message


@asynccontextmanager
async def _venue(login_delay: float = 0.0):
    venue = FakeVenue(login_delay=login_delay)
    async with serve(venue.handler, "127.0.0.1", 0) as server:
        yield venue, next(iter(server.sockets)).getsockname()[1]


@pytest.mark.asyncio
@pytest.mark.parametrize("fault, settle", [("timeout", 3.0), ("error", 1.5)])
async def test_a_refused_resubscribe_is_not_a_reconnect(fault, settle):
    """
    Test that a resubscribe the venue does not confirm keeps the session down.
    """

    received: list = []
    async with _venue() as (venue, port), _settled(venue, port, received) as session:
        venue.fault = fault
        await venue.drop_all()
        await asyncio.sleep(settle)

        assert venue.seen["rpc:subscribe"] > 1, "the test never exercised a resubscribe"
        assert not await session._state.is_connected(), "connected, but no channel came back"

        venue.fault = None
        await asyncio.sleep(4)
        await _assert_delivers(venue, received, "the venue recovered and the channel did not")


@pytest.mark.asyncio
async def test_one_refused_channel_does_not_take_the_others_down():
    """
    Test that a channel the venue will not serve leaves the rest working.
    """

    received: list = []
    async with _venue() as (venue, port), _settled(venue, port, received, channels=(CHANNEL, OTHER)) as session:
        venue.refuse[OTHER] = "Channel does not exist"
        await venue.drop_all()
        await asyncio.sleep(4)

        assert await session._state.is_connected(), "one bad channel took the session down"
        await _assert_delivers(venue, received, "the healthy channel did not come back")
        assert await venue.publish(OTHER) == 0, "the refused channel cannot be live"


@pytest.mark.asyncio
async def test_a_channel_the_venue_will_not_parse_does_not_silence_the_rest():
    """
    Test the fallback when the venue rejects the whole request over one channel.
    """

    received: list = []
    async with _venue() as (venue, port), _settled(venue, port, received, channels=(CHANNEL, OTHER)) as session:
        venue.poison.add(OTHER)
        await venue.drop_all()
        await asyncio.sleep(6)

        assert await session._state.is_connected(), "one unparseable channel took the session down"
        await _assert_delivers(venue, received, "the healthy channel did not come back")


@pytest.mark.asyncio
async def test_a_refusal_that_leaves_nothing_is_a_failed_attempt():
    """
    Test that refusing every channel is treated as a connection failure.
    """

    received: list = []
    async with _venue() as (venue, port), _settled(venue, port, received) as session:
        venue.refuse[CHANNEL] = "not authenticated"
        await venue.drop_all()
        await asyncio.sleep(4)

        assert not await session._state.is_connected(), "connected with nothing subscribed"

        venue.refuse.clear()
        await asyncio.sleep(5)
        await _assert_delivers(venue, received, "the venue recovered and the channel did not")


@pytest.mark.asyncio
async def test_current_subscriptions_decides_and_status_explains():
    """
    Test that confirmation comes from `current_subscriptions`, not `status`.
    """

    received: list = []
    async with _venue() as (venue, port), _settled(venue, port, received, channels=(CHANNEL, OTHER)) as session:
        venue.ack = "subscriptions"  # no status at all
        await venue.drop_all()
        await asyncio.sleep(2)
        assert await session._state.is_connected(), "current_subscriptions alone did not confirm"
        await _assert_delivers(venue, received, "reconnected, but the channel is silent")

        venue.ack = "both"
        venue.refuse[OTHER] = "Channel does not exist"
        await venue.drop_all()
        await asyncio.sleep(4)
        assert await session._state.is_connected(), "a refused channel took the session down"
        assert await venue.publish(OTHER) == 0, "refused, yet reported as subscribed"


@pytest.mark.asyncio
async def test_a_drop_while_resubscribing_does_not_strand_the_session():
    """
    Test that a disconnect inside the resubscribe window still recovers.

    Passes against 0.3.15 too: it guards the new ownership model, not the bug.
    """

    received: list = []
    async with _venue() as (venue, port), _settled(venue, port, received) as session:
        venue.fault = "drop"
        await venue.drop_all()
        await asyncio.sleep(5)

        assert venue.fault is None, "the test never exercised a drop while resubscribing"
        await _assert_delivers(venue, received, "reconnected, but the channel is silent")
        assert await session._state.is_connected()


@pytest.mark.asyncio
async def test_reopening_a_closed_session_resubscribes():
    """
    Test that close() then open() does not come back silent.
    """

    received: list = []
    async with _venue() as (venue, port), _settled(venue, port, received) as session:
        await session.close()
        await session.open()

        assert await session._state.is_connected()
        await _assert_delivers(venue, received, "reopened, but the channel is silent")


@pytest.mark.asyncio
async def test_open_during_a_reconnect_is_refused():
    """
    Test that open() does not build a second connection under a reconnect.
    """

    received: list = []
    async with _venue() as (venue, port), _settled(venue, port, received) as session:
        venue.fault = "timeout"
        await venue.drop_all()
        await asyncio.sleep(1)
        assert await session._state.is_reconnecting(), "the test never caught a reconnect"

        await session.open()
        assert not await session._state.is_connected(), "open() connected under the reconnect"

        venue.fault = None
        await asyncio.sleep(5)
        await _assert_delivers(venue, received, "the reconnect did not survive the open()")


@pytest.mark.asyncio
async def test_overlapping_reconnects_do_not_storm_or_lose_the_channel():
    """
    Test that drops arriving faster than a reconnect completes do not pile up.
    """

    received: list = []
    holder: dict = {}

    async def reauth():
        # A real round trip, so a racing reconnect has the same window as live.
        await holder["session"]._send_request("public/login", {})

    async with (
        _venue(login_delay=LOGIN_DELAY) as (venue, port),
        _settled(venue, port, received, on_before_resubscribe=reauth) as session,
    ):
        holder["session"] = session

        for _ in range(10):
            await venue.drop_all()
            await asyncio.sleep(0.6)
        await asyncio.sleep(10)

        # One reconnect per drop, give or take; a storm is hundreds.
        assert venue.seen["connections"] < 15, f"reconnect storm: {venue.seen['connections']} connections for 10 drops"
        await _assert_delivers(venue, received, "survived the drops, but the channel is silent")


def _live(venue: FakeVenue) -> int:
    """Connections the venue still has open."""
    return len(venue._subscriptions)


async def _eventually(predicate, timeout: float = 2.0) -> bool:
    """Poll for a condition: a socket closes on both ends, not just ours."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        if predicate():
            return True
        await asyncio.sleep(0.05)
    return predicate()


@pytest.mark.asyncio
async def test_an_open_that_cannot_restore_leaves_nothing_behind():
    """
    Test that an open() which fails to restore its channels closes its socket.
    """

    received: list = []
    async with _venue() as (venue, port), _settled(venue, port, received) as session:
        await session.close()

        venue.refuse[CHANNEL] = "not authenticated"
        with pytest.raises(ConnectionError):
            await session.open()

        assert await _eventually(lambda: _live(venue) == 0), "the failed open() left a connection open"

        venue.refuse.clear()
        await session.open()
        assert _live(venue) == 1, "reopening dialled on top of the failed open()"
        await _assert_delivers(venue, received, "reopened, but the channel is silent")


@pytest.mark.asyncio
async def test_subscribing_to_a_channel_the_venue_refuses_fails():
    """
    Test that a refused subscribe is reported rather than quietly registered.
    """

    received: list = []
    async with _venue() as (venue, port), _settled(venue, port, received) as session:
        venue.refuse[OTHER] = "Channel does not exist"

        with pytest.raises(ConnectionError):
            await session.subscribe(OTHER, lambda _data: None, notification_type=dict)

        assert await venue.publish(OTHER) == 0, "refused, yet reported as subscribed"
        await _assert_delivers(venue, received, "a refused subscribe took the live channel down")
