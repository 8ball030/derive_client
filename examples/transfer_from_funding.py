"""
Example of how to withdraw USDC from a subaccount to the funding account.
"""

import os
from pathlib import Path

import click
from dotenv import load_dotenv

from derive_client import DeriveClient
from derive_client.data_types import Currency, Environment


@click.command()
@click.option("--signer-key-path", required=True, help="Path to signer key file")
@click.option("--derive-sc-wallet", required=True, help="Derive SC wallet address")
@click.option(
    "--asset",
    type=click.Choice([c.name for c in Currency]),
    default=Currency.USDC.name,
    required=True,
    help="The asset to transfer",
)
@click.option(
    "--amount",
    type=float,
    default=0.1,
    required=True,
    help="The amount to transfer",
)
def main(signer_key_path, derive_sc_wallet, asset: str, amount: float):
    """
    python examples/transfer_from_funding.py --signer-key-path ethereum_private_key.txt --derive-sc-wallet="0x0000000000000000000000000000000000000000" --asset "DRV"
    """  # noqa: E501
    key_file = Path(signer_key_path)
    if not key_file.exists():
        click.echo(f"Signer key file not found: {signer_key_path}")
        return

    load_dotenv()
    subaccount_id = os.environ.get("SUBACCOUNT_ID")
    if not subaccount_id:
        click.echo("SUBACCOUNT_ID not found in environment variables.")
        return

    client = DeriveClient(
        private_key=key_file.read_text(),
        wallet=derive_sc_wallet,
        env=Environment.PROD,
        subaccount_id=subaccount_id,
    )

    asset_name = Currency[asset].name

    if click.confirm(f"Withdraw {asset_name} from subaccount to funding account?", default=False):
        to_funding_req = client.transfer_from_subaccount_to_funding(
            subaccount_id=client.subaccount_id,
            asset_name=asset_name,
            amount=amount,
        )
        print(f"Transfer from subaccount {client.subaccount_id} to funding account: {to_funding_req}")
    elif click.confirm(f"Withdraw {asset_name} from funding account to subaccount?", default=False):
        to_subaccount_req = client.transfer_from_funding_to_subaccount(
            subaccount_id=subaccount_id,
            asset_name=asset_name,
            amount=amount,
        )
        print(f"Transfer from funding account to subaccount {client.subaccount_id}: {to_subaccount_req}")
    else:
        print("No transfer action selected.")


if __name__ == "__main__":
    main()
