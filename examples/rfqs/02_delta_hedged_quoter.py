"""
Example of how to act as a RFQ quoter that prices incoming RFQs and sends quotes.
This is a more advanced example that sets the stage for implementing a delta-hedging strategy.
This example connects to the WebSocket API, listens for incoming RFQs on a specified wallet,
prices the legs using current market prices, and sends quotes back to the RFQs.
It performs basic delta-hedging on the accepted quotes by;
- Listening on to quote acceptances, calculating the implied delta from the quoted legs and
  performing hedging trades to neutralize the delta exposure.
- It also periodically checks the position and balance updates to ensure the hedging is effective.
IT SHOULD NOT BE USED AS A TRADING STRATEGY!!!
"""

import asyncio
import warnings
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from logging import Logger
from typing import List

from config import ADMIN_TEST_WALLET as TEST_WALLET
from config import SESSION_KEY_PRIVATE_KEY

from derive_client import WebSocketClient
from derive_client.data_types import Environment
from derive_client.data_types.channel_models import QuoteResultSchema
from derive_client.data_types.generated_models import (
    AssetType,
    Direction,
    LegPricedSchema,
    OrderResponseSchema,
    OrderType,
    PositionResponseSchema,
    PrivateSendQuoteResultSchema,
    PublicGetTickerResultSchema,
    RFQResultPublicSchema,
    Status,
    TradeResponseSchema,
    TxStatus4,
)
from derive_client.data_types.utils import D

warnings.filterwarnings("ignore", category=DeprecationWarning)

SUBACCOUNT_ID = 31049

# Quoting parameters
UNDERLYING_TO_QUOTE = "ETH"  # Only quote RFQs for ETH options
QUOTE_SPREAD_BPS = D("0")  # Spread in basis points (currently 0 for tight pricing)
FALLBACK_TO_MARK_PRICE_PREMIUM_BPS = D("1000")  # 10% premium if order book prices unavailable

# Hedging parameters - these control when and how we hedge our delta exposure
MAX_DELTA_TO_QUOTE = D("100.0")  # Maximum absolute delta we're willing to take on per RFQ
MIN_DELTA_EXPOSURE = D("-0.1")  # Minimum portfolio delta before hedging (short exposure threshold)
MAX_DELTA_EXPOSURE = D("0.1")   # Maximum portfolio delta before hedging (long exposure threshold)
HEDGE_INTERVAL = 30  # How often to check portfolio delta (seconds)
HEDGE_ORDER_LABEL = "delta_hedge"  # Label for identifying our hedge orders
HEDGE_ORDER_TIMEOUT_S = 60  # How long hedge orders remain valid before expiring


