"""
Create an rfq using the REST API.
"""

import json
import sys
from datetime import datetime
from decimal import Decimal
from enum import Enum
from time import sleep

import rich_click as click
from ccxt import deribit
from derive_action_signing.module_data import RFQExecuteModuleData, RFQQuoteDetails

from derive_client import DeriveClient
from derive_client.data_types import Environment
from derive_client.data_types.enums import AssetType, OrderSide, UnderlyingCurrency
from tests.conftest import OWNER_TEST_WALLET, TEST_PRIVATE_KEY


class TxStatus(Enum):
    """Transaction status enum."""

    PENDING = 'pending'
    REVERTED = 'reverted'
    REQUESTED = 'requested'


deribit_client = deribit()


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
    default=AssetType.OPTION,
    help="Instrument name to use for the RFQ (e.g. ETH-30JUN23-1500-C)",
)
def create(side: str, amount: float, instrument: str, instrument_type: AssetType = AssetType.OPTION):
    """
    Sample of polling for RFQs and printing their status.
    """

    client: DeriveClient = DeriveClient(
        private_key=TEST_PRIVATE_KEY,
        wallet=OWNER_TEST_WALLET,
        env=Environment.TEST,
    )

    client.subaccount_id = client.subaccount_ids[-1]

    # we get an option market
    markets = client.fetch_instruments(
        instrument_type=instrument_type,
        currency=UnderlyingCurrency.ETH,
        expired=False,
    )

    if instrument:
        markets = [m for m in markets if m['instrument_name'] == instrument]
        if not markets:
            print(f"No market found for instrument {instrument}. Please check the instrument name and try again.")
            return

    if not instrument and instrument_type == AssetType.OPTION:
        sorted_markets = sorted(markets, key=lambda m: (m['option_details']['expiry']))

        zero_day_markets = list(
            filter(
                lambda m: (m['option_details']['expiry'] - datetime.utcnow().timestamp()) < (3600 * 24), sorted_markets
            )
        )
        print(f"Found {len(zero_day_markets)} zero day markets")
        selected_market = zero_day_markets[0]
        expiry_time = selected_market['option_details']['expiry']
        current_time = datetime.utcnow().timestamp()
        print(
            f"Expiry time: {expiry_time}, current time: {current_time}, time to expiry: {(expiry_time - current_time) / 3600:.2f} hours"  # noqa: E501
        )
    else:
        selected_market = markets[0]
    print(json.dumps(selected_market, indent=2))

    request_direction: OrderSide = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL

    leg = RFQQuoteDetails(
        instrument_name=selected_market['instrument_name'],
        amount=Decimal(str(amount)),
        direction=request_direction.value,
        asset_address=selected_market['base_asset_address'],
        sub_id=int(selected_market['base_asset_sub_id']),
        price=None,  # we are willing to pay 10% more than the mark price
    )
    request = RFQExecuteModuleData(
        global_direction=OrderSide.BUY.value,
        legs=[leg],
        max_fee=Decimal(10),
    )
    rfq = client.send_rfq(request.to_rfq_json())
    print("RFQ created with id:", rfq['rfq_id'])
    auction_duration = 5  # seconds

    start_time = datetime.utcnow().timestamp()
    end_time = start_time + auction_duration

    current_quotes = []
    while True:
        quotes = client.poll_quotes(
            rfq_id=rfq['rfq_id'],
        )
        if quotes.get('quotes'):
            quotes = quotes['quotes']
            new_quotes = [q for q in quotes if q not in current_quotes]
            for q in new_quotes:
                on_new_quote(client, q)
            current_quotes.extend(new_quotes)
        # check the time
        current_time = datetime.utcnow().timestamp()
        if current_time > end_time:
            print("Timeout reached, exiting")
            break
    print("Final quotes:")
    current_quotes = [f for f in current_quotes if f['status'] == 'open']
    print(json.dumps(current_quotes, indent=2))
    # we now select the best price.

    def pricer(quote: dict) -> float:
        """
        we need to get the total price of the quote
        """
        total_price = 0.0
        for leg in quote['legs']:
            total_price += float(leg['price']) * float(leg['amount'])
        return total_price

    if not current_quotes:
        print("No quotes received, exiting")
        return
    print(rfq)
    ordered_quotes = sorted(current_quotes, key=lambda q: pricer(q), reverse=True)
    print("Best quote is:")
    print("Total quotes received:", len(ordered_quotes))
    # print(json.dumps(ordered_quotes[0], indent=2))
    print("Best price is:", pricer(ordered_quotes[0]))

    best_quote = ordered_quotes[0]
    # use display a spinner for a few seconds
    if accept := input("Do you want to accept this quote? (y/n): ") == 'y':
        if not accept:
            print("Quote not accepted, exiting")
            return

        for leg, quote in zip(request.legs, best_quote['legs']):
            leg.price = Decimal(str(quote['price']))

        accepted_quote = client.execute_quote(
            quote=request,
            quote_id=best_quote['quote_id'],
            rfq_id=best_quote['rfq_id'],
        )
        print("Accepted quote:", json.dumps(accepted_quote['quote_id'], indent=2))
        is_filled = False
        is_finalised = False

        while not is_filled:
            polled_quote = client.poll_quotes(quote_id=accepted_quote['quote_id'])
            for quote in polled_quote.get('quotes', []):
                quote_price = sum(float(leg['price']) * float(leg['amount']) for leg in quote['legs'])
                print(f"Quote ID: {quote['quote_id']} Status: {quote['status']}, Price: {quote_price}")
                if quote['status'] in ['accepted', 'expired', 'rejected', 'cancelled', "filled"]:
                    print(f"Quote ID: {quote['quote_id']} final status: {quote['status']}")
                    is_filled = quote['status'] == 'filled'
                    is_finalised = False
                    break

        print("Waiting for quote to be finalised...")
        failed_status = ['reverted']
        success_status = ['settled']
        while not is_finalised:
            polled_quote = client.poll_quotes(quote_id=accepted_quote['quote_id'])
            for quote in polled_quote.get('quotes', []):
                tx_hash, tx_status = quote.get('tx_hash'), quote.get('tx_status')
                print(
                    f"Quote ID: {quote['quote_id']} Status: {quote['status']}, Tx Hash: {tx_hash}, Tx Status: {tx_status}"  # noqa: E501
                )
                if tx_hash and tx_status in (success_status + failed_status):
                    is_finalised = True
                    break
            if not is_finalised:
                print("Waiting before next poll...")
            sleep(SLEEP_TIME)
        print("Quote finalised.")

        if quote['tx_status'] in success_status:
            print("Quote executed successfully with status:", quote['tx_status'])
        elif quote['tx_status'] in failed_status:
            print("Quote execution failed with status:", quote['tx_status'])
            sys.exit(1)
            return

    else:
        print("Quote not accepted, exiting")


def on_new_quote(derive_client: DeriveClient, quote: dict):
    """
    Handle a new quote by printing it.
    """
    print(f"New quote received: {quote}")


if __name__ == "__main__":
    rfq()
