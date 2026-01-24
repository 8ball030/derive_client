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
    OrderType,
    PositionResponseSchema,
    PrivateSendQuoteResultSchema,
    PublicGetTickerResultSchema,
    RFQResultPublicSchema,
    Status,
    TradeResponseSchema,
    TxStatus,
)
from derive_client.data_types.utils import D

warnings.filterwarnings("ignore", category=DeprecationWarning)

SLEEP_TIME = 1
SUBACCOUNT_ID = 31049

UNDERLYING_TO_QUOTE = "ETH"

# Hedging parameters
MAX_DELTA_TO_QUOTE = D("100.0")
MIN_DELTA_EXPOSURE = D("-0.1")
MAX_DELTA_EXPOSURE = D("0.1")
HEDGE_INTERVAL = 30  # seconds


class DeltaQuoterStrategy:
    quote_tickers: dict[str, PublicGetTickerResultSchema] = {}
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
            if leg.instrument_name not in self.quote_tickers:
                # fetch and cache ticker
                ticker = await self.client.markets.get_ticker(instrument_name=leg.instrument_name)
                self.quote_tickers[leg.instrument_name] = ticker
            else:
                ticker = self.quote_tickers[leg.instrument_name]
            if not ticker.option_pricing:
                self.logger.info(
                    f"    - Cannot calculate delta for leg {leg.instrument_name} due to missing option pricing data."
                )
                is_error = True
                break
            leg_delta = ticker.option_pricing.delta * leg.amount
            if leg.direction == Direction.buy:
                total_delta += leg_delta
            else:
                total_delta -= leg_delta
        return total_delta, is_error

    async def price_legs(self, rfq: RFQResultPublicSchema) -> List[LegPricedSchema]:
        # Implement logic to price the legs of the RFQ
        priced_legs = []
        expected_delta = D("0.0")  # delta that selling the RFQ would add to the portfolio
        shouldnt_price = False
        expected_delta, is_error = await self.calculate_delta_from_quote(rfq)
        if is_error:
            return []
        for unpriced_leg in rfq.legs:
            ticker = self.quote_tickers[unpriced_leg.instrument_name]
            expected_delta += unpriced_leg.amount * ticker.option_pricing.delta  # type: ignore
            base_price = ticker.mark_price
            price = base_price * D("0.999") if unpriced_leg.direction == Direction.buy else base_price * D("1.001")
            price = price.quantize(ticker.tick_size)
            priced_leg = LegPricedSchema(
                price=price,
                amount=unpriced_leg.amount,
                direction=unpriced_leg.direction,
                instrument_name=unpriced_leg.instrument_name,
            )
            priced_legs.append(priced_leg)
        return priced_legs if not shouldnt_price else []

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
    quotes: dict[str, PrivateSendQuoteResultSchema] = {}
    is_hedging: bool = False

    def __init__(self, client: WebSocketClient):
        self.client = client
        self.logger = client._logger

    async def create_quote(self, rfq):
        # Price legs using current market prices NOTE! This is just an example and not a trading strategy!!!
        delta_quoter_strategy = DeltaQuoterStrategy(self.client, self.logger)
        if not await delta_quoter_strategy.should_quote(rfq):
            self.logger.info(f"  - Skipping quoting for RFQ {rfq.rfq_id} based on strategy decision.")
            return []
        priced_legs = await delta_quoter_strategy.price_legs(rfq)
        self.logger.info(
            f"  ✓ Priced legs for RFQ {rfq.rfq_id} at total price {sum(leg.price * leg.amount for leg in priced_legs)}"
        )
        return priced_legs

    async def on_rfq(self, rfqs: List[RFQResultPublicSchema]):
        for rfq in rfqs:
            if rfq.status in {Status.expired, Status.cancelled} and rfq.rfq_id in self.quotes:
                del self.quotes[rfq.rfq_id]
        open_rfqs = [r for r in rfqs if r.status == Status.open]
        if not open_rfqs:
            return

        priced = await asyncio.gather(*(self.create_quote(r) for r in open_rfqs))
        quotable = [(r, legs) for r, legs in zip(open_rfqs, priced) if legs]

        if not quotable:
            return

        results = await asyncio.gather(
            *(self.client.rfq.send_quote(rfq_id=r.rfq_id, legs=legs, direction=Direction.sell) for r, legs in quotable),
            return_exceptions=True,
        )
        for r, result in zip(quotable, results):
            rfq, _ = r
            if isinstance(result, PrivateSendQuoteResultSchema):
                self.quotes[rfq.rfq_id] = result
            else:
                self.logger.info(f"  ❌ Failed to send quote for RFQ {rfq.rfq_id}: {result}")

    async def on_quote(self, quotes_list: List[QuoteResultSchema]):
        for quote in quotes_list:
            self.logger.info(f"  - Quote {quote.quote_id} {quote.rfq_id}: {quote.status}")
            if quote.status == Status.expired and quote.rfq_id in self.quotes:
                del self.quotes[quote.rfq_id]
                self.logger.info(f"  ✗ Our quote {quote.quote_id} expired Better luck next time!")
            elif quote.status == Status.filled and quote.rfq_id in self.quotes:
                del self.quotes[quote.rfq_id]
                self.logger.info(f"  ✓ Our quote {quote.quote_id} was accepted!")

    async def execute_hedge(self, delta_to_hedge: Decimal):
        self.is_hedging = True
        instrument_name = f"{UNDERLYING_TO_QUOTE}-PERP"
        ticker = await self.client.markets.get_ticker(instrument_name=instrument_name)
        trade_direction = Direction.buy if delta_to_hedge < 0 else Direction.sell
        price = (
            ticker.mark_price * D("1.01") if trade_direction == Direction.buy else ticker.mark_price * D("0.99")
        )  # to make sure we fill
        trade_amount = abs(delta_to_hedge)
        if trade_amount < ticker.tick_size:
            self.logger.info(f"    - Hedge amount {trade_amount} is below min order size {ticker.tick_size}, skipping.")
            self.is_hedging = False
            return
        self.logger.info(f"    - Executing hedge for delta amount: {delta_to_hedge} in direction {trade_direction}")
        await self.client.orders.create(
            amount=trade_amount,
            instrument_name=instrument_name,
            limit_price=price.quantize(ticker.tick_size),
            direction=trade_direction,
            order_type=OrderType.limit,
            reduce_only=False,
        )
        self.is_hedging = False

    async def on_trade(self, trades: List[TradeResponseSchema], timeout_s=30):
        """Handle trade updates if needed for more advanced hedging logic."""

        trades_to_check = []
        settled_trades = []
        for trade in trades:
            self.logger.info(
                f"  - {trade.direction} executed: market {trade.instrument_name} at price {trade.trade_price} "
                + f"amount {trade.trade_amount} status: {trade.tx_status}"
            )
            # Wait for pending trades a little while
            if trade.tx_status in {TxStatus.pending, TxStatus.requested}:
                trades_to_check.append(trade)
            elif trade.tx_status == TxStatus.settled:
                settled_trades.append(trade)
            else:
                self.logger.info(f"    - Trade {trade.trade_id} has unexpected status {trade.tx_status}, skipping.")

        for trade in trades_to_check:
            waited_s = 0
            all_settled = False
            while not all_settled and waited_s < timeout_s:
                await asyncio.sleep(1)
                waited_s += 1
                trade_trades = await self.client.trades.list_private(order_id=trade.order_id)
                settled = []
                for trade_part in trade_trades:
                    if trade_part.tx_status == TxStatus.settled:
                        settled.append(trade)
                if len(settled) == len(trade_trades):
                    all_settled = True
                    settled_trades.append(trade)
                    break
        if settled_trades:
            delta_quoter_strategy = DeltaQuoterStrategy(self.client, self.logger)
            delta_to_hedge = await delta_quoter_strategy.calculate_portfolio_delta()
            await self.execute_hedge(delta_to_hedge)

    async def run(self):
        await self.client.connect()
        await self.client.private_channels.rfqs_by_wallet(wallet=TEST_WALLET, callback=self.on_rfq)
        await self.client.private_channels.quotes_by_subaccount_id(
            subaccount_id=str(SUBACCOUNT_ID),
            callback=self.on_quote,
        )
        await self.client.private_channels.trades_by_subaccount_id(
            subaccount_id=str(SUBACCOUNT_ID),
            callback=self.on_trade,
        )
        await self.run_portfolio_hedging()
        while True:
            await asyncio.sleep(HEDGE_INTERVAL)
            if not self.is_hedging:
                await self.run_portfolio_hedging()

    async def run_portfolio_hedging(self):
        # Implement periodic portfolio delta checking and hedging if necessary
        delta_hedger_strategy = DeltaQuoterStrategy(self.client, self.logger)
        current_delta = await delta_hedger_strategy.calculate_portfolio_delta()
        self.logger.info(f"  - Current portfolio delta: {current_delta}")
        if current_delta < MIN_DELTA_EXPOSURE or current_delta > MAX_DELTA_EXPOSURE:
            self.logger.info("  - Portfolio delta out of bounds, executing hedge.")
            await self.execute_hedge(current_delta)


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
