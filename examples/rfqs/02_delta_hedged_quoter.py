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
UNDERLYING_TO_QUOTE = "ETH"
QUOTE_SPREAD_BPS = D("0")
FALLBACK_TO_MARK_PRICE_PREMIUM_BPS = D("1000")  # 10% premium if no book price available

# Hedging parameters
MAX_DELTA_TO_QUOTE = D("100.0")
MIN_DELTA_EXPOSURE = D("-0.1")
MAX_DELTA_EXPOSURE = D("0.1")
HEDGE_INTERVAL = 30  # seconds
HEDGE_ORDER_LABEL = "delta_hedge"
HEDGE_ORDER_TIMEOUT_S = 60


class DeltaQuoterStrategy:
    client: WebSocketClient
    logger: Logger

    def __init__(self, client: WebSocketClient, logger: Logger):
        self.client = client
        self.logger = logger

    async def should_quote(self, rfq: RFQResultPublicSchema) -> bool:
        # Implement logic to decide whether to quote the RFQ based on current portfolio delta exposure
        # we have a simple descrimintaor here that only quotes RFQs on a specific underlying
        is_for_target_underlying = all([UNDERLYING_TO_QUOTE in leg.instrument_name for leg in rfq.legs])

        def is_option(instrument_name: str) -> bool:
            return instrument_name.endswith(("-C", "-P"))

        is_only_options = all([is_option(leg.instrument_name) for leg in rfq.legs])
        if not is_for_target_underlying or not is_only_options:
            return False

        total_delta, is_error = await self.calculate_delta_from_quote(rfq)
        self.logger.info(f"    - RFQ {rfq.rfq_id} total delta impact would be {total_delta}")

        return all(
            [
                is_for_target_underlying,
                is_only_options,
                abs(total_delta) <= MAX_DELTA_TO_QUOTE,
                not is_error,
            ]
        )

    async def calculate_delta_from_quote(
        self, quote: QuoteResultSchema | RFQResultPublicSchema
    ) -> tuple[Decimal, bool]:
        """Calculates the hedge amount needed to neutralize delta exposure from the quote."""
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
        # Implement logic to price the legs of the RFQ
        priced_legs = []
        expected_delta, is_error = await self.calculate_delta_from_quote(rfq)
        if is_error or abs(expected_delta) > MAX_DELTA_TO_QUOTE:
            return []
        for unpriced_leg in rfq.legs:
            ticker: PublicGetTickerResultSchema = await self.client.markets.get_ticker(
                instrument_name=unpriced_leg.instrument_name
            )
            # we base on the book price here
            if unpriced_leg.direction == Direction.buy:
                if ticker.best_ask_price is None or ticker.best_ask_price == D("0"):
                    self.logger.info(
                        f"    - fallback pricing used as no mark price for: {unpriced_leg.instrument_name}."
                    )
                    base_price = ticker.mark_price * (D("1") + FALLBACK_TO_MARK_PRICE_PREMIUM_BPS / D("10000"))
                else:
                    base_price = ticker.best_ask_price
            else:
                if ticker.best_bid_price is None or ticker.best_bid_price == D("0"):
                    self.logger.info(
                        f"    - fallback pricing used as no mark price for: {unpriced_leg.instrument_name}."
                    )
                    base_price = ticker.mark_price * (D("1") - FALLBACK_TO_MARK_PRICE_PREMIUM_BPS / D("10000"))
                else:
                    base_price = ticker.best_bid_price
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
    client: WebSocketClient
    logger: Logger

    def __init__(self, client: WebSocketClient, logger: Logger):
        self.client = client
        self.logger = logger

    async def calculate_portfolio_delta(self) -> Decimal:
        # Implement logic to calculate the current portfolio delta
        positions: List[PositionResponseSchema] = await self.client.positions.list(
            is_open=True, currency=UNDERLYING_TO_QUOTE
        )
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
        option_deltas = sum([p.delta * p.amount for p in option_positions])
        perp_delta = sum([p.amount for p in perp_positions])  # Perp has delta of 1 per unit
        spot_delta = sum([p.amount for p in spot_positions])  # Spot has delta of 1 per unit
        total_delta = option_deltas + perp_delta + spot_delta
        return Decimal(total_delta)


