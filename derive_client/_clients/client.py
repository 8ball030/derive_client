#!/usr/bin/env python3
"""
run_client_with_server.py

1) spawn synthetic_server.py in a subprocess
2) start a minimal websocket client that subscribes to channels
3) consume stream for `duration` seconds and print client-side metrics
"""

import argparse
import asyncio
import subprocess
import sys
import threading
import time
from collections import defaultdict, deque
from typing import Any, Callable, DefaultDict, Deque, Dict, List, Optional, Tuple

# optional performance libs
try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except Exception:
    pass

import websockets

# Prefer orjson if present
try:
    import orjson as _orjson  # type: ignore

    def json_loads(b: Any):
        return _orjson.loads(b)
except Exception:
    import json as _json

    def json_loads(b: Any):
        # websockets delivers str by default
        return _json.loads(b)


STARTUP_MARKER = "Synthetic data server running on"


class MinimalWSClient:
    def __init__(self, uri: str, queue_size: int = 200_000):
        self.uri = uri
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)
        self._handlers: Dict[str, List[Callable[[str, dict], None]]] = defaultdict(list)
        self._metrics = {
            "messages_received": 0,
            "messages_processed": 0,
            "bytes_received": 0,
            "dropped": 0,
        }
        self._parse_ns: Deque[int] = deque(maxlen=20000)
        self._dispatch_ns: Deque[int] = deque(maxlen=20000)
        self._handler_ns: Deque[int] = deque(maxlen=20000)

        self._ws = None
        self._running = False
        self._recv_task = None
        self._dispatch_task = None
        self._monitor_task = None

    def subscribe(self, channel: str, handler: Callable[[str, dict], None]):
        if asyncio.iscoroutinefunction(handler):
            raise ValueError("handler must be synchronous (fast)")
        self._handlers[channel].append(handler)

    async def connect(self):
        self._ws = await websockets.connect(
            self.uri,
            max_size=16 * 1024 * 1024,
            compression=None,
            ping_interval=20,
            ping_timeout=10,
        )
        # Confirm connection state immediately
        try:
            # websockets library has .open attribute
            if getattr(self._ws, "open", True):
                print(f"[client] connected to {self.uri}")
            else:
                print(f"[client] connection object created but not open: {self._ws}")
        except Exception:
            print("[client] connected (couldn't introspect protocol object)")

    async def disconnect(self):
        self._running = False
        tasks = [t for t in (self._recv_task, self._dispatch_task, self._monitor_task) if t]
        for t in tasks:
            t.cancel()
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

    async def _receive_loop(self):
        try:
            async for raw in self._ws:
                # robustly account for bytes OR str
                try:
                    if isinstance(raw, (bytes, bytearray)):
                        b = bytes(raw)
                        self._metrics["bytes_received"] += len(b)
                        # decode only in parser stage; keep queue payload as bytes to avoid reencoding
                        # but our dispatch expects a str/json loader; put raw as-is
                        self._queue.put_nowait(b)
                    else:
                        # raw is str
                        self._metrics["bytes_received"] += len(raw.encode("utf-8"))
                        self._queue.put_nowait(raw)
                    self._metrics["messages_received"] += 1
                except asyncio.QueueFull:
                    self._metrics["dropped"] += 1
                except Exception as e:
                    # Unexpected error while queuing: log and continue receiving
                    print(f"[client.receive] queue error: {e}")
        except websockets.exceptions.ConnectionClosed as exc:
            print(
                f"[client.receive] connection closed: code={getattr(exc, 'code', None)} reason={getattr(exc, 'reason', None)}"
            )
            raise
        except asyncio.CancelledError:
            # expected on shutdown
            return
        except Exception as exc:
            # Something unexpected happened; log it so we can diagnose
            print(f"[client.receive] unexpected error: {exc}")
            raise

    async def _dispatch_loop(self):
        while self._running:
            try:
                raw = await self._queue.get()
            except asyncio.CancelledError:
                break

            parse_start = time.perf_counter_ns()
            try:
                payload = json_loads(raw)
            except Exception:
                # skip malformed payloads
                continue
            parse_ns = time.perf_counter_ns() - parse_start
            self._parse_ns.append(parse_ns)

            channel = payload.get("channel", "default")
            handlers = self._handlers.get(channel)
            if not handlers:
                continue

            dispatch_start = time.perf_counter_ns()
            for h in handlers:
                h_start = time.perf_counter_ns()
                try:
                    h(channel, payload)
                except Exception:
                    pass
                self._handler_ns.append(time.perf_counter_ns() - h_start)
            dispatch_ns = time.perf_counter_ns() - dispatch_start
            self._dispatch_ns.append(dispatch_ns)
            self._metrics["messages_processed"] += 1

    async def _monitor(self, interval: float = 1.0):
        start = time.perf_counter()
        while self._running:
            await asyncio.sleep(interval)
            now = time.perf_counter()
            elapsed = now - start
            proc = self._metrics["messages_processed"]
            recv = self._metrics["messages_received"]
            dropped = self._metrics["dropped"]
            mb = self._metrics["bytes_received"] / 1024.0 / 1024.0

            def pctiles(dq):
                if not dq:
                    return {}
                s = sorted(dq)
                n = len(s)

                def idx(p):
                    return min(n - 1, max(0, int(p * n)))

                return {
                    "p95_us": s[idx(0.95)] / 1000.0,
                    "p99_us": s[idx(0.99)] / 1000.0,
                    "avg_us": (sum(s) / n) / 1000.0,
                }

            parse_stats = pctiles(self._parse_ns)
            disp_stats = pctiles(self._dispatch_ns)
            print(
                f"[monitor] elapsed={int(elapsed)}s recv={recv:,} proc={proc:,} "
                f"throughput={proc / elapsed:.0f} msg/s dropped={dropped:,} mb={mb:.2f} "
                f"parse_p95={parse_stats.get('p95_us', 0):.2f}us disp_p95={disp_stats.get('p95_us', 0):.2f}us"
            )

    async def start(self):
        await self.connect()
        self._running = True
        self._recv_task = asyncio.create_task(self._receive_loop())
        self._dispatch_task = asyncio.create_task(self._dispatch_loop())
        self._monitor_task = asyncio.create_task(self._monitor())

    def queue_size(self):
        return self._queue.qsize()

    def final_metrics(self):
        return {
            "metrics": dict(self._metrics),
            "parse_ns_sample": list(self._parse_ns)[-10:],
            "dispatch_ns_sample": list(self._dispatch_ns)[-10:],
            "handler_ns_sample": list(self._handler_ns)[-10:],
        }


