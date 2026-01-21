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

from decimal import Decimal
from pathlib import Path

from derive_client import HTTPClient
from derive_client.data_types import AssetType, D, Direction, OrderType
from derive_client.data_types.generated_models import TickerSlimSchema, TimeInForce

# Setup
env_file = Path(__file__).parent.parent / ".env.template"
client = HTTPClient.from_env(env_file=env_file)
client.connect()

CURRENCY = "ETH"
INSTRUMENT_TYPE = AssetType.perp
INSTRUMENT = f"{CURRENCY}-PERP"
MINIMUM_AMOUNT = D("0.10")


def get_ticker_data(ticker_slim: TickerSlimSchema):
    """Helper to extract readable data from TickerSlimSchema."""

    return {
        'best_bid_price': ticker_slim.b,
        'best_ask_price': ticker_slim.a,
        'best_bid_amount': ticker_slim.B,
        'best_ask_amount': ticker_slim.A,
        'mark_price': ticker_slim.M,
        'index_price': ticker_slim.I,
        'max_price': ticker_slim.maxp,
        'min_price': ticker_slim.minp,
        'timestamp': ticker_slim.t,
        'funding_rate': ticker_slim.f,  # perps only
    }


print("=" * 60)
print("1. LIMIT ORDERS")
print("=" * 60)

# Get current market price using new get_tickers API
tickers = client.markets.get_tickers(instrument_type=INSTRUMENT_TYPE, currency=CURRENCY)
ticker_slim = tickers[INSTRUMENT]
ticker_data = get_ticker_data(ticker_slim)

mid_price = (ticker_data['best_bid_price'] + ticker_data['best_ask_price']) / 2
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
if replaced.order:
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


# Check liquidity before attempting market orders
def has_sufficient_liquidity(ticker_slim: TickerSlimSchema, direction: Direction, amount: Decimal) -> tuple[bool, str]:
    """Check if there's sufficient liquidity for a market order."""
    ticker_data = get_ticker_data(ticker_slim)

    if direction == Direction.buy:
        available = ticker_data['best_ask_amount']
        price = ticker_data['best_ask_price']
        side = "ask"
    else:
        available = ticker_data['best_bid_amount']
        price = ticker_data['best_bid_price']
        side = "bid"

    # Check if there's any liquidity
    if available == 0 or price == 0:
        return False, f"No liquidity on {side} side"

    # Check if there's enough for our order
    if available < amount:
        return False, f"Insufficient liquidity: {available} available, {amount} needed"

    # Check for unreasonably wide spread (indicates thin market)
    if ticker_data['best_bid_price'] > 0 and ticker_data['best_ask_price'] > 0:
        spread_pct = (
            (ticker_data['best_ask_price'] - ticker_data['best_bid_price']) / ticker_data['best_bid_price'] * 100
        )
        if spread_pct > 5:  # More than 5% spread
            return False, f"Spread too wide ({spread_pct:.1f}%), market likely illiquid"

    return True, "Sufficient liquidity"


# Refresh ticker to get latest market data
tickers = client.markets.get_tickers(instrument_type=INSTRUMENT_TYPE, currency=CURRENCY)
ticker_slim = tickers[INSTRUMENT]
ticker_data = get_ticker_data(ticker_slim)

# Check liquidity for buy order
can_buy, buy_msg = has_sufficient_liquidity(ticker_slim, Direction.buy, MINIMUM_AMOUNT)
print("\nLiquidity check for BUY:")
print(f"  Best ask: ${ticker_data['best_ask_price']} x {ticker_data['best_ask_amount']}")
print(f"  Best bid: ${ticker_data['best_bid_price']} x {ticker_data['best_bid_amount']}")
print(f"  Status: {buy_msg}")

if can_buy:
    # Market orders execute immediately at best available price
    # It is necessary to ensure that there is a limit price which is the
    # Absolute Worst price acceptable by the trader.
    market_order = client.orders.create(
        instrument_name=INSTRUMENT,
        amount=MINIMUM_AMOUNT,
        direction=Direction.buy,
        limit_price=ticker_data['best_ask_price'],
        order_type=OrderType.market,
    )
    print("\n✓ Market BUY order executed:")
    print(f"  Order ID: {market_order.order_id}")
    print(f"  Status: {market_order.order_status}")

    # Check liquidity for sell order to close position
    can_sell, sell_msg = has_sufficient_liquidity(ticker_slim, Direction.sell, MINIMUM_AMOUNT)

    if can_sell:
        # Close the position we just opened
        close_order = client.orders.create(
            instrument_name=INSTRUMENT,
            amount=MINIMUM_AMOUNT,
            direction=Direction.sell,
            limit_price=ticker_data['best_bid_price'] * D("0.99"),  # Acceptable worst price
            order_type=OrderType.market,
        )
        print(f"\n✓ Position closed: {close_order.order_id}")
        print(f"  Status: {close_order.order_status}")
    else:
        print(f"\n⚠ Cannot close position: {sell_msg}")
        print("  Position remains open - close manually or wait for liquidity")
else:
    print("\n⚠ Skipping market orders - insufficient liquidity")
    print("  This is common on testnets with limited market makers")
    print("  In production, check liquidity before market orders or use limit orders")

client.disconnect()

print("\n✅ Trading basics complete!")
