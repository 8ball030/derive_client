"""
Example of bridging funds from Base to a Derive smart contract funding account
"""

import os

import click
from dotenv import load_dotenv

from derive_client.bridge.enums import ChainID, Currency
from derive_client.bridge.models import Address
from derive_client.derive import DeriveClient
from tests.conftest import Environment

ChainChoice = click.Choice([f"{c.name}" for c in ChainID])
CurrencyChoice = click.Choice(map(str, Currency))


@click.command()
@click.option("--chain-id", "-c", type=ChainChoice, required=True, help="The chain ID to bridge FROM.")
@click.option("--receiver", "-r", type=Address, required=True, help="The Derive smart contract wallet.")
@click.option("--currency", "-t", type=CurrencyChoice, required=True, help="The token symbol (e.g. weETH) to bridge.")
@click.option("--amount", "-a", type=float, required=True, help="The amount to deposit in ETH.")
def main(chain_id, receiver, currency, amount):
    """
    Deposit asset from L1/L2 into Derive subaccount via Superbridge.
    """

    load_dotenv()

    if (private_key := os.environ.get("ETH_PRIVATE_KEY")) is None:
        raise ValueError("`ETH_PRIVATE_KEY` not found in env.")

    client = DeriveClient(
        private_key=private_key,
        wallet=receiver,
        env=Environment.PROD,
    )

    client.deposit_to_derive(chain_id=chain_id, receiver=receiver, currency=currency, amount=amount)


if __name__ == "__main__":
    main()
