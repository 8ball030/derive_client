"""
Sample of fetching instruments from the derive client, and printing the result.
"""
from rich import print

from derive.derive import DeriveClient
from derive.enums import Environment, InstrumentType
from tests.test_main import TEST_PRIVATE_KEY


def main():
    """
    Demonstrate fetching instruments from the derive client.
    """

    client = DeriveClient(TEST_PRIVATE_KEY, env=Environment.PROD, subaccount_id=1)

    for instrument_type in [InstrumentType.OPTION, InstrumentType.PERP]:
        print(f"Fetching instruments for {instrument_type}")
        instruments = client.fetch_instruments(instrument_type=instrument_type)
        print(instruments)


if __name__ == "__main__":
    main()
