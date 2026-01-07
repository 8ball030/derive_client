"""
Synchronous WebSocket session with automatic reconnection and auth hook.
"""

from __future__ import annotations

import threading
import time
import uuid
import weakref
from logging import Logger
from queue import Empty, Full, Queue
from typing import Any, Callable, Optional, Type, TypeVar

import msgspec
from websockets import Data
from websockets.exceptions import ConnectionClosed
from websockets.sync.client import ClientConnection, connect

from derive_client._clients.utils import JSONRPCEnvelope, decode_envelope
from derive_client.utils.logger import get_logger

MessageT = TypeVar('MessageT')
Handler = Callable[[MessageT], None]


class Subscribe(msgspec.Struct):
    channels: list[str]


class ConnectionState:
    """Thread-safe connection state tracking."""

    def __init__(self):
        self._lock = threading.Lock()
        self._connected = False
        self._reconnecting = False

    def set_connected(self):
        with self._lock:
            self._connected = True
            self._reconnecting = False

    def set_disconnected(self):
        with self._lock:
            self._connected = False

    def set_reconnecting(self):
        with self._lock:
            self._reconnecting = True

    def is_connected(self) -> bool:
        with self._lock:
            return self._connected

    def is_reconnecting(self) -> bool:
        with self._lock:
            return self._reconnecting


