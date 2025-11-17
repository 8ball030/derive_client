# Examples

The best way to learn Derive is by running the example scripts. All examples are complete, runnable Python scripts with detailed comments.

## Prerequisites

The examples use `.env.template` with pre-configured testnet credentials - you can run them immediately without setup!

```bash
git clone git@github.com:8ball030/derive_client.git
cd derive_client
python examples/01_quickstart.py
```

## Example Scripts

### [01_quickstart.py](https://github.com/8ball030/derive_client/blob/main/examples/01_quickstart.py)

**Your first trade in 5 minutes**

Learn how to:

1. Set up the client
2. Check your balance
3. View available markets
4. Place a simple order
5. Check order status

---

### [02_market_data.py](https://github.com/8ball030/derive_client/blob/main/examples/02_market_data.py)

**Real-time market data**

Learn how to:

1. Discovering available currencies and instruments
2. Finding trading opportunities (bid-ask spreads)
3. Monitoring market conditions across assets
4. Comparing perpetual vs option markets

---

### [03_collateral_management.py](https://github.com/8ball030/derive_client/blob/main/examples/03_collateral_management.py)

**Manage your collateral**

Learn how to:

1. Viewing current collateral balances
2. Depositing assets from LightAccount to subaccount
3. Withdrawing assets from subaccount to LightAccount
4. Checking margin requirements
5. Simulating collateral changes (what-if scenarios)

---

### [04_trading_basics.py](https://github.com/8ball030/derive_client/blob/main/examples/04_trading_basics.py)

**Advanced order types and strategies**

Learn how to:

1. Placing different order types (limit, market, post-only)
2. Modifying orders (replace)
3. Cancelling orders (single, batch, by label)
4. Monitoring order status and fills
5. Viewing trade history

---

### [05_position_transfer.py](https://github.com/8ball030/derive_client/blob/main/examples/05_position_transfer.py)

**Transfer positions between subaccounts**

Learn how to:

1. Viewing positions across multiple subaccounts
2. Transferring a single position between subaccounts
3. Batch transferring multiple positions
4. Simulating margin impact before transfers
5. Viewing collateral distribution after transfers

---

### [06_bridging.py](https://github.com/8ball030/derive_client/blob/main/examples/06_bridging.py)

**Bridge assets to Derive L2**

Learn how to:

1. Bridging native ETH from Mainnet to Derive EOA (for gas)
2. Depositing ERC20 assets to Derive LightAccount
3. Withdrawing ERC20 assets from Derive LightAccount to external chains

---

## Using Your Own Account

To trade on mainnet or with your own testnet account:

1. Register at [derive.xyz](https://derive.xyz)
2. Create a session key at [app.derive.xyz/developers](https://app.derive.xyz/developers)
3. Copy `.env.template` to `.env` and add your credentials:

```bash
DERIVE_WALLET=0x...           # Your LightAccount address
DERIVE_SESSION_KEY=0x...      # Session key private key
DERIVE_SUBACCOUNT_ID=1        # Your subaccount ID
DERIVE_ENV=PROD               # TEST or PROD
```

## Next Steps

- **Need conceptual background?** Read the [Concepts](concepts/account-model.md) guides
- **Want API details?** See the [API Reference](reference/SUMMARY.md)
- **Have questions?** Check [GitHub Issues](https://github.com/8ball030/derive_client/issues)
