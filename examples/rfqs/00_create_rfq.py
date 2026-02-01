"""
Simple demonstration of creating and executing an RFQ.
"""

import asyncio
from typing import List

from config import OWNER_TEST_WALLET, SESSION_KEY_PRIVATE_KEY, TAKER_SUBACCOUNT_ID

from derive_client import WebSocketClient
from derive_client.data_types import Environment
from derive_client.data_types.channel_models import BestQuoteChannelResultSchema
from derive_client.data_types.generated_models import Direction, LegUnpricedSchema, QuoteResultPublicSchema
from derive_client.data_types.utils import D
from derive_client.utils.logger import get_logger


async def create_and_execute_rfq(
    legs: List[LegUnpricedSchema],
):
    """
    Create an RFQ, wait for quotes, and execute the best one.

    Args:
        legs: List of unpriced legs representing the instruments and amounts to trade.
              Each leg specifies the instrument name, amount, and direction (buy/sell).
    
    Flow:
        1. Initialize WebSocket client and connect to the exchange
        2. Send RFQ (Request for Quote) with the specified legs
        3. Subscribe to the best quotes channel to receive quote updates
        4. Wait for market makers to respond with their quotes
        5. Execute the best received quote if available
    """
    # Initialize the WebSocket client with authentication credentials and connect to the test environment
    client = WebSocketClient(
        session_key=SESSION_KEY_PRIVATE_KEY,
        wallet=OWNER_TEST_WALLET,
        env=Environment.TEST,
        subaccount_id=TAKER_SUBACCOUNT_ID,
    )
    await client.connect()
    logger = get_logger()

    # Send the RFQ to the exchange - this broadcasts the request to all market makers
    # who can then respond with their quotes
    rfq_result = await client.rfq.send_rfq(legs=legs)
    logger.info(f"✓ RFQ created: {rfq_result.rfq_id}")

    # Track the best quote received from market makers
    # This will be updated as better quotes arrive
    best_quote: QuoteResultPublicSchema | None = None

    def handle_quote(quotes: List[BestQuoteChannelResultSchema]):
        """
        Callback function that processes incoming quote updates.
        Each time a better quote arrives, we update our tracked best quote.
        """
        nonlocal best_quote
        for quote in quotes:
            if quote.result and quote.result.best_quote:
                best_quote = quote.result.best_quote
                # Calculate the total price across all legs for logging
                total_price = sum(leg.price * leg.amount for leg in best_quote.legs)
                logger.info(f"✓ Best quote received: {total_price}")

    # Subscribe to the best quotes channel for this subaccount
    # This allows us to receive real-time updates as market makers send quotes
    await client.private_channels.best_quotes_by_subaccount_id(
        subaccount_id=str(TAKER_SUBACCOUNT_ID),
        callback=handle_quote,
    )

    # Wait for market makers to respond with their quotes
    # In a production system, you might want to wait until the RFQ expires or use a different timing strategy
    await asyncio.sleep(10)

    if not best_quote:
        logger.error("✗ No quotes received")
        return

    # Execute the best quote we received
    # Note: We must take the opposite direction of the quote
    # If the market maker is buying (quote.direction == buy), we must sell to them
    execute_direction = Direction.sell if best_quote.direction == Direction.buy else Direction.buy
    await client.rfq.execute_quote(
        direction=execute_direction,
        legs=best_quote.legs,
        rfq_id=best_quote.rfq_id,
        quote_id=best_quote.quote_id,
    )
    # Log the successful execution with the final price
    logger.info(
        f"✓ Quote {best_quote.quote_id} executed at total price: "
        + f"{sum(leg.price * leg.amount for leg in best_quote.legs)}"
    )


if __name__ == "__main__":
    # Example usage: Create an RFQ to sell 1 ETH put option
    # This will:
    # 1. Send the RFQ to market makers
    # 2. Wait for quotes to come in
    # 3. Execute the best quote automatically
    legs = [
        LegUnpricedSchema(
            instrument_name="ETH-20260327-4800-P",  # ETH put option expiring March 27, 2026 with strike 4800
            amount=D("1"),  # Trade 1 contract
            direction=Direction.sell,  # We want to sell this option
        ),
    ]
    asyncio.run(
        create_and_execute_rfq(
            legs=legs,
        )
    )