# ----------------------------
# Runner: spawn server subprocess, run client, shutdown
# ----------------------------


def _start_process(cmd: list, cwd: Optional[str] = None) -> subprocess.Popen:
    # Start server subprocess capturing stdout/stderr so we can show errors
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )


def _stream_pipe(prefix: str, pipe):
    """Read lines from pipe and echo them to stdout with prefix (runs in thread)."""
    try:
        for line in iter(pipe.readline, ""):
            if not line:
                break
            # strip trailing newline but keep message
            sys.stdout.write(f"{prefix}{line}")
            sys.stdout.flush()
    except Exception:
        return


def _start_streaming_io(proc: subprocess.Popen):
    """Start threads to stream stdout & stderr to parent terminal."""
    if proc.stdout:
        t_out = threading.Thread(target=_stream_pipe, args=("[server stdout] ", proc.stdout), daemon=True)
        t_out.start()
    if proc.stderr:
        t_err = threading.Thread(target=_stream_pipe, args=("[server stderr] ", proc.stderr), daemon=True)
        t_err.start()


def wait_for_ws(uri: str, timeout: float = 8.0, poll_interval: float = 0.2) -> bool:
    """Try to open a websocket connection repeatedly until timeout.
    Returns True if a connection succeeded, False on timeout.
    """
    deadline = time.time() + timeout

    async def _try_connect_once():
        try:
            async with websockets.connect(uri, ping_interval=None, open_timeout=1):
                return True
        except Exception:
            return False

    while time.time() < deadline:
        if asyncio.run(_try_connect_once()):
            return True
        time.sleep(poll_interval)
    return False


