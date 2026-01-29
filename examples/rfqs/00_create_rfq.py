"""
Simple demonstration of creating and executing an RFQ.
"""

import asyncio
from pathlib import Path
from typing import List

from config import TAKER_SUBACCOUNT_ID

from derive_client import WebSocketClient
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
    repo_root = Path(__file__).parent.parent.parent
    env_file = repo_root / ".env.template"
    client = WebSocketClient.from_env(env_file=env_file)

    # Connect client
    await client.connect()
    logger = get_logger()

    # Send RFQ
    rfq_result = await client.rfq.send_rfq(legs=legs)
    logger.info(f"✓ RFQ created: {rfq_result.rfq_id}")

    # Create queue to collect quotes
    quote_queue: asyncio.Queue[BestQuoteChannelResultSchema] = asyncio.Queue()

    def handle_best_quotes(quotes: List[BestQuoteChannelResultSchema]):
        """Handler pushes all quotes to queue for processing"""

        for quote in quotes:
            quote_queue.put_nowait(quote)

    # Subscribe to quotes
    await client.private_channels.best_quotes_by_subaccount_id(
        subaccount_id=str(TAKER_SUBACCOUNT_ID),
        callback=handle_best_quotes,
    )

    # Await the best quote for the RFQ
    best_quote: QuoteResultPublicSchema | None = None
    try:
        while True:
            quote = await asyncio.wait_for(quote_queue.get(), timeout=10.0)

            if quote.rfq_id == rfq_result.rfq_id:
                if quote.result and quote.result.best_quote:
                    best_quote = quote.result.best_quote
                    total_price = sum(leg.price * leg.amount for leg in best_quote.legs)
                    logger.info(f"✓ Best quote received for {rfq_result.rfq_id}: {total_price}")
                    break
            else:
                # In production, you'd handle other RFQs as well
                logger.info(f"📝 Quote received for different RFQ: {quote.rfq_id}")

    except asyncio.TimeoutError:
        logger.error(f"✗ No quotes received for RFQ {rfq_result.rfq_id}, cancelling...")
        await client.rfq.cancel_rfq(rfq_id=rfq_result.rfq_id)
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
