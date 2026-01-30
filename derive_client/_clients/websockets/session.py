"""
Asynchronous WebSocket session with automatic reconnection and auth hook.
"""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import uuid
import weakref
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional, Type, cast

import msgspec
from msgspec import ValidationError
from websockets import Data
from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed

from derive_client._clients.utils import JSONRPCEnvelope, decode_envelope
from derive_client.data_types import LoggerType
from derive_client.utils.logger import get_logger

if TYPE_CHECKING:
    from derive_client._clients.websockets.api import Handler, MessageT

LifecycleCallback = Callable[[], None] | Callable[[], Awaitable[None]]


class Subscribe(msgspec.Struct):
    channels: list[str]


class ConnectionState:
    """Task-safe connection state tracking."""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._connected = False
        self._reconnecting = False

    async def set_connected(self):
        async with self._lock:
            self._connected = True
            self._reconnecting = False

    async def set_disconnected(self):
        async with self._lock:
            self._connected = False

    async def set_reconnecting(self):
        async with self._lock:
            self._reconnecting = True

    async def is_connected(self) -> bool:
        async with self._lock:
            return self._connected

    async def is_reconnecting(self) -> bool:
        async with self._lock:
            return self._reconnecting


class WebSocketSession:
    """Asynchronous WebSocket session with automatic reconnection."""

    _on_disconnect: LifecycleCallback | None
    _on_reconnect: LifecycleCallback | None
    _on_before_resubscribe: LifecycleCallback | None

    def __init__(
        self,
        url: str,
        request_timeout: float = 10.0,
        reconnect: bool = True,
        reconnect_delay: float = 1.0,
        max_reconnect_delay: float = 60.0,
        logger: LoggerType | None = None,
        on_disconnect: LifecycleCallback | None = None,
        on_reconnect: LifecycleCallback | None = None,
        on_before_resubscribe: LifecycleCallback | None = None,
        max_handler_tasks: int = 100,  # Limit concurrent handler tasks
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
            max_handler_tasks: Maximum number of concurrent handler tasks
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
        self._channel_types_lock = asyncio.Lock()

        # Connection state
        self._ws: ClientConnection | None = None
        self._state = ConnectionState()

        # Message routing - ONE handler per channel
        self._handlers: dict[str, Handler] = {}
        self._handlers_lock = asyncio.Lock()

        # RPC tracking
        self._pending_requests: dict[str | int, asyncio.Queue] = {}
        self._requests_lock = asyncio.Lock()

        # Background tasks
        self._receiver_task: asyncio.Task | None = None
        self._reconnect_task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

        # Handler task management
        self._handler_tasks: set[asyncio.Task] = set()
        self._max_handler_tasks = max_handler_tasks
        self._handler_semaphore = asyncio.Semaphore(max_handler_tasks)

        # Cleanup
        self._finalizer = weakref.finalize(self, self._finalize, logger=self._logger)

    async def open(self) -> None:
        """Establish WebSocket connection and start receiver task."""
        if await self._state.is_connected():
            self._logger.warning("WebSocket already connected")
            return

        await self._connect()

    async def close(self) -> None:
        """Close connection and stop all tasks. Idempotent."""
        if self._ws is None and not await self._state.is_reconnecting():
            return

        self._logger.info("Closing WebSocket session")
        self._stop_event.set()

        # Close WebSocket
        await self._close_connection()

        # Cancel background tasks
        for task in [self._receiver_task, self._reconnect_task]:
            if task and not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

        self._receiver_task = None
        self._reconnect_task = None

        # Wait for handler tasks to complete (with timeout)
        if self._handler_tasks:
            self._logger.info(f"Waiting for {len(self._handler_tasks)} handler tasks to complete")
            try:
                await asyncio.wait_for(asyncio.gather(*self._handler_tasks, return_exceptions=True), timeout=5.0)
            except asyncio.TimeoutError:
                self._logger.warning("Handler tasks did not complete in time, cancelling")
                for task in self._handler_tasks:
                    task.cancel()

        self._handler_tasks.clear()

        # Clear state
        await self._state.set_disconnected()

        # Cancel pending requests
        async with self._requests_lock:
            for rid, queue in self._pending_requests.items():
                try:
                    queue.put_nowait({"error": "Connection closed"})
                except asyncio.QueueFull:
                    self._logger.warning("Failed to queue Connection closed")
            self._pending_requests.clear()

        self._logger.info("WebSocket session closed")

    async def subscribe(
        self,
        channel: str,
        handler: Handler[MessageT],
        notification_type: Optional[Type[MessageT]] = None,
    ) -> JSONRPCEnvelope:
        """
        Subscribe to a channel with a handler.

        Only one handler allowed per channel. If channel already has a handler,
        replaces it and logs a warning.

        Args:
            channel: Channel name (e.g., "BTC-PERP.trades")
            handler: Callback function(data) or async function to handle messages
            notification_type: Type to decode notifications into

        Returns:
            JSONRPCEnvelope with subscription confirmation
        """
        if not await self._state.is_connected():
            raise RuntimeError("WebSocket not connected. Call open() first.")

        async with self._handlers_lock:
            if channel in self._handlers:
                self._logger.warning(
                    f"Channel {channel} already has a handler - replacing it. "
                    "Consider using unsubscribe() first for explicit control."
                )

            self._handlers[channel] = handler
            if notification_type:
                async with self._channel_types_lock:
                    self._channel_types[channel] = notification_type

        params = Subscribe(channels=[channel])

        self._logger.info(f"Subscribing to channel: {channel}")
        try:
            envelope = await self._send_request("subscribe", params=params)
            self._logger.debug(f"Subscribe RPC response for {channel}: {envelope}")
            return envelope
        except Exception:
            # Rollback handler registration on failure
            async with self._handlers_lock:
                self._handlers.pop(channel, None)
            self._logger.exception(f"Subscribe RPC failed for {channel}")
            raise

    async def unsubscribe(self, channel: str) -> JSONRPCEnvelope | None:
        """
        Unsubscribe from a channel and remove its handler.

        Args:
            channel: Channel name

        Returns:
            JSONRPCEnvelope with unsubscribe confirmation
        """
        async with self._handlers_lock:
            if channel not in self._handlers:
                self._logger.warning(f"Not subscribed to channel: {channel}")
                return None

            del self._handlers[channel]

        self._logger.info(f"Unsubscribing from channel: {channel}")
        try:
            envelope = await self._send_request("unsubscribe", {"channels": [channel]})
            self._logger.debug(f"Unsubscribe RPC response for {channel}: {envelope}")
            return envelope
        except Exception:
            self._logger.exception(f"Unsubscribe RPC failed for {channel}")
            raise

    async def _connect(self) -> None:
        """Establish WebSocket connection and start receiver task."""
        self._logger.info(f"Connecting to {self._url}")

        try:
            self._ws = await connect(
                self._url,
                max_size=16 * 1024 * 1024,  # 16MB max message
                open_timeout=10.0,
                close_timeout=5.0,
            )
        except Exception as e:
            self._logger.error(f"Connection failed: {e}")
            raise

        await self._state.set_connected()

        # Start receiver task
        self._stop_event.clear()
        self._receiver_task = asyncio.create_task(self._receive_loop(), name="ws-receiver")

        self._logger.info("WebSocket connected, receiver task started")

    async def _close_connection(self) -> None:
        """Close the WebSocket connection."""
        if self._ws:
            try:
                await self._ws.close()
            except Exception as e:
                self._logger.debug(f"Error closing WebSocket: {e}")
            finally:
                self._ws = None

        await self._state.set_disconnected()

    async def _handle_disconnect(self) -> None:
        """Handle disconnection and trigger reconnection if enabled."""
        if self._stop_event.is_set():
            return

        await self._state.set_disconnected()
        self._logger.warning("WebSocket disconnected")

        # Notify user callback
        if self._on_disconnect is not None:
            try:
                res = self._on_disconnect()
                if inspect.isawaitable(res):
                    await cast(Awaitable[None], res)
            except Exception as e:
                self._logger.error(f"Error in on_disconnect callback: {e}")

        # Start reconnection if enabled
        if self._reconnect_enabled and not await self._state.is_reconnecting():
            await self._state.set_reconnecting()
            self._reconnect_task = asyncio.create_task(
                self._reconnect_loop(),
                name="ws-reconnect",
            )

    async def _reconnect_loop(self) -> None:
        """Reconnection loop with exponential backoff."""
        delay = self._reconnect_delay
        attempt = 1

        while not self._stop_event.is_set() and not await self._state.is_connected():
            self._logger.info(f"Reconnection attempt {attempt} in {delay:.1f}s")
            await asyncio.sleep(delay)

            if self._stop_event.is_set():
                break

            try:
                # Close old connection if exists
                await self._close_connection()

                # Establish new connection
                await self._connect()

                # Call reconnect callback (for re-auth, etc.)
                if self._on_reconnect is not None:
                    try:
                        res = self._on_reconnect()
                        if inspect.isawaitable(res):
                            await cast(Awaitable[None], res)
                    except Exception as e:
                        self._logger.error(f"Error in on_reconnect callback: {e}")
                        # Don't fail reconnection if callback fails

                # Call before_resubscribe callback (for re-authentication)
                if self._on_before_resubscribe is not None:
                    try:
                        res = self._on_before_resubscribe()
                        if inspect.isawaitable(res):
                            await cast(Awaitable[None], res)
                    except Exception as e:
                        self._logger.error(f"Error in on_before_resubscribe callback: {e}")
                        raise  # Re-auth failure should trigger retry

                # Resubscribe to all channels
                await self._resubscribe_all()

                self._logger.info(f"Reconnected successfully after {attempt} attempts")
                return

            except Exception as e:
                self._logger.error(f"Reconnection attempt {attempt} failed: {e}")
                attempt += 1
                delay = min(delay * 2, self._max_reconnect_delay)

        await self._state.set_disconnected()
        self._logger.info("Reconnection stopped")

    async def _resubscribe_all(self) -> None:
        """Resubscribe to all channels after reconnection."""
        async with self._handlers_lock:
            channels = list(self._handlers.keys())

        if not channels:
            self._logger.debug("No channels to resubscribe")
            return

        self._logger.info(f"Resubscribing to {len(channels)} channels")

        for channel in channels:
            try:
                params = Subscribe(channels=[channel])
                envelope = await self._send_request("subscribe", params=params)
                self._logger.debug(f"Resubscribed to {channel}: {envelope}")
            except Exception as e:
                self._logger.error(f"Failed to resubscribe to {channel}: {e}")
                # Continue trying other channels

    async def _send_request(self, method: str, params: msgspec.Struct | dict) -> JSONRPCEnvelope:
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

        response_queue: asyncio.Queue = asyncio.Queue(maxsize=1)

        async with self._requests_lock:
            self._pending_requests[request_id] = response_queue

        try:
            await self._ws.send(data)

            try:
                envelope = await asyncio.wait_for(response_queue.get(), timeout=self._request_timeout)
                return envelope
            except asyncio.TimeoutError:
                self._logger.error(f"RPC timeout for {method} after {self._request_timeout}s")
                raise TimeoutError(f"RPC timeout after {self._request_timeout}s")

        finally:
            async with self._requests_lock:
                self._pending_requests.pop(request_id, None)

    async def _receive_loop(self) -> None:
        """Background task: continuously receive and dispatch messages."""
        self._logger.info("Receiver task started")

        try:
            while not self._stop_event.is_set() and self._ws:
                try:
                    message = await self._ws.recv()
                    # Dispatch as a task so we don't block receiving
                    asyncio.create_task(self._dispatch_message(message))

                except TimeoutError:
                    continue

                except ConnectionClosed as e:
                    self._logger.warning(f"Connection closed: {e}")
                    await self._handle_disconnect()
                    break

                except Exception as e:
                    if not self._stop_event.is_set():
                        self._logger.error(f"Receive error: {e}", exc_info=True)
                        await self._handle_disconnect()
                    break

        finally:
            self._logger.info("Receiver task stopped")

    async def _dispatch_message(self, data: Data) -> None:
        """Dispatch message to appropriate handler."""
        try:
            envelope = decode_envelope(data)
        except Exception as e:
            self._logger.error(f"Failed to decode envelope: {e}")
            return

        # RPC response
        if envelope.id is not msgspec.UNSET:
            async with self._requests_lock:
                queue = self._pending_requests.get(envelope.id)

            if queue:
                try:
                    queue.put_nowait(envelope)
                except asyncio.QueueFull:
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

            async with self._handlers_lock:
                handler = self._handlers.get(channel)

            async with self._channel_types_lock:
                notification_type = self._channel_types.get(channel)

            if not handler:
                self._logger.debug(f"No handler for channel: {channel}")
                return

            # Decode notification
            data_raw = params_dict.get("data")
            try:
                notification = msgspec.convert(data_raw, type=notification_type)
            except ValidationError as e:
                self._logger.error(f"Notification decode error for {channel}: {e} data: {data_raw}", exc_info=True)
                return

            # Invoke handler as task
            await self._invoke_handler(channel, handler, notification)
            return

        # Other notification
        self._logger.debug(f"Unhandled notification: {envelope.method}")

    async def _invoke_handler(self, channel: str, handler: Handler, notification: Any) -> None:
        """Invoke handler as a background task with concurrency control."""
        async with self._handler_semaphore:
            task = asyncio.create_task(self._run_handler(channel, handler, notification), name=f"handler-{channel}")
            self._handler_tasks.add(task)
            task.add_done_callback(self._handler_tasks.discard)

    async def _run_handler(self, channel: str, handler: Handler, notification: Any) -> None:
        """Run handler (sync or async) and catch exceptions."""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(notification)
            else:
                # Run sync handler in executor to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, handler, notification)
        except Exception as e:
            self._logger.error(f"Handler error for {channel}: {e}", exc_info=True)

    @staticmethod
    def _finalize(logger: LoggerType) -> None:
        """Finalizer for cleanup."""
        logger.debug("WebSocketSession garbage collected without explicit close()")

    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