class WebSocketSession:
    """Synchronous WebSocket session with automatic reconnection."""

    def __init__(
        self,
        url: str,
        request_timeout: float = 10.0,
        reconnect: bool = True,
        reconnect_delay: float = 1.0,
        max_reconnect_delay: float = 60.0,
        logger: Logger | None = None,
        on_disconnect: Callable[[], None] | None = None,
        on_reconnect: Callable[[], None] | None = None,
        on_before_resubscribe: Callable[[], None] | None = None,
    ):
        """
        Args:
            url: WebSocket URL
            request_timeout: RPC request timeout in seconds
            reconnect: Enable automatic reconnection
            reconnect_delay: Initial reconnection delay in seconds
            max_reconnect_delay: Maximum reconnection delay (for backoff)
            logger: Logger instance
            on_disconnect: Callback when disconnection is detected
            on_reconnect: Callback after successful reconnection (before resubscribe)
            on_before_resubscribe: Callback before resubscribing channels (for re-auth)
        """
        self._url = url
        self._request_timeout = request_timeout
        self._logger = logger if logger is not None else get_logger()

        # Reconnection config
        self._reconnect_enabled = reconnect
        self._reconnect_delay = reconnect_delay
        self._max_reconnect_delay = max_reconnect_delay
        self._on_disconnect = on_disconnect
        self._on_reconnect = on_reconnect
        self._on_before_resubscribe = on_before_resubscribe

        # Channel type registry
        self._channel_types: dict[str, Type] = {}
        self._channel_types_lock = threading.Lock()

        # Connection state
        self._ws: ClientConnection | None = None
        self._state = ConnectionState()

        # Message routing - ONE handler per channel
        self._handlers: dict[str, Callable[[Any], None]] = {}
        self._handlers_lock = threading.RLock()

        # RPC tracking
        self._pending_requests: dict[str | int, Queue] = {}
        self._requests_lock = threading.Lock()

        # Background threads
        self._receiver_thread: threading.Thread | None = None
        self._reconnect_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # Cleanup
        self._finalizer = weakref.finalize(self, self._finalize, logger=self._logger)

    def open(self) -> None:
        """Establish WebSocket connection and start receiver thread."""
        if self._state.is_connected():
            self._logger.warning("WebSocket already connected")
            return

        self._connect()

    def close(self) -> None:
        """Close connection and stop all threads. Idempotent."""
        if self._ws is None and not self._state.is_reconnecting():
            return

        self._logger.info("Closing WebSocket session")
        self._stop_event.set()

        # Close WebSocket
        self._close_connection()

        # Join threads
        for thread in [self._receiver_thread, self._reconnect_thread]:
            if thread and thread.is_alive():
                thread.join(timeout=5.0)
                if thread.is_alive():
                    self._logger.warning(f"Thread {thread.name} did not stop cleanly")

        self._receiver_thread = None
        self._reconnect_thread = None

        # Clear state
        self._state.set_disconnected()

        # Cancel pending requests
        with self._requests_lock:
            for rid, queue in self._pending_requests.items():
                try:
                    queue.put_nowait({"error": "Connection closed"})
                except Full:
                    self._logger.warning("Failed to queue Connection closed")
            self._pending_requests.clear()

        self._logger.info("WebSocket session closed")

    def subscribe(
        self,
        channel: str,
        handler: Handler,
        notification_type: Optional[Type] = None,
    ) -> JSONRPCEnvelope:
        """
        Subscribe to a channel with a handler.

        Only one handler allowed per channel. If channel already has a handler,
        replaces it and logs a warning.

        Args:
            channel: Channel name (e.g., "BTC-PERP.trades")
            handler: Callback function(data) to handle messages
            notification_type: Type to decode notifications into

        Returns:
            JSONRPCEnvelope with subscription confirmation
        """
        if not self._state.is_connected():
            raise RuntimeError("WebSocket not connected. Call open() first.")

        with self._handlers_lock:
            if channel in self._handlers:
                self._logger.warning(
                    f"Channel {channel} already has a handler - replacing it. "
                    "Consider using unsubscribe() first for explicit control."
                )

            self._handlers[channel] = handler
            if notification_type:
                with self._channel_types_lock:
                    self._channel_types[channel] = notification_type

        params = Subscribe(channels=[channel])

        self._logger.info(f"Subscribing to channel: {channel}")
        try:
            envelope = self._send_request("subscribe", params=params)
            self._logger.debug(f"Subscribe RPC response for {channel}: {envelope}")
            return envelope
        except Exception:
            # Rollback handler registration on failure
            with self._handlers_lock:
                self._handlers.pop(channel, None)
            self._logger.exception(f"Subscribe RPC failed for {channel}")
            raise

    def unsubscribe(self, channel: str) -> JSONRPCEnvelope | None:
        """
        Unsubscribe from a channel and remove its handler.

        Args:
            channel: Channel name

        Returns:
            JSONRPCEnvelope with unsubscribe confirmation
        """
        with self._handlers_lock:
            if channel not in self._handlers:
                self._logger.warning(f"Not subscribed to channel: {channel}")
                return None

            del self._handlers[channel]

        self._logger.info(f"Unsubscribing from channel: {channel}")
        try:
            envelope = self._send_request("unsubscribe", {"channels": [channel]})
            self._logger.debug(f"Unsubscribe RPC response for {channel}: {envelope}")
            return envelope
        except Exception:
            self._logger.exception(f"Unsubscribe RPC failed for {channel}")
            raise

    def _connect(self) -> None:
        """Establish WebSocket connection and start receiver thread."""
        self._logger.info(f"Connecting to {self._url}")

        try:
            self._ws = connect(
                self._url,
                max_size=16 * 1024 * 1024,  # 16MB max message
                open_timeout=10.0,
                close_timeout=5.0,
            )
        except Exception as e:
            self._logger.error(f"Connection failed: {e}")
            raise

        self._state.set_connected()

        # Start receiver thread
        self._stop_event.clear()
        self._receiver_thread = threading.Thread(
            target=self._receive_loop,
            daemon=True,
            name="ws-receiver",
        )
        self._receiver_thread.start()

        self._logger.info("WebSocket connected, receiver thread started")

    def _close_connection(self) -> None:
        """Close the WebSocket connection."""
        if self._ws:
            try:
                self._ws.close()
            except Exception as e:
                self._logger.debug(f"Error closing WebSocket: {e}")
            finally:
                self._ws = None

        self._state.set_disconnected()

    def _handle_disconnect(self) -> None:
        """Handle disconnection and trigger reconnection if enabled."""
        if self._stop_event.is_set():
            return

        self._state.set_disconnected()
        self._logger.warning("WebSocket disconnected")

        # Notify user callback
        if self._on_disconnect:
            try:
                self._on_disconnect()
            except Exception as e:
                self._logger.error(f"Error in on_disconnect callback: {e}")

        # Start reconnection if enabled
        if self._reconnect_enabled and not self._state.is_reconnecting():
            self._state.set_reconnecting()
            self._reconnect_thread = threading.Thread(
                target=self._reconnect_loop,
                daemon=True,
                name="ws-reconnect",
            )
            self._reconnect_thread.start()

    def _reconnect_loop(self) -> None:
        """Reconnection loop with exponential backoff."""
        delay = self._reconnect_delay
        attempt = 1

        while not self._stop_event.is_set() and not self._state.is_connected():
            self._logger.info(f"Reconnection attempt {attempt} in {delay:.1f}s")
            time.sleep(delay)

            if self._stop_event.is_set():
                break

            try:
                # Close old connection if exists
                self._close_connection()

                # Establish new connection
                self._connect()

                # Call reconnect callback (for re-auth, etc.)
                if self._on_reconnect:
                    try:
                        self._on_reconnect()
                    except Exception as e:
                        self._logger.error(f"Error in on_reconnect callback: {e}")
                        # Don't fail reconnection if callback fails

                # Call before_resubscribe callback (for re-authentication)
                if self._on_before_resubscribe:
                    try:
                        self._on_before_resubscribe()
                    except Exception as e:
                        self._logger.error(f"Error in on_before_resubscribe callback: {e}")
                        raise  # Re-auth failure should trigger retry

                # Resubscribe to all channels
                self._resubscribe_all()

                self._logger.info(f"Reconnected successfully after {attempt} attempts")
                return

            except Exception as e:
                self._logger.error(f"Reconnection attempt {attempt} failed: {e}")
                attempt += 1
                delay = min(delay * 2, self._max_reconnect_delay)

        self._state.set_disconnected()
        self._logger.info("Reconnection stopped")

    def _resubscribe_all(self) -> None:
        """Resubscribe to all channels after reconnection."""
        with self._handlers_lock:
            channels = list(self._handlers.keys())

        if not channels:
            self._logger.debug("No channels to resubscribe")
            return

        self._logger.info(f"Resubscribing to {len(channels)} channels")

        for channel in channels:
            try:
                params = Subscribe(channels=[channel])
                envelope = self._send_request("subscribe", params=params)
                self._logger.debug(f"Resubscribed to {channel}: {envelope}")
            except Exception as e:
                self._logger.error(f"Failed to resubscribe to {channel}: {e}")
                # Continue trying other channels

    def _send_request(self, method: str, params: msgspec.Struct | dict) -> JSONRPCEnvelope:
        """Send RPC request and return decoded envelope."""
        if not self._ws:
            raise RuntimeError("WebSocket not connected")

        request_id = str(uuid.uuid4())

        if isinstance(params, msgspec.Struct):
            params_dict = msgspec.structs.asdict(params)
            params_filtered = {k: v for k, v in params_dict.items() if v is not None}
        else:
            params_filtered = params

        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params_filtered,
            "id": request_id,
        }
        data = msgspec.json.encode(request).decode("utf-8")

        response_queue: Queue = Queue(maxsize=1)

        with self._requests_lock:
            self._pending_requests[request_id] = response_queue

        try:
            self._ws.send(data)

            try:
                envelope = response_queue.get(timeout=self._request_timeout)
                return envelope
            except Empty:
                self._logger.error(f"RPC timeout for {method} after {self._request_timeout}s")
                raise TimeoutError(f"RPC timeout after {self._request_timeout}s")

        finally:
            with self._requests_lock:
                self._pending_requests.pop(request_id, None)

    def _receive_loop(self) -> None:
        """Background thread: continuously receive and dispatch messages."""
        self._logger.info("Receiver thread started")

        try:
            while not self._stop_event.is_set() and self._ws:
                try:
                    message = self._ws.recv(timeout=1.0)
                    self._dispatch_message(message)

                except TimeoutError:
                    continue

                except ConnectionClosed as e:
                    self._logger.warning(f"Connection closed: {e}")
                    self._handle_disconnect()
                    break

                except Exception as e:
                    if not self._stop_event.is_set():
                        self._logger.error(f"Receive error: {e}", exc_info=True)
                        self._handle_disconnect()
                    break

        finally:
            self._logger.info("Receiver thread stopped")

    def _dispatch_message(self, data: Data) -> None:
        """Dispatch message to appropriate handler."""
        envelope = decode_envelope(data)

        # RPC response
        if envelope.id is not msgspec.UNSET:
            with self._requests_lock:
                queue = self._pending_requests.get(envelope.id)

            if queue:
                try:
                    queue.put_nowait(envelope)
                except Full:
                    self._logger.warning(f"Failed to queue RPC response: {envelope.id}")
            else:
                self._logger.debug(f"No pending request for id: {envelope.id}")
            return

        # Subscription notification
        if envelope.method == "subscription":
            if envelope.params is msgspec.UNSET:
                self._logger.warning("Subscription message missing params")
                return

            params_dict = msgspec.json.decode(envelope.params)
            channel = params_dict.get("channel")

            if not channel:
                self._logger.warning("Subscription params missing channel")
                return

            with self._handlers_lock:
                handler = self._handlers.get(channel)
                with self._channel_types_lock:
                    notification_type = self._channel_types.get(channel)

            if not handler:
                self._logger.debug(f"No handler for channel: {channel}")
                return

            # Decode and invoke handler
            data_raw = params_dict.get("data")
            data_bytes = msgspec.json.encode(data_raw)
            notification = msgspec.json.decode(data_bytes, type=notification_type)

            try:
                handler(notification)
            except Exception as e:
                self._logger.error(f"Handler error for {channel}: {e}", exc_info=True)
            return

        # Other notification
        self._logger.debug(f"Unhandled notification: {envelope.method}")

    @staticmethod
    def _finalize(logger: Logger) -> None:
        """Finalizer for cleanup."""
        logger.debug("WebSocketSession garbage collected without explicit close()")

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
