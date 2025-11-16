"""
Position Transfers: Moving Positions Between Subaccounts

This example demonstrates:
1. Viewing positions across multiple subaccounts
2. Transferring a single position between subaccounts
3. Batch transferring multiple positions
4. Simulating margin impact before transfers
5. Viewing collateral distribution after transfers

Prerequisites:
- Multiple subaccounts (create via client.account.create_subaccount())
- At least one open position to transfer

Use cases:
- Risk management: Isolate risky positions in separate subaccounts
- Strategy separation: Keep different trading strategies in different accounts
- Collateral optimization: Move positions to better-funded subaccounts
"""

from pathlib import Path

from derive_client import HTTPClient
from derive_client.data_types import D, Direction, OrderType, PositionTransfer
from derive_client.data_types.generated_models import SimulatedPositionSchema

# Setup
env_file = Path(__file__).parent.parent / ".env.template"
client = HTTPClient.from_env(env_file=env_file)
client.connect()

print("=" * 60)
print("1. SURVEY YOUR SUBACCOUNTS")
print("=" * 60)

# Fetch first 2 subaccounts
subaccounts = client.fetch_subaccounts()[:2]
print(f"\nTotal subaccounts: {len(subaccounts)}")

if len(subaccounts) < 2:
    print("\n⚠️  You need at least 2 subaccounts for this example")
    print("Create another: client.account.create_subaccount()")
    client.disconnect()
    exit(0)

# Show overview of each subaccount and build currency mapping
subaccount_positions_by_currency = {}

for sub in subaccounts:
    positions = sub.positions.list(is_open=True)
    collaterals = sub.collateral.get()

    total_collateral = sum(c.amount * c.mark_price for c in collaterals.collaterals)

    print(f"\n  Subaccount {sub.id}:")
    print(f"    Collateral: ${total_collateral:.2f}")
    print(f"    Open positions: {len(positions)}")

    # Track positions by currency for each subaccount
    positions_by_currency = {}
    for pos in positions:
        if pos.amount != 0:
            # Extract currency from instrument name (e.g., "ETH-PERP" -> "ETH")
            currency = pos.instrument_name.split("-")[0]
            if currency not in positions_by_currency:
                positions_by_currency[currency] = []
            positions_by_currency[currency].append(pos)

            pnl_sign = "+" if pos.unrealized_pnl >= 0 else ""
            print(f"      {pos.instrument_name}: {pos.amount} ({pnl_sign}${pos.unrealized_pnl:.2f})")

    subaccount_positions_by_currency[sub.id] = positions_by_currency

print("\n" + "=" * 60)
print("2. PREPARE FOR TRANSFER")
print("=" * 60)

# Find a source subaccount with at least one position for single transfer
source_sub = None
target_sub = None

for sub in subaccounts:
    positions = sub.positions.list(is_open=True)
    if positions:
        source_sub = sub
        # Pick a different subaccount as target
        target_sub = next((s for s in subaccounts if s.id != source_sub.id), None)
        break

if not source_sub or not target_sub:
    print("\n⚠️  Need at least one subaccount with positions and another to transfer to")
    client.disconnect()
    exit(0)

print(f"\nSource: Subaccount {source_sub.id}")
print(f"Target: Subaccount {target_sub.id}")

# Check source has a position
source_positions = source_sub.positions.list(is_open=True)
if not source_positions:
    print("\n⚠️  Source subaccount has no positions")
    print("Creating a small position first...")

    order = source_sub.orders.create(
        instrument_name="ETH-PERP",
        amount=D("0.01"),
        direction=Direction.buy,
        order_type=OrderType.market,
    )
    print(f"✅ Position created: {order.order.order_id}")
    source_positions = source_sub.positions.list(is_open=True)

position_to_transfer = source_positions[0]
print("\nPosition to transfer:")
print(f"  Instrument: {position_to_transfer.instrument_name}")
print(f"  Size: {position_to_transfer.amount}")
print(f"  Entry: ${position_to_transfer.average_price:.2f}")
print(f"  Unrealized P&L: ${position_to_transfer.unrealized_pnl:.2f}")

print("\n" + "=" * 60)
print("3. SIMULATE MARGIN IMPACT")
print("=" * 60)

# Check current margin in both accounts
source_margin_before = source_sub.collateral.get_margin()
target_margin_before = target_sub.collateral.get_margin()

print("\nCurrent margin status:")
print(f"  Source (sub {source_sub.id}):")
print(f"    Initial margin: ${source_margin_before.post_initial_margin:.2f}")
print(f"  Target (sub {target_sub.id}):")
print(f"    Initial margin: ${target_margin_before.post_initial_margin:.2f}")

# Simulate transfer impact
transfer_amount = position_to_transfer.amount / 2  # Transfer 50%

# Source loses position (negative amount)
source_simulation = [
    SimulatedPositionSchema(
        instrument_name=position_to_transfer.instrument_name,
        amount=-transfer_amount,
        entry_price=position_to_transfer.average_price,
    )
]

# Target gains position (positive amount)
target_simulation = [
    SimulatedPositionSchema(
        instrument_name=position_to_transfer.instrument_name,
        amount=transfer_amount,
        entry_price=position_to_transfer.average_price,
    )
]

