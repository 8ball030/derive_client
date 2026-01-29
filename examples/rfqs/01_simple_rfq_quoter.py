"""
Example of how to act as a simple RFQ quoter that prices incoming RFQs and sends quotes.
This example connects to the WebSocket API, listens for incoming RFQs on a specified wallet,
prices the legs using current market prices, and sends quotes back to the RFQs.
It also listens for quote updates to track the status of the quotes sent.
IT SHOULD NOT BE USED AS A TRADING STRATEGY!!!
"""

import asyncio
from datetime import datetime, timezone
from typing import List

from config import ADMIN_TEST_WALLET as TEST_WALLET
from config import SESSION_KEY_PRIVATE_KEY

from derive_client import WebSocketClient
from derive_client.data_types import Environment
from derive_client.data_types.channel_models import QuoteResultSchema
from derive_client.data_types.generated_models import (
    AssetType,
    Direction,
    InstrumentPublicResponseSchema,
    LegPricedSchema,
    PrivateSendQuoteResultSchema,
    RFQResultPublicSchema,
    Status,
    TickerSlimSchema,
)
from derive_client.data_types.utils import D

SLEEP_TIME = 1
SUBACCOUNT_ID = 31049  # another subaccount of this LightAccount (test wallet)


class SimpleRfqQuoter:
    def __init__(self, client: WebSocketClient, currency: str, instrument_type: AssetType):
        self.client = client
        self.currency = currency
        self.instrument_type = instrument_type

        self.logger = client._logger
        self.quotes: dict[str, PrivateSendQuoteResultSchema] = {}

    async def _get_non_expired_instruments(self) -> list[InstrumentPublicResponseSchema]:
        """Get non-expired instruments."""

        expired = False
        return await self.client.markets.get_instruments(
            instrument_type=self.instrument_type,
            expired=expired,
            currency=self.currency,
        )

    async def _get_instrument_tickers(self) -> dict[str, TickerSlimSchema]:
        """Get instrument tickers."""

        instruments = await self._get_non_expired_instruments()

        all_tickers = {}
        for expiry in {instrument.option_details.expiry for instrument in instruments}:
            expiry_date = datetime.fromtimestamp(expiry, tz=timezone.utc).strftime("%Y%m%d")
            tickers = await self.client.markets.get_tickers(
                instrument_type=self.instrument_type,
                currency=self.currency,
                expiry_date=expiry_date,
            )
            all_tickers.update(tickers)

        self.logger.info(f"Fetched fresh tickers data for {self.currency} {self.instrument_type.name}")
        return all_tickers

    async def price_rfq(self, rfq: RFQResultPublicSchema) -> list[LegPricedSchema]:
        """Price RFQ legs using mark price with naive 0.1% spread (example only, not a trading strategy)."""

        self.logger.info(f"  - Pricing legs for RFQ {rfq.legs}...")

        # This is not optimal, but ensures we have fresh tickers to quote the RFQ, which suffices for this example.
        tickers = await self._get_instrument_tickers()

        priced_legs = []
        for unpriced_leg in rfq.legs:
            # In case the instrument is anything other than a ETH option, we defer quoting
            ticker_slim_schema = tickers.get(unpriced_leg.instrument_name)
            if not ticker_slim_schema:
                self.logger.info(f"No ticker for instrument: {unpriced_leg.instrument_name}")
                return []

            # In this simply example, we do not price the RFQ is there is no ticker.mark_price
            # Otherwise the Derive JSON RPC will return code -32602 (Invalid params: Leg price must be positive)
            ticker_mark_price = ticker_slim_schema.M
            if ticker_mark_price == D("0.0"):
                self.logger.info(f"No mark price for instrument: {unpriced_leg.instrument_name}")
                return []

            # Naive pricing, and round to tick size (required by Derive API)
            spread_multiplier = D("0.999") if unpriced_leg.direction == Direction.buy else D("1.001")
            price = ticker_mark_price * spread_multiplier

            priced_leg = LegPricedSchema(
                price=price,
                amount=unpriced_leg.amount,
                direction=unpriced_leg.direction,
                instrument_name=unpriced_leg.instrument_name,
            )
            priced_legs.append(priced_leg)

        total_price = sum(leg.price * leg.amount for leg in priced_legs)
        self.logger.info(f"  ✓ Priced legs for RFQ {rfq.rfq_id} at total price {total_price}")

        return priced_legs

    async def on_rfq(self, rfqs: List[RFQResultPublicSchema]):
        """Handle incoming RFQ updates."""

        # Clean up expired/cancelled RFQs from tracking
        for rfq in rfqs:
            if rfq.status in {Status.expired, Status.cancelled} and self.quotes.pop(rfq.rfq_id, None):
                self.logger.info(f"  🗑️  Removed {rfq.status} RFQ {rfq.rfq_id} from tracking")

        # Filter to only open RFQs
        open_rfqs = [rfq for rfq in rfqs if rfq.status == Status.open]
        if not open_rfqs:
            return

        self.logger.info(f"  📝 Processing {len(open_rfqs)} open RFQ(s)")

        # Price all open RFQs concurrently
        pricing_tasks = [self.price_rfq(rfq) for rfq in open_rfqs]
        priced_legs_list = await asyncio.gather(*pricing_tasks, return_exceptions=True)

        # Pair RFQs with their priced legs, filter out empty results
        quotable_rfqs = [(rfq, legs) for rfq, legs in zip(open_rfqs, priced_legs_list) if legs]

        if not quotable_rfqs:
            self.logger.info("  ⚠️  No quotable RFQs after pricing")
            return

        # Send all quotes concurrently
        quote_tasks = [
            self.client.rfq.send_quote(rfq_id=rfq.rfq_id, legs=legs, direction=Direction.sell)
            for rfq, legs in quotable_rfqs
        ]
        results = await asyncio.gather(*quote_tasks, return_exceptions=True)

        # Process results
        for (rfq, _), result in zip(quotable_rfqs, results):
            if isinstance(result, PrivateSendQuoteResultSchema):
                self.quotes[rfq.rfq_id] = result
                self.logger.info(f"  ✅ Sent quote for RFQ {rfq.rfq_id}")
            else:
                self.logger.info(f"  ❌ Failed to send quote for RFQ {rfq.rfq_id}: {result}")

    async def on_quote(self, quotes_list: List[QuoteResultSchema]):
        """Handle incoming quotes."""

        for quote in quotes_list:
            self.logger.info(f"  - Quote {quote.quote_id} {quote.rfq_id}: {quote.status}")

            if quote.status == Status.filled:
                self.quotes.pop(quote.rfq_id, None)
                self.logger.info(f"  ✓ Our quote {quote.quote_id} was accepted!")
                # Here we could proceed to perform some type of hedging or other action based on the filled quote.

            elif quote.status == Status.expired:
                self.quotes.pop(quote.rfq_id, None)
                self.logger.info(f"  ✗ Our quote {quote.quote_id} expired. Better luck next time!")

    async def run(self):
        """Run a RFQ quoter for ETH options."""

        await self.client.connect()
        await self.client.private_channels.rfqs_by_wallet(wallet=TEST_WALLET, callback=self.on_rfq)
        await self.client.private_channels.quotes_by_subaccount_id(
            subaccount_id=str(SUBACCOUNT_ID),
            callback=self.on_quote,
        )
        await asyncio.Event().wait()  # Keep the connection alive


async def main():
    """Run the RFQ quoter. Handling is event-driven (push/callback)"""

    client = WebSocketClient(
        session_key=SESSION_KEY_PRIVATE_KEY,
        wallet=TEST_WALLET,
        env=Environment.TEST,
        subaccount_id=SUBACCOUNT_ID,
    )

    # We setup an RFQ quoter for ETH options
    currency = "ETH"
    instrument_type = AssetType.option
    rfq_quoter = SimpleRfqQuoter(
        client=client,
        currency=currency,
        instrument_type=instrument_type,
    )

    while True:
        try:
            await rfq_quoter.run()
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    asyncio.run(main())