class DeltaQuoterStrategy:
    """
    Strategy for deciding whether to quote an RFQ and how to price it.
    
    This strategy implements delta-neutral market making by:
    1. Filtering RFQs to only quote relevant instruments (ETH options)
    2. Calculating the delta impact of quoting an RFQ
    3. Rejecting RFQs that would push delta exposure beyond limits
    4. Pricing legs based on current order book prices
    
    Delta is the rate of change of option price with respect to underlying price.
    By managing delta exposure, we reduce directional risk from price movements.
    """
    client: WebSocketClient
    logger: Logger

    def __init__(self, client: WebSocketClient, logger: Logger):
        self.client = client
        self.logger = logger

    async def should_quote(self, rfq: RFQResultPublicSchema) -> bool:
        """
        Determine if we should quote this RFQ based on our strategy criteria.
        
        Criteria for quoting:
        1. All legs must be for our target underlying (ETH)
        2. All legs must be options (not perps or spot)
        3. Total delta impact must be within our risk limits
        4. Must be able to calculate delta (option pricing data available)
        
        Args:
            rfq: The RFQ to evaluate
            
        Returns:
            True if we should quote this RFQ, False otherwise
        """
        # Implement logic to decide whether to quote the RFQ based on current portfolio delta exposure
        # we have a simple discriminator here that only quotes RFQs on a specific underlying
        is_for_target_underlying = all([UNDERLYING_TO_QUOTE in leg.instrument_name for leg in rfq.legs])

        def is_option(instrument_name: str) -> bool:
            """Check if instrument is an option (ends with -C for call or -P for put)"""
            return instrument_name.endswith(("-C", "-P"))

        is_only_options = all([is_option(leg.instrument_name) for leg in rfq.legs])
        if not is_for_target_underlying or not is_only_options:
            return False

        # Calculate what our delta exposure would be if we quote this RFQ
        total_delta, is_error = await self.calculate_delta_from_quote(rfq)
        self.logger.info(f"    - RFQ {rfq.rfq_id} total delta impact would be {total_delta}")

        return all(
            [
                is_for_target_underlying,
                is_only_options,
                abs(total_delta) <= MAX_DELTA_TO_QUOTE,  # Delta impact within limits
                not is_error,  # Successfully calculated delta
            ]
        )

    async def calculate_delta_from_quote(
        self, quote: QuoteResultSchema | RFQResultPublicSchema
    ) -> tuple[Decimal, bool]:
        """
        Calculate the net delta exposure from a quote.
        
        Delta represents how much the position value changes for a $1 move in the underlying.
        For example, a delta of +10 means the position gains $10 if ETH rises by $1.
        
        As market makers, we SELL quotes, meaning we take the opposite side of each leg:
        - If the RFQ wants to BUY an option from us, we SELL it (negative delta impact)
        - If the RFQ wants to SELL an option to us, we BUY it (positive delta impact)
        
        Args:
            quote: The quote or RFQ to calculate delta for
            
        Returns:
            Tuple of (total_delta, is_error)
            - total_delta: Net delta exposure from this quote
            - is_error: True if we couldn't calculate delta (missing pricing data)
        """
        total_delta = D("0.0")
        is_error = False
        for leg in quote.legs:
            # Get current market data including option Greeks
            ticker = await self.client.markets.get_ticker(instrument_name=leg.instrument_name)
            if not ticker.option_pricing:
                self.logger.info(
                    f"    - Cannot calculate delta for leg {leg.instrument_name} due to missing option pricing data."
                )
                is_error = True
                break
            # Delta per contract * number of contracts
            leg_delta = ticker.option_pricing.delta * leg.amount
            # we are the SELLER of the quote so we are in effect taking the opposite side of the leg direction
            # we therefore subtract the delta for buy legs and add for sell legs
            if leg.direction == Direction.sell:
                # Taker sells to us = we buy = positive delta
                total_delta += leg_delta
            else:
                # Taker buys from us = we sell = negative delta
                total_delta -= leg_delta
        return total_delta, is_error

    async def price_legs(self, rfq: RFQResultPublicSchema) -> List[LegPricedSchema]:
        """
        Price the legs of an RFQ based on current order book prices.
        
        Pricing strategy:
        1. Use best bid/ask from order book for competitive pricing
        2. Fall back to mark price with premium if order book is empty
        3. Verify delta impact is acceptable before pricing
        4. Round prices to instrument tick size
        
        This approach provides tighter pricing than using mark price alone,
        but requires more liquidity in the order book.
        
        Args:
            rfq: The RFQ to price
            
        Returns:
            List of priced legs, or empty list if we can't/won't quote
        """
        # Implement logic to price the legs of the RFQ
        priced_legs = []
        # Double-check delta impact before pricing
        expected_delta, is_error = await self.calculate_delta_from_quote(rfq)
        if is_error or abs(expected_delta) > MAX_DELTA_TO_QUOTE:
            return []
        for unpriced_leg in rfq.legs:
            ticker: PublicGetTickerResultSchema = await self.client.markets.get_ticker(
                instrument_name=unpriced_leg.instrument_name
            )
            # we base on the book price here
            if unpriced_leg.direction == Direction.buy:
                # Taker wants to buy from us, so we use the ask side pricing
                if ticker.best_ask_price is None or ticker.best_ask_price == D("0"):
                    self.logger.info(
                        f"    - fallback pricing used as no mark price for: {unpriced_leg.instrument_name}."
                    )
                    # No order book price available, use mark + premium as fallback
                    base_price = ticker.mark_price * (D("1") + FALLBACK_TO_MARK_PRICE_PREMIUM_BPS / D("10000"))
                else:
                    # Use current best ask from order book
                    base_price = ticker.best_ask_price
            else:
                # Taker wants to sell to us, so we use the bid side pricing
                if ticker.best_bid_price is None or ticker.best_bid_price == D("0"):
                    self.logger.info(
                        f"    - fallback pricing used as no mark price for: {unpriced_leg.instrument_name}."
                    )
                    # No order book price available, use mark - premium as fallback
                    base_price = ticker.mark_price * (D("1") - FALLBACK_TO_MARK_PRICE_PREMIUM_BPS / D("10000"))
                else:
                    # Use current best bid from order book
                    base_price = ticker.best_bid_price
            # Quantize to the instrument's tick size (minimum price increment)
            price = base_price.quantize(ticker.tick_size)
            priced_leg = LegPricedSchema(
                price=price,
                amount=unpriced_leg.amount,
                direction=unpriced_leg.direction,
                instrument_name=unpriced_leg.instrument_name,
            )
            priced_legs.append(priced_leg)
        return priced_legs


