"""
Implement tests for the RFQ class.
"""

from pydantic import BaseModel

from derive_client.data_types import OrderSide
from derive_client.data_types.enums import Currency, InstrumentType, Leg
from derive_client.derive import DeriveClient


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
    return quote


def test_poll_quotes(derive_client: DeriveClient):

    quote = test_create_quote(derive_client)
    derive_client.subaccount_id = derive_client.subaccount_ids[0]  # do the nasty
    rfq_id = quote["rfq_id"]
    quote_id = quote["quote_id"]
    quotes = derive_client.poll_quotes(rfq_id=rfq_id, quote_id=quote_id)
    quotes = quotes.get('quotes', [])
    assert quotes, f"No quote matching RFQ id {rfq_id} and Quote id {quote_id} found"
    return quotes


def test_execute_quote(derive_client: DeriveClient):

    quotes = test_poll_quotes(derive_client)
    first_quote = quotes[0]
    assert first_quote["status"] == "open"

    executed_quote = derive_client.execute_quote(first_quote)

    assert not executed_quote["subaccount_id"] == first_quote["subaccount_id"]
    assert executed_quote["legs"] == first_quote["legs"]
    assert executed_quote["status"] == "filled"
    assert executed_quote["rfq_id"] == first_quote["rfq_id"]
