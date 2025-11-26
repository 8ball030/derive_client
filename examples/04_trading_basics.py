"""
Trading Basics: Order Lifecycle and Management

This example demonstrates:
1. Placing different order types (limit, market, post-only)
2. Modifying orders (replace)
3. Cancelling orders (single, batch, by label)
4. Monitoring order status and fills
5. Viewing trade history

Prerequisites:
- Funded subaccount
- Run 01_quickstart.py first
"""

from pathlib import Path

from derive_client import HTTPClient
from derive_client.data_types import D, Direction, OrderType
from derive_client.data_types.generated_models import TimeInForce

# Setup
env_file = Path(__file__).parent.parent / ".env.template"
client = HTTPClient.from_env(env_file=env_file)
client.connect()

INSTRUMENT = "ETH-PERP"
MINIMUM_AMOUNT = D("0.10")


print("=" * 60)
print("1. LIMIT ORDERS")
print("=" * 60)

# Get current market price
ticker = client.markets.get_ticker(instrument_name=INSTRUMENT)
mid_price = (D(ticker.best_bid_price) + D(ticker.best_ask_price)) / 2
print(f"\nCurrent mid price: ${mid_price:.2f}")

# Place limit buy order below market
buy_price = mid_price * D("0.95")  # 5% below
buy_order = client.orders.create(
    instrument_name=INSTRUMENT,
    amount=MINIMUM_AMOUNT,
    limit_price=buy_price,
    direction=Direction.buy,
    order_type=OrderType.limit,
    label="example_buy",  # Custom label for tracking
)
print(f"\nLimit BUY created: {buy_order.order_id}")
print(f"  Price: ${buy_price:.2f}")
print(f"  Label: {buy_order.label}")

# Place limit sell order above market
sell_price = mid_price * D("1.05")  # 5% above
sell_order = client.orders.create(
    instrument_name=INSTRUMENT,
    amount=MINIMUM_AMOUNT,
    limit_price=sell_price,
    direction=Direction.sell,
    order_type=OrderType.limit,
    label="example_sell",
)
print(f"\nLimit SELL created: {sell_order.order_id}")
print(f"  Price: ${sell_price:.2f}")

print("\n" + "=" * 60)
print("2. POST-ONLY ORDERS (Market Making)")
print("=" * 60)

# Post-only ensures you're always the maker (or order is rejected)
post_only_order = client.orders.create(
    instrument_name=INSTRUMENT,
    amount=MINIMUM_AMOUNT,
    limit_price=mid_price * D("0.98"),
    direction=Direction.buy,
    order_type=OrderType.limit,
    time_in_force=TimeInForce.post_only,
    label="maker_order",
)
print(f"\nPost-only order: {post_only_order.order_id}")
print("  Guarantees maker fees")

print("\n" + "=" * 60)
print("3. REPLACE ORDER (Modify Price)")
print("=" * 60)

# Update the buy order price
new_buy_price = mid_price * D("0.96")
replaced = client.orders.replace(
    order_id_to_cancel=buy_order.order_id,
    instrument_name=INSTRUMENT,
    amount=MINIMUM_AMOUNT,
    limit_price=new_buy_price,
    direction=Direction.buy,
    order_type=OrderType.limit,
    time_in_force=TimeInForce.post_only,
    label=buy_order.label,
)
print("\nOrder replaced:")
print(f"  Old price: ${buy_price:.2f}")
print(f"  New price: ${new_buy_price:.2f}")
print(f"  New order ID: {replaced.order.order_id}")

print("\n" + "=" * 60)
print("4. ORDER STATUS & FILLS")
print("=" * 60)

# Check specific order
order_detail = client.orders.get(order_id=sell_order.order_id)
fill_pct = (order_detail.filled_amount / order_detail.amount) * 100
print(f"\nOrder {order_detail.order_id}:")
print(f"  Status: {order_detail.order_status}")
print(f"  Filled: {fill_pct:.1f}% ({order_detail.filled_amount}/{order_detail.amount})")

# List all open orders
open_orders = client.orders.list_open()
print(f"\nTotal open orders: {len(open_orders)}")
for order in open_orders:
    print(f"  {order.direction} {order.amount} @ ${order.limit_price} ({order.label or 'no label'})")

print("\n" + "=" * 60)
print("5. TRADE HISTORY")
print("=" * 60)

# Get recent trades for this subaccount
trades = client.trades.list_private(instrument_name=INSTRUMENT)
print(f"\nRecent trades: {len(trades)}")
for trade in trades[:3]:  # Show last 3
    print(f"  {trade.instrument_name} - {trade.direction} {trade.trade_amount} @ ${trade.trade_price}")
    print(f"    Fee: ${trade.trade_fee}, Role: {trade.liquidity_role}")

print("\n" + "=" * 60)
print("6. CANCEL ORDERS")
print("=" * 60)

# Cancel by label
cancelled_by_label = client.orders.cancel_by_label(
    label="example_buy",
    instrument_name=INSTRUMENT,
)

print(f"\nCancelled orders with label 'example_buy': {cancelled_by_label.cancelled_orders}")

# Cancel by instrument
cancelled_by_instrument = client.orders.cancel_by_instrument(
    instrument_name=INSTRUMENT,
)
print(f"Cancelled all {INSTRUMENT} orders: {cancelled_by_instrument.cancelled_orders}")

# Verify all closed
remaining = client.orders.list_open()
print(f"\nRemaining open orders: {len(remaining)}")

print("\n" + "=" * 60)
print("7. MARKET ORDERS (Immediate Execution)")
print("=" * 60)

# Market orders execute immediately at best available price
# It is necessary to ensure that there is a limit price which is the
# Absolute Worst price acceptable by the trader.
market_order = client.orders.create(
    instrument_name=INSTRUMENT,
    amount=MINIMUM_AMOUNT,
    direction=Direction.buy,
    limit_price=ticker.best_ask_price,
    order_type=OrderType.market,
)
print("\nMarket order executed:")
print(f"  Order ID: {market_order.order_id}")
print(f"  Status: {market_order.order_status}")
# if market_order.trades:
#     avg_price = sum(t.price * t.amount for t in market_order.trades) / sum(t.amount for t in market_order.trades)
#     print(f"  Avg fill price: ${avg_price:.2f}")
#     print(f"  Fills: {len(market_order.trades)}")

# Close the position we just opened
close_order = client.orders.create(
    instrument_name=INSTRUMENT,
    amount=MINIMUM_AMOUNT,
    direction=Direction.sell,
    limit_price=ticker.best_bid_price * D("0.99"),  # Acceptable worst price
    order_type=OrderType.market,
)
print(f"\nPosition closed: {close_order.order_id}")
print(f"  Order ID: {close_order.order_id}")
print(f"  Status: {close_order.order_status}")

client.disconnect()

print("\n✅ Trading basics complete!")