class PortfolioDeltaCalculator:
    """
    Calculates the total delta exposure across the entire portfolio.
    
    This aggregates delta from three sources:
    1. Options: Uses Greeks (delta) from option pricing models
    2. Perpetuals: Each unit has delta of 1 (linear exposure)
    3. Spot: Each unit has delta of 1 (linear exposure)
    
    The total portfolio delta tells us how much our portfolio value will change
    for a $1 movement in the underlying asset price.
    """
    client: WebSocketClient
    logger: Logger

    def __init__(self, client: WebSocketClient, logger: Logger):
        self.client = client
        self.logger = logger

    async def calculate_portfolio_delta(self) -> Decimal:
        """
        Calculate the current total delta exposure of the portfolio.
        
        Process:
        1. Fetch all open positions for the target underlying
        2. Separate positions by type (option, perp, spot)
        3. Calculate delta contribution from each position type
        4. Sum to get total portfolio delta
        
        Returns:
            Total portfolio delta across all positions
        """
        # Implement logic to calculate the current portfolio delta
        # Get all open positions for our target underlying
        positions: List[PositionResponseSchema] = await self.client.positions.list(
            is_open=True, currency=UNDERLYING_TO_QUOTE
        )
        # Filter positions by instrument type
        option_positions = [
            p
            for p in positions
            if p.instrument_name
            and p.instrument_type == AssetType.option
            and p.instrument_name.startswith(UNDERLYING_TO_QUOTE)
        ]

        perp_positions = [
            p
            for p in positions
            if p.instrument_name
            and p.instrument_type == AssetType.perp
            and p.instrument_name.startswith(UNDERLYING_TO_QUOTE)
        ]
        spot_positions = [
            p
            for p in positions
            if p.instrument_name
            and p.instrument_type == AssetType.erc20
            and p.instrument_name.startswith(UNDERLYING_TO_QUOTE)
        ]
        # Calculate delta contributions
        # Options: delta is provided by pricing model (0 to 1 for calls, -1 to 0 for puts)
        option_deltas = sum([p.delta * p.amount for p in option_positions])
        # Perps and spot: delta is 1 per unit (full linear exposure)
        perp_delta = sum([p.amount for p in perp_positions])  # Perp has delta of 1 per unit
        spot_delta = sum([p.amount for p in spot_positions])  # Spot has delta of 1 per unit
        total_delta = option_deltas + perp_delta + spot_delta
        return Decimal(total_delta)


