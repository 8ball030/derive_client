"""
Example of bridging funds from a Derive smart contract funding account to BASE
"""

import os

import click
from derive_client.derive import DeriveClient
from dotenv import load_dotenv

from derive_client.data_types import Address, ChainID, Currency, Environment

ChainChoice = click.Choice([c.name for c in ChainID])
CurrencyChoice = click.Choice([c.name for c in Currency])


@click.command()
@click.option("--chain-id", "-c", type=ChainChoice, required=True, help="The chain ID to bridge FROM.")
@click.option("--wallet", "-r", type=Address, required=True, help="The Derive smart contract wallet.")
@click.option("--currency", "-t", type=CurrencyChoice, required=True, help="The token symbol (e.g. weETH) to bridge.")
@click.option("--amount", "-a", type=float, required=True, help="The amount to deposit in ETH.")
def main(chain_id, wallet, currency, amount):
    """
    Withdraw asset from Derive to L1/L2 via the WithdrawWrapper.
    """

    load_dotenv()

    if (private_key := os.environ.get("ETH_PRIVATE_KEY")) is None:
        raise ValueError("`ETH_PRIVATE_KEY` not found in env.")

    client = DeriveClient(
        private_key=private_key,
        wallet=wallet,
        env=Environment.PROD,
    )

    receiver = client.signer.address
    client.withdraw_from_derive(chain_id=ChainID[chain_id], receiver=receiver, currency=currency, amount=amount)


if __name__ == "__main__":
    main()
