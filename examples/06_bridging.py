"""
Bridging: Moving Assets Between Chains

This example demonstrates cross-chain asset transfers:
1. Bridging native ETH from Mainnet to Derive EOA (for gas)
2. Depositing ERC20 assets to Derive LightAccount
3. Withdrawing ERC20 assets from Derive LightAccount to external chains

Supported chains: Mainnet, Base, Arbitrum, Optimism ↔ Derive

Prerequisites:
- Assets on external chain (Mainnet, Base, Arbitrum, or Optimism)
- PROD environment only (bridging not available in TEST)

⚠️  IMPORTANT DISCLAIMERS:
- Bridging involves risk - always test with small amounts first
- Don't trust, verify: inspect prepared transactions before submitting
- Bridge operations can take several minutes depending on network congestion
- This is third-party open-source software; we are not affiliated with Derive
- You are responsible for your own funds - use at your own risk

For simpler workflows, consider using the derive_client CLI tool.
For sophisticated error handling and automation, use this programmatic API.
"""

from pathlib import Path

import rich_click as click

from derive_client import HTTPClient
from derive_client.cli._bridge import EnumChoice
from derive_client.cli._utils import rich_prepared_tx
from derive_client.data_types import ChainID, Currency, D
from derive_client.exceptions import PartialBridgeResult

# ⚠️  Bridging only available in PROD!
default = Path(__file__).parent.parent / ".env"
env_file = click.prompt(
    "Enter path to your envfile",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=default,
)
client = HTTPClient.from_env(env_file=env_file)
client.connect()

print("=" * 60)
print("BRIDGE OPERATIONS: 3-STEP PROCESS")
print("=" * 60)
print("\nEvery bridge operation follows this pattern:")
print("  1. prepare_tx  → Review transaction details and gas estimates")
print("  2. submit_tx   → Execute transaction (returns immediately)")
print("  3. poll_tx     → Wait for finality on both chains (can take minutes)")
print("\nLet's begin...\n")

print("=" * 60)
print("1. GAS FUNDING: ETH FROM MAINNET TO DERIVE EOA")
print("=" * 60)

# Your EOA on Derive needs ETH for gas when withdrawing assets back to external chains
# This is a one-time setup (or occasional top-up)
print("\nWhy this matters:")
print("  • Trading on Derive is gasless (paymaster covers fees)")
print("  • But withdrawing to external chains requires ETH in your EOA for gas")
print("  • This operation bridges native ETH specifically for gas funding")


# Withdrawal costs to bridge from Derive to an external chain are typically low.
# In order to get an estimate of how many such transactions this amount of ETH can support,
# we recommend to inspect such the cost of recent transactions, to the external chain of interest, on-chain.
amount_eth = click.prompt(
    "Enter amount of native ETH to bridge from Mainnet for gas funding (0 to skip, recommended: 0.001)",
    type=D,
    default=D("0"),
    show_default=True,
)

if amount_eth > 0:
    # Step 1: Prepare and inspect
    print(f"\n📋 Step 1: Preparing to bridge {amount_eth} ETH for gas...")
    prepared_tx = client.bridge.prepare_gas_deposit_tx(amount=amount_eth)

    print("\nTransaction prepared:")
    print(rich_prepared_tx(prepared_tx))
    if not click.confirm("Do you want to submit this transaction?", default=False):
        print("[yellow]Aborted by user.[/yellow]")

    else:
        print("\n🚀 Step 2: Submitting transaction...")
        tx_result = client.bridge.submit_tx(prepared_tx=prepared_tx)
        print(f"✅ Submitted! Source tx hash: {tx_result.source_tx.tx_hash}")

        # Step 3: Poll for finality
        print("\n⏳ Step 3: Polling for finality (this may take several minutes)...")
        print("  • Waiting for source chain finality...")
        print("  • Detecting event on target chain...")
        print("  • Waiting for target chain finality...")

        try:
            tx_result = client.bridge.poll_tx_progress(tx_result=tx_result)
            print("\n✅ Bridge complete!")
            print(f"  Source status: {tx_result.source_tx.status}")
            print(f"  Target status: {tx_result.target_tx.status if tx_result.target_tx else 'N/A'}")
            print(f"  Total gas used: {tx_result.gas_used} ({tx_result.total_fee / 1e18:.6f} ETH)")

        except PartialBridgeResult as e:
            # Bridge partially completed - inspect state to decide next action
            print(f"\n⚠️  Bridge partially completed: {e}")
            print("\nPartial state:")
            print(f"  Source tx: {e.tx_result.source_tx.status}")
            print(f"  Target tx: {e.tx_result.target_tx.status if e.tx_result.target_tx else 'Not started'}")

            # The underlying exception is available for detailed error handling
            if e.cause:
                print(f"\nUnderlying error: {type(e.cause).__name__}: {e.cause}")

            print("\n💡 Possible actions:")
            print("  • Wait longer and retry: client.bridge.poll_tx_progress(tx_result)")
            print("  • Inspect source tx on block explorer")
            print("  • If source succeeded but target pending, bridge may complete later")

            # You can continue with the partial result or retry
            tx_result = e.tx_result


print("\n" + "=" * 60)
print("2. DEPOSIT: ASSET FROM EXTERNAL CHAIN TO DERIVE LIGHTACCOUNT WALLET")
print("=" * 60)