class DeltaHedgerRfqQuoter:
    """
    Advanced RFQ quoter with automatic delta hedging.
    
    This market maker implementation:
    1. Receives and prices RFQs based on order book data
    2. Monitors portfolio delta exposure in real-time
    3. Automatically hedges delta exposure using perpetual futures
    4. Tracks quote fills and updates hedging strategy accordingly
    
    Delta hedging reduces directional risk by maintaining near-zero net delta,
    allowing the market maker to profit from spreads rather than directional bets.
    
    Key components:
    - DeltaQuoterStrategy: Decides what to quote and how to price
    - PortfolioDeltaCalculator: Monitors total delta exposure
    - Hedging system: Executes offsetting trades to neutralize delta
    
    WARNING: This is a demonstration of concepts only. Production systems require:
    - More sophisticated risk management (gamma, vega, theta)
    - Better order execution and slippage control
    - Comprehensive error handling and recovery
    - Capital efficiency optimizations
    """
    logger: Logger
    client: WebSocketClient

    def __init__(self, client: WebSocketClient):
        self.client = client
        self.logger = client._logger
        self.portfolio_delta_calculator = PortfolioDeltaCalculator(client, self.logger)
        self.delta_quoter_strategy = DeltaQuoterStrategy(client, self.logger)
        # Track active quotes by RFQ ID
        self.quotes: dict[str, PrivateSendQuoteResultSchema] = {}
        # hedging state
        self.hedging_queue = asyncio.Queue()  # Queue of delta calculations triggering hedge checks
        self.hedger_task: asyncio.Task[None]  # Background task for hedging
        self.hedge_order: OrderResponseSchema | None = None  # Currently active hedge order
        self.hedge_lock = asyncio.Lock()  # Prevent concurrent hedge executions
        # state locks
        self.quoting_lock = asyncio.Lock()  # Prevent race conditions in quote tracking

    async def create_quote(self, rfq):
        """
        Create and price a quote for an RFQ if our strategy allows it.
        
        Args:
            rfq: The RFQ to potentially quote
            
        Returns:
            List of priced legs, or empty list if we decline to quote
        """
        # Price legs using current market prices NOTE! This is just an example and not a trading strategy!!!
        if not await self.delta_quoter_strategy.should_quote(rfq):
            self.logger.info(f"  - Skipping quoting for RFQ {rfq.rfq_id} based on strategy decision.")
            return []
        priced_legs = await self.delta_quoter_strategy.price_legs(rfq)
        self.logger.info(
            f"  ✓ Priced legs for RFQ {rfq.rfq_id} at total price {sum(leg.price * leg.amount for leg in priced_legs)}"
        )
        return priced_legs

    async def on_rfq(self, rfqs: List[RFQResultPublicSchema]):
        """
        Handle incoming RFQ updates from the WebSocket channel.
        
        Process:
        1. Clean up expired/cancelled RFQs from tracking
        2. Filter for open RFQs that need quotes
        3. Price all quotable RFQs concurrently
        4. Submit all quotes concurrently
        5. Track successful quotes for monitoring
        
        Args:
            rfqs: List of RFQ updates
        """
        for rfq in rfqs:
            async with self.quoting_lock:
                if rfq.status in {Status.expired, Status.cancelled} and rfq.rfq_id in self.quotes:
                    del self.quotes[rfq.rfq_id]
        open_rfqs = [r for r in rfqs if r.status == Status.open]
        if not open_rfqs:
            return

        priced = await asyncio.gather(*(self.create_quote(r) for r in open_rfqs))
        quotable = [(r, legs) for r, legs in zip(open_rfqs, priced) if legs]

        if not quotable:
            return

        # as we are the quoter, we always sell the quotes
        results = await asyncio.gather(
            *(self.client.rfq.send_quote(rfq_id=r.rfq_id, legs=legs, direction=Direction.sell) for r, legs in quotable),
            return_exceptions=True,
        )
        for r, result in zip(quotable, results):
            rfq, _ = r
            if isinstance(result, PrivateSendQuoteResultSchema):
                async with self.quoting_lock:
                    self.quotes[rfq.rfq_id] = result
            else:
                self.logger.info(f"  ❌ Failed to send quote for RFQ {rfq.rfq_id}: {result}")

    async def on_quote(self, quotes_list: List[QuoteResultSchema]):
        """
        Handle quote status updates.
        
        When quotes expire or fill, we:
        1. Remove them from tracking
        2. Log the outcome
        3. (Hedging is triggered separately via trade settlements)
        
        Args:
            quotes_list: List of quote status updates
        """
        for quote in quotes_list:
            self.logger.info(f"  - Quote {quote.quote_id} {quote.rfq_id}: {quote.status}")
            async with self.quoting_lock:
                if quote.status == Status.expired and quote.rfq_id in self.quotes:
                    del self.quotes[quote.rfq_id]
                    self.logger.info(f"  ✗ Our quote {quote.quote_id} expired Better luck next time!")
                elif quote.status == Status.filled and quote.rfq_id in self.quotes:
                    del self.quotes[quote.rfq_id]
                    self.logger.info(f"  ✓ Our quote {quote.quote_id} was accepted!")

    async def execute_hedge(self, delta_to_hedge: Decimal):
        """
        Execute a hedge trade to neutralize delta exposure.
        
        Strategy:
        - If portfolio delta is positive (long), sell perpetuals to reduce exposure
        - If portfolio delta is negative (short), buy perpetuals to increase exposure
        - Use limit orders at current best bid/ask for better execution
        - Orders expire after HEDGE_ORDER_TIMEOUT_S seconds if not filled
        
        Args:
            delta_to_hedge: The amount of delta to neutralize (signed value)
        """
        instrument_name = f"{UNDERLYING_TO_QUOTE}-PERP"
        if self.hedge_order is not None:
            self.logger.info(
                f"    - Existing hedge {self.hedge_order.order_id} in progress, skipping new hedge {delta_to_hedge}."
            )
            return
        ticker = await self.client.markets.get_ticker(instrument_name=instrument_name)
        # if we need to hedge negative delta, we need to buy the underlying perp
        # if we need to hedge positive delta, we need to sell the underlying perp
        trade_direction = Direction.sell if delta_to_hedge < 0 else Direction.buy
        # Use appropriate side of the book for our direction
        price = ticker.best_bid_price if trade_direction == Direction.sell else ticker.best_ask_price
        if price is None or price == D("0"):
            # Fallback to mark price if order book is empty
            price = ticker.mark_price
        trade_amount = abs(delta_to_hedge)
        if trade_amount < ticker.minimum_amount:
            self.logger.info(
                f"    - Hedge amount {trade_amount} is below min order size {ticker.minimum_amount}, skipping."
            )
            return
        self.logger.info(f"    - Executing hedge for delta amount: {delta_to_hedge} in direction {trade_direction}")
        # Create a limit order to hedge the delta exposure
        self.hedge_order = await self.client.orders.create(
            amount=trade_amount,
            instrument_name=instrument_name,
            limit_price=price.quantize(ticker.tick_size),
            direction=trade_direction,
            order_type=OrderType.limit,
            reduce_only=False,  # We want to open new positions to hedge
            label=HEDGE_ORDER_LABEL,  # Tag for tracking hedge orders
            reject_timestamp=int((datetime.now(UTC) + timedelta(seconds=HEDGE_ORDER_TIMEOUT_S)).timestamp() * 1000),
        )

    async def on_trade_settlement(self, trades: List[TradeResponseSchema]):
        """
        Handle trade settlement notifications.
        
        When an RFQ trade settles (completes), we need to re-evaluate our
        portfolio delta because our option positions have changed. This may
        trigger a hedge if the delta is now outside our target range.
        
        Args:
            trades: List of settled trades
        """

        rfq_trades = []
        for trade in trades:
            self.logger.info(
                f"  - {trade.instrument_name}-{trade.direction} {trade.trade_amount} at {trade.trade_price}"
            )
            if trade.quote_id:
                # This trade was from an RFQ quote we provided
                rfq_trades.append(trade)
        if rfq_trades:
            self.logger.info(f"  ✓ Detected {len(rfq_trades)} RFQ trades settled, re-evaluating portfolio delta.")
            # Queue up a delta calculation to potentially trigger hedging
            await self.hedging_queue.put(await self.portfolio_delta_calculator.calculate_portfolio_delta())

    async def on_order(self, orders: List[OrderResponseSchema]):
        """
        Handle order status updates.
        
        We monitor our hedge orders to know when they complete (fill, cancel, expire).
        When a hedge order finishes, we clear the tracking variable and re-evaluate
        delta to see if additional hedging is needed.
        
        Args:
            orders: List of order updates
        """
        for order in orders:
            self.logger.info(f"  - Order {order.order_id} status update: {order.order_status}")
            if order.label == HEDGE_ORDER_LABEL and order.order_status in {
                Status.filled,
                Status.cancelled,
                Status.expired,
            }:
                self.logger.info(
                    f"  ✓ Hedge order {order.order_id} status {order.order_status}, re-evaluating total delta."
                )
                # Clear the hedge order tracking
                self.hedge_order = None
                # Re-calculate portfolio delta after hedge completes
                await self.hedging_queue.put(await self.portfolio_delta_calculator.calculate_portfolio_delta())

    async def run(self):
        """
        Main execution loop - sets up all subscriptions and background tasks.
        
        Subscriptions:
        1. RFQs by wallet - to receive RFQ requests to quote
        2. Quotes by subaccount - to track status of our quotes
        3. Trades by subaccount - to detect when RFQ trades settle
        4. Orders by subaccount - to track hedge order status
        
        Background tasks:
        - Portfolio hedging task runs continuously to monitor and hedge delta
        """
        await self.client.connect()
        # Subscribe to RFQs we can quote
        await self.client.private_channels.rfqs_by_wallet(wallet=TEST_WALLET, callback=self.on_rfq)
        # Subscribe to our quote status updates
        await self.client.private_channels.quotes_by_subaccount_id(
            subaccount_id=str(SUBACCOUNT_ID),
            callback=self.on_quote,
        )
        # Subscribe to settled trades to trigger delta recalculation
        await self.client.private_channels.trades_tx_status_by_subaccount_id(
            subaccount_id=SUBACCOUNT_ID,
            callback=self.on_trade_settlement,
            tx_status=TxStatus4.settled,  # Only care about finalized trades
        )
        # Subscribe to order updates to track hedge order status
        await self.client.private_channels.orders_by_subaccount_id(
            subaccount_id=str(SUBACCOUNT_ID),
            callback=self.on_order,
        )
        # Start the background hedging task
        self.hedger_task = asyncio.create_task(self.portfolio_hedging_task())
        # we send a request to evaluate the current delta on startup
        await self.hedging_queue.put(await self.portfolio_delta_calculator.calculate_portfolio_delta())
        # Keep running indefinitely
        await asyncio.Event().wait()

    async def portfolio_hedging_task(self):
        """
        Background task that continuously monitors and hedges portfolio delta.
        
        Operation:
        1. Check queue for triggered delta recalculations (from trades/orders)
        2. If no trigger, periodically recalculate delta based on HEDGE_INTERVAL
        3. If delta exceeds thresholds (MIN_DELTA_EXPOSURE or MAX_DELTA_EXPOSURE),
           execute a hedge trade to bring it back to neutral
        
        This runs continuously in the background, ensuring our delta exposure
        stays within acceptable risk limits.
        """
        # Implement periodic portfolio delta checking and hedging if necessary

        last_check_time = datetime.now(UTC)

        while True:
            # Drain queue of any pending delta calculations
            portfolio_delta: Decimal | None = None
            while True:
                try:
                    portfolio_delta = self.hedging_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

            # If no triggered calculation, check if it's time for periodic check
            if portfolio_delta is None:
                now = datetime.now(UTC)
                if (now - last_check_time).total_seconds() >= HEDGE_INTERVAL:
                    portfolio_delta = await self.portfolio_delta_calculator.calculate_portfolio_delta()
                    last_check_time = now
                else:
                    # Not time yet, sleep and check again
                    await asyncio.sleep(1)
                    continue

            # Check if delta is outside acceptable range and needs hedging
            async with self.hedge_lock:
                if portfolio_delta < MIN_DELTA_EXPOSURE or portfolio_delta > MAX_DELTA_EXPOSURE:
                    # Calculate hedge amount (negative of current delta to neutralize)
                    delta_to_hedge = -portfolio_delta
                    self.logger.info(
                        f"  - Portfolio delta {portfolio_delta} outside exposure limits, hedging {delta_to_hedge}."
                    )
                    await self.execute_hedge(delta_to_hedge)


async def main():
    """
    Main entry point for the delta-hedged RFQ quoter.
    
    This creates a WebSocket client configured for the test environment
    and runs the quoter with automatic reconnection on failures.
    """

    client = WebSocketClient(
        session_key=SESSION_KEY_PRIVATE_KEY,
        wallet=TEST_WALLET,
        env=Environment.TEST,
        subaccount_id=SUBACCOUNT_ID,
    )
    rfq_quoter = DeltaHedgerRfqQuoter(client)
    while True:
        try:
            await rfq_quoter.run()
        except KeyboardInterrupt:
            # Allow clean shutdown
            break


if __name__ == "__main__":
    asyncio.run(main())
