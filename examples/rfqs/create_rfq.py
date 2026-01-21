"""
Create an rfq using the REST API.
"""

from datetime import UTC, datetime
from time import sleep
from typing import List

import rich_click as click
from config import OWNER_TEST_WALLET, SESSION_KEY_PRIVATE_KEY, TAKER_SUBACCOUNT_ID

from derive_client import WebSocketClient
from derive_client.data_types import Environment
from derive_client.data_types.channel_models import BestQuoteChannelResultSchema
from derive_client.data_types.generated_models import AssetType, Direction, LegUnpricedSchema
from derive_client.data_types.utils import D

SLEEP_TIME = 1


@click.group()
def rfq():
    """RFQ related commands."""
    pass


@rfq.command(help="Create an RFQ and poll for quotes")
@click.option(
    '-s',
    '--side',
    type=click.Choice(['buy', 'sell'], case_sensitive=False),
    required=True,
    help="Side of the RFQ (buy or sell)",
)
@click.option(
    '-a',
    '--amount',
    type=click.FLOAT,
    required=False,
    default=1.0,
    help="Amount of the Leg of the RFQ",
)
@click.option(
    '-i',
    '--instrument',
    type=click.STRING,
    required=False,
    default=None,
    help="Instrument name to use for the RFQ (e.g. ETH-30JUN23-1500-C)",
)
@click.option(
    '-it',
    '--instrument-type',
    type=AssetType,
    required=False,
    default=AssetType.option,
    help="Instrument name to use for the RFQ (e.g. ETH-30JUN23-1500-C)",
)
def create(side: str, amount: float, instrument: str, instrument_type: AssetType = AssetType.option):
    """
    Sample of polling for RFQs and printing their status.
    """
    click.echo(
        f"Creating RFQ: side={side}, amount={amount}, instrument={instrument}, instrument_type={instrument_type}"
    )

    client: WebSocketClient = WebSocketClient(
        session_key=SESSION_KEY_PRIVATE_KEY,
        wallet=OWNER_TEST_WALLET,
        env=Environment.TEST,
        subaccount_id=TAKER_SUBACCOUNT_ID,
    )
    client.connect()

    # we get an option market
    markets = client.markets.fetch_instruments(
        instrument_type=instrument_type,
        expired=False,
    )

    if instrument:
        markets = [m for m in markets if m == instrument]
        if not markets:
            click.echo(f"No market found for instrument {instrument}. Please check the instrument name and try again.")
            return

    request_direction: Direction = Direction.buy if side.lower() == 'buy' else Direction.sell

    result = client.rfq.send_rfq(
        legs=[
            LegUnpricedSchema(
                amount=D(amount),
                instrument_name=instrument,
                direction=request_direction,
            )
        ],
    )
    print("RFQ created with id:", result.rfq_id)

    def on_new_quote(quotes: List[BestQuoteChannelResultSchema]):
        """
        Handle a new quote received for the RFQ.
        """
        for quote in quotes:
            if quote.result and quote.result.best_quote:
                print(f"New best quote received: {quote.result.best_quote}")

    client.private_channels.best_quotes_by_subaccount_id(
        subaccount_id=str(client._subaccount_id), callback=on_new_quote
    )

    start_time = datetime.now(UTC).timestamp()
    end_time = start_time + 30  # run for 30 seconds

    while datetime.now(UTC).timestamp() < end_time:
        sleep(1)
    print("Final quotes:")
    click.echo("RFQ process completed.")


if __name__ == "__main__":
    rfq()
