"""
Example of how to poll RFQ (Request for Quote) status and handle transfers between subaccount and funding account.
"""

import asyncio
from typing import Sequence

from config import ADMIN_TEST_WALLET as TEST_WALLET
from config import SESSION_KEY_PRIVATE_KEY
from rich import print

from derive_client import WebSocketClient
from derive_client._clients.utils import DeriveJSONRPCError
from derive_client.data_types import Environment
from derive_client.data_types.channel_models import RFQResultPublicSchema
from derive_client.data_types.generated_models import (
    Direction,
    LegPricedSchema,
)
from derive_client.data_types.utils import D

SLEEP_TIME = 1
SUBACCOUNT_ID = 31049


async def create_priced_legs(client: WebSocketClient, rfq):
    # Price legs using current market prices
    priced_legs = []
    for unpriced_leg in rfq.legs:
        ticker = await client.markets.get_ticker(instrument_name=unpriced_leg.instrument_name)

        base_price = ticker.index_price

        price = base_price * D("1.02") if unpriced_leg.direction == Direction.buy else base_price * D("0.98")

        price = price.quantize(ticker.tick_size)
        priced_leg = LegPricedSchema(
            price=price,
            amount=unpriced_leg.amount,
            direction=unpriced_leg.direction,
            instrument_name=unpriced_leg.instrument_name,
        )
        priced_legs.append(priced_leg)

    return priced_legs


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
    await client.connect()

    async def on_rfq(rfqs: Sequence[RFQResultPublicSchema]):
        # here we get a price for the rfq.
        # we first get the index price for the instrument
        print(f"Received {len(rfqs)} RFQs")
        for rfq in rfqs:
            priced_legs = await create_priced_legs(client, rfq)
            print(f"Total legs price: {sum([leg.price * leg.amount for leg in priced_legs])}")
            try:
                await client.rfq.send_quote(rfq_id=rfq.rfq_id, legs=priced_legs, direction=Direction.sell)
            except DeriveJSONRPCError as e:
                print(f"Error creating quote for RFQ {rfq.rfq_id}: {e}")

    await client.private_channels.rfqs_by_wallet(
        wallet=TEST_WALLET,
        callback=on_rfq,
    )

    await asyncio.Event().wait()

    # rfqs = []
    # from_timestamp = 0
    # while True:
    #     new_rfqs = await client.rfq.poll_rfqs(from_timestamp=from_timestamp)
    #     for rfq in new_rfqs.rfqs:
    #         if rfq.last_update_timestamp > from_timestamp:
    #             from_timestamp = rfq.last_update_timestamp + 1
    #         if rfq.status is Status.open:
    #             task = asyncio.create_task(on_rfq(rfq))
    #             rfqs.append(task)
    #     for task in rfqs:
    #         if task.done():
    #             rfqs.remove(task)

    #     sleep(SLEEP_TIME)


if __name__ == "__main__":
    asyncio.run(main())
