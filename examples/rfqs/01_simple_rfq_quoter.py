"""
Example of how to act as a simple RFQ quoter that prices incoming RFQs and sends quotes.

This example demonstrates the market maker side of RFQ trading:
- Connects to the WebSocket API and listens for incoming RFQs on a specified wallet
- Prices the legs using current market prices with a small spread
- Sends quotes back to the RFQs
- Listens for quote updates to track the status of quotes sent (filled, expired, etc.)

IMPORTANT: This is a simplified example for educational purposes.
IT SHOULD NOT BE USED AS A TRADING STRATEGY!!!
The pricing logic here does not account for:
- Risk management (position limits, exposure limits)
- Proper spread calculation based on volatility and liquidity
- Greeks hedging (delta, gamma, vega, theta)
- Inventory management
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
    """
    A simple RFQ quoter that listens for incoming RFQs and responds with quotes.

    This class demonstrates the basic flow of:
    1. Receiving RFQs from the exchange
    2. Pricing the requested instruments
    3. Sending quotes back to the taker
    4. Tracking quote status updates
    """

    logger: Logger
    client: WebSocketClient
    quotes: dict[str, PrivateSendQuoteResultSchema] = {}  # Track all active quotes by RFQ ID

    def __init__(self, client: WebSocketClient):
        self.client = client
        self.logger = client._logger

    async def price_rfq(self, rfq):
        """
        Price all legs of an RFQ using a simple strategy based on mark prices.

        Pricing strategy:
        - For legs where we would BUY from the taker: Quote 0.1% below mark price (we pay less)
        - For legs where we would SELL to the taker: Quote 0.1% above mark price (we receive more)

        This ensures we make a small profit on each leg, but is NOT a proper trading strategy.
        A real market maker would consider:
        - Current bid-ask spread
        - Market volatility
        - Position exposure and risk limits
        - Greeks hedging costs

        Returns:
            List of priced legs, or empty list if pricing fails
        """
        # Price legs using current market prices NOTE! This is just an example and not a trading strategy!!!
        self.logger.info(f"  - Pricing legs for RFQ {rfq.rfq_id}...")
        priced_legs = []
        for unpriced_leg in rfq.legs:
            # Fetch current market data for this instrument
            ticker = await self.client.markets.get_ticker(instrument_name=unpriced_leg.instrument_name)

            base_price = ticker.mark_price

            # Apply a simple spread: Quote slightly favorable prices to us
            # If taker wants to BUY (we SELL), we quote 0.1% above mark
            # If taker wants to SELL (we BUY), we quote 0.1% below mark
            price = base_price * D("0.999") if unpriced_leg.direction == Direction.buy else base_price * D("1.001")

            # Round to the instrument's tick size (minimum price increment)
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
        """
        Handle incoming RFQ updates.

        This callback is triggered when:
        - New RFQs are created
        - Existing RFQs change status (expired, cancelled, etc.)

        Flow:
        1. Clean up any quotes for expired/cancelled RFQs
        2. Filter for open RFQs that need quotes
        3. Price all open RFQs in parallel
        4. Send quotes for all successfully priced RFQs
        """
        # First, clean up quotes for RFQs that are no longer active
        for rfq in rfqs:
            if rfq.status in {Status.expired, Status.cancelled} and rfq.rfq_id in self.quotes:
                del self.quotes[rfq.rfq_id]

        # Filter for RFQs that are still open and need quotes
        open_rfqs = [r for r in rfqs if r.status == Status.open]
        if not open_rfqs:
            return

        # Price all open RFQs in parallel for efficiency
        priced = await asyncio.gather(*(self.price_rfq(r) for r in open_rfqs))
        quotable = [(r, legs) for r, legs in zip(open_rfqs, priced) if legs]

        if not quotable:
            return

        # Send quotes for all successfully priced RFQs
        # We always quote as SELL direction (we're the market maker taking the other side)
        results = await asyncio.gather(
            *(self.client.rfq.send_quote(rfq_id=r.rfq_id, legs=legs, direction=Direction.sell) for r, legs in quotable),
            return_exceptions=True,
        )
        # Track successfully sent quotes
        for r, result in zip(quotable, results):
            rfq, _ = r
            if isinstance(result, PrivateSendQuoteResultSchema):
                self.quotes[rfq.rfq_id] = result
            else:
                self.logger.info(f"  ❌ Failed to send quote for RFQ {rfq.rfq_id}: {result}")

    async def on_quote(self, quotes_list: List[QuoteResultSchema]):
        """
        Handle quote status updates.

        This callback is triggered when quotes we sent change status:
        - FILLED: The taker executed our quote (we have a trade!)
        - EXPIRED: The quote expired before being executed
        - CANCELLED: The quote was cancelled

        When a quote is filled, this is where you would typically:
        - Update position tracking
        - Initiate hedging trades
        - Update risk metrics
        """
        for quote in quotes_list:
            self.logger.info(f"  - Quote {quote.quote_id} {quote.rfq_id}: {quote.status}")
            if quote.status == Status.filled and quote.rfq_id in self.quotes:
                del self.quotes[quote.rfq_id]
                self.logger.info(f"  ✓ Our quote {quote.quote_id} was accepted!")
                # Here we could proceed to perform some type of hedging or other action based on the filled quote.
                # For example: hedge delta exposure, update inventory, adjust risk limits, etc.
            if quote.status == Status.expired and quote.rfq_id in self.quotes:
                del self.quotes[quote.rfq_id]
                self.logger.info(f"  ✗ Our quote {quote.quote_id} expired. Better luck next time!")

    async def run(self):
        """
        Main execution loop for the RFQ quoter.

        Sets up WebSocket connections and subscriptions:
        1. Subscribe to RFQs for our wallet - receive incoming RFQ requests
        2. Subscribe to quotes for our subaccount - receive status updates on our quotes
        3. Keep the connection alive indefinitely
        """
        await self.client.connect()
        # Subscribe to RFQs targeted at our wallet
        await self.client.private_channels.rfqs_by_wallet(wallet=TEST_WALLET, callback=self.on_rfq)
        # Subscribe to quote updates for quotes we've sent
        await self.client.private_channels.quotes_by_subaccount_id(
            subaccount_id=str(SUBACCOUNT_ID),
            callback=self.on_quote,
        )
        await asyncio.Event().wait()  # Keep the connection alive indefinitely


async def main():
    """
    Initialize and run the simple RFQ quoter.

    This will:
    1. Create a WebSocket client connected to the test environment
    2. Initialize the RFQ quoter
    3. Run continuously, quoting on all incoming RFQs
    4. Automatically reconnect if the connection drops
    """

    client = WebSocketClient(
        session_key=SESSION_KEY_PRIVATE_KEY,
        wallet=TEST_WALLET,
        env=Environment.TEST,
        subaccount_id=SUBACCOUNT_ID,
    )
    rfq_quoter = SimpleRfqQuoter(client)
    # Run indefinitely with automatic reconnection on failure
    while True:
        try:
            await rfq_quoter.run()
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    asyncio.run(main())
