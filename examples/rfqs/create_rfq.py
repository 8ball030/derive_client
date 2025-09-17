"""
Create an rfq using the REST API.
"""

import json
from datetime import datetime

from derive_client import DeriveClient
from derive_client.data_types import Environment
from derive_client.data_types.enums import InstrumentType, OrderSide, UnderlyingCurrency
from tests.conftest import TEST_PRIVATE_KEY, TEST_WALLET
from tests.test_rfq import Leg, Rfq

SLEEP_TIME = 1


def main():
    """
    Sample of polling for RFQs and printing their status.
    """

    client: DeriveClient = DeriveClient(
        private_key=TEST_PRIVATE_KEY,
        wallet=TEST_WALLET,
        env=Environment.TEST,
    )

    # we get an option market
    markets = client.fetch_instruments(
        instrument_type=InstrumentType.OPTION,
        currency=UnderlyingCurrency.ETH,
        expired=False,
    )

    sorted_markets = sorted(markets, key=lambda m: (m['option_details']['expiry']))

    zero_day_markets = list(
        filter(lambda m: (m['option_details']['expiry'] - datetime.utcnow().timestamp()) < (3600 * 24), sorted_markets)
    )
    print("Zero day markets:")
    selected_market = zero_day_markets[0]
    print(json.dumps(selected_market, indent=2))
    print(f"Found {len(zero_day_markets)} zero day markets")
    expiry_time = selected_market['option_details']['expiry']
    current_time = datetime.utcnow().timestamp()
    print(
        f"Expiry time: {expiry_time}, current time: {current_time}, time to expiry: {(expiry_time - current_time) / 3600:.2f} hours"
    )

    # we create an rfq for this market

    leg = Leg(instrument_name=selected_market['instrument_name'], amount=1, direction=OrderSide.BUY)
    request = Rfq(
        legs=[leg],
        subaccount_id=client.subaccount_id,
    )
    rfq = client.send_rfq(request.model_dump())
    print("RFQ created with id:", rfq['rfq_id'])


if __name__ == "__main__":
    main()