source_margin_after = source_sub.collateral.get_margin(simulated_position_changes=source_simulation)
target_margin_after = target_sub.collateral.get_margin(simulated_position_changes=target_simulation)

source_margin_change = source_margin_after.post_initial_margin - source_margin_before.post_initial_margin
target_margin_change = target_margin_after.post_initial_margin - target_margin_before.post_initial_margin
print(f"\nAfter transferring {transfer_amount} {position_to_transfer.instrument_name}:")
print(f"  Source margin change: ${source_margin_change:+.2f}")
print(f"  Target margin change: ${target_margin_change:+.2f}")

# Check if transfer is safe
source_collateral = sum(c.amount * c.mark_price for c in source_sub.collateral.get().collaterals)
target_collateral = sum(c.amount * c.mark_price for c in target_sub.collateral.get().collaterals)

source_safe = source_collateral > source_margin_after.post_initial_margin * D("1.2")
target_safe = target_collateral > target_margin_after.post_initial_margin * D("1.2")

if source_safe and target_safe:
    print("\n✅ Transfer is safe for both accounts")
else:
    if not source_safe:
        print("\n⚠️  Warning: Source account may have low margin after transfer")
    if not target_safe:
        print("\n⚠️  Warning: Target account may have low margin after transfer")

print("\n" + "=" * 60)
print("4. EXECUTE SINGLE POSITION TRANSFER")
print("=" * 60)

print(f"\nTransferring {transfer_amount} {position_to_transfer.instrument_name}...")
print(f"  From: Subaccount {source_sub.id}")
print(f"  To: Subaccount {target_sub.id}")

transfer_result = source_sub.positions.transfer(
    instrument_name=position_to_transfer.instrument_name,
    amount=transfer_amount,
    to_subaccount=target_sub.id,
)

print("\n✅ Transfer complete!")
print(f"  Maker trade: {transfer_result.maker_trade.trade_id}")
print(f"  Taker trade: {transfer_result.taker_trade.trade_id}")
print(f"  Price: ${transfer_result.maker_trade.trade_price:.2f}")
print("  Fee: $0.00 (transfers are free)")

# Verify positions updated
source_pos_after = source_sub.positions.list(is_open=True)
target_pos_after = target_sub.positions.list(is_open=True)

source_position = sum(p.amount for p in source_pos_after if p.instrument_name == position_to_transfer.instrument_name)
target_position = sum(p.amount for p in target_pos_after if p.instrument_name == position_to_transfer.instrument_name)
print(f"\n  Source position now: {source_position}")
print(f"  Target position now: {target_position}")

print("\n" + "=" * 60)
print("5. BATCH TRANSFER MULTIPLE POSITIONS")
print("=" * 60)

# Find a subaccount with multiple positions in the same currency (required for batch)
batch_source_sub = None
batch_currency = None

for sub in subaccounts:
    positions_by_currency = subaccount_positions_by_currency.get(sub.id, {})
    for currency, positions in positions_by_currency.items():
        if len(positions) >= 2:
            batch_source_sub = sub
            batch_currency = currency
            break
    if batch_source_sub:
        break

if batch_source_sub and batch_currency:
    batch_target_sub = next((s for s in subaccounts if s.id != batch_source_sub.id), None)

    if batch_target_sub:
        positions_to_batch = subaccount_positions_by_currency[batch_source_sub.id][batch_currency]

        print(f"\nTransferring {len(positions_to_batch)} {batch_currency} positions in batch...")
        print(f"  From: Subaccount {batch_source_sub.id}")
        print(f"  To: Subaccount {batch_target_sub.id}")

        # Build transfer list
        transfers = []
        for pos in positions_to_batch[:3]:  # Max 3 for demo
            if abs(pos.amount) < D(0.1):
                continue
            transfers.append(
                PositionTransfer(
                    instrument_name=pos.instrument_name,
                    amount=pos.amount,
                )
            )

        # Direction should match the position direction
        sample_pos = positions_to_batch[0]
        direction = Direction.buy if sample_pos.amount > 0 else Direction.sell

        batch_result = batch_source_sub.positions.transfer_batch(
            positions=transfers,
            direction=direction,
            to_subaccount=batch_target_sub.id,
        )

        print("✅ Batch transfer complete!")
        print(f"  Maker quote: {batch_result.maker_quote.quote_id}")
        print(f"  Taker quote: {batch_result.taker_quote.quote_id}")

        for i, transfer in enumerate(transfers, 1):
            print(f"  {i}. {transfer.instrument_name}: {transfer.amount}")
    else:
        print("\nNo target subaccount available for batch transfer")
else:
    print("\nSkipping batch transfer:")
    print("  Batch transfers require 2+ positions in the same currency")
    print("  (Cross-currency batch transfers are not supported)")
    print("\n  Current state:")
    for sub_id, positions_by_curr in subaccount_positions_by_currency.items():
        print(f"    Subaccount {sub_id}:")
        for curr, positions in positions_by_curr.items():
            print(f"      {curr}: {len(positions)} position(s)")

client.disconnect()

print("\n✅ Position transfer complete!")
print("\nKey takeaways:")
print("  • Use position transfers to reorganize risk across subaccounts")
print("  • Always simulate margin impact before large transfers")
print("  • Batch transfers are more efficient for multiple positions")
print("  • Transfers are free (no trading fees)")
print("  • Keep track of margin requirements in each subaccount")
