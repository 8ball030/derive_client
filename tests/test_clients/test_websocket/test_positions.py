"""Tests for Positions module."""

import time

import pytest

from derive_client._clients.rest.http.subaccount import Subaccount
from derive_client._clients.utils import PositionTransfer
from derive_client.data_types.generated_models import (
    Direction,
    PositionResponseSchema,
    PrivateTransferPositionResultSchema,
    PrivateTransferPositionsResultSchema,
    TxStatus,
)
from tests.conftest import assert_api_calls


def _get_open_positions_for_instrument(
    subaccount: Subaccount,
    *instrument_name: str,
) -> list[PositionResponseSchema]:
    positions = subaccount.positions.list()
    return [p for p in positions if p.instrument_name in instrument_name and p.amount != 0]


def _wait_for_tx_settlement(
    client,
    transaction_id: str,
    timeout: int = 30,
    poll_interval: float = 1.0,
):
    start_time = time.time()
    while time.time() - start_time < timeout:
        transaction = client.transactions.get(transaction_id=transaction_id)
        if transaction.status == TxStatus.settled:
            return transaction
        time.sleep(poll_interval)
    raise TimeoutError(f"on transaction settlement: transaction_id={transaction_id} timeout={timeout}s")


@pytest.mark.skip("Requires liquidity on testnet for market orders.")
def test_position_transfer(client_owner_wallet_with_position):
    instrument_name = "ETH-PERP"

    client_owner_wallet_with_position.fetch_subaccounts()
    subaccount_a, subaccount_b = client_owner_wallet_with_position.cached_subaccounts[:2]

    positions_a = _get_open_positions_for_instrument(subaccount_a, instrument_name)
    positions_b = _get_open_positions_for_instrument(subaccount_b, instrument_name)

    if positions_a and not positions_b:
        source = subaccount_a
        target = subaccount_b
        initial_position = positions_a[0]
    elif positions_b and not positions_a:
        source = subaccount_b
        target = subaccount_a
        initial_position = positions_b[0]
    else:
        source = subaccount_a
        target = subaccount_b
        initial_position = positions_a[0]

    with assert_api_calls(client_owner_wallet_with_position, expected=1):
        transfer = source.positions.transfer(
            amount=initial_position.amount,  # can be negative
            instrument_name=initial_position.instrument_name,
            to_subaccount=target.id,
        )

    assert isinstance(transfer, PrivateTransferPositionResultSchema)
    assert transfer.taker_trade.transaction_id == transfer.maker_trade.transaction_id

    _wait_for_tx_settlement(
        client=client_owner_wallet_with_position,
        transaction_id=transfer.taker_trade.transaction_id,
    )

    source_positions = _get_open_positions_for_instrument(source, instrument_name)
    target_positions = _get_open_positions_for_instrument(target, instrument_name)

    assert not source_positions
    assert target_positions


@pytest.mark.skip("Requires liquidity on testnet for market orders.")
def test_position_transfer_batch(client_owner_wallet_with_position):
    client_owner_wallet_with_position.fetch_subaccounts()
    subaccount_a, subaccount_b = client_owner_wallet_with_position.cached_subaccounts[1:3]

    positions_a = [p for p in subaccount_a.positions.list(is_open=True)]
    positions_b = [p for p in subaccount_b.positions.list(is_open=True)]

    if len(positions_a) >= 2:
        source = subaccount_a
        target = subaccount_b
        initial_positions = positions_a
    elif len(positions_b) >= 2:
        source = subaccount_b
        target = subaccount_a
        initial_positions = positions_b
    else:
        raise ValueError(
            "Expected exactly one subaccount to have open positions. ",
            f"Found: subaccount_a={len(positions_a)}, subaccount_b={len(positions_b)}",
        )

    positions_by_currency: dict[str, list[PositionResponseSchema]] = {}
    for position in initial_positions:
        positions_by_currency.setdefault(position.instrument_name.split("-")[0], []).append(position)

    most_position_currency = max(positions_by_currency.items(), key=lambda item: len(item[1]))[0]
    most_positions = positions_by_currency[most_position_currency]
    positions = [
        PositionTransfer(
            amount=position.amount,
            instrument_name=position.instrument_name,
        )
        for position in most_positions
    ]

    direction = Direction.buy
    with assert_api_calls(client_owner_wallet_with_position, expected=1):
        transfer_batch = source.positions.transfer_batch(
            positions=positions,
            direction=direction,
            to_subaccount=target.id,
        )
        time.sleep(1)

    assert isinstance(transfer_batch, PrivateTransferPositionsResultSchema)
    assert transfer_batch.maker_quote.rfq_id == transfer_batch.taker_quote.rfq_id

    source_positions = subaccount_a.positions.list(is_open=True, currency=most_position_currency)
    target_positions = subaccount_b.positions.list(is_open=True, currency=most_position_currency)

    assert len(source_positions) == 0
    assert len(target_positions) >= 0