class DeltaHedgerRfqQuoter:
    logger: Logger
    client: WebSocketClient

    def __init__(self, client: WebSocketClient):
        self.client = client
        self.logger = client._logger
        self.portfolio_delta_calculator = PortfolioDeltaCalculator(client, self.logger)
        self.delta_quoter_strategy = DeltaQuoterStrategy(client, self.logger)
        self.quotes: dict[str, PrivateSendQuoteResultSchema] = {}
        # hedging state
        self.hedging_queue = asyncio.Queue()
        self.hedger_task: asyncio.Task[None]
        self.hedge_order: OrderResponseSchema | None = None
        self.hedge_lock = asyncio.Lock()
        # state locks
        self.quoting_lock = asyncio.Lock()

    async def create_quote(self, rfq):
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
        price = ticker.best_bid_price if trade_direction == Direction.sell else ticker.best_ask_price
        if price is None or price == D("0"):
            price = ticker.mark_price
        trade_amount = abs(delta_to_hedge)
        if trade_amount < ticker.minimum_amount:
            self.logger.info(
                f"    - Hedge amount {trade_amount} is below min order size {ticker.minimum_amount}, skipping."
            )
            return
        self.logger.info(f"    - Executing hedge for delta amount: {delta_to_hedge} in direction {trade_direction}")
        self.hedge_order = await self.client.orders.create(
            amount=trade_amount,
            instrument_name=instrument_name,
            limit_price=price.quantize(ticker.tick_size),
            direction=trade_direction,
            order_type=OrderType.limit,
            reduce_only=False,
            label=HEDGE_ORDER_LABEL,
            reject_timestamp=int((datetime.now(UTC) + timedelta(seconds=HEDGE_ORDER_TIMEOUT_S)).timestamp() * 1000),
        )

    async def on_trade_settlement(self, trades: List[TradeResponseSchema]):
        """Handle trade updates if needed for more advanced hedging logic."""

        rfq_trades = []
        for trade in trades:
            self.logger.info(
                f"  - {trade.instrument_name}-{trade.direction} {trade.trade_amount} at {trade.trade_price}"
            )
            if trade.quote_id:
                rfq_trades.append(trade)
        if rfq_trades:
            self.logger.info(f"  ✓ Detected {len(rfq_trades)} RFQ trades settled, re-evaluating portfolio delta.")
            await self.hedging_queue.put(await self.portfolio_delta_calculator.calculate_portfolio_delta())

    async def on_order(self, orders: List[OrderResponseSchema]):
        """Handle order updates if needed for more advanced hedging logic."""
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
                self.hedge_order = None
                await self.hedging_queue.put(await self.portfolio_delta_calculator.calculate_portfolio_delta())

    async def run(self):
        await self.client.connect()
        await self.client.private_channels.rfqs_by_wallet(wallet=TEST_WALLET, callback=self.on_rfq)
        await self.client.private_channels.quotes_by_subaccount_id(
            subaccount_id=str(SUBACCOUNT_ID),
            callback=self.on_quote,
        )
        await self.client.private_channels.trades_tx_status_by_subaccount_id(
            subaccount_id=SUBACCOUNT_ID,
            callback=self.on_trade_settlement,
            tx_status=TxStatus4.settled,
        )
        await self.client.private_channels.orders_by_subaccount_id(
            subaccount_id=str(SUBACCOUNT_ID),
            callback=self.on_order,
        )
        self.hedger_task = asyncio.create_task(self.portfolio_hedging_task())
        # we send a request to evaluate the current delta on startup
        await self.hedging_queue.put(await self.portfolio_delta_calculator.calculate_portfolio_delta())
        await asyncio.Event().wait()

    async def portfolio_hedging_task(self):
        # Implement periodic portfolio delta checking and hedging if necessary

        last_check_time = datetime.now(UTC)

        while True:
            portfolio_delta: Decimal | None = None
            while True:
                try:
                    portfolio_delta = self.hedging_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

            if portfolio_delta is None:
                now = datetime.now(UTC)
                if (now - last_check_time).total_seconds() >= HEDGE_INTERVAL:
                    portfolio_delta = await self.portfolio_delta_calculator.calculate_portfolio_delta()
                    last_check_time = now
                else:
                    await asyncio.sleep(1)
                    continue

            async with self.hedge_lock:
                if portfolio_delta < MIN_DELTA_EXPOSURE or portfolio_delta > MAX_DELTA_EXPOSURE:
                    delta_to_hedge = -portfolio_delta
                    self.logger.info(
                        f"  - Portfolio delta {portfolio_delta} outside exposure limits, hedging {delta_to_hedge}."
                    )
                    await self.execute_hedge(delta_to_hedge)


async def main():
    """
    Sample of polling for RFQs and printing their status.
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
            break


if __name__ == "__main__":
    asyncio.run(main())
