"""
Example of how to act as a RFQ quoter with delta hedging.

This is a more advanced example that demonstrates a realistic market-making strategy:
- Connects to the WebSocket API and listens for incoming RFQs
- Prices legs using current market bid-ask prices (not just mark prices)
- Implements a delta-hedging strategy to manage options exposure
- Monitors portfolio delta and automatically hedges when outside risk limits

Delta hedging explained:
- Options have "delta" - how much their value changes when the underlying asset moves
- When we sell options, we take on delta exposure to the underlying asset
- Delta hedging means trading the underlying (perpetuals) to neutralize this exposure
- This protects us from directional price risk, leaving us with pure volatility exposure

Strategy flow:
1. Receive RFQ -> Calculate if accepting would exceed our delta limits
2. If safe to quote -> Price using current bid-ask + spread
3. When quote is filled -> Calculate new portfolio delta
4. If delta exceeds limits -> Execute hedge trade in the underlying perpetual
5. Continuously monitor and rebalance delta exposure

IMPORTANT: While more realistic than the simple quoter, this is still educational.
IT SHOULD NOT BE USED AS A TRADING STRATEGY without additional risk management!
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
QUOTE_SPREAD_BPS = D("0")  # Additional spread to add to bid-ask (0 = quote at market)
FALLBACK_TO_MARK_PRICE_PREMIUM_BPS = D("1000")  # 10% premium if no bid-ask available

# Hedging parameters - these define our risk limits
MAX_DELTA_TO_QUOTE = D("100.0")  # Maximum delta impact from a single RFQ we'll accept
MIN_DELTA_EXPOSURE = D("-0.1")  # Minimum portfolio delta before hedging (slightly short)
MAX_DELTA_EXPOSURE = D("0.1")  # Maximum portfolio delta before hedging (slightly long)
HEDGE_INTERVAL = 30  # Seconds between periodic delta checks
HEDGE_ORDER_LABEL = "delta_hedge"  # Label for hedge orders to track them
HEDGE_ORDER_TIMEOUT_S = 60  # How long to wait for hedge order to fill before cancelling


class DeltaQuoterStrategy:
    """
    Strategy for deciding which RFQs to quote and how to price them.
    
    This class handles:
    - Filtering RFQs based on criteria (underlying, instrument type, delta impact)
    - Calculating delta exposure from options positions
    - Pricing legs using market bid-ask prices
    """
    client: WebSocketClient
    logger: Logger

    def __init__(self, client: WebSocketClient, logger: Logger):
        self.client = client
        self.logger = logger

    async def should_quote(self, rfq: RFQResultPublicSchema) -> bool:
        """
        Determine whether to quote on this RFQ based on risk limits and filters.
        
        Checks:
        1. Is the RFQ for our target underlying (ETH)?
        2. Are all legs options (not perps or spot)?
        3. Would accepting this RFQ exceed our single-trade delta limit?
        4. Can we successfully calculate delta for all legs?
        
        Returns:
            True if we should quote, False otherwise
        """
        # Implement logic to decide whether to quote the RFQ based on current portfolio delta exposure
        # we have a simple descrimintaor here that only quotes RFQs on a specific underlying
        is_for_target_underlying = all([UNDERLYING_TO_QUOTE in leg.instrument_name for leg in rfq.legs])

        def is_option(instrument_name: str) -> bool:
            """Check if instrument is an option (ends with -C for call or -P for put)"""
            return instrument_name.endswith(("-C", "-P"))

        is_only_options = all([is_option(leg.instrument_name) for leg in rfq.legs])
        if not is_for_target_underlying or not is_only_options:
            return False

        # Calculate the delta impact of this RFQ on our portfolio
        total_delta, is_error = await self.calculate_delta_from_quote(rfq)
        self.logger.info(f"    - RFQ {rfq.rfq_id} total delta impact would be {total_delta}")

        # Only quote if all conditions are met
        return all(
            [
                is_for_target_underlying,
                is_only_options,
                abs(total_delta) <= MAX_DELTA_TO_QUOTE,  # Delta impact is within limits
                not is_error,  # No errors calculating delta
            ]
        )

    async def calculate_delta_from_quote(
        self, quote: QuoteResultSchema | RFQResultPublicSchema
    ) -> tuple[Decimal, bool]:
        """
        Calculate the net delta exposure from accepting a quote or RFQ.
        
        Delta calculation logic:
        - Each option has a delta value (from 0 to 1 for calls, 0 to -1 for puts)
        - Multiply delta by amount to get total delta per leg
        - As the SELLER of the quote, we take the opposite side of the taker
        - If taker is buying (we sell), we subtract delta
        - If taker is selling (we buy), we add delta
        
        Returns:
            tuple: (total_delta, is_error)
            - total_delta: Net delta exposure we would have after this trade
            - is_error: True if we couldn't calculate delta (missing data)
        """
        total_delta = D("0.0")
        is_error = False
        for leg in quote.legs:
            ticker = await self.client.markets.get_ticker(instrument_name=leg.instrument_name)
            if not ticker.option_pricing:
                self.logger.info(
                    f"    - Cannot calculate delta for leg {leg.instrument_name} due to missing option pricing data."
                )
                is_error = True
                break
            leg_delta = ticker.option_pricing.delta * leg.amount
            # we are the SELLER of the quote so we are in effect taking the opposite side of the leg direction
            # we therefore subtract the delta for buy legs and add for sell legs
            if leg.direction == Direction.sell:
                total_delta += leg_delta
            else:
                total_delta -= leg_delta
        return total_delta, is_error

    async def price_legs(self, rfq: RFQResultPublicSchema) -> List[LegPricedSchema]:
        """
        Price all legs of an RFQ using current market bid-ask prices.
        
        Pricing strategy:
        - Use bid-ask prices from the order book (better than mark price for execution)
        - For legs we BUY: Use best ask price (we pay the ask)
        - For legs we SELL: Use best bid price (we receive the bid)
        - Fallback to mark price + premium if no bid-ask available
        - Verify delta impact is within our limits before pricing
        
        Returns:
            List of priced legs, or empty list if we shouldn't quote
        """
        # Implement logic to price the legs of the RFQ
        priced_legs = []
        # First check if the delta impact is acceptable
        expected_delta, is_error = await self.calculate_delta_from_quote(rfq)
        if is_error or abs(expected_delta) > MAX_DELTA_TO_QUOTE:
            return []
        
        for unpriced_leg in rfq.legs:
            ticker: PublicGetTickerResultSchema = await self.client.markets.get_ticker(
                instrument_name=unpriced_leg.instrument_name
            )
            # We base pricing on the current order book bid-ask prices
            # This is more accurate than mark price for immediate execution
            if unpriced_leg.direction == Direction.buy:
                # Taker wants to buy, we sell -> quote at ask price
                if ticker.best_ask_price is None or ticker.best_ask_price == D("0"):
                    self.logger.info(
                        f"    - fallback pricing used as no ask price for: {unpriced_leg.instrument_name}."
                    )
                    # Fallback: Use mark price with a premium to compensate for illiquidity
                    base_price = ticker.mark_price * (D("1") + FALLBACK_TO_MARK_PRICE_PREMIUM_BPS / D("10000"))
                else:
                    base_price = ticker.best_ask_price
            else:
                # Taker wants to sell, we buy -> quote at bid price
                if ticker.best_bid_price is None or ticker.best_bid_price == D("0"):
                    self.logger.info(
                        f"    - fallback pricing used as no bid price for: {unpriced_leg.instrument_name}."
                    )
                    # Fallback: Use mark price with a discount for illiquidity
                    base_price = ticker.mark_price * (D("1") - FALLBACK_TO_MARK_PRICE_PREMIUM_BPS / D("10000"))
                else:
                    base_price = ticker.best_bid_price
            # Round to the instrument's tick size
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
    Calculator for determining the total delta exposure across our entire portfolio.
    
    This class:
    - Fetches all open positions (options, perpetuals, spot)
    - Calculates delta contribution from each position type
    - Returns the total portfolio delta
    
    Portfolio delta is the sum of:
    - Options: delta * amount (from option pricing models)
    - Perpetuals: amount (perps have delta = 1)
    - Spot: amount (spot has delta = 1)
    """
    client: WebSocketClient
    logger: Logger

    def __init__(self, client: WebSocketClient, logger: Logger):
        self.client = client
        self.logger = logger

    async def calculate_portfolio_delta(self) -> Decimal:
        """
        Calculate total portfolio delta across all positions.
        
        Returns:
            Decimal: Net delta exposure (positive = long, negative = short)
        """
        # Implement logic to calculate the current portfolio delta
        # Fetch all open positions for our underlying
        positions: List[PositionResponseSchema] = await self.client.positions.list(
            is_open=True, currency=UNDERLYING_TO_QUOTE
        )
        # Separate positions by type for clarity
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
        # Calculate delta contribution from each position type
        option_deltas = sum([p.delta * p.amount for p in option_positions])
        perp_delta = sum([p.amount for p in perp_positions])  # Perp has delta of 1 per unit
        spot_delta = sum([p.amount for p in spot_positions])  # Spot has delta of 1 per unit
        total_delta = option_deltas + perp_delta + spot_delta
        return Decimal(total_delta)


