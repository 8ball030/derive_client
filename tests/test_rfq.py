"""
Implement tests for the RFQ class.
"""

from pydantic import BaseModel

from derive_client.data_types import OrderSide
from derive_client.data_types.enums import Currency, InstrumentType
from derive_client.derive import DeriveClient


class Leg(BaseModel):
    instrument_name: str
    amount: float
    direction: str
    price: float | None = None


class Rfq(BaseModel):
    subaccount_id: int
    legs: list[Leg]

    def model_dump(self, *args, **kwargs):
        kwargs.setdefault("exclude_none", True)
        data = super().model_dump(*args, **kwargs)
        data["legs"].sort(key=lambda x: x.get("instrument_name"))
        return data


def test_create_rfq(derive_client: DeriveClient):

    subaccount_id = derive_client.subaccount_id

    markets = derive_client.fetch_instruments(instrument_type=InstrumentType.OPTION, currency=Currency.ETH)

    active_markets = [m for m in markets if m['is_active']]
    assert active_markets, "No active markets found"
    leg_1_name = active_markets[0]['instrument_name']
    leg_2_name = active_markets[1]['instrument_name']

    leg_1 = Leg(instrument_name=leg_1_name, amount=1, direction=OrderSide.BUY.value)
    leg_2 = Leg(instrument_name=leg_2_name, amount=1, direction=OrderSide.SELL.value)
    rfq = Rfq(legs=[leg_1, leg_2], subaccount_id=subaccount_id)
    result = derive_client.send_rfq(rfq.model_dump())
    assert result['rfq_id']
    assert result['status'] == 'open'
    return result


def test_cancel_rfq(derive_client: DeriveClient):
    rfq = test_create_rfq(derive_client)
    result = derive_client.cancel_rfq(rfq_id=rfq['rfq_id'])
    assert result == 'ok'


def test_cancel_all_rfqs(derive_client: DeriveClient):
    result = derive_client.cancel_batch_rfqs()
    cancelled_ids = result.get('cancelled_ids', [])
    assert isinstance(cancelled_ids, list)


def test_poll_rfqs(derive_client: DeriveClient):

    rfq_id = test_create_rfq(derive_client).get('rfq_id')
    quotes = derive_client.poll_rfqs()
    rfqs = quotes.get('rfqs', [])
    assert rfqs, "RFQs should not be empty"
    filtered_rfqs = [r for r in rfqs if r['rfq_id'] == rfq_id]
    assert filtered_rfqs, f"RFQ with id {rfq_id} not found"


def test_create_quote(derive_client: DeriveClient):

    rfq = test_create_rfq(derive_client)

    price = 42
    direction = "sell"
    derive_client.subaccount_id = derive_client.subaccount_ids[1]

    legs = []
    for leg in rfq['legs']:
        leg = Leg(**leg)
        leg.price = price
        legs.append(leg)

    quote = derive_client.create_quote(
        rfq_id=rfq['rfq_id'],
        legs=[leg.model_dump() for leg in legs],
        direction=direction,
    )
    assert quote["status"] == "open"
    assert quote["direction"] == direction
    assert rfq["creation_timestamp"] < quote["creation_timestamp"]
    assert len(rfq["legs"]) == len(quote["legs"])
    for rfq_leg, quote_leg in zip(rfq["legs"], quote["legs"]):
        assert rfq_leg != quote_leg
        assert Leg(**rfq_leg, price=price) == Leg(**quote_leg)
    return rfq

def test_poll_quotes(derive_client: DeriveClient):

    rfq = test_create_quote(derive_client)
    derive_client.subaccount_id = derive_client.subaccount_ids[0]
    quotes = derive_client.poll_quotes(rfq_id=rfq['rfq_id'])
    polled_rfqs = quotes.get('quotes', [])
    assert polled_rfqs, "Polled RFQs should not be empty"
