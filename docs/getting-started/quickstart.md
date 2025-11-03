# Quick Start

This guide walks you through funding your account and placing your first trade.

> Assumes you have completed:
>
> - Installation ([installation.md](installation.md))
> - Account registration ([authentication.md](authentication.md))
> - You should already have:
>   - `DERIVE_SESSION_KEY`
>   - `DERIVE_WALLET`
>   - `DERIVE_SUBACCOUNT_ID`

## 1. Set Up Environment Variables

You can manage your credentials via a `.env` file to keep them out of your code:

```shell
DERIVE_SESSION_KEY=
DERIVE_WALLET=
DERIVE_SUBACCOUNT_ID=
```

Then load them in Python using `python-dotenv` (or any preferred method):

```python
from dotenv import load_dotenv
import os

load_dotenv()

session_key = os.environ["DERIVE_SESSION_KEY"]
wallet = os.environ["DERIVE_WALLET"]
subaccount_id = os.environ.get("DERIVE_SUBACCOUNT_ID")
```

## 2. Initialize the HTTPClient

```python
from derive_client import HTTPClient, Environment

client = HTTPClient(
    session_key=session_key,
    wallet=wallet,
    subaccount_id=subaccount_id,
    env=Environment.PROD,
)
```

- Authenticates via your session key
- Supports core JSON-RPC methods and bridging operations
- Ideal for scripts and minimal setups

Async and WebSocket clients are available for high-concurrency or real-time workflows (see [clients.md](clients.md)).

## 3. Fund Your Account

**Quick Reference:**

- **EOA** → Your externally owned account (needs ETH for gas to withdraw)
- **LightAccount** → Your smart contract wallet on Derive (holds bridged assets)
- **Subaccount** → Your trading account (where you place orders)

Trading requires funds in the right places. Here's the complete funding flow:

### Understanding Bridge Operations

Each bridge operation follows a safe 3-step pattern:

1. **Prepare** - Calculate fees, validate, return transaction details for review.
2. **Submit** - Execute transaction and return tracking information
3. **Poll** - Monitor progress across both chains until completion:
   - Finality on source chain
   - Event on target chain
   - Finality on target chain

### Funding Steps

#### Step 1: Fund EOA with gas money

Bridge ETH to your EOA on Derive for gas fees (needed for withdrawals later):

```python
from derive_client.data_types import ChainID, Currency, D

# D - convenience wrapper that returns Decimal from int, float or str
amount_eth = D(0.001)

# Bridge ETH from ETH Mainnet to Derive - needed for gas fees when withdrawing later
prepared_tx = client.bridge.prepare_gas_deposit_tx(amount=amount_eth)

# One may inspect the prepared transaction, including estimated gas costs, before submission
tx_result = client.bridge.submit_tx(prepared_tx=prepared_tx)

# A BridgeTxResult, including the transaction hash on source chain, is immediately returned.
# This can be passed along for finality checks.
tx_result = client.bridge.poll_tx_progress(tx_result=tx_result)
```

> **Note:** All trading operations on Derive (orders, transfers between subaccounts, rfq operations) are gasless - the Derive paymaster covers transaction costs. You only need ETH in your EOA for withdrawing funds back to external chains.

#### Step 2: Bridge Trading Assets

Bridge assets to your LightAccount wallet for trading:

```python
amount_usdc = D(100.0)

prepared_tx = client.bridge.prepare_deposit_tx(
    amount=amount_usdc,
    currency=Currency.USDC,
    chain_id=ChainID.BASE,
)
tx_result = client.submit_bridge_tx(prepared_tx=prepared_tx)
tx_result = client.poll_bridge_progress(tx_result=tx_result)
```

#### Step 3: Transfer to Subaccount

Move funds from your LightAccount wallet to a subaccount to trade:

```python
tx_result = client.transactions.deposit_to_subaccount(
    amount=amount_usdc,
    token=Currency.USDC,
)
```

## 4. Withdrawing Funds

Withdrawal is a two-step process in the reverse direction:

```python
# Step 1: Withdraw from subaccount to your LightAccount wallet
tx_result = client.transactions.withdraw_from_subaccount(
    amount=amount_usdc,
    token=Currency.USDC,
)

# Step 2: Bridge to an external chain (funds sent to LightAccount wallet's owner address)
prepared_tx = client.bridge.prepare_withdrawal_tx(
    amount=amount_usdc,
    currency=Currency.USDC,
    chain_id=ChainID.BASE,
)
tx_result = client.submit_bridge_tx(prepared_tx=prepared_tx)
tx_result = client.poll_bridge_progress(tx_result=tx_result)
```

## 5. Place Your First Trade

Now that your subaccount is funded, let's place a simple order:

### Check Available Markets

```python
# Get current ticker for ETH perpetual
ticker = client.get_ticker(instrument_name="ETH-PERP")

print(f"ETH-PERP bid: {ticker.best_bid_price}, ask: {ticker.best_ask_price}")
```

### Create a Limit Order

```python
from derive_client.data.generated.models import Direction, OrderType

# Place a limit buy order at $3000
order = client.orders.create(
    instrument_name="ETH-PERP",
    amount=D("0.1"),  # 0.1 ETH
    limit_price=D("3000"),
    direction=Direction.buy,
    order_type=OrderType.limit,
)

print(f"Order created: {order.order.order_id}")
print(f"Status: {order.order.order_status}")

# if (part of) it filled immediately, a non-empty array of trades will be returned:
for trade in order.trades:
    print(f"Trade: {trade.amount} @ tx id: {trade.transaction_id})
```

### Check Order Status

```python
# List all open orders
open_orders = client.orders.list_open()
for order in open_orders.orders:
    print(f"{order.instrument_name}: {order.amount} @ {order.limit_price}")

# Get specific order details
order_detail = client.orders.get(order_id=order.order_id)
print(f"Filled: {order_detail.filled_amount/order_detail.amount:.2f}")
```

### View Your Positions

```python
# Check your positions
positions = client.positions.list()
for position in positions:
    print(f"{position.instrument_name}: {position.amount} @ avg {position.average_price:.2f}")
```

### Cancel Orders

```python
# Cancel a specific order
cancelled_order = client.orders.cancel(order_id=order.order_id, instrument_name="ETH-PERP")
print(f"Order status: {cancelled_order.order_status.value}, reason: {cancelled_order.cancel_reason.value}")

# Or cancel all outstanding orders
client.orders.cancel_all()
```

---

Next:

- Start exploring example scripts for trading: [examples](examples/)
- Refer to API documentation: [API Reference](reference/)
  1
