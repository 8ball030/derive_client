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

    This function demonstrates the complete RFQ (Request for Quote) lifecycle from the taker's perspective:
    1. Connects to the WebSocket API
    2. Sends an RFQ with unpriced legs (instruments and amounts without prices)
    3. Subscribes to quote updates and tracks the best available quote
    4. Executes the best quote after waiting for market makers to respond

    Args:
        legs: List of unpriced legs representing the instruments and amounts to trade
              Each leg specifies instrument_name, amount, and direction (buy/sell)
    """
    # Initialize the WebSocket client with authentication credentials
    # The client will be used to communicate with the Derive API
    client = WebSocketClient(
        session_key=SESSION_KEY_PRIVATE_KEY,  # Private key for signing requests
        wallet=OWNER_TEST_WALLET,              # Ethereum wallet address
        env=Environment.TEST,                  # Use test environment
        subaccount_id=TAKER_SUBACCOUNT_ID,     # Subaccount to execute trades under
    )
    await client.connect()
    logger = get_logger()

    # Send the RFQ to the network
    # This broadcasts the request to all market makers subscribed to the wallet
    rfq_result = await client.rfq.send_rfq(legs=legs)
    logger.info(f"✓ RFQ created: {rfq_result.rfq_id}")

    # Track the best quote received from market makers
    # This will be updated as better quotes arrive via the WebSocket channel
    best_quote: QuoteResultPublicSchema | None = None

    def handle_quote(quotes: List[BestQuoteChannelResultSchema]):
        """
        Callback function that handles incoming quote updates.
        
        This is called whenever a new quote is received or an existing quote is updated.
        It extracts the best quote from the update and calculates its total price.
        """
        nonlocal best_quote
        for quote in quotes:
            if quote.result and quote.result.best_quote:
                # Update our tracking variable with the latest best quote
                best_quote = quote.result.best_quote
                # Calculate total price by summing price * amount for all legs
                total_price = sum(leg.price * leg.amount for leg in best_quote.legs)
                logger.info(f"✓ Best quote received: {total_price}")

    # Subscribe to the best quotes channel for this subaccount
    # This establishes a WebSocket subscription that will call handle_quote
    # whenever market makers submit quotes for our RFQ
    await client.private_channels.best_quotes_by_subaccount_id(
        subaccount_id=str(TAKER_SUBACCOUNT_ID),
        callback=handle_quote,
    )

    # Wait for market makers to respond with quotes
    # In a production system, you might want to wait for a specific number of quotes
    # or use a more sophisticated decision mechanism
    await asyncio.sleep(10)

    if not best_quote:
        logger.error("✗ No quotes received")
        return

    # Execute the best quote we received
    # Note: We take the opposite direction from the quote's direction
    # If the quote is buying from us (Direction.buy), we sell to them (Direction.sell)
    execute_direction = Direction.sell if best_quote.direction == Direction.buy else Direction.buy
    await client.rfq.execute_quote(
        direction=execute_direction,
        legs=best_quote.legs,              # Use the priced legs from the quote
        rfq_id=best_quote.rfq_id,          # Reference to our original RFQ
        quote_id=best_quote.quote_id,      # Specific quote we're accepting
    )
    logger.info(
        f"✓ Quote {best_quote.quote_id} executed at total price: "
        + f"{sum(leg.price * leg.amount for leg in best_quote.legs)}"
    )


if __name__ == "__main__":
    # Example usage: Create a simple RFQ for a single ETH put option
    # In a real scenario, you might include multiple legs for complex strategies
    # like spreads, straddles, or butterflies
    legs = [
        LegUnpricedSchema(
            instrument_name="ETH-20260327-4800-P",  # ETH put option expiring March 27, 2026, strike 4800
            amount=D("1"),                           # Trade 1 contract
            direction=Direction.sell,                # We want to sell this option
        ),
        # Additional legs commented out - these show how to create multi-leg strategies:
        # - Multiple puts at different strikes (e.g., put spreads)
        # - Combination of buys and sells (e.g., iron condors)
        # LegUnpricedSchema(
        #     instrument_name="ETH-20260125-3050-P",
        #     amount=D("1.0"),
        #     direction=Direction.sell,
        # ),
        # LegUnpricedSchema(
        #     instrument_name="ETH-20260125-2900-P",
        #     amount=D("1.0"),
        #     direction=Direction.sell,
        # ),
        # LegUnpricedSchema(
        #     instrument_name="ETH-20260125-3000-P",
        #     amount=D("1.0"),
        #     direction=Direction.buy,
        # ),
        # LegUnpricedSchema(
        #     instrument_name="ETH-20260126-2900-P",
        #     amount=D("1.0"),
        #     direction=Direction.buy,
        # ),
    ]
    asyncio.run(
        create_and_execute_rfq(
            legs=legs,
        )
    )
