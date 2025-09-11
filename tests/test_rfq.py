"""
Implement tests for the RFQ class.
"""

from dataclasses import asdict, dataclass

import pytest

from derive_client.data_types import OrderSide
from derive_client.data_types.enums import Currency, InstrumentType
from derive_client.derive import DeriveClient


@dataclass
class Leg:
    instrument_name: str
    amount: str
    direction: str


@dataclass
class Rfq:
    subaccount_id: str
    leg_1: Leg
    leg_2: Leg

    def to_dict(self):
        return {
            "legs": sorted([asdict(self.leg_1), asdict(self.leg_2)], key=lambda x: x['instrument_name']),
            "subaccount_id": self.subaccount_id,
        }


def test_derive_client_create_rfq(
    derive_client: DeriveClient,
):
    """
    Test the DeriveClient class.
    """

    subaccount_id = derive_client.subaccount_id

    markets = derive_client.fetch_instruments(instrument_type=InstrumentType.OPTION, currency=Currency.ETH)

    active_markets = [m for m in markets if m['is_active']]
    assert active_markets, "No active markets found"
    leg_1_name = active_markets[0]['instrument_name']
    leg_2_name = active_markets[1]['instrument_name']

    leg_1 = Leg(instrument_name=leg_1_name, amount='1', direction=OrderSide.BUY.value)
    leg_2 = Leg(instrument_name=leg_2_name, amount='1', direction=OrderSide.SELL.value)
    rfq = Rfq(leg_1=leg_1, leg_2=leg_2, subaccount_id=subaccount_id)
    result = derive_client.send_rfq(rfq.to_dict())
    assert result['rfq_id']
    assert result['status'] == 'open'
    return result


def test_poll_rfqs(derive_client: DeriveClient):
    """
    Test the DeriveClient class.
    """
    rfq_id = test_derive_client_create_rfq(derive_client).get('rfq_id')
    quotes = derive_client.poll_rfqs()
    rfqs = quotes.get('rfqs', [])
    assert rfqs, "RFQs should not be empty"
    filtered_rfqs = [r for r in rfqs if r['rfq_id'] == rfq_id]
    assert filtered_rfqs, f"RFQ with id {rfq_id} not found"


@pytest.mark.skip(reason="Skipping quote creation test")
def test_derive_client_create_quote(
    derive_client: DeriveClient,
):
    """
    Test the DeriveClient class.
    """

    rfq = test_derive_client_create_rfq(derive_client)

    # we now create the quote
    quote = derive_client.create_quote_object(
        rfq_id=rfq['rfq_id'],
        legs=rfq['legs'],
        direction='sell',
    )
    # we now sign it
    assert derive_client._sign_quote(quote)