def spawn_server_and_wait(
    python_executable: str,
    server_path: str,
    rate: int,
    port: int,
    timeout: float = 8.0,
    duration=10,
) -> Tuple[subprocess.Popen, str]:
    cmd = [
        python_executable,
        "-m",
        "derive_client._clients.synthetic_server",
        "--rate",
        str(rate),
        "--port",
        str(port),
        "--duration",
        str(duration),
    ]
    proc = _start_process(cmd)
    # Start streaming server stdout/stderr immediately so we can see runtime logs
    _start_streaming_io(proc)

    # Wait for the TCP port to accept connections (not a perfect WebSocket handshake check but useful)
    host = "127.0.0.1"
    uri = f"ws://{host}:{port}"
    started = wait_for_ws(uri, timeout=timeout)

    if started:
        return proc, f"server listening on {host}:{port}"
    else:
        # server failed to start or bind in time; capture anything left and raise
        try:
            out, err = proc.communicate(timeout=1.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, err = proc.communicate(timeout=1.0)
        msg = (
            f"Server failed to start within {timeout}s.\n"
            f"Process returncode={proc.returncode}\n"
            f"stdout:\n{(out or '').strip()}\n\nstderr:\n{(err or '').strip()}\n"
        )
        raise RuntimeError(msg)


async def run_client_cycle(uri: str, duration: int, rate: int):
    client = MinimalWSClient(uri)

    # very cheap handlers for the synthetic messages
    counts: DefaultDict[str, int] = defaultdict(int)

    def ticker_h(ch, payload):
        counts[ch] += 1
        # cheap numeric extraction
        _ = payload["data"].get("last_price", 0)

    def book_h(ch, payload):
        counts[ch] += 1
        _ = len(payload["data"].get("bids", ()))

    # subscribe to the synthetic server's channels
    client.subscribe("ticker.BTC-PERPETUAL", ticker_h)
    client.subscribe("ticker.ETH-PERPETUAL", ticker_h)
    client.subscribe("ticker.SOL-PERPETUAL", ticker_h)
    client.subscribe("book.BTC-PERPETUAL", book_h)
    client.subscribe("book.ETH-PERPETUAL", book_h)
    client.subscribe("book.SOL-PERPETUAL", book_h)

    await client.start()
    print("client started, running...")

    # run for duration seconds
    try:
        await asyncio.sleep(duration)
    except asyncio.CancelledError:
        pass

    await client.disconnect()
    print("client stopped")
    print("final metrics:", client.final_metrics())
    print("counts by channel:")
    for ch, c in sorted(counts.items()):
        print(f"  {ch:30s}: {c:,}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--server", default="synthetic_server.py", help="path to synthetic server script")
    p.add_argument("--rate", type=int, default=10000, help="server message rate (msg/s)")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--duration", type=int, default=10, help="seconds client runs")
    p.add_argument("--python", default=sys.executable, help="python executable to spawn the server")
    args = p.parse_args()

    # spawn server subprocess
    try:
        proc, info = spawn_server_and_wait(args.python, args.server, args.rate, args.port, timeout=8.0)
        print(f"spawned server pid={proc.pid} rate={args.rate} port={args.port} ({info})")
    except RuntimeError as e:
        print("Server startup failed:\n", e)
        return

    # give server a moment to start
    time.sleep(0.8)

    uri = f"ws://localhost:{args.port}"
    try:
        asyncio.run(run_client_cycle(uri, args.duration, args.rate))
    except KeyboardInterrupt:
        print("interrupted")
    finally:
        # terminate server subprocess
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            proc.kill()
        print("server terminated")


if __name__ == "__main__":
    main()
