"""
User tests
"""


from time import sleep

import pytest

from lyra.enums import OrderSide, OrderType


@pytest.mark.parametrize(
    "instrument_name, side, price",
    [
        ("ETH-PERP", OrderSide.BUY, 200),
    ],
)
def test_can_get_tickers(lyra_client, instrument_name, side, price):
    """
    Test if user can get tickers
    We wait for 60 seconds to confirm we have not lost connection
    """
    result = lyra_client.create_order(
        price=price,
        amount=1,
        instrument_name=instrument_name,
        side=OrderSide(side),
        order_type=OrderType.LIMIT,
    )
    assert "error" not in result
    sleep(60)
    lyra_client.cancel_all()
