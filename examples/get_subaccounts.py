"""
Simple demo script to show how to get a list of subaccounts.

This script is equivalent to the test_fetch_first_subaccount() test in tests/test_main.py.
"""

from pathlib import Path

import click
from derive_client.clients import HttpClient as DeriveClient

from derive_client.data_types import Environment


@click.command()
@click.option('--signer-key-path', required=True, type=Path, help='Path to signer key file')
@click.option('--derive-sc-wallet', required=True, help='Derive SC wallet address')
def main(signer_key_path: Path, derive_sc_wallet: str):
    """
    Demonstrate fetching subaccounts from the derive client.
    """

    if not signer_key_path.exists():
        click.echo(f"Signer key file not found: {signer_key_path}")

    client = DeriveClient(
        private_key=signer_key_path.read_text(),
        wallet=derive_sc_wallet,
        env=Environment.PROD,
    )
    subaccounts = client.fetch_subaccounts()
    for subaccount in subaccounts:
        print(subaccount)

    subaccounts = client.fetch_subaccounts()
    for subaccount in subaccounts['subaccount_ids']:
        client.subaccount_id = subaccount
        print(f"Subaccount ID: {subaccount}")
        client.cancel_all()
    print(subaccounts)


if __name__ == '__main__':
    main()
