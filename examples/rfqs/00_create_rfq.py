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
    rfq_result = await client.rfq.send_rfq(legs=legs)
    logger.info(f"✓ RFQ created: {rfq_result.rfq_id}")

    # Track best quote
    best_quote: QuoteResultPublicSchema | None = None

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
    logger.info(
        f"✓ Quote {best_quote.quote_id} executed at total price: "
        + f"{sum(leg.price * leg.amount for leg in best_quote.legs)}"
    )


if __name__ == "__main__":
    # Example usage
    legs = [
        LegUnpricedSchema(
            instrument_name="ETH-20260327-4800-P",
            amount=D("1"),
            direction=Direction.sell,
        ),
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
