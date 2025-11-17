# CLI Reference

The `drv` command-line tool provides access to Derive functionality from your terminal.

## Getting Help

Run any command with `--help` to see detailed usage:

```bash
drv --help              # Show all commands
drv bridge --help       # Show bridge command options
```

## Command Tree

```
Derive Client
├── account........................... Account details.
│   ├── get........................... Account details.
│   └── portfolios.................... Get all portfolios of a wallet.
├── bridge............................ Bridge assets to/from Derive (ETH, ERC20, DRV).
│   ├── deposit....................... Deposit funds via the socket superbridge to a Derive funding account.
│   ├── gas........................... Deposit gas (native token) for bridging via the standard bridge to the owner's EOA.
│   └── withdraw...................... Withdraw funds from Derive funding account via the Withdraw Wrapper contract.
├── collateral........................ Manage collateral and margin.
│   ├── deposit-to-subaccount......... Deposit an asset to your subaccount.
│   ├── get........................... Get subaccount collaterals.
│   ├── get-margin.................... Calculates margin for a given subaccount.
│   └── withdraw-from-subaccount...... Withdraw an asset to your lightaccount wallet.
├── market............................ Query market data: currencies, instruments, tickers.
│   ├── currency...................... Get currency details.
│   ├── instrument.................... Get instrument details.
│   └── ticker........................ Get ticker details.
├── mmp............................... Market maker protection configuration.
│   ├── get-config.................... Get the current mmp config for a subaccount (optionally filtered by currency).
│   ├── reset......................... Resets (unfreezes) the mmp state for a subaccount (optionally filtered by currency).
│   └── set-config.................... Set the mmp config for the subaccount and currency.
├── order............................. Create, view, list, and cancel orders.
│   ├── cancel........................ Cancel a single order.
│   ├── cancel-all.................... Cancel all orders.
│   ├── create........................ Create a new order.
│   ├── get........................... Get state of an order by order id.
│   └── list-open..................... List all open orders of a subacccount.
├── position.......................... Inspect and transfer positions across subaccounts.
│   ├── list.......................... List active positions of a subaccount.
│   └── transfer...................... Transfers a positions from one subaccount to another, owned by the same wallet.
├── transaction....................... Query transaction status and details.
│   └── get........................... Used for getting a transaction by its transaction id.
└── tree.............................. Print the command tree structure.
```

## Demo

![CLI Demo](cli_demo.gif)

