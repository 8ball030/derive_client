"""
Tests for position transfer functionality (transfer_position and transfer_positions methods).
"""

from decimal import Decimal

import pytest

from derive_client.clients.http_client import HttpClient
from derive_client.data_types import (
    DeriveTxResult,
    DeriveTxStatus,
    InstrumentType,
    OrderSide,
    OrderStatus,
    OrderType,
    PositionSpec,
    TimeInForce,
    UnderlyingCurrency,
)
from derive_client.utils import wait_until


def is_settled(res: DeriveTxResult) -> bool:
    return res.status is DeriveTxStatus.SETTLED


def is_filled(order: dict) -> bool:
    return order["order_status"] == OrderStatus.FILLED.value


def get_all_positions(derive_client: HttpClient) -> dict[str, list[dict]]:
    _subaccount_id = derive_client.subaccount_id

    def is_zero(position):
        return position["amount"] == "0"

    positions = {}
    for subaccount_id in derive_client.subaccount_ids:
        derive_client.subaccount_id = subaccount_id
        positions[subaccount_id] = list(filter(lambda p: not is_zero(p), derive_client.get_positions()))

    derive_client.subaccount_id = _subaccount_id
    return positions


def close_all_positions(derive_client):
    _subaccount_id = derive_client.subaccount_id
    all_positions = get_all_positions(derive_client)
    for subaccount_id, positions in all_positions.items():
        derive_client.subaccount_id = subaccount_id  # this is nasty
        for position in positions:
            amount = float(position["amount"])

            side = OrderSide.SELL if amount > 0 else OrderSide.BUY
            ticker = derive_client.fetch_ticker(instrument_name=position["instrument_name"])
            price = float(ticker["best_ask_price"]) if amount < 0 else float(ticker["best_bid_price"])
            price = price * 1.05 if side == OrderSide.BUY else price * 0.95
            price = float(Decimal(price).quantize(Decimal(ticker["tick_size"])))
            amount = abs(amount)

            derive_client.create_order(
                price=price,
                amount=amount,
                instrument_name=position["instrument_name"],
                reduce_only=True,
                instrument_type=InstrumentType(position["instrument_type"]),
                side=side,
                order_type=OrderType.MARKET,
                time_in_force=TimeInForce.FOK,
            )

    derive_client.subaccount_id = _subaccount_id


@pytest.fixture
def client_with_position(request, derive_client):
    """Setup position for transfer"""

    currency, instrument_type, side = request.param

    assert len(derive_client.subaccount_ids) >= 2, "Need at least 2 subaccounts for position transfer tests"

    close_all_positions(derive_client)
    positions = get_all_positions(derive_client)
    if any(positions.values()):
        raise ValueError(f"Pre-existing positions found: {positions}")

    instrument_name = f"{currency.name}-{instrument_type.name}"

    ticker = derive_client.fetch_ticker(instrument_name)
    if not ticker["is_active"]:
        raise RuntimeError(f"Instrument ticker status inactive: {instrument_name}: {ticker}")

    min_amount = float(ticker["minimum_amount"])
    best_price = ticker["best_ask_price"] if side == OrderSide.BUY else ticker["best_bid_price"]

    # Derive RPC 11013: Limit price X must not have more than Y decimal places
    price = float(best_price)

    # TODO: balances ????
    collaterals = derive_client.get_collaterals()
    assert len(collaterals) == 1, "Account collaterals assumption violated"

    collateral = collaterals.pop()
    if float(collateral["mark_value"]) < min_amount * price:
        msg = (
            f"Cannot afford minimum position size.\n"
            f"Minimum: {min_amount}, Price: {price}, Total cost: {min_amount * price}\n"
            f"Collateral market value: {collateral['mark_value']}"
        )
        raise ValueError(msg)

    order = derive_client.create_order(
        price=price,
        amount=min_amount,
        instrument_name=instrument_name,
        side=side,
        order_type=OrderType.MARKET,
        instrument_type=instrument_type,
    )

    wait_until(
        derive_client.get_order,
        condition=is_filled,
        order_id=order["order_id"],
    )

    yield derive_client

    close_all_positions(derive_client)
    remaining_positions = get_all_positions(derive_client)
    if any(remaining_positions.values()):
        raise ValueError(f"Post-existing positions found: {remaining_positions}")


