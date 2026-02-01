"""
Example of how to act as a simple RFQ quoter that prices incoming RFQs and sends quotes.
This example connects to the WebSocket API, listens for incoming RFQs on a specified wallet,
prices the legs using current market prices, and sends quotes back to the RFQs.
It also listens for quote updates to track the status of the quotes sent.
IT SHOULD NOT BE USED AS A TRADING STRATEGY!!!
"""

import asyncio
import warnings
from logging import Logger
from typing import List

from config import ADMIN_TEST_WALLET as TEST_WALLET
from config import SESSION_KEY_PRIVATE_KEY

from derive_client import WebSocketClient
from derive_client.data_types import Environment
from derive_client.data_types.channel_models import QuoteResultSchema
from derive_client.data_types.generated_models import (
    Direction,
    LegPricedSchema,
    PrivateSendQuoteResultSchema,
    RFQResultPublicSchema,
    Status,
)
from derive_client.data_types.utils import D

warnings.filterwarnings("ignore", category=DeprecationWarning)

SLEEP_TIME = 1
SUBACCOUNT_ID = 31049


class SimpleRfqQuoter:
    logger: Logger
    client: WebSocketClient
    quotes: dict[str, PrivateSendQuoteResultSchema] = {}

    def __init__(self, client: WebSocketClient):
        self.client = client
        self.logger = client._logger

    async def price_rfq(self, rfq):
        # Price legs using current market prices NOTE! This is just an example and not a trading strategy!!!
        self.logger.info(f"  - Pricing legs for RFQ {rfq.rfq_id}...")
        priced_legs = []
        for unpriced_leg in rfq.legs:
            ticker = await self.client.markets.get_ticker(instrument_name=unpriced_leg.instrument_name)

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

        priced = await asyncio.gather(*(self.price_rfq(r) for r in open_rfqs))
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
            if quote.status == Status.filled and quote.rfq_id in self.quotes:
                del self.quotes[quote.rfq_id]
                self.logger.info(f"  ✓ Our quote {quote.quote_id} was accepted!")
                # Here we could proceed to perform some type of hedging or other action based on the filled quote.
            if quote.status == Status.expired and quote.rfq_id in self.quotes:
                del self.quotes[quote.rfq_id]
                self.logger.info(f"  ✗ Our quote {quote.quote_id} expired. Better luck next time!")

    async def run(self):
        await self.client.connect()
        await self.client.private_channels.rfqs_by_wallet(wallet=TEST_WALLET, callback=self.on_rfq)
        await self.client.private_channels.quotes_by_subaccount_id(
            subaccount_id=str(SUBACCOUNT_ID),
            callback=self.on_quote,
        )
        await asyncio.Event().wait()  # Keep the connection alive


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
    rfq_quoter = SimpleRfqQuoter(client)
    while True:
        try:
            await rfq_quoter.run()
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    asyncio.run(main())