print("External chain to bridge FROM:")
chain_id = click.prompt(
    "Select chain ID",
    type=EnumChoice(ChainID),
)

print("\nCurrency to bridge:")
currency = click.prompt(
    "Select currency",
    type=EnumChoice(Currency),
)

print("\nAmount to bridge:")
amount = click.prompt(
    "Enter amount of currency to bridge to Derive LightAccount wallet (0 to skip)",
    type=D,
    default=D("0"),
    show_default=True,
)
if amount > 0:
    print(f"\nDepositing {amount} {currency.name} to your LightAccount wallet on Derive...")

    print(f"\n📋 Step 1: Preparing to deposit {amount} {currency.name} from {chain_id.name}...")
    prepared_tx = client.bridge.prepare_deposit_tx(
        amount=amount,
        currency=currency,
        chain_id=chain_id,
    )

    print("\nTransaction prepared:")
    print(rich_prepared_tx(prepared_tx))
    if not click.confirm("Do you want to submit this transaction?", default=False):
        print("[yellow]Aborted by user.[/yellow]")

    else:
        print("\n🚀 Step 2: Submitting...")
        tx_result = client.bridge.submit_tx(prepared_tx=prepared_tx)
        print(f"✅ Submitted! Tx hash: {tx_result.source_tx.tx_hash}")

        print("\n⏳ Step 3: Polling for finality...")
        try:
            tx_result = client.bridge.poll_tx_progress(tx_result=tx_result)
            print("✅ Deposit complete!")

            # Now funds are in your LightAccount wallet
            # To transfer assets to your subaccount: see 03_collateral_management.py

        except PartialBridgeResult as e:
            print(f"⚠️  Partial result: {e}")
            print("You can retry polling with the partial tx_result")
            tx_result = e.tx_result


# Withdraw assets from your Derive LightAccount back to external chain
# Note: Funds must be in LightAccount wallet (not subaccount)
# Use client.collateral.withdraw_from_subaccount() first if needed
print("\n" + "=" * 60)
print("3. WITHDRAWAL: ASSET FROM DERIVE LIGHTACCOUNT WALLET TO EXTERNAL CHAIN")
print("=" * 60)

print("External chain to bridge TO:")
chain_id = click.prompt(
    "Select chain ID",
    type=EnumChoice(ChainID),
)

print("\nCurrency to bridge:")
currency = click.prompt(
    "Select currency",
    type=EnumChoice(Currency),
)
print("\nAmount to bridge:")
amount = click.prompt(
    "Enter amount of currency to bridge from Derive LightAccount wallet (0 to skip)",
    type=D,
    default=D("0"),
    show_default=True,
)

if amount > 0:
    print("\nWithdrawing from LightAccount wallet back to external chain...")
    print("⚠️  Note: Assets are sent to your EOA address on the target chain")

    print(f"\n📋 Step 1: Preparing to withdraw {amount} {currency.name} to {chain_id.name}...")
    prepared_tx = client.bridge.prepare_withdrawal_tx(
        amount=amount,
        currency=currency,
        chain_id=chain_id,
    )

    print("\nTransaction prepared:")
    print(rich_prepared_tx(prepared_tx))
    if not click.confirm("Do you want to submit this transaction?", default=False):
        print("[yellow]Aborted by user.[/yellow]")

    else:
        print("\n🚀 Step 2: Submitting...")
        tx_result = client.bridge.submit_tx(prepared_tx=prepared_tx)
        print(f"✅ Submitted! Tx hash: {tx_result.source_tx.tx_hash}")

        print("\n⏳ Step 3: Polling for finality...")
        try:
            tx_result = client.bridge.poll_tx_progress(tx_result=tx_result)
            print("✅ Withdrawal complete!")
            print(f"Check your Base wallet for the {amount} {currency}")

        except PartialBridgeResult as e:
            print(f"⚠️  Partial result: {e}")
            print("\nYou can inspect the partial state and retry if needed:")
            print("  tx_result = e.tx_result")
            print("  client.bridge.poll_tx_progress(tx_result)")
            tx_result = e.tx_result

print("\n" + "=" * 60)
print("ERROR HANDLING & ADVANCED USAGE")
print("=" * 60)

print("\nWhen poll_tx_progress fails:")
print("  1. PartialBridgeResult exception contains updated tx_result")
print("  2. Access underlying error via exception.cause")
print("  3. Common scenarios:")
print("     • FinalityTimeout: wait longer, retry polling")
print("     • TxPendingTimeout: tx still pending, wait or resubmit")
print("     • TransactionDropped: tx not found, likely dropped")
print("\n  4. For monadic error handling, use AsyncBridgeClient directly")
print("     • Returns IOResult[BridgeTxResult, Exception]")
print("     • Catches ALL exceptions, not just custom ones")
print("     • Enables match-case logic for comprehensive error handling")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

client.disconnect()

print("\n✅ Bridge operations demonstrated!")
print("\nKey points:")
print("  • Always test with small amounts first")
print("  • Inspect prepared transactions before submitting")
print("  • Polling can take minutes - be patient")
print("  • PartialBridgeResult contains latest state for retry")
print("  • See CLI tool for simpler workflows: `drv bridge --help`")
print("  • For automation, consider AsyncBridgeClient with IOResult")
print("\n⚠️  Reminder: Bridging involves inherent risks - use at your own discretion")
