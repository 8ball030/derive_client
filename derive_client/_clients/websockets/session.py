"""
Synchronous WebSocket session with threaded message receiver.
"""

from __future__ import annotations

import threading
import uuid
import weakref
from collections import defaultdict
from logging import Logger
from queue import Empty, Full, Queue
from typing import Any, Callable, Optional, Type, TypeVar

import msgspec
from websockets.sync.client import ClientConnection, connect

from derive_client._clients.utils import JSONRPCEnvelope, decode_envelope
from derive_client.utils.logger import get_logger

MessageT = TypeVar('MessageT')
Handler = Callable[[MessageT], None]


class WebSocketSession:
    """Synchronous WebSocket session with background receiver thread."""

    def __init__(
        self,
        url: str,
        request_timeout: float = 10.0,
        logger: Logger | None = None,
    ):
        self._url = url
        self._request_timeout = request_timeout
        self._logger = logger if logger is not None else get_logger()

        self._channel_types: dict[str, Type] = {}
        self._channel_types_lock = threading.Lock()

        # Connection state
        self._ws: ClientConnection | None = None
        self._connected = threading.Event()

        # Message routing - multiple handlers per channel
        self._handlers: dict[str, list[Callable[[Any], None]]] = defaultdict(list)
        self._handlers_lock = threading.RLock()

        # RPC tracking (for subscribe/unsubscribe responses)
        self._pending_requests: dict[str, Queue] = {}
        self._requests_lock = threading.Lock()

        # Background receiver thread
        self._receiver_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # Cleanup finalizer
        self._finalizer = weakref.finalize(self, self._finalize, logger=self._logger)

    def open(self) -> None:
        """Establish WebSocket connection and start receiver thread."""

        if self._ws is not None:
            self._logger.warning("WebSocket already connected")
            return

        self._logger.info(f"Connecting to {self._url}")

        # Connect with websockets.sync
        self._ws = connect(
            self._url,
            max_size=16 * 1024 * 1024,  # 16MB max message
            open_timeout=10.0,
            close_timeout=5.0,
        )

        self._connected.set()

        # Start background receiver thread
        self._stop_event.clear()
        self._receiver_thread = threading.Thread(
            target=self._receive_loop,
            daemon=True,
            name="ws-receiver",
        )
        self._receiver_thread.start()

        self._logger.info("WebSocket connected, receiver thread started")

    def close(self) -> None:
        """Close connection and stop receiver thread. Idempotent."""

        if self._ws is None:
            return

        self._logger.info("Closing WebSocket connection")
        self._stop_event.set()

        # Close WebSocket
        try:
            self._ws.close()
        except Exception as e:
            self._logger.debug(f"Error closing WebSocket: {e}")
        finally:
            self._ws = None

        # Join receiver thread
        if self._receiver_thread and self._receiver_thread.is_alive():
            self._receiver_thread.join(timeout=5.0)
            if self._receiver_thread.is_alive():
                self._logger.warning("Receiver thread did not stop cleanly")
            self._receiver_thread = None

        # Clear state
        self._connected.clear()
        self._handlers.clear()

        # Cancel any pending requests
        with self._requests_lock:
            for rid, queue in self._pending_requests.items():
                try:
                    queue.put_nowait({"error": "Connection closed"})
                except Full:
                    self._logger.warning(f"Could not notify pending request of closure: {rid}")
            self._pending_requests.clear()

        self._logger.info("WebSocket closed")

    def subscribe(
        self,
        channel: str,
        handler: Handler,
        notification_type: Optional[Type] = None,
    ) -> None:
        """
        Subscribe to a channel with a handler.

        Multiple handlers can be registered for the same channel.
        Only sends subscribe RPC if this is the first handler for the channel.

        Args:
            channel: Channel name (e.g., "BTC-PERP.trades")
            handler: Callback function(data) to handle messages
        """

        if not self._connected.is_set():
            raise RuntimeError("WebSocket not connected. Call open() first.")

        with self._handlers_lock:
            is_first_handler = not self._handlers[channel]
            self._handlers[channel].append(handler)
            if notification_type:
                self._channel_types[channel] = notification_type

        class Subscribe(msgspec.Struct):
            channels: list[str]

        params = Subscribe(channels=[channel])

        # Only send subscribe RPC if this is the first handler
        if is_first_handler:
            self._logger.info(f"Subscribing to channel: {channel}")
            try:
                envelope = self._send_request("subscribe", params=params)
                self._logger.debug(f"Subscribe RPC response for {channel}: {envelope}")
                return envelope
            except Exception:
                self._logger.exception(f"Subscribe RPC failed for {channel}")
                raise
        else:
            self._logger.debug(f"Added handler for existing subscription: {channel}")

    def unsubscribe(
        self,
        channel: str,
        handler: Handler | None = None,
    ) -> None:
        """
        Unsubscribe from a channel.

        If handler is provided, only removes that handler.
        If handler is None, removes all handlers for the channel.
        Only sends unsubscribe RPC when last handler is removed.

        Args:
            channel: Channel name
            handler: Specific handler to remove (or None for all)
        """

        with self._handlers_lock:
            if channel not in self._handlers:
                self._logger.warning(f"Not subscribed to channel: {channel}")
                return

            if handler is None:
                del self._handlers[channel]
                should_unsubscribe = True
            else:
                try:
                    self._handlers[channel].remove(handler)
                    should_unsubscribe = len(self._handlers[channel]) == 0
                    if should_unsubscribe:
                        del self._handlers[channel]
                except ValueError:
                    self._logger.warning(f"Handler not found for channel: {channel}")
                    return

        if should_unsubscribe:
            self._logger.info(f"Unsubscribing from channel: {channel}")
            try:
                envelope = self._send_request("unsubscribe", {"channels": [channel]})
                self._logger.debug(f"Unsubscribe RPC response for {channel}: {envelope}")
                return envelope
            except Exception:
                self._logger.exception(f"Unsubscribe RPC failed for {channel}")
                raise

        return None

    def _send_request(self, method: str, params: msgspec.Struct) -> JSONRPCEnvelope:
        """Send RPC request and return decoded envelope"""

        if not self._ws:
            raise RuntimeError("WebSocket not connected")

        request_id = str(uuid.uuid4())
        params_dict = msgspec.structs.asdict(params)
        params_filtered = {k: v for k, v in params_dict.items() if v is not None}
        request = {"jsonrpc": "2.0", "method": method, "params": params_filtered, "id": request_id}
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
        """
        Background thread: continuously receive and dispatch messages.

        Runs until stop_event is set or connection closes.
        """

        self._logger.info("Receiver thread started")

        try:
            while not self._stop_event.is_set() and self._ws:
                try:
                    # Blocking receive with 1s timeout to check stop_event
                    message = self._ws.recv(timeout=1.0)
                    self._dispatch_message(message)

                except TimeoutError:
                    # Normal - allows checking stop_event periodically
                    continue

                except Exception as e:
                    if not self._stop_event.is_set():
                        self._logger.error(f"Receive error: {e}")
                    break

        finally:
            self._logger.info("Receiver thread stopped")

    def _dispatch_message(self, data: bytes) -> None:
        """
        Hot path: minimal deserialization for dispatch routing.

        Three message types:
        1. RPC response (has id) -> queue for pending request
        2. Subscription (method="subscription") -> invoke channel handlers
        3. Other notification -> log
        """

        envelope = decode_envelope(data)

        # RPC response message
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

        # Subscription message
        if envelope.method == "subscription":
            if envelope.params is None:
                self._logger.warning("Subscription message missing params")
                return

            # Decode minimal channel info for routing
            params_dict = msgspec.json.decode(envelope.params)
            channel = params_dict.get("channel")

            if not channel:
                self._logger.warning("Subscription params missing channel")
                return

            with self._handlers_lock:
                handlers = list(self._handlers.get(channel, []))
                notification_type = self._channel_types.get(channel)

            if not handlers:
                self._logger.debug(f"No handlers for channel: {channel}")
                return

            # Pass raw data to handlers - they decode based on channel schema
            data_raw = params_dict.get("data")
            data_bytes = msgspec.json.encode(data_raw)
            notification = msgspec.json.decode(data_bytes, type=notification_type)

            for handler in handlers:
                try:
                    handler(notification)
                except Exception as e:
                    self._logger.error(f"Handler error for {channel}: {e}", exc_info=True)
            return

        # Other notification
        self._logger.debug(f"Unhandled notification: {envelope.method}")

    @staticmethod
    def _finalize(logger: Logger) -> None:
        """Finalizer for cleanup if session not explicitly closed."""
        logger.debug("WebSocketSession was garbage collected without explicit close()")

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
