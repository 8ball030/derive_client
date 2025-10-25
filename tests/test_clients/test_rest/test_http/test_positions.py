"""Tests for Positions module."""

import time

from derive_client._clients.rest.http.subaccount import Subaccount
from derive_client._clients.utils import PositionTransfer
from derive_client.data.generated.models import (
    Direction,
    PositionResponseSchema,
    PrivateTransferPositionResultSchema,
    PrivateTransferPositionsResultSchema,
    TxStatus,
)
from tests.test_clients.test_rest.test_http.conftest import assert_api_calls


def _get_open_positions_for_instrument(subaccount: Subaccount, *instrument_name: str) -> list[PositionResponseSchema]:
    positions = subaccount.positions.list().positions
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


def test_position_transfer(client_owner_wallet):
    instrument_name = "ETH-PERP"

    client_owner_wallet.fetch_subaccounts()
    subaccount_a, subaccount_b = client_owner_wallet.cached_subaccounts[:2]

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
        raise ValueError(
            f"Expected exactly one subaccount to have {instrument_name} position. ",
            f"Found: subaccount_a={len(positions_a)}, subaccount_b={len(positions_b)}",
        )

    with assert_api_calls(client_owner_wallet, expected=1):
        transfer = source.positions.transfer(
            amount=initial_position.amount,  # can be negative
            instrument_name=initial_position.instrument_name,
            to_subaccount=target.id,
        )

    assert isinstance(transfer, PrivateTransferPositionResultSchema)
    assert transfer.taker_trade.transaction_id == transfer.maker_trade.transaction_id

    _transaction = _wait_for_tx_settlement(
        client=client_owner_wallet,
        transaction_id=transfer.taker_trade.transaction_id,
    )

    source_positions = _get_open_positions_for_instrument(source, instrument_name)
    target_positions = _get_open_positions_for_instrument(target, instrument_name)

    assert not source_positions
    assert target_positions


def test_position_transfer_batch(client_owner_wallet):
    instrument_names = ("BTC-PERP", "BTC-20251226-110000-C")

    client_owner_wallet.fetch_subaccounts()
    subaccount_a, subaccount_b = client_owner_wallet.cached_subaccounts[:2]

    positions_a = _get_open_positions_for_instrument(subaccount_a, *instrument_names)
    positions_b = _get_open_positions_for_instrument(subaccount_b, *instrument_names)

    if len(positions_a) == 2 and len(positions_b) != 2:
        source = subaccount_a
        target = subaccount_b
        initial_positions = positions_a
    elif len(positions_b) == 2 and len(positions_a) != 2:
        source = subaccount_b
        target = subaccount_a
        initial_positions = positions_b
    else:
        raise ValueError(
            f"Expected exactly one subaccount to have {instrument_names} positions. ",
            f"Found: subaccount_a={len(positions_a)}, subaccount_b={len(positions_b)}",
        )

    positions = []
    for position in initial_positions:
        position = PositionTransfer(
            amount=position.amount,
            instrument_name=position.instrument_name,
        )
        positions.append(position)

    direction = Direction.buy
    with assert_api_calls(client_owner_wallet, expected=1):
        transfer_batch = source.positions.transfer_batch(
            positions=positions,
            direction=direction,
            to_subaccount=target.id,
        )

    assert isinstance(transfer_batch, PrivateTransferPositionsResultSchema)
    assert transfer_batch.maker_quote.rfq_id == transfer_batch.taker_quote.rfq_id

    source_positions = _get_open_positions_for_instrument(source, *instrument_names)
    target_positions = _get_open_positions_for_instrument(target, *instrument_names)

    assert len(source_positions) != 2
    assert len(target_positions) == 2
