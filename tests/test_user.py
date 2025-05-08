"""
User tests
"""

from time import sleep

import pytest

from derive_client.data_types import OrderSide, OrderType


@pytest.mark.skip(reason="This test is not meant to be run in CI")
@pytest.mark.parametrize(
    "instrument_name, side, price",
    [
        ("ETH-PERP", OrderSide.BUY, 200),
    ],
)
def test_can_get_tickers(derive_client, instrument_name, side, price):
    """
    Test if user can get tickers
    We wait for 60 seconds to confirm we have not lost connection
    """
    result = derive_client.create_order(
        price=price,
        amount=1,
        instrument_name=instrument_name,
        side=OrderSide(side),
        order_type=OrderType.LIMIT,
    )
    assert "error" not in result
    sleep(60)
    derive_client.cancel_all()
