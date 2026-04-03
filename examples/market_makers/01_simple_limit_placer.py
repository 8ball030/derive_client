"""
Example to demonstrate a simple placer for DRV market spot / limit orders as a proposal for the weekly buy backs.

Problem statement:
- we have weekly buy backs where we want to buy DRV.
- At present we simply TWAP into the market over the course of a week.
- This is simple, however the opportunity cost is that we dont have leave any liquidity in
  the order book for other market participants to fill, and we also have no control over the price we get filled at.
Proposed solution:
- we use 50% of the buy back amount to place limit orders, we use 50% for twap as before.
- We place limit orders at the 0.9% mark of the index price, these orders expire after 1 hour if not filled.
- We place new limit orders every hour, so we always have some liquidity in the order book,
  but we also have a chance of price improvement.
"""

import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from derive_client import HTTPClient
from derive_client.data_types import AssetType, D, Direction, OrderType
from derive_client.data_types.generated_models import TimeInForce

# Configuration
INSTRUMENT_NAME = "DRV-USDC"  # The DRV-USDC market
WEEKLY_BUYBACK_AMOUNT = D("1000.0")  # Total weekly buyback amount in USDC
LIMIT_ORDER_PERCENTAGE = D("0.5")  # 50% for limit orders
MARKET_ORDER_PERCENTAGE = D("0.5")  # 50% for market orders (TWAP)
PRICE_DISCOUNT = D("0.90")  # Buy at 90% of index price (10% discount)
ORDER_EXPIRY_HOURS = 1  # Orders expire after 1 hour
CHECK_INTERVAL_SECONDS = 300  # Check every 5 minutes (300 seconds)
MARKET_ORDER_INTERVAL_SECONDS = 3600  # Place market orders every hour (TWAP)


