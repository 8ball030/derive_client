"""
Example of how to poll RFQ (Request for Quote) status and handle transfers between subaccount and funding account.
"""

from time import sleep

from derive_client import DeriveClient
from derive_client.data_types import Environment
from tests.conftest import TEST_PRIVATE_KEY, TEST_WALLET

SLEEP_TIME = 1


def main():
    """
    Sample of polling for RFQs and printing their status.
    """

    client = DeriveClient(
        private_key=TEST_PRIVATE_KEY,
        wallet=TEST_WALLET,
        env=Environment.TEST,
    )

    processed_rfqs = set()

    while True:
        quotes = client.poll_rfqs()
        sleep(SLEEP_TIME)  # Sleep for a while before polling again
        raw_rfqs = quotes.get('rfqs', [])
        rfqs = {rfq['rfq_id']: rfq for rfq in raw_rfqs}

        if not rfqs:
            print("No RFQs found, exiting.")
            break
        for rfq_id in rfqs:
            if rfq_id in processed_rfqs:
                continue
            rfq = rfqs[rfq_id]
            print(f"RFQ ID: {rfq_id} Status: {rfq['status']}, Legs: {len(rfq['legs'])}")
            processed_rfqs.add(rfq_id)
        for rfq in processed_rfqs.copy():
            if rfq not in rfqs:
                print(f"RFQ ID {rfq} no longer present in polled RFQs, removing from processed list.")
                processed_rfqs.remove(rfq)




if __name__ == "__main__":
    main()
