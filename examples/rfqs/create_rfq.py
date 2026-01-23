"""
Simple demonstration of creating and executing an RFQ.
"""

import asyncio
from typing import List

from config import OWNER_TEST_WALLET, SESSION_KEY_PRIVATE_KEY, TAKER_SUBACCOUNT_ID

from derive_client import WebSocketClient
from derive_client.data_types import Environment
from derive_client.data_types.channel_models import BestQuoteChannelResultSchema
from derive_client.data_types.generated_models import Direction, LegUnpricedSchema
from derive_client.data_types.utils import D
from derive_client.utils.logger import get_logger


async def create_and_execute_rfq(
    instrument: str,
    side: str,
    amount: float,
):
    """
    Create an RFQ, wait for quotes, and execute the best one.

    Args:
        instrument: Instrument name (e.g. "ETH-30JUN23-1500-C")
        side: "buy" or "sell"
        amount: Contract amount
    """
    # Initialize client
    client = WebSocketClient(
        session_key=SESSION_KEY_PRIVATE_KEY,
        wallet=OWNER_TEST_WALLET,
        env=Environment.TEST,
        subaccount_id=TAKER_SUBACCOUNT_ID,
    )
    await client.connect()
    logger = get_logger()

    # Send RFQ
    direction = Direction.buy if side.lower() == "buy" else Direction.sell
    rfq_result = await client.rfq.send_rfq(
        legs=[
            LegUnpricedSchema(
                amount=D(amount),
                instrument_name=instrument,
                direction=direction,
            )
        ],
    )
    logger.info(f"✓ RFQ created: {rfq_result.rfq_id}")

    # Track best quote
    best_quote = None

    def handle_quote(quotes: List[BestQuoteChannelResultSchema]):
        nonlocal best_quote
        for quote in quotes:
            if quote.result and quote.result.best_quote:
                best_quote = quote.result.best_quote
                total_price = sum(leg.price * leg.amount for leg in best_quote.legs)
                logger.info(f"✓ Best quote received: {total_price}")

    # Subscribe to quotes
    await client.private_channels.best_quotes_by_subaccount_id(
        subaccount_id=str(TAKER_SUBACCOUNT_ID),
        callback=handle_quote,
    )

    # Wait for quotes
    await asyncio.sleep(10)

    if not best_quote:
        logger.error("✗ No quotes received")
        return

    # Execute quote
    execute_direction = Direction.sell if best_quote.direction == Direction.buy else Direction.buy
    await client.rfq.execute_quote(
        direction=execute_direction,
        legs=best_quote.legs,
        rfq_id=best_quote.rfq_id,
        quote_id=best_quote.quote_id,
    )
    logger.info(f"✓ Quote executed at: {best_quote.quote_id}")


if __name__ == "__main__":
    # Example usage
    asyncio.run(
        create_and_execute_rfq(
            instrument="ETH-PERP",
            side="sell",
            amount=1.0,
        )
    )
