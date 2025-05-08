"""
Implement tests for the RFQ class.
"""

from dataclasses import asdict, dataclass

import pytest

from derive_client.data_types import OrderSide

LEG_1_NAME = 'ETH-20240329-2400-C'
LEG_2_NAME = 'ETH-20240329-2600-C'

LEGS_TO_SUB_ID: any = {
    'ETH-20240329-2400-C': '39614082287924319838483674368',
    'ETH-20240329-2600-C': '39614082373823665758483674368',
}


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
        return {"legs": [asdict(self.leg_1), asdict(self.leg_2)], "subaccount_id": self.subaccount_id}


@pytest.mark.skip(reason="This test is not meant to be run in CI")
def test_derive_client_create_rfq(
    derive_client,
):
    """
    Test the DeriveClient class.
    """

    subaccount_id = derive_client.subaccount_id
    leg_1 = Leg(instrument_name=LEG_1_NAME, amount='1', direction=OrderSide.BUY.value)
    leg_2 = Leg(instrument_name=LEG_2_NAME, amount='1', direction=OrderSide.SELL.value)
    rfq = Rfq(leg_1=leg_1, leg_2=leg_2, subaccount_id=subaccount_id)
    assert derive_client.send_rfq(rfq.to_dict())


@pytest.mark.skip(reason="This test is not meant to be run in CI")
def test_derive_client_create_quote(
    derive_client,
):
    """
    Test the DeriveClient class.
    """

    subaccount_id = derive_client.subaccount_id
    leg_1 = Leg(instrument_name=LEG_1_NAME, amount='1', direction=OrderSide.BUY.value)
    leg_2 = Leg(instrument_name=LEG_2_NAME, amount='1', direction=OrderSide.SELL.value)
    rfq = Rfq(leg_1=leg_1, leg_2=leg_2, subaccount_id=subaccount_id)
    res = derive_client.send_rfq(rfq.to_dict())

    # we now create the quote
    quote = derive_client.create_quote_object(
        rfq_id=res['rfq_id'],
        legs=[asdict(leg_1), asdict(leg_2)],
        direction='sell',
    )
    # we now sign it
    assert derive_client._sign_quote(quote)


@pytest.mark.skip(reason="This test is not meant to be run in CI")
def test_poll_rfqs(derive_client):
    """
    Test the DeriveClient class.
    """
    subaccount_id = derive_client.subaccount_id
    leg_1 = Leg(instrument_name=LEG_1_NAME, amount='1', direction=OrderSide.BUY.value)
    leg_2 = Leg(instrument_name=LEG_2_NAME, amount='1', direction=OrderSide.SELL.value)
    rfq = Rfq(leg_1=leg_1, leg_2=leg_2, subaccount_id=subaccount_id)
    assert derive_client.send_rfq(rfq.to_dict())
    quotes = derive_client.poll_rfqs()
    assert quotes
