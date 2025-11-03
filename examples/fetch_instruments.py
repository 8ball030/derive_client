"""
Sample of fetching instruments from the derive client, and printing the result.
"""

from derive_client.derive import DeriveClient
from rich import print

from derive_client.data_types import Environment, InstrumentType, UnderlyingCurrency
from tests.conftest import TEST_PRIVATE_KEY, TEST_WALLET


def main():
    """
    Demonstrate fetching instruments from the derive client.
    """

    client = DeriveClient(
        wallet=TEST_WALLET,
        private_key=TEST_PRIVATE_KEY,
        env=Environment.TEST,
    )

    currency = UnderlyingCurrency.BTC
    for instrument_type in [InstrumentType.OPTION, InstrumentType.PERP]:
        print(f"Fetching instruments for {currency} {instrument_type}")
        instruments = client.fetch_instruments(instrument_type=instrument_type, currency=currency)
        print(instruments)


if __name__ == "__main__":
    main()