class SimpleLimitPlacer:
    """
    A hybrid limit + market order strategy for DRV buybacks.

    This strategy:
    1. Places limit buy orders at 90% of the index price (50% of budget)
    2. Limit orders expire after 1 hour if not filled
    3. Places market orders every hour for TWAP execution (50% of budget)
    4. Tracks filled amounts to stay within weekly budget
    """

    def __init__(self, client: HTTPClient):
        self.client = client
        self.current_order_id = None
        self.order_placed_at = None
        self.last_market_order_time = None
        self.total_limit_filled_this_week = D("0")
        self.total_market_filled_this_week = D("0")
        self.unfilled_limit_budget = D("0")  # Accumulated unfilled limit order budget
        self.unfilled_market_budget = D("0")  # Accumulated unfilled market order budget
        self.week_start_time = time.time()

    def get_hourly_limit_amount(self, target_price: Decimal) -> Decimal:
        """Calculate how much to allocate for limit orders this hour, including carryover."""
        # Total weekly amount for limit orders (50% of buyback)
        weekly_limit_amount = WEEKLY_BUYBACK_AMOUNT * LIMIT_ORDER_PERCENTAGE / target_price

        # Divide by hours in a week (168 hours)
        hours_in_week = 168
        hourly_amount = weekly_limit_amount / hours_in_week

        # Add any unfilled budget from previous intervals
        total_amount = hourly_amount + self.unfilled_limit_budget

        return total_amount

    def get_hourly_market_amount(self, current_price: Decimal) -> Decimal:
        """Calculate how much to allocate for market orders this hour (TWAP), including carryover."""
        # Total weekly amount for market orders (50% of buyback)
        weekly_market_amount = WEEKLY_BUYBACK_AMOUNT * MARKET_ORDER_PERCENTAGE / current_price

        # Divide by hours in a week (168 hours)
        hours_in_week = 168
        hourly_amount = weekly_market_amount / hours_in_week

        # Add any unfilled budget from previous intervals
        total_amount = hourly_amount + self.unfilled_market_budget

        return total_amount

    def should_reset_weekly_tracking(self) -> bool:
        """Check if we should reset the weekly filled amount tracker."""
        time_elapsed = time.time() - self.week_start_time
        one_week_seconds = 7 * 24 * 60 * 60

        if time_elapsed >= one_week_seconds:
            total_filled = self.total_limit_filled_this_week + self.total_market_filled_this_week
            print(f"\n✅ Week complete! Total filled: {total_filled} DRV")
            print(f"   Limit orders: {self.total_limit_filled_this_week} DRV")
            print(f"   Market orders: {self.total_market_filled_this_week} DRV")
            print(f"   Unfilled limit budget carried: {self.unfilled_limit_budget} DRV")
            print(f"   Unfilled market budget carried: {self.unfilled_market_budget} DRV")
            self.total_limit_filled_this_week = D("0")
            self.total_market_filled_this_week = D("0")
            # Note: We do NOT reset unfilled budgets - they continue to accumulate
            self.week_start_time = time.time()
            return True
        return False

    def get_target_price(self) -> Decimal:
        """Get the target price for limit orders (90% of index price)."""
        # Fetch current market data
        tickers = self.client.markets.get_tickers(
            instrument_type=AssetType.erc20,
        )
        ticker = tickers[INSTRUMENT_NAME]

        # Get index price and apply discount
        index_price = ticker.I  # index_price
        target_price = index_price * PRICE_DISCOUNT

        # Round to instrument's tick size
        instrument = self.client.markets.get_instrument(instrument_name=INSTRUMENT_NAME)
        target_price = target_price.quantize(instrument.tick_size)

        return target_price

    def check_and_update_filled_orders(self):
        """Check if our current order has been filled and update tracking."""
        if self.current_order_id is None:
            return

        try:
            order = self.client.orders.get(order_id=self.current_order_id)

            # If order was filled (fully or partially)
            if order.filled_amount > D("0"):
                newly_filled = order.filled_amount
                self.total_limit_filled_this_week += newly_filled
                print(f"  ✅ Limit order filled: {newly_filled} DRV @ ${order.average_price}")
                total_filled = self.total_limit_filled_this_week + self.total_market_filled_this_week
                print(f"  📊 Total filled this week: {total_filled} DRV")

                # If order is completely filled, clear tracking
                if order.filled_amount >= order.amount:
                    self.current_order_id = None
                    self.order_placed_at = None

        except Exception as e:
            print(f"  ⚠️  Error checking order status: {e}")
            # Order might not exist anymore, clear it
            self.current_order_id = None
            self.order_placed_at = None

    def should_place_new_order(self) -> bool:
        """Determine if we should place a new order."""
        # No active order? Place one!
        if self.current_order_id is None:
            return True

        # Check if current order has expired (1 hour)
        if self.order_placed_at is not None:
            time_since_placed = time.time() - self.order_placed_at
            if time_since_placed >= ORDER_EXPIRY_HOURS * 3600:
                print(f"  ⏰ Current order expired (placed {ORDER_EXPIRY_HOURS}h ago)")

                # Before cancelling, check if it was partially filled
                try:
                    order = self.client.orders.get(order_id=self.current_order_id)
                    unfilled_amount = order.amount - order.filled_amount
                    if unfilled_amount > D("0"):
                        # Add unfilled amount to carryover budget
                        self.unfilled_limit_budget += unfilled_amount
                        print(f"  📊 Carrying over unfilled amount: {unfilled_amount} DRV")
                        print(f"     Total unfilled limit budget: {self.unfilled_limit_budget} DRV")
                except Exception as e:
                    print(f"  ⚠️  Could not check order before cancelling: {e}")

                # Cancel the expired order
                try:
                    self.client.orders.cancel(order_id=self.current_order_id, instrument_name=INSTRUMENT_NAME)
                    print(f"  🗑️  Cancelled expired order {self.current_order_id}")
                except Exception as e:
                    print(f"  ⚠️  Error cancelling order: {e}")

                self.current_order_id = None
                self.order_placed_at = None
                return True

        return False

    def place_limit_order(self):
        """Place a new limit buy order at the target price."""
        try:
            # Get target price and amount
            target_price = self.get_target_price()
            order_amount = self.get_hourly_limit_amount(target_price)

            print("\n  📝 Placing limit BUY order:")
            print(f"     Amount: {order_amount} DRV")
            if self.unfilled_limit_budget > D("0"):
                print(f"     (includes {self.unfilled_limit_budget} DRV carryover)")
            print(f"     Price: ${target_price}")

            # Place the order
            order = self.client.orders.create(
                instrument_name=INSTRUMENT_NAME,
                amount=order_amount,
                limit_price=target_price,
                direction=Direction.buy,
                order_type=OrderType.limit,
                time_in_force=TimeInForce.gtc,  # Good 'til cancelled
                label="buyback_limit",
            )

            self.current_order_id = order.order_id
            self.order_placed_at = time.time()

            # Reset the unfilled budget since we've now placed a new order with it
            self.unfilled_limit_budget = D("0")

            print(f"  ✅ Order placed: {order.order_id}")
            print(f"     Status: {order.order_status}")

        except Exception as e:
            print(f"  ❌ Error placing order: {e}")

    def should_place_market_order(self) -> bool:
        """Determine if we should place a market order (TWAP)."""
        # Never placed a market order? Place one!
        if self.last_market_order_time is None:
            return True

        # Check if it's time for the next market order
        time_since_last = time.time() - self.last_market_order_time
        return time_since_last >= MARKET_ORDER_INTERVAL_SECONDS

    def place_market_order(self):
        """Place a market buy order at current best ask (TWAP component)."""
        try:
            # Get current market price
            tickers = self.client.markets.get_tickers(
                instrument_type=AssetType.erc20,
            )
            ticker = tickers[INSTRUMENT_NAME]

            # Use best ask as the limit price (maximum acceptable price)
            best_ask = ticker.a  # best_ask_price
            if best_ask == 0:
                print("  ⚠️  No liquidity available (best ask = 0), skipping market order")
                # Carry over the budget to next interval since we couldn't place
                weekly_market_amount = WEEKLY_BUYBACK_AMOUNT * MARKET_ORDER_PERCENTAGE / D("1.0")  # Rough estimate
                hours_in_week = 168
                hourly_amount = weekly_market_amount / hours_in_week
                self.unfilled_market_budget += hourly_amount
                print(f"  📊 Carrying over market order budget: {hourly_amount} DRV")
                return

            # Calculate order amount
            order_amount = self.get_hourly_market_amount(best_ask)

            print("\n  🔥 Placing MARKET BUY order (TWAP):")
            print(f"     Amount: {order_amount} DRV")
            if self.unfilled_market_budget > D("0"):
                print(f"     (includes {self.unfilled_market_budget} DRV carryover)")
            print(f"     Max price: ${best_ask}")

            # Place the market order
            # Note: We set a limit price as a safety mechanism to prevent slippage
            order = self.client.orders.create(
                instrument_name=INSTRUMENT_NAME,
                amount=order_amount,
                limit_price=best_ask * D("1.02"),  # Allow up to 2% slippage
                direction=Direction.buy,
                order_type=OrderType.market,
                label="buyback_market",
            )

            self.last_market_order_time = time.time()

            # Market orders should fill immediately, track it
            if order.filled_amount > D("0"):
                self.total_market_filled_this_week += order.filled_amount
                print(f"  ✅ Market order filled: {order.filled_amount} DRV @ ${order.average_price}")
                total_filled = self.total_limit_filled_this_week + self.total_market_filled_this_week
                print(f"  📊 Total filled this week: {total_filled} DRV")

                # Check if order was partially filled
                unfilled_amount = order.amount - order.filled_amount
                if unfilled_amount > D("0"):
                    # Carry over the unfilled amount
                    self.unfilled_market_budget += unfilled_amount
                    print(f"  ⚠️  Partially filled - carrying over: {unfilled_amount} DRV")
                else:
                    # Fully filled, reset carryover
                    self.unfilled_market_budget = D("0")
            else:
                print(f"  ⚠️  Market order status: {order.order_status}")
                # Order didn't fill, carry over the amount
                self.unfilled_market_budget += order.amount
                print(f"  📊 Carrying over unfilled: {order.amount} DRV")

        except Exception as e:
            print(f"  ❌ Error placing market order: {e}")
            # If there was an error, try to carry over the budget
            # Use a rough estimate if we can't get the price
            weekly_market_amount = WEEKLY_BUYBACK_AMOUNT * MARKET_ORDER_PERCENTAGE / D("1.0")
            hours_in_week = 168
            hourly_amount = weekly_market_amount / hours_in_week
            self.unfilled_market_budget += hourly_amount
            print(f"  📊 Carrying over budget due to error: {hourly_amount} DRV")

    def run_strategy(self, duration_hours: int = 24):
        """
        Run the limit order placement strategy.

        Args:
            duration_hours: How many hours to run the strategy (default 24 = 1 day)
        """
        print("=" * 60)
        print("DRV BUYBACK HYBRID STRATEGY")
        print("=" * 60)
        print(f"Instrument: {INSTRUMENT_NAME}")
        print(f"Weekly buyback amount: ${WEEKLY_BUYBACK_AMOUNT} USDC")
        print(f"Limit order allocation: {LIMIT_ORDER_PERCENTAGE * 100}%")
        print(f"Market order allocation (TWAP): {MARKET_ORDER_PERCENTAGE * 100}%")
        print(f"Limit price target: {PRICE_DISCOUNT * 100}% of index")
        print(f"Limit order expiry: {ORDER_EXPIRY_HOURS} hour(s)")
        print(f"Market order interval: {MARKET_ORDER_INTERVAL_SECONDS / 3600:.1f} hour(s)")
        print(f"Check interval: {CHECK_INTERVAL_SECONDS} seconds")
        print("=" * 60)

        start_time = time.time()
        end_time = start_time + (duration_hours * 3600)

        try:
            while time.time() < end_time:
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking strategy...")

                # Reset weekly tracking if needed
                self.should_reset_weekly_tracking()

                # Check if current limit order has been filled
                self.check_and_update_filled_orders()

                # Place new limit order if needed
                if self.should_place_new_order():
                    self.place_limit_order()
                else:
                    print(f"  ℹ️  Active limit order: {self.current_order_id}")
                    if self.order_placed_at:
                        time_remaining = ORDER_EXPIRY_HOURS * 3600 - (time.time() - self.order_placed_at)
                        print(f"     Time until expiry: {time_remaining / 60:.0f} minutes")

                # Place market order if it's time (TWAP)
                if self.should_place_market_order():
                    self.place_market_order()
                elif self.last_market_order_time:
                    time_since_market = time.time() - self.last_market_order_time
                    time_until_market = MARKET_ORDER_INTERVAL_SECONDS - time_since_market
                    print(f"  ℹ️  Next market order in: {time_until_market / 60:.0f} minutes")

                # Sleep until next check
                print(f"\n  😴 Sleeping for {CHECK_INTERVAL_SECONDS} seconds...")
                time.sleep(CHECK_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            print("\n\n⚠️  Strategy interrupted by user")
        finally:
            # Cleanup: cancel any active orders
            if self.current_order_id is not None:
                try:
                    print(f"\n🧹 Cleaning up: cancelling order {self.current_order_id}")
                    self.client.orders.cancel(order_id=self.current_order_id, instrument_name=INSTRUMENT_NAME)
                except Exception as e:
                    print(f"  ⚠️  Error during cleanup: {e}")

            print("\n" + "=" * 60)
            print("STRATEGY COMPLETE")
            print("=" * 60)
            total_filled = self.total_limit_filled_this_week + self.total_market_filled_this_week
            print(f"Total filled this week: {total_filled} DRV")
            print(f"  Limit orders: {self.total_limit_filled_this_week} DRV")
            print(f"  Market orders: {self.total_market_filled_this_week} DRV")
            print("\nCarryover budgets:")
            print(f"  Unfilled limit budget: {self.unfilled_limit_budget} DRV")
            print(f"  Unfilled market budget: {self.unfilled_market_budget} DRV")
            limit_remaining = (WEEKLY_BUYBACK_AMOUNT * LIMIT_ORDER_PERCENTAGE) - self.total_limit_filled_this_week
            market_remaining = (WEEKLY_BUYBACK_AMOUNT * MARKET_ORDER_PERCENTAGE) - self.total_market_filled_this_week
            print("\nRemaining weekly budgets:")
            print(f"  Limit budget: ${limit_remaining:.2f} USDC")
            print(f"  Market budget: ${market_remaining:.2f} USDC")


def main():
    """Main entry point for the simple limit placer strategy."""
    # Initialize client
    env_file = Path(__file__).parent.parent.parent / ".env.template"
    client = HTTPClient.from_env(env_file=env_file)
    client.connect()

    print("\n" + "=" * 60)
    print("ACCOUNT SETUP")
    print("=" * 60)

    # Show account info
    portfolios = client.account.get_all_portfolios()
    print(f"Subaccounts: {len(portfolios)}")
    print(f"Active subaccount: {client.active_subaccount.id}")

    # Show collateral
    collaterals = client.collateral.get()
    print("\nCollateral:")
    for collateral in collaterals.collaterals:
        print(f"  {collateral.asset_name}: {collateral.amount}")

    # Initialize and run strategy
    strategy = SimpleLimitPlacer(client)

    # Run for 24 hours (or until interrupted)
    strategy.run_strategy(duration_hours=168)

    # Cleanup
    client.disconnect()
    print("\n✅ Example complete!")


if __name__ == "__main__":
    main()