class DeltaHedgerRfqQuoter:
    """
    Complete RFQ quoter with automated delta hedging.
    
    This is the main class that coordinates:
    1. Receiving and filtering RFQs
    2. Pricing and sending quotes
    3. Monitoring quote fills
    4. Calculating portfolio delta exposure
    5. Executing hedge trades when needed
    
    The class maintains several concurrent tasks:
    - Main event loop: Handles incoming RFQs and quotes
    - Hedging task: Monitors delta and executes hedges
    - WebSocket callbacks: Process real-time updates
    """
    logger: Logger
    client: WebSocketClient

    def __init__(self, client: WebSocketClient):
        self.client = client
        self.logger = client._logger
        self.portfolio_delta_calculator = PortfolioDeltaCalculator(client, self.logger)
        self.delta_quoter_strategy = DeltaQuoterStrategy(client, self.logger)
        self.quotes: dict[str, PrivateSendQuoteResultSchema] = {}  # Track active quotes
        # Hedging state management
        self.hedging_queue = asyncio.Queue()  # Queue delta calculations for hedging task
        self.hedger_task: asyncio.Task[None]  # Background task that executes hedges
        self.hedge_order: OrderResponseSchema | None = None  # Current active hedge order
        self.hedge_lock = asyncio.Lock()  # Prevent concurrent hedge executions
        # State locks to prevent race conditions
        self.quoting_lock = asyncio.Lock()

    async def create_quote(self, rfq):
        """
        Create a quote for an RFQ if it passes our strategy filters.
        
        Returns:
            List of priced legs if we should quote, empty list otherwise
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
        Handle incoming RFQ updates from the exchange.
        
        Similar to simple quoter but with delta-aware filtering.
        """
        # Clean up quotes for expired/cancelled RFQs
        for rfq in rfqs:
            async with self.quoting_lock:
                if rfq.status in {Status.expired, Status.cancelled} and rfq.rfq_id in self.quotes:
                    del self.quotes[rfq.rfq_id]
        
        # Filter for open RFQs
        open_rfqs = [r for r in rfqs if r.status == Status.open]
        if not open_rfqs:
            return

        # Price RFQs in parallel (strategy will filter based on delta limits)
        priced = await asyncio.gather(*(self.create_quote(r) for r in open_rfqs))
        quotable = [(r, legs) for r, legs in zip(open_rfqs, priced) if legs]

        if not quotable:
            return

        # Send quotes (always as seller - we're the market maker)
        results = await asyncio.gather(
            *(self.client.rfq.send_quote(rfq_id=r.rfq_id, legs=legs, direction=Direction.sell) for r, legs in quotable),
            return_exceptions=True,
        )
        # Track successfully sent quotes
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
        
        When quotes expire or fill, we clean up tracking.
        No hedging is triggered here - that happens in on_trade_settlement.
        """
        for quote in quotes_list:
            self.logger.info(f"  - Quote {quote.quote_id} {quote.rfq_id}: {quote.status}")
            async with self.quoting_lock:
                if quote.status == Status.expired and quote.rfq_id in self.quotes:
                    del self.quotes[quote.rfq_id]
                    self.logger.info(f"  ✗ Our quote {quote.quote_id} expired. Better luck next time!")
                elif quote.status == Status.filled and quote.rfq_id in self.quotes:
                    del self.quotes[quote.rfq_id]
                    self.logger.info(f"  ✓ Our quote {quote.quote_id} was accepted!")

    async def execute_hedge(self, delta_to_hedge: Decimal):
        """
        Execute a hedge trade to neutralize delta exposure.
        
        Hedging logic:
        - If portfolio delta is negative (short), buy perpetuals to neutralize
        - If portfolio delta is positive (long), sell perpetuals to neutralize
        - Use market bid-ask prices for immediate execution
        - Set order timeout to prevent hanging orders
        
        Args:
            delta_to_hedge: Amount of delta to hedge (negative = need to buy, positive = need to sell)
        """
        instrument_name = f"{UNDERLYING_TO_QUOTE}-PERP"
        # Only allow one hedge order at a time
        if self.hedge_order is not None:
            self.logger.info(
                f"    - Existing hedge {self.hedge_order.order_id} in progress, skipping new hedge {delta_to_hedge}."
            )
            return
        
        # Fetch current market prices for the perpetual
        ticker = await self.client.markets.get_ticker(instrument_name=instrument_name)
        
        # Determine trade direction:
        # If delta_to_hedge is negative, we need to increase delta (buy)
        # If delta_to_hedge is positive, we need to decrease delta (sell)
        trade_direction = Direction.sell if delta_to_hedge < 0 else Direction.buy
        price = ticker.best_bid_price if trade_direction == Direction.sell else ticker.best_ask_price
        if price is None or price == D("0"):
            # Fallback to mark price if no bid-ask available
            price = ticker.mark_price
        
        trade_amount = abs(delta_to_hedge)
        # Check if order meets minimum size requirements
        if trade_amount < ticker.minimum_amount:
            self.logger.info(
                f"    - Hedge amount {trade_amount} is below min order size {ticker.minimum_amount}, skipping."
            )
            return
        
        self.logger.info(f"    - Executing hedge for delta amount: {delta_to_hedge} in direction {trade_direction}")
        # Place hedge order with timeout to prevent hanging orders
        self.hedge_order = await self.client.orders.create(
            amount=trade_amount,
            instrument_name=instrument_name,
            limit_price=price.quantize(ticker.tick_size),
            direction=trade_direction,
            order_type=OrderType.limit,
            reduce_only=False,
            label=HEDGE_ORDER_LABEL,  # Label helps us track hedge orders
            reject_timestamp=int((datetime.now(UTC) + timedelta(seconds=HEDGE_ORDER_TIMEOUT_S)).timestamp() * 1000),
        )

    async def on_trade_settlement(self, trades: List[TradeResponseSchema]):
        """
        Handle trade settlement notifications.
        
        When RFQ trades settle, we need to recalculate our portfolio delta
        and potentially execute a hedge. This is the key trigger for hedging.
        """

        rfq_trades = []
        for trade in trades:
            self.logger.info(
                f"  - {trade.instrument_name}-{trade.direction} {trade.trade_amount} at {trade.trade_price}"
            )
            # Identify trades from RFQ fills (they have a quote_id)
            if trade.quote_id:
                rfq_trades.append(trade)
        
        if rfq_trades:
            self.logger.info(f"  ✓ Detected {len(rfq_trades)} RFQ trades settled, re-evaluating portfolio delta.")
            # Queue a delta recalculation which will trigger hedging if needed
            await self.hedging_queue.put(await self.portfolio_delta_calculator.calculate_portfolio_delta())

    async def on_order(self, orders: List[OrderResponseSchema]):
        """
        Handle order status updates.
        
        When our hedge orders complete (filled/cancelled/expired), we:
        1. Clear the hedge_order state to allow new hedges
        2. Recalculate portfolio delta to see if more hedging is needed
        """
        for order in orders:
            self.logger.info(f"  - Order {order.order_id} status update: {order.order_status}")
            # Check if this is one of our hedge orders
            if order.label == HEDGE_ORDER_LABEL and order.order_status in {
                Status.filled,
                Status.cancelled,
                Status.expired,
            }:
                self.logger.info(
                    f"  ✓ Hedge order {order.order_id} status {order.order_status}, re-evaluating total delta."
                )
                self.hedge_order = None  # Clear hedge order state
                # Queue delta recalculation to check if we need more hedging
                await self.hedging_queue.put(await self.portfolio_delta_calculator.calculate_portfolio_delta())

    async def run(self):
        """
        Start the quoter and all its background tasks.
        
        Sets up:
        1. WebSocket subscriptions for RFQs, quotes, trades, and orders
        2. Background hedging task that monitors portfolio delta
        3. Initial delta calculation on startup
        """
        await self.client.connect()
        # Subscribe to all the channels we need
        await self.client.private_channels.rfqs_by_wallet(wallet=TEST_WALLET, callback=self.on_rfq)
        await self.client.private_channels.quotes_by_subaccount_id(
            subaccount_id=str(SUBACCOUNT_ID),
            callback=self.on_quote,
        )
        await self.client.private_channels.trades_tx_status_by_subaccount_id(
            subaccount_id=SUBACCOUNT_ID,
            callback=self.on_trade_settlement,
            tx_status=TxStatus4.settled,  # Only get settled trades
        )
        await self.client.private_channels.orders_by_subaccount_id(
            subaccount_id=str(SUBACCOUNT_ID),
            callback=self.on_order,
        )
        # Start background hedging task
        self.hedger_task = asyncio.create_task(self.portfolio_hedging_task())
        # Calculate initial portfolio delta on startup
        await self.hedging_queue.put(await self.portfolio_delta_calculator.calculate_portfolio_delta())
        await asyncio.Event().wait()  # Keep running indefinitely

    async def portfolio_hedging_task(self):
        """
        Background task that continuously monitors and hedges portfolio delta.
        
        This task runs in parallel with the main event loop and:
        1. Processes delta calculations from the queue (triggered by trades/orders)
        2. Periodically recalculates delta (every HEDGE_INTERVAL seconds)
        3. Executes hedge trades when delta exceeds MIN/MAX_DELTA_EXPOSURE limits
        
        The queue-based approach ensures we don't miss hedging opportunities
        even during rapid trading, while periodic checks catch any drift.
        """
        # Implement periodic portfolio delta checking and hedging if necessary

        last_check_time = datetime.now(UTC)

        while True:
            # Drain the queue - get the latest delta if available
            portfolio_delta: Decimal | None = None
            while True:
                try:
                    portfolio_delta = self.hedging_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

            # If no queued delta, check if it's time for periodic recalculation
            if portfolio_delta is None:
                now = datetime.now(UTC)
                if (now - last_check_time).total_seconds() >= HEDGE_INTERVAL:
                    portfolio_delta = await self.portfolio_delta_calculator.calculate_portfolio_delta()
                    last_check_time = now
                else:
                    # Not time yet, sleep and try again
                    await asyncio.sleep(1)
                    continue

            # Check if delta is outside our acceptable range and hedge if needed
            async with self.hedge_lock:
                if portfolio_delta < MIN_DELTA_EXPOSURE or portfolio_delta > MAX_DELTA_EXPOSURE:
                    # Calculate how much to hedge to bring delta back to neutral
                    delta_to_hedge = -portfolio_delta
                    self.logger.info(
                        f"  - Portfolio delta {portfolio_delta} outside exposure limits, hedging {delta_to_hedge}."
                    )
                    await self.execute_hedge(delta_to_hedge)


async def main():
    """
    Initialize and run the delta-hedged RFQ quoter.
    
    This creates a sophisticated market maker that:
    - Quotes on incoming ETH options RFQs
    - Automatically hedges delta exposure by trading perpetuals
    - Maintains delta within configured risk limits
    - Runs continuously with automatic reconnection
    
    To use this effectively, you should:
    1. Adjust risk parameters (MAX_DELTA_TO_QUOTE, MIN/MAX_DELTA_EXPOSURE)
    2. Monitor the logs to understand hedging behavior
    3. Test thoroughly on testnet before production use
    4. Consider adding additional risk controls (position limits, PnL stops, etc.)
    """

    client = WebSocketClient(
        session_key=SESSION_KEY_PRIVATE_KEY,
        wallet=TEST_WALLET,
        env=Environment.TEST,
        subaccount_id=SUBACCOUNT_ID,
    )
    rfq_quoter = DeltaHedgerRfqQuoter(client)
    # Run indefinitely with automatic reconnection on failure
    while True:
        try:
            await rfq_quoter.run()
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    asyncio.run(main())
