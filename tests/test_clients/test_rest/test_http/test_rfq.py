"""Tests for RFQ module."""

import time
from decimal import Decimal

from derive_client.constants import INT64_MAX
from derive_client.data.generated.models import (
    Direction,
    InstrumentType,
    LegPricedSchema,
    LegUnpricedSchema,
    LiquidityRole,
    PrivateCancelBatchRfqsResultSchema,
    PrivateExecuteQuoteResultSchema,
    PrivateGetQuotesResultSchema,
    PrivateGetRfqsResultSchema,
    PrivatePollQuotesResultSchema,
    PrivatePollRfqsResultSchema,
    PrivateRfqGetBestQuoteResultSchema,
    PrivateSendQuoteResultSchema,
    PrivateSendRfqResultSchema,
    Result,
)
from tests.test_clients.test_rest.test_http.conftest import assert_api_calls


def _create_unpriced_legs(client):
    # Derive RPC 10004: Multiple currencies not supported
    # [data={'subaccount_currency': 'ETH', 'base_asset_currency': 'BTC', 'note': 'sometimes due to risk caching of instruments, local tests will create new currency_id without risk updating cache'}]
    currency = client.active_subaccount._state.currency
    if currency == "all":  # SM
        currency = "ETH"

    n_legs = 2
    direction = Direction.buy
    instruments = client.markets.get_instruments(
        currency=currency,
        instrument_type=InstrumentType.option,
        expired=False,
    )
    active_instruments = [instrument for instrument in instruments if instrument.is_active]

    legs = []
    for instrument in active_instruments[:n_legs]:
        amount = instrument.amount_step
        instrument_name = instrument.instrument_name
        leg = LegUnpricedSchema(
            amount=amount,
            instrument_name=instrument_name,
            direction=direction,
        )
        legs.append(leg)

    return legs


def _create_priced_legs(client, rfq):
    # Price legs using current market prices
    priced_legs = []
    for unpriced_leg in rfq.legs:
        ticker = client.markets.get_ticker(instrument_name=unpriced_leg.instrument_name)

        # Derive RPC 11107: Quote maker total cost too high  [data={'worst_cost': '6.33919554', 'total_cost': '80.596'}]
        # Use mark price (more realistic than index for options)
        # Add a small buffer to ensure quote is profitable
        base_price = ticker.mark_price
        if unpriced_leg.direction == Direction.buy:
            # Maker is selling - quote ask side (higher)
            price = base_price * Decimal("1.02")  # 2% above mark
        else:
            # Maker is buying - quote bid side (lower)
            price = base_price * Decimal("0.98")  # 2% below mark

        price = price.quantize(ticker.tick_size)
        # keep original direction here:
        # Derive RPC 11103: Quote leg does not match RFQ leg  [data={'RFQ leg direction': 'buy', 'Quote leg direction': 'sell'}]
        priced_leg = LegPricedSchema(
            price=price,
            amount=unpriced_leg.amount,
            direction=unpriced_leg.direction,
            instrument_name=unpriced_leg.instrument_name,
        )
        priced_legs.append(priced_leg)

    return priced_legs


def _create_rfq(client) -> PrivateSendRfqResultSchema:
    unpriced_legs = _create_unpriced_legs(client)
    label = "test_rfq"
    rfq = client.rfq.send_rfq(legs=unpriced_legs, label=label)
    return rfq


def test_rfq_send_rfq(client_owner_wallet):
    rfq = _create_rfq(client_owner_wallet)
    assert isinstance(rfq, PrivateSendRfqResultSchema)


def test_rfq_get_rfqs(client_owner_wallet):
    rfqs = client_owner_wallet.rfq.get_rfqs()
    assert isinstance(rfqs, PrivateGetRfqsResultSchema)


def test_rfq_cancel_rfq(client_owner_wallet):
    rfq = _create_rfq(client_owner_wallet)
    result = client_owner_wallet.rfq.cancel_rfq(rfq_id=rfq.rfq_id)
    assert isinstance(result, Result)


def test_rfq_cancel_batch_rfqs(client_admin_wallet):
    rfq = _create_rfq(client_admin_wallet)
    cancelled_batch = client_admin_wallet.rfq.cancel_batch_rfqs()
    assert isinstance(cancelled_batch, PrivateCancelBatchRfqsResultSchema)
    assert rfq.rfq_id in cancelled_batch.cancelled_ids


def test_rfq_poll_rfqs(client_admin_wallet):
    polled_rfqs = client_admin_wallet.rfq.poll_rfqs()
    assert isinstance(polled_rfqs, PrivatePollRfqsResultSchema)


def test_rfq_get_quotes(client_owner_wallet):
    quotes = client_owner_wallet.rfq.get_quotes()
    assert isinstance(quotes, PrivateGetQuotesResultSchema)


def test_rfq_poll_quotes(client_owner_wallet):
    quotes = client_owner_wallet.rfq.poll_quotes()
    assert isinstance(quotes, PrivatePollQuotesResultSchema)


def test_rfq_get_best_quote(client_owner_wallet):
    unpriced_legs = _create_unpriced_legs(client_owner_wallet)
    best_quote = client_owner_wallet.rfq.get_best_quote(legs=unpriced_legs)
    assert isinstance(best_quote, PrivateRfqGetBestQuoteResultSchema)


def test_rfq_full_lifecycle(client_admin_wallet, client_owner_wallet):
    # Derive RPC 11007: Self-crossing disallowed: use two wallets

    # Only admin as authorization as RFQ maker
    # hence: owner wallet sends RFQ and admin wallet quotes
    taker = client_owner_wallet
    maker = client_admin_wallet

    taker_direction = Direction.buy
    maker_direction = Direction.sell

    unpriced_legs = _create_unpriced_legs(taker)
    label = "test_rfq"
    rfq = taker.rfq.send_rfq(legs=unpriced_legs, label=label)

    signature_expiry_sec = INT64_MAX
    max_fee = Decimal("1000")

    priced_legs = _create_priced_legs(maker, rfq)

    # Quote direction, buy means trading each leg at its direction, sell means trading each leg in the opposite direction.
    utc_now_s = int(time.time())
    with assert_api_calls(maker, expected=1):
        sent_quote = maker.rfq.send_quote(
            direction=maker_direction,
            legs=priced_legs,
            max_fee=max_fee,
            rfq_id=rfq.rfq_id,
            signature_expiry_sec=utc_now_s + 330,
        )

    assert isinstance(sent_quote, PrivateSendQuoteResultSchema)
    assert rfq.rfq_id == sent_quote.rfq_id

    # best_quote = taker.rfq.get_best_quote(legs=unpriced_legs, direction=maker_direction)
    quotes = taker.rfq.poll_quotes(rfq_id=rfq.rfq_id)
    quote = quotes.quotes[0]

    assert quote.subaccount_id == maker.active_subaccount.id
    assert quote.liquidity_role == LiquidityRole.maker
    assert quote.direction == maker_direction

    with assert_api_calls(taker, expected=1):
        executed_quote = taker.rfq.execute_quote(
            direction=taker_direction,
            legs=quote.legs,
            max_fee=max_fee,
            quote_id=quote.quote_id,
            rfq_id=rfq.rfq_id,
            signature_expiry_sec=signature_expiry_sec,
        )

    assert isinstance(executed_quote, PrivateExecuteQuoteResultSchema)
    assert executed_quote.liquidity_role == LiquidityRole.taker
