"""
Example of how to poll RFQ (Request for Quote) status and handle transfers between subaccount and funding account.
"""

import asyncio
from typing import List

from config import ADMIN_TEST_WALLET as TEST_WALLET
from config import SESSION_KEY_PRIVATE_KEY
from rich import print

from derive_client import WebSocketClient
from derive_client._clients.utils import DeriveJSONRPCError
from derive_client.data_types import Environment
from derive_client.data_types.channel_models import QuoteResultSchema
from derive_client.data_types.generated_models import Direction, LegPricedSchema, RFQResultPublicSchema, Status
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
    print(f"  ✓ Priced legs for RFQ {rfq.rfq_id} at total price {sum(leg.price * leg.amount for leg in priced_legs)}")
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
    quotes = {}

    async def on_rfq(rfqs: List[RFQResultPublicSchema]):
        for rfq in rfqs:
            if rfq.status == Status.filled and rfq.rfq_id in quotes:
                print(f"[blue]Quote {quotes[rfq.rfq_id].quote_id} accepted![/blue]")
                del quotes[rfq.rfq_id]
            elif rfq.status == Status.expired and rfq.rfq_id in quotes:
                print(f"[yellow]Quote {quotes[rfq.rfq_id].quote_id} expired.[/yellow]")
                del quotes[rfq.rfq_id]
        open_rfqs = [r for r in rfqs if r.status == Status.open]
        print(f"Received {len(rfqs)} RFQs ({len(open_rfqs)} open)")
        if not open_rfqs:
            return

        priced = await asyncio.gather(*(create_priced_legs(client, r) for r in open_rfqs))
        quotable = [(r, legs) for r, legs in zip(open_rfqs, priced) if legs]

        if not quotable:
            return

        results = await asyncio.gather(
            *(client.rfq.send_quote(rfq_id=r.rfq_id, legs=legs, direction=Direction.sell) for r, legs in quotable),
            return_exceptions=True,
        )
        for r, result in zip(quotable, results):
            rfq, _ = r
            if isinstance(result, DeriveJSONRPCError):
                print(f"[red]Failed to send quote for RFQ {rfq.rfq_id}: {result}[/red]")
            else:
                quotes[rfq.rfq_id] = result
                print(f"[green]Sent quote for RFQ {rfq.rfq_id}[/green]")

    async def on_quote(quotes_list: List[QuoteResultSchema]):
        print(f"Received {len(quotes_list)} quotes")
        for quote in quotes_list:
            print(f"  - Quote {quote.quote_id} for RFQ {quote.rfq_id} is {quote.status}")

    await client.connect()

    await client.private_channels.rfqs_by_wallet(wallet=TEST_WALLET, callback=on_rfq)
    await client.private_channels.quotes_by_subaccount_id(
        subaccount_id=str(SUBACCOUNT_ID),
        callback=on_quote,
    )

    await asyncio.Event().wait()  # Keep the connection alive


if __name__ == "__main__":
    asyncio.run(main())
