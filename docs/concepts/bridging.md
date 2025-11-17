# Bridging & Funding

Now that you understand Derive's account model, let's get your funds where they need to be.

Remember: you have **two different addresses** that need funding for different purposes:

- **Your EOA** needs ETH for paying gas on bridge transactions
- **Your LightAccount** needs trading assets (USDC, WETH, etc.) for actual trading

The Derive client handles three different bridge protocols automatically, so you don't need to worry about the technical details.

---

## Supported Bridges

### 1. Standard Bridge

- Used **only** for transferring native ETH from Ethereum mainnet to the Derive owner EOA.
- Purpose: fund the Derive EOA with native ETH to cover gas for bridging operations.
- Currently restricted to ETH-only. Other assets and chains may be supported in the future.

### 2. Socket Superbridge

- Used for transferring **ERC20 tokens** (e.g. USDC, WETH, etc.) between
  - Ethereum mainnet, Base, Arbitrum, Optimism
  - and Derive
- Supports **bidirectional transfers**.
- Bridge and gas costs are always paid by the **Derive EOA in native ETH**.

### 3. LayerZero

- Used exclusively for the **DRV token**:
  - Deposits into Derive: gas is paid in the source chain's native token.
  - Withdrawals from Derive: gas is paid in Derive's native **DRV token**.

---

## Restrictions and Client Behavior

- **Owner-only bridging:**  
  While Derive contracts allow admin-level secondary signers to bridge, this client restricts bridging to the **owner EOA only**. This prevents accidental transfers between the wrong addresses.

- **No ETH deposit to LightAccount:**  
  Although the deployed contracts support bridging ETH directly to the Derive LightAccount, this automatically wraps it into WETH. To avoid confusion, the client currently **does not support this**. If you want WETH on your LightAccount, you should therefore wrap ETH into WETH on the source chain first, and then bridge WETH to Derive.

---

## After Bridging: Moving Funds Into Subaccounts

Assets bridged into Derive first arrive in your LightAccount (funding wallet). However, you cannot trade directly from the LightAccount. To trade, funds must be transferred into a subaccount.

- Transfers are supported both ways:
  - LightAccount -> Subaccount (to fund trading)
  - Subaccount -> LightAccount (to withdraw trading balance)

When creating a subaccount, you choose a margin model:

- **Standard Margin:** margin calculated per position, conservative but simple.
- **Portfolio Margin:** margin calculated on the overall portfolio with stress tests, usually more capital efficient but limited to a single base asset type.

For detailed descriptions of margin models and liquidation rules, see the Derive documenation:

- [Standard Margin](https://docs.derive.xyz/docs/standard-margin-1)
- [Portfolio Margin](https://docs.derive.xyz/docs/portfolio-margin-1)

---

## How Bridging Works (Conceptual Flow)

All bridge operations follow the same general lifecycle:

1. Prepare a transaction on the source chain
2. Sign and submit the transaction
3. Wait for finality on the source chain
4. Event is picked up by the bridge
5. Wait for confirmation and finality on the target chain

This flow is abstracted in the client.  
You only need to call the high-level methods exposed on the `HTTPClient`.

---

## Usage

The client exposes bridging via high-level methods on `HTTPClient.bridge`.

- Refer to [Quickstart](../quickstart.md) or [Examples](../examples.md) for usage patterns and sample code.

---

Next: [Clients](clients.md) - choose the right client type (sync, async, websocket) for your use case.
