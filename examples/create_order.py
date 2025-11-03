"""
Sample for creating an order on the derive client.
"""

from derive_client.derive import DeriveClient
from rich import print

from derive_client.data_types import Environment, InstrumentType, OrderSide, UnderlyingCurrency
from tests.conftest import TEST_PRIVATE_KEY, TEST_WALLET


def main():
    """
    Demonstrate fetching instruments from the derive client.
    """

    instrument = InstrumentType.PERP
    currency = UnderlyingCurrency.ETH  # needs to match the subaccount_currency
    instrument_name = f"{currency.value}-{instrument.value}".upper()

    client = DeriveClient(wallet=TEST_WALLET, private_key=TEST_PRIVATE_KEY, env=Environment.TEST)
    order = client.create_order(
        instrument_name=instrument_name,
        side=OrderSide.BUY,
        price=1000,
        amount=1,
    )
    print(order)


if __name__ == "__main__":
    main()
