"""
Sample for cancelling an order on the derive client.
"""

from derive_client.derive import DeriveClient
from rich import print

from derive_client.data_types import Environment
from tests.conftest import TEST_PRIVATE_KEY, TEST_WALLET


def main():
    """
    Demonstrate canceling all orders on the derive client.
    """

    client = DeriveClient(wallet=TEST_WALLET, private_key=TEST_PRIVATE_KEY, env=Environment.TEST)
    order = client.cancel_all()
    print(order)


if __name__ == "__main__":
    main()
