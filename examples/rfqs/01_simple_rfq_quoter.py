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
    """
    A basic RFQ quoter implementation that acts as a market maker.
    
    This class demonstrates how to:
    1. Listen for incoming RFQs from takers
    2. Price the requested instruments based on current market data
    3. Send quotes back to the takers
    4. Track quote status (filled, expired, etc.)
    
    WARNING: This is a simplified example for demonstration purposes only.
    It does NOT include proper risk management, inventory management, or hedging.
    DO NOT use this as a production trading strategy.
    """
    logger: Logger
    client: WebSocketClient
    # Dictionary to track active quotes by RFQ ID
    quotes: dict[str, PrivateSendQuoteResultSchema] = {}

    def __init__(self, client: WebSocketClient):
        self.client = client
        self.logger = client._logger

    async def price_rfq(self, rfq):
        """
        Price the legs of an RFQ based on current market prices.
        
        This simple implementation uses mark price with a small spread:
        - For buy legs (we're selling to the taker): mark_price * 1.001 (0.1% markup)
        - For sell legs (we're buying from the taker): mark_price * 0.999 (0.1% discount)
        
        A real market maker would use more sophisticated pricing that considers:
        - Order book depth and liquidity
        - Volatility and Greeks (delta, gamma, vega)
        - Inventory positions and risk limits
        - Competition from other market makers
        
        Args:
            rfq: The RFQ request containing unpriced legs to quote
            
        Returns:
            List of priced legs with calculated prices
        """
        # Price legs using current market prices NOTE! This is just an example and not a trading strategy!!!
        self.logger.info(f"  - Pricing legs for RFQ {rfq.rfq_id}...")
        priced_legs = []
        for unpriced_leg in rfq.legs:
            # Fetch current market data for this instrument
            ticker = await self.client.markets.get_ticker(instrument_name=unpriced_leg.instrument_name)

            # Use mark price as the base reference price
            base_price = ticker.mark_price

            # Apply a simple spread depending on the direction
            # If the taker wants to buy (we sell), we charge slightly above mark
            # If the taker wants to sell (we buy), we pay slightly below mark
            price = base_price * D("0.999") if unpriced_leg.direction == Direction.buy else base_price * D("1.001")

            # Round price to the instrument's tick size (minimum price increment)
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
        Callback handler for incoming RFQ updates via WebSocket.
        
        This method is called whenever there are updates to RFQs we're subscribed to.
        It filters for open RFQs, prices them, and sends quotes.
        
        Args:
            rfqs: List of RFQ updates (can include new RFQs, status changes, etc.)
        """
        # Clean up tracking for expired or cancelled RFQs
        for rfq in rfqs:
            if rfq.status in {Status.expired, Status.cancelled} and rfq.rfq_id in self.quotes:
                del self.quotes[rfq.rfq_id]
        
        # Filter to only process RFQs that are still accepting quotes
        open_rfqs = [r for r in rfqs if r.status == Status.open]
        if not open_rfqs:
            return

        # Price all open RFQs concurrently for efficiency
        priced = await asyncio.gather(*(self.price_rfq(r) for r in open_rfqs))
        # Filter out any RFQs we couldn't price (e.g., missing market data)
        quotable = [(r, legs) for r, legs in zip(open_rfqs, priced) if legs]

        if not quotable:
            return

        # Send all quotes concurrently
        # Note: We're always on the SELL side as market makers (selling quotes to takers)
        results = await asyncio.gather(
            *(self.client.rfq.send_quote(rfq_id=r.rfq_id, legs=legs, direction=Direction.sell) for r, legs in quotable),
            return_exceptions=True,  # Don't fail entire batch if one quote fails
        )
        # Track successful quotes and log failures
        for r, result in zip(quotable, results):
            rfq, _ = r
            if isinstance(result, PrivateSendQuoteResultSchema):
                self.quotes[rfq.rfq_id] = result
            else:
                self.logger.info(f"  ❌ Failed to send quote for RFQ {rfq.rfq_id}: {result}")

    async def on_quote(self, quotes_list: List[QuoteResultSchema]):
        """
        Callback handler for quote status updates.
        
        This method is called when our submitted quotes change status:
        - FILLED: A taker accepted our quote (we made a trade!)
        - EXPIRED: The RFQ expired before the taker accepted our quote
        - CANCELLED: The RFQ was cancelled by the taker
        
        In a real trading system, a FILLED status would typically trigger:
        - Risk management updates
        - Hedging activities to manage inventory
        - P&L calculations
        - Position rebalancing
        
        Args:
            quotes_list: List of quote status updates
        """
        for quote in quotes_list:
            self.logger.info(f"  - Quote {quote.quote_id} {quote.rfq_id}: {quote.status}")
            if quote.status == Status.filled and quote.rfq_id in self.quotes:
                # Our quote was accepted! Remove from tracking.
                del self.quotes[quote.rfq_id]
                self.logger.info(f"  ✓ Our quote {quote.quote_id} was accepted!")
                # Here we could proceed to perform some type of hedging or other action based on the filled quote.
            if quote.status == Status.expired and quote.rfq_id in self.quotes:
                # Quote expired without being filled. Clean up tracking.
                del self.quotes[quote.rfq_id]
                self.logger.info(f"  ✗ Our quote {quote.quote_id} expired Better luck next time!")

    async def run(self):
        """
        Main execution loop for the RFQ quoter.
        
        This method:
        1. Establishes WebSocket connection to Derive
        2. Subscribes to RFQ channel for the wallet (to receive RFQ requests)
        3. Subscribes to quotes channel for the subaccount (to track our quote statuses)
        4. Keeps the connection alive indefinitely
        """
        await self.client.connect()
        # Subscribe to RFQs directed to our wallet
        await self.client.private_channels.rfqs_by_wallet(wallet=TEST_WALLET, callback=self.on_rfq)
        # Subscribe to quote updates for our subaccount
        await self.client.private_channels.quotes_by_subaccount_id(
            subaccount_id=str(SUBACCOUNT_ID),
            callback=self.on_quote,
        )
        # Keep the connection alive and process incoming messages
        await asyncio.Event().wait()  # Keep the connection alive


async def main():
    """
    Main entry point for the simple RFQ quoter.
    
    This creates a WebSocket client and runs the quoter in a loop with error recovery.
    If the connection drops, it will automatically reconnect and resume quoting.
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
            # Allow clean shutdown with Ctrl+C
            break


if __name__ == "__main__":
    asyncio.run(main())
