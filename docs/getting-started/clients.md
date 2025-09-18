# Clients

Derive offers multiple client interfaces so you can choose the one that best fits your application needs. All clients use the same underlying **JSON-RPC API**; the difference is in the transport protocol (HTTP vs WebSocket).

---

## Available Clients

| Client Type          | Transport Protocol   | Best For                                            | Real-Time Channels? |
| -------------------- | -------------------- | --------------------------------------------------- | ------------------- |
| **Sync HTTP**        | HTTP POST / JSON-RPC | Simple scripts, CLI tools, one-off queries          | ❌ No               |
| **Async HTTP**       | HTTP POST / JSON-RPC | High-performance, multi-concurrent workflows        | ❌ No               |
| **WebSocket Client** | WebSocket JSON-RPC   | Low latency, live updates, market data, event feeds | ✅ Yes              |

**All clients support**: Trading methods, account management, and bridging operations

---

## Transport Differences

**HTTP (Sync & Async):**

- Request-response pattern, new connection per call
- Simple, reliable, fewer moving parts

**WebSocket:**

- Persistent connection, lower latency for multiple requests
- Real-time subscriptions to live data streams

**Real-Time Channels (WebSocket Only):**

- **Public**: Orderbook, trade feeds, ticker data
- **Private**: Account updates, order status, personal notifications

---

## Choosing the Right Client

- **Occasional queries** → **Sync HTTP** (simplest)
- **High-frequency operations** → **Async HTTP** (concurrent requests)
- **Real-time applications** → **WebSocket** (live data streams)

All clients have identical trading and bridging APIs - choose based on your performance and real-time data needs.

---

Next: **[Quick Start](quickstart.md)** — Connect, fund, and start trading.
