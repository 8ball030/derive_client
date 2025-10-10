"""
Implement tests for the RFQ class.
"""

from decimal import Decimal
from typing import Literal

from derive_action_signing.module_data import RFQExecuteModuleData, RFQQuoteDetails
from pydantic import BaseModel

from derive_client.data_types import OrderSide
from derive_client.data_types.enums import Currency, InstrumentType
from derive_client.derive import DeriveClient


class Leg(BaseModel):
    instrument_name: str
    amount: Decimal
    direction: Literal["buy", "sell"]
    price: Decimal | None = None
    sub_id: str | None = None
    asset_address: str | None = None


class Rfq(BaseModel):
    subaccount_id: int
    legs: list[Leg]
    global_direction: Literal["buy", "sell"] | None = None
    max_fee: Decimal | None = None
    quote_id: str | None = None
    rfq_id: str | None = None

    def model_dump(self, *args, **kwargs):
        kwargs.setdefault("exclude_none", True)
        data = super().model_dump(*args, **kwargs)
        data["legs"].sort(key=lambda x: x.get("instrument_name"))
        return data

    def from_dict(data: dict) -> "Rfq":
        data = data.copy()
        data["legs"] = [Leg(**leg) for leg in data.get("legs", [])]
        return Rfq(**data)


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
    return rfq, result


def test_cancel_rfq(derive_client: DeriveClient):
    _, request_result = test_create_rfq(derive_client)
    result = derive_client.cancel_rfq(rfq_id=request_result['rfq_id'])
    assert result == 'ok'


def test_cancel_all_rfqs(derive_client: DeriveClient):
    result = derive_client.cancel_batch_rfqs()
    cancelled_ids = result.get('cancelled_ids', [])
    assert isinstance(cancelled_ids, list)


def test_poll_rfqs(derive_client: DeriveClient):
    _, rfq_result = test_create_rfq(derive_client)
    rfq_id = rfq_result['rfq_id']
    quotes = derive_client.poll_rfqs()
    rfqs = quotes.get('rfqs', [])
    assert rfqs, "RFQs should not be empty"
    filtered_rfqs = [r for r in rfqs if r['rfq_id'] == rfq_id]
    assert filtered_rfqs, f"RFQ with id {rfq_id} not found"


def test_create_quote(derive_client: DeriveClient, derive_client_2: DeriveClient):
    rfq, rfq_result = test_create_rfq(derive_client_2)

    direction = "sell"
    derive_client.subaccount_id = derive_client.subaccount_ids[1]

    legs = []
    for leg in rfq_result['legs']:
        leg = Leg(**leg)
        price = Decimal(derive_client.fetch_ticker(leg.instrument_name)['mark_price'])
        leg.price = price
        legs.append(leg)

    quote = derive_client.create_quote(
        rfq_id=rfq_result['rfq_id'],
        legs=[leg.model_dump() for leg in legs],
        direction=direction,
    )
    assert quote["status"] == "open"
    assert quote["direction"] == direction
    assert quote['fee']
    assert quote['max_fee']
    assert rfq_result["creation_timestamp"] < quote["creation_timestamp"]
    assert len(rfq_result["legs"]) == len(quote["legs"])
    for rfq_leg, quote_leg in zip(rfq_result["legs"], quote["legs"]):
        assert rfq_leg != quote_leg
        assert Leg(**rfq_leg, price=quote_leg['price']) == Leg(**quote_leg)
    return quote, rfq


def test_poll_quotes(derive_client: DeriveClient, derive_client_2: DeriveClient):
    quote, _ = test_create_quote(derive_client, derive_client_2)
    rfq_id = quote["rfq_id"]
    quote_id = quote["quote_id"]
    quotes = derive_client_2.poll_quotes(rfq_id=rfq_id, quote_id=quote_id)
    quotes = quotes.get('quotes', [])
    assert quotes, f"No quote matching RFQ id {rfq_id} and Quote id {quote_id} found"
    return quotes


def test_execute_quote(derive_client: DeriveClient, derive_client_2: DeriveClient):
    quote, rfq = test_create_quote(derive_client, derive_client_2)
    assert quote["status"] == "open"

    for leg, quote_leg in zip(rfq.legs, quote["legs"]):
        leg.price = Decimal(quote_leg['price'])

    markets = {
        m['instrument_name']: m
        for m in derive_client.fetch_instruments(instrument_type=InstrumentType.OPTION, currency=Currency.ETH)
    }

    executed_quote = derive_client_2.execute_quote(
        quote=RFQExecuteModuleData(
            global_direction="buy",
            legs=[
                RFQQuoteDetails(
                    instrument_name=leg.instrument_name,
                    amount=leg.amount,
                    direction=leg.direction,
                    price=leg.price,
                    asset_address=markets[leg.instrument_name]['base_asset_address'],
                    sub_id=int(markets[leg.instrument_name]['base_asset_sub_id']),
                )
                for leg in rfq.legs
            ],
            max_fee=Decimal(quote["max_fee"]),
        ),
        quote_id=quote["quote_id"],
        rfq_id=quote["rfq_id"],
    )

    assert executed_quote["subaccount_id"] != quote["subaccount_id"]
    assert executed_quote["legs"] == quote["legs"]
    assert executed_quote["status"] == "filled"
    assert executed_quote["rfq_id"] == quote["rfq_id"]
