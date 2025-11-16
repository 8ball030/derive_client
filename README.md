# Derive Client

> Python client for [Derive Protocol](https://derive.xyz) - a decentralized derivatives trading platform on its own Ethereum L2

Trade options, perpetuals, and spot with full self-custody through smart contract wallets.

[Full Documentation](https://8ball030.github.io/derive_client/)

## CLI Tool Demo

Here is a quick demonstration of the CLI functionality:

![Demo of CLI tools](docs/cli_demo.gif)

## Installation from PyPI

```bash
pip install derive-client
```

## Quickstart

Create .env file

```bash
DERIVE_SESSION_KEY=0x2ae8be44db8a590d20bffbe3b6872df9b569147d3bf6801a35a28281a4816bbd
DERIVE_WALLET=0xA419f70C696a4b449a4A24F92e955D91482d44e9
DERIVE_SUBACCOUNT_ID=137626
DERIVE_ENV=TEST
```

Setup client, check market data and place an order.

```python
from derive_client import HTTPClient
from derive_client.data_types import D, Direction, OrderType

# Initialize client
client = HTTPClient.from_env()

# Check market data
ticker = client.markets.get_ticker(instrument_name="ETH-PERP")

# Place an order
order_result = client.orders.create(
    instrument_name="ETH-PERP",
    amount=D("0.10"),  # 0.10 ETH
    limit_price=D("1000"),  # Buy at $1000
    direction=Direction.buy,
    order_type=OrderType.limit,
)
```

### Examples

The fastest way to learn is by running the [examples](/examples/):

```bash
# Clone the repo (examples are not included in the package)
git clone git@github.com:8ball030/derive_client.git
cd derive_client

# Install editable with pip
pip install -e .

# Run with testnet credentials (pre-configured)
python examples/01_quickstart.py
```

The examples use `.env.template` with **pre-filled testnet credentials**, so you can run them immediately without setup.

- **01_quickstart.py** - Connect and Place Your First Trade
- **02_market_data.py** - Exploring Available Markets and Price Information
- **03_collateral_management.py** - Deposits, Withdrawals, and Margin.
- **04_trading_basics.py** - Order Lifecycle and Management
- **05_position_transfer.py** - Moving Positions Between Subaccounts
- **06_bridging.py** - Moving Assets Between Chains

**NOTE:** The bridging example cannot be ran using the TEST environment, as bridging is only available in PROD.

## Using Your Own Account

To trade on mainnet or with your own testnet account:

1. Register at [derive.xyz](https://derive.xyz) to get your LightAccount wallet
2. Create a [subaccount](https://app.derive.xyz/subaccounts)
3. Register a session key (regular Ethereum private key for an EOA) as session key via the [Developers page](https://app.derive.xyz/developers)
4. Copy `.env.template` to `.env` and add your credentials:

```bash
DERIVE_WALLET=0x...           # Your LightAccount address
DERIVE_SESSION_KEY=0x...      # Session key private key
DERIVE_SUBACCOUNT_ID=1        # Your subaccount ID
DERIVE_ENV=PROD               # TEST or PROD
```

See [authentication.md](docs/concepts/authentication.md) for a more detailed explanation.

## Documentation

📖 **[Full Documentation](https://8ball030.github.io/derive_client/)**

- **[Concepts](docs/concepts/)** - Account model, authentication, bridging, clients
- **[API Reference](docs/reference/)** - Public API documentation
- **[Internal API](docs/internal/)** - Internal API documentation

## Development

### From Source (for development)

```bash
git clone git@github.com:8ball030/derive_client.git
cd derive_client

# Install and spawn the virtual environment
make install
poetry shell
```

### Quick Commands

```bash
make fmt        # Format code
make lint       # Run linters
make typecheck  # Type checking
make tests      # Run tests
```

### Code Generation

```bash
make codegen-all
```

### API Docs Generation

```bash
make docs
```

Or, run all the above make commands sequentially using simply:

```bash
make all
```

### Releasing

Bump version and create release:

```bash
export new_version=0.1.5
tbump $new_version
```

The release workflow will automatically create a GitHub release and publish to PyPI.
