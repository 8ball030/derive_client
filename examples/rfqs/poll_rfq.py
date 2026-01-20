"""
Example of how to poll RFQ (Request for Quote) status and handle transfers between subaccount and funding account.
"""

from decimal import Decimal
from threading import Thread
from time import sleep

from derive_client import WebSocketClient
from derive_client.data_types import Environment
from derive_client.exceptions import DeriveJSONRPCException
from tests.conftest import ADMIN_TEST_WALLET as TEST_WALLET
from tests.conftest import SESSION_KEY_PRIVATE_KEY

SLEEP_TIME = 1
SUBACCOUNT_ID = 31049


    # while True:
    #     rfqs = client.poll_rfqs()
    #     sleep(SLEEP_TIME)  # Sleep for a while before polling again
    #     raw_rfqs = rfqs.get('rfqs', [])
    #     rfqs = {rfq['rfq_id']: rfq for rfq in raw_rfqs}

    #     if not rfqs:
    #         print("No RFQs found, exiting.")
    #         continue
    #     for rfq_id in rfqs:
    #         if rfq_id in processed_rfqs:
    #             continue
    #         rfq = rfqs[rfq_id]
    #         print(f"RFQ ID: {rfq_id} Status: {rfq['status']}, Legs: {len(rfq['legs'])}")
    #         processed_rfqs.add(rfq_id)
    #         on_new_rfq(client, rfq)

    #     for rfq in processed_rfqs.copy():
    #         if rfq not in rfqs:
    #             print(f"RFQ ID {rfq} no longer present in polled RFQs, removing from processed list.")
    #             processed_rfqs.remove(rfq)


# def on_quote_created(derive_client: DeriveClient, quote: dict):
#     """
#     Handle a new quote by polling its status until it is accepted or expired
#     """
#     print(f"New Quote detected: {quote['quote_id']} for RFQ: {quote['rfq_id']}, polling status...")
#     attempts = 10
#     while True:
#         polled_quote = derive_client.poll_quotes(quote_id=quote['quote_id'], status=RfqStatus.OPEN)
#         for quote in polled_quote.get('quotes', []):
#             print(
#                 f"Quote ID: {polled_quote['quote_id']} Status: {polled_quote['status']}, Price: {polled_quote['price']}"
#             )
#             if polled_quote['status'] in ['accepted', 'expired', 'rejected', 'cancelled']:
#                 print(f"Quote ID: {polled_quote['quote_id']} final status: {polled_quote['status']}")
#                 break
#         if not polled_quote.get('quotes') and attempts < 0:
#             print(f"Quote ID: {quote['quote_id']} not found, exiting polling.")
#             break
#         attempts -= 1
#         print(f"Waiting before next poll... for quote {quote['quote_id']}")
#         sleep(SLEEP_TIME)


# def on_new_rfq(derive_client: DeriveClient, rfq: dict):
#     """
#     Handle a new RFQ by returning a quote for the RFQ based on the index price
#     """
#     print(f"New RFQ detected: {rfq['rfq_id']}")

#     if rfq['status'] != 'open':
#         print(f"RFQ {rfq['rfq_id']} is not open (status: {rfq['status']}), skipping.")
#         return
#     # we check that the subaccount isnt the same as ours
#     if rfq['subaccount_id'] == derive_client.subaccount_id:
#         print(f"RFQ {rfq['rfq_id']} is from our own subaccount, skipping.")
#         return
#     print("RFQ details:")
#     print(rfq)

#     leg_tickers = {i['instrument_name']: derive_client.fetch_ticker(i['instrument_name']) for i in rfq['legs']}

#     premium_per_rfq = 0.01  # 1% premium on top of index price
#     premium_per_rfq = 0.0  # 1% premium on top of index price
#     fixed_cost_per_leg = 0.5  # $0.5 fixed cost per leg to cover fees
#     total_price: float = 0.0

#     quote_legs = []
#     for leg in rfq['legs']:
#         ticker = leg_tickers[leg['instrument_name']]
#         print(f"Leg: {leg['instrument_name']} amount: {leg['amount']}, direction: {leg['direction']}")

#         if_leg_sell = leg['direction'] == 'sell'

#         if leg['direction'] == 'buy':
#             price = float(ticker['mark_price']) * (1 + premium_per_rfq) + fixed_cost_per_leg
#         elif leg['direction'] == 'sell':
#             price = float(ticker['mark_price']) * (1 - premium_per_rfq) + fixed_cost_per_leg
#         else:
#             print(f"Unknown leg direction: {leg['direction']}, skipping RFQ.")
#             return
#         leg_price = price * float(leg['amount'])

#         leg['price'] = Decimal(f"{price:.2f}")
#         quote_legs.append(leg)
#         total_price += leg_price if if_leg_sell else -leg_price
#         print(f"  -> Leg Price: {leg_price:.2f} USD at Price: {price:.2f} USD")
#     print(f"Total RFQ Price: {total_price:.2f} USD")
#     print("responding with quote...")

#     try:
#         quote = derive_client.create_quote(
#             legs=quote_legs,
#             rfq_id=rfq['rfq_id'],
#             direction='sell',
#         )
#         print("Quote response:", quote)
#     except DeriveJSONRPCException as e:
#         print(f"Error creating quote: {e}")
#         return

#     print(f"Quote created: {quote['quote_id']} for RFQ: {rfq['rfq_id']} with total price: {total_price:.2f} USD")
#     print("Starting to poll quote status. in background...")
#     Thread(target=on_quote_created, args=(derive_client, quote)).start()
#     print("Continuing to poll for new RFQs...")


def main():
    """
    Sample of polling for RFQs and printing their status.
    """

    client = WebSocketClient(
        session_key=SESSION_KEY_PRIVATE_KEY,
        wallet=TEST_WALLET,
        env=Environment.TEST,
        subaccount_id=SUBACCOUNT_ID,
    )

    def on_rfq(Rfq):
        print(f"Received RFQ: {Rfq}")


    client.connect()


    rfqs = []
    from_timestamp = 0
    while True:
        new_rfqs = client.rfq.poll_rfqs(from_timestamp=from_timestamp)
        rfqs.extend(new_rfqs.rfqs)
        for rfq in new_rfqs.rfqs:
            if rfq.last_update_timestamp > from_timestamp:
                from_timestamp = rfq.last_update_timestamp + 1
            on_rfq(rfq)
        sleep(SLEEP_TIME)


if __name__ == "__main__":
    main()
