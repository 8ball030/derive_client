# Quick Start

This guide will help you get started with the **Derive Python Client** using a minimal, synchronous HTTP setup. You will initialize your client, fund your subaccount, and prepare it for trading.

> Assumes you have completed:
>
> - Installation ([installation.md](installation.md))
> - Account registration ([authentication.md](authentication.md))  
>   You should already have:
> - `DERIVE_SESSION_PRIVATE_KEY`
> - `DERIVE_WALLET`
> - `DERIVE_SUBACCOUNT`

## 1. Set Up Environment Variables

You can manage your credentials via a `.env` file to keep them out of your code:

```shell
DERIVE_SESSION_PRIVATE_KEY=
DERIVE_WALLET=
DERIVE_SUBACCOUNT=
```

Then load them in Python using `python-dotenv` (or any preferred method):

```python
from dotenv import load_dotenv
import os

load_dotenv()

private_key = os.environ["DERIVE_SESSION_PRIVATE_KEY"]
wallet = os.environ["DERIVE_WALLET"]
subaccount_id = os.environ.get("DERIVE_SUBACCOUNT")
```

## 2. Initialize the Sync HTTP Client

```python
from derive_client import DeriveClient

client = DeriveClient(
    private_key=private_key,
    wallet=wallet,
    subaccount_id=subaccount_id
)
```

- Authenticates via your session key
- Supports core JSON-RPC methods and bridging operations
- Ideal for scripts and minimal setups

Async and WebSocket clients are available for high-concurrency or real-time workflows (see [clients.md](clients.md)).

## 3. Fund Your Account

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

Bridge ETH to your EOA for gas fees (needed for withdrawals later):

```python
# Bridge ETH for gas - ensures you can always withdraw funds
prepared_tx = client.bridge.prepare_deposit(
    human_amount=0.01,
    currency="ETH",
    source_chain="ETH",
    target_chain="DERIVE",  # Goes to your EOA
)
tx_result = client.bridge.submit_deposit(prepared_tx=prepared_tx)
tx_result = client.bridge.poll_progress(tx_result=tx_result)
```

#### Step 2: Bridge Trading Assets

Bridge tokens to your LightAccount for trading:

```python
# Bridge trading capital to LightAccount
prepared_tx = client.bridge.prepare_deposit(
    human_amount=100.0,
    currency="USDC",
    source_chain="BASE",
    target_chain="DERIVE",  # Goes to LightAccount
)
tx_result = client.bridge.submit_deposit(prepared_tx=prepared_tx)
tx_result = client.bridge.poll_progress(tx_result=tx_result)
```

#### Step 3: Transfer to Subaccount

Move funds from LightAccount to your trading subaccount:

```python
# Transfer to subaccount for trading
tx_result = client.transfer_to_subaccount(
    amount=100.0,
    token="USDC",
    subaccount_id=subaccount_id,
)
```

## 4. Withdrawing Funds

When you want to move funds back to external chains:

```python
# Withdraw from subaccount to LightAccount first
tx_result = client.transfer_from_subaccount(
    amount=100.0,
    token="USDC",
    subaccount_id=subaccount_id,
)

# Then bridge back to external chain
prepared_tx = client.bridge.prepare_withdrawal(
    human_amount=100.0,
    currency="USDC",
    source_chain="DERIVE",
    target_chain="BASE",
)
tx_result = client.bridge.submit_withdrawal(prepared_tx=prepared_tx)
tx_result = client.bridge.poll_progress(tx_result=tx_result)
```

---

Next:

- Start exploring example scripts for trading: [examples](examples/)
- Refer to API documentation: [API Reference](reference/)
