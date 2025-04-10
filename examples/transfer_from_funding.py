"""
Example of how to withdraw USDC from a subaccount to the funding account.
"""

from pathlib import Path

import click

from derive_client import DeriveClient
from derive_client.enums import CollateralAsset, Environment


@click.command()
@click.option('--signer-key-path', required=True, help='Path to signer key file')
@click.option('--derive-sc-wallet', required=True, help='Derive SC wallet address')
def main(signer_key_path, derive_sc_wallet):
    key_file = Path(signer_key_path)
    if not key_file.exists():
        click.echo(f"Signer key file not found: {signer_key_path}")
        return

    client = DeriveClient(
        private_key=key_file.read_text(),
        wallet=derive_sc_wallet,
        env=Environment.PROD,
    )
    subaccount_id = 48206
    client.subaccount_id = subaccount_id
    subaccounts = client.fetch_subaccounts()
    for subaccount in subaccounts:
        print(subaccount)

    if input("Do you want to withdraw USDC from subaccount to funding account? (y/n): ").lower() == 'y':
        print("Withdrawal cancelled.")
        to_funding_req = client.transfer_from_subaccount_to_funding(
            subaccount_id=client.subaccount_id,
            asset_name=CollateralAsset.USDC.name,
            amount=0.1,
        )

        print(f"Transfer from subaccount {client.subaccount_id} to funding account: {to_funding_req}")

    if input("Do you want to withdraw USDC from funding account to subaccount? (y/n): ").lower() == 'y':
        print("Withdrawal cancelled.")
        to_subaccount_req = client.transfer_from_funding_to_subaccount(
            subaccount_id=subaccount_id,
            asset_name=CollateralAsset.USDC.name,
            amount=0.1,
        )
        print(f"Transfer from funding account to subaccount {client.subaccount_id}: {to_subaccount_req}")


if __name__ == '__main__':
    main()
