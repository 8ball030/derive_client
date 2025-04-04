"""
Sample of fetching instruments from the derive client, and printing the result.
"""
from rich import print

from derive_client.derive import DeriveClient
from derive_client.enums import Environment, InstrumentType
from tests.conftest import TEST_PRIVATE_KEY, TEST_WALLET


def main():
    """
    Demonstrate fetching instruments from the derive client.
    """

    client = DeriveClient(
        TEST_PRIVATE_KEY,
        wallet=TEST_WALLET,
        env=Environment.TEST,
    )
    client.subaccount_id = 132849

    for instrument_type in [InstrumentType.OPTION, InstrumentType.PERP]:
        print(f"Fetching instruments for {instrument_type}")
        instruments = client.fetch_instruments(instrument_type=instrument_type)
        print(instruments)


if __name__ == "__main__":
    main()
