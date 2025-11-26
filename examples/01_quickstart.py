"""
Quickstart: Connect and Place Your First Trade

This example shows the basics:
1. Set up the client
2. Check your balance
3. View available markets
4. Place a simple order
5. Check order status

Prerequisites:
- DERIVE_SESSION_KEY environment variable
- DERIVE_WALLET environment variable
- DERIVE_SUBACCOUNT_ID environment variable
- Funded subaccount (see 03_bridging_and_funding.py if needed)
"""

from pathlib import Path

from derive_client import HTTPClient
from derive_client.data_types import D, Direction, OrderType

# Initialize client
env_file = Path(__file__).parent.parent / ".env.template"
client = HTTPClient.from_env(env_file=env_file)

# Connect and fetch initial data
client.connect()

print("=" * 60)
print("ACCOUNT INFO")
print("=" * 60)

# Your LightAccount wallet can have multiple subaccounts (trading accounts)
# Each subaccount tracks positions, collateral, and orders independently
portfolios = client.account.get_all_portfolios()
print(f"\nYour LightAccount has {len(portfolios)} subaccount(s):")

for portfolio in portfolios:
    print(f"\n  Subaccount {portfolio.subaccount_id} ({portfolio.margin_type}):")
    print(f"    Total value: ${portfolio.subaccount_value:.2f}")
    print(f"    Collateral: ${portfolio.collaterals_value:.2f}")
    print(f"    Positions: ${portfolio.positions_value:.2f}")
    print(f"    Initial margin: ${portfolio.initial_margin:.2f}")
    print(f"    Open orders: {len(portfolio.open_orders)}")

print("\n" + "=" * 60)
print("ACTIVE SUBACCOUNT")
print("=" * 60)

# The client provides direct access to operations on your active subaccount
# (the one specified by DERIVE_SUBACCOUNT_ID) for convenience
print(f"\nWorking with subaccount {client.active_subaccount.id}:")

# Check collateral balances in this subaccount
collaterals = client.collateral.get()
print("\nCollateral:")
for collateral in collaterals.collaterals:
    print(f"  {collateral.asset_name}: {collateral.amount}")


print("\n" + "=" * 60)
print("MARKET DATA")
print("=" * 60)

# View ETH perpetual market
ticker = client.markets.get_ticker(instrument_name="ETH-PERP")
print("\nETH-PERP")
print(f"  Bid: ${ticker.best_bid_price}")
print(f"  Ask: ${ticker.best_ask_price}")
print(f"  Mark: ${ticker.mark_price}")

print("\n" + "=" * 60)
print("PLACE ORDER")
print("=" * 60)

# Place a limit buy order
order_result = client.orders.create(
    instrument_name="ETH-PERP",
    amount=D("0.10"),  # 0.10 ETH
    limit_price=ticker.index_price * D(0.95),  # Buy at 95% of the index price
    direction=Direction.buy,
    order_type=OrderType.limit,
)

order = order_result
print(f"\nOrder created: {order.order_id}")
print(f"Status: {order.order_status}")
print(f"Amount: {order.amount} @ ${order.limit_price}")

print("\n" + "=" * 60)
print("CHECK STATUS")
print("=" * 60)

# List open orders
open_orders = client.orders.list_open()
print(f"\nOpen orders: {len(open_orders)}")
for o in open_orders:
    print(f"  {o.instrument_name}: {o.amount} @ ${o.limit_price}")

# Check positions
positions = client.positions.list()
print(f"\nPositions: {len(positions)}")
for pos in positions:
    pnl_sign = "+" if pos.unrealized_pnl >= 0 else ""
    print(f"  {pos.instrument_name}: {pos.amount} (PnL: {pnl_sign}${pos.unrealized_pnl:.2f})")

print("\n" + "=" * 60)
print("CANCEL ORDER")
print("=" * 60)

# Cancel the order
cancelled = client.orders.cancel(order_id=order.order_id, instrument_name=order.instrument_name)
print(f"\nOrder {cancelled.order_id} cancelled")
print(f"Reason: {cancelled.cancel_reason}")

# Clean up
client.disconnect()

print("\n✅ Quickstart complete!")