@pytest.mark.parametrize(
    "client_with_position",
    [
        (UnderlyingCurrency.ETH, InstrumentType.PERP, OrderSide.BUY),
        (UnderlyingCurrency.ETH, InstrumentType.PERP, OrderSide.SELL),
    ],
    indirect=True,
    ids=["eth-perp-buy", "eth-perp-sell"],
)
def test_single_position_transfer(client_with_position):
    """Test single position transfer using transfer_position method"""

    derive_client = client_with_position
    source_subaccount_id = derive_client.subaccount_ids[0]
    target_subaccount_id = derive_client.subaccount_ids[1]
    assert derive_client.subaccount_id == source_subaccount_id

    initial_positions = get_all_positions(derive_client)

    if len(source_positions := initial_positions[source_subaccount_id]) != 1:
        raise ValueError(f"Expected one open position on source, found: {source_positions}")
    if target_positions := initial_positions[target_subaccount_id]:
        raise ValueError(f"Expected zero open position on target, found: {target_positions}")

    initial_position = source_positions[0]
    amount = float(initial_position["amount"])
    instrument_name = initial_position["instrument_name"]
    position_transfer = derive_client.transfer_position(
        instrument_name=instrument_name,
        amount=amount,
        to_subaccount_id=target_subaccount_id,
    )

    assert position_transfer.maker_trade.transaction_id == position_transfer.taker_trade.transaction_id

    derive_tx_result = wait_until(
        derive_client.get_transaction,
        condition=is_settled,
        transaction_id=position_transfer.maker_trade.transaction_id,
    )

    assert derive_tx_result.status == DeriveTxStatus.SETTLED

    action_data = derive_tx_result.data["action_data"]
    assert position_transfer.taker_trade.subaccount_id == action_data["taker_account"]
    assert position_transfer.maker_trade.subaccount_id == action_data["fill_details"][0]["filled_account"]

    final_positions = get_all_positions(derive_client)
    assert len(final_positions[source_subaccount_id]) == 0
    assert len(final_positions[target_subaccount_id]) == 1

    final_position = final_positions[target_subaccount_id][0]
    assert final_position["instrument_name"] == initial_position["instrument_name"]
    assert final_position["amount"] == initial_position["amount"]


@pytest.fixture
def client_with_positions(derive_client):
    """Setup position for transfer"""
    currency = UnderlyingCurrency.ETH
    instruments = derive_client.fetch_instruments(
        instrument_type=InstrumentType.OPTION,
        currency=currency,
    )
    active = [i for i in instruments if i.get("is_active")]
    currency = derive_client.fetch_currency(currency.name)
    spot = Decimal(currency["spot_price"])

    groups = {}
    for instrument in active:
        option_details = instrument["option_details"]
        expiry = option_details["expiry"]
        strike = Decimal(option_details["strike"])
        option_type = option_details["option_type"]
        key = (expiry, strike)
        groups.setdefault(key, {})[option_type] = instrument

    candidates = []
    for (expiry, strike), pair in groups.items():
        if "C" in pair and "P" in pair:
            call_ticker = derive_client.fetch_ticker(pair["C"]["instrument_name"])
            put_ticker = derive_client.fetch_ticker(pair["P"]["instrument_name"])

            # select those that we cannot only open, but also close to cleanup test
            call_has_liquidity = (
                Decimal(call_ticker["best_bid_amount"]) > 0 and Decimal(call_ticker["best_ask_amount"]) > 0
            )
            put_has_liquidity = (
                Decimal(put_ticker["best_bid_amount"]) > 0 and Decimal(put_ticker["best_ask_amount"]) > 0
            )
            if call_has_liquidity and put_has_liquidity:
                dist = abs(strike - spot)
                candidates.append((expiry, dist, strike, call_ticker, put_ticker))

    # choose earliest expiry, then nearest strike (min dist)
    candidates.sort(key=lambda t: (t[0], t[1]))
    chosen_expiry, _, chosen_strike, call_ticker, put_ticker = candidates[0]

    call_amount = Decimal(call_ticker["minimum_amount"])
    put_amount = Decimal(put_ticker["minimum_amount"])

    call_price = float(call_ticker["best_ask_price"]) * 1.05
    put_price = float(put_ticker["best_ask_price"]) * 1.05

    # call leg
    order = derive_client.create_order(
        price=call_price,
        amount=str(call_amount),
        instrument_name=call_ticker["instrument_name"],
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        instrument_type=InstrumentType.OPTION,
        time_in_force=TimeInForce.GTC,
    )

    wait_until(
        derive_client.get_order,
        condition=is_filled,
        order_id=order["order_id"],
    )

    # put leg
    derive_client.create_order(
        price=put_price,
        amount=str(put_amount),
        instrument_name=put_ticker["instrument_name"],
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        instrument_type=InstrumentType.OPTION,
        time_in_force=TimeInForce.GTC,
    )

    wait_until(
        derive_client.get_order,
        condition=is_filled,
        order_id=order["order_id"],
    )

    yield derive_client

    close_all_positions(derive_client)
    remaining_positions = get_all_positions(derive_client)
    if any(remaining_positions.values()):
        raise ValueError(f"Post-existing positions found: {remaining_positions}")


def test_transfer_positions(client_with_positions):
    """Test transfering positions."""

    derive_client = client_with_positions

    source_subaccount_id = derive_client.subaccount_ids[0]
    target_subaccount_id = derive_client.subaccount_ids[1]
    assert derive_client.subaccount_id == source_subaccount_id

    initial_positions = get_all_positions(derive_client)

    if len(source_positions := initial_positions[source_subaccount_id]) < 2:
        raise ValueError(f"Expected at least two open position on source, found: {source_positions}")
    if target_positions := initial_positions[target_subaccount_id]:
        raise ValueError(f"Expected zero open position on target, found: {target_positions}")

    positions = []
    for position in source_positions:
        position_spec = PositionSpec(
            amount=position["amount"],
            instrument_name=position["instrument_name"],
        )
        positions.append(position_spec)

    positions_transfer = derive_client.transfer_positions(
        positions=positions,
        to_subaccount_id=target_subaccount_id,
        direction=OrderSide.BUY,
    )

    assert positions_transfer  # TODO

    final_positions = get_all_positions(derive_client)

    assert len(final_positions[source_subaccount_id]) == 0
    assert len(final_positions[target_subaccount_id]) > 1
