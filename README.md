# Derive.xyz Python Client.

This repo provides a unified interface for the Derive Exchange.

Please checkout the [examples](./examples) directory for usage.

Here is a quick demonstration of the cli functionality.

![alt text](derive_demo.gif "Demo of cli tools.")


## Preparing Keys for the Client

To use the client, you will need to generate an API key from the Derive Exchange.

The process involves linking your local signer to the account you want to use programmatically.

Here are the steps:

0. Generate a local signer using your preferred method. For example, you can use the Open Aea Ledger Ethereum Cli.
    ```bash
    aea generate-key ethereum
    ```
    This will generate a new private key in the `ethereum_private_key.txt` file.

1. Go to the [Derive Exchange](https://derive.xyz) and create an account.
2. Go to the API section and create a new [API key](https://.derive.xyz/api-keys/developers).
3. Register a new Session key with the Public Address of the account your signer generated in step 0.

Once you have the API key, you can use it to interact with the Derive Exchange.

You need;

`DERIVE_WALLET` - The programtic wallet generated upon account creation. It can be found in the Developer section of the Derive Exchange.
`SIGNER_PRIVATE_KEY` - The private key generated in step 0.
`SUBACCOOUNT_ID` - The subaccount id you want to use for the API key.

```python
derive_client = DeriveClient(
    private_key=TEST_PRIVATE_KEY, 
    env=Environment.TEST, # or Environment.PROD
    wallet=TEST_WALLET,
    subaccount_id = 123456
    )
```

## Orders Operations
You can filter by status, instrument name, and more.
```python

orders = derive_client.orders.list(
    status=OrderStatus.open,
)
```




## Install

```bash
pip install derive-client
```

## Dev

### Formatting

```bash
make fmt
```

### Linting

```bash
make lint
```

### Tests

```bash
make tests
```

For convience, all commands can be run with:

```
make all
```

### Releasing

We can use `tbump` to automatically bump our versions in preparation of a release.

```bash 
export new_version=0.1.5
tbump $new_version
```

The release workflow will then detect that a branch with a `v` prefix exists and create a release from it.

Additionally, the package will be published to PyPI.

