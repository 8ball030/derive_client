"""
Example of how to withdraw USDC from a subaccount to the funding account.
"""

import os
from pathlib import Path

import click
from dotenv import load_dotenv

from derive_client import HTTPClient
from derive_client.data_types import Currency, Environment

directions = {
    "withdraw_from_subaccount": "Withdraw from subaccount to funding account",
    "deposit_to_subaccount": "Transfer from funding account to subaccount",
}


@click.command()
@click.option("--signer-key-path", required=True, help="Path to signer key file")
@click.option("--derive-sc-wallet", required=True, help="Derive SC wallet address")
@click.option(
    "--currency",
    type=click.Choice([c.name for c in Currency]),
    default=Currency.USDC.name,
    required=True,
    help="The currency to transfer",
)
@click.option(
    "--amount",
    type=float,
    default=0.1,
    required=True,
    help="The amount to transfer",
)
@click.option(
    "--function",
    type=click.Choice(directions.keys()),
    help="Function to execute: transfer_subaccount_to_funding or transfer_funding_to_subaccount",
    default="withdraw_from_subaccount",
)
@click.option(
    "--auto-confirm",
    is_flag=True,
    default=False,
    help="Confirm the transfer automatically without prompting",
)
def main(signer_key_path, derive_sc_wallet, currency: str, amount: float, function: str, auto_confirm: bool):
    """
    python examples/transfer_from_funding.py --signer-key-path ethereum_private_key.txt --derive-sc-wallet="0x0000000000000000000000000000000000000000" --currency "DRV"
    """  # noqa: E501
    key_file = Path(signer_key_path)
    if not key_file.exists():
        click.echo(f"Signer key file not found: {signer_key_path}")
        return

    load_dotenv()
    subaccount_id = os.environ.get("DERIVE_SUBACCOUNT_ID")
    if not subaccount_id:
        click.echo("SUBACCOUNT_ID not found in environment variables.")
        return

    subaccount_id = int(subaccount_id)

    currency = Currency[currency]
    client = HTTPClient(
        session_key=key_file.read_text(),
        wallet=derive_sc_wallet,
        env=Environment.PROD,
        subaccount_id=subaccount_id,
    )

    click.echo(f"Using subaccount ID: {client._subaccount_id}")
    click.echo(f"Using currency: {currency.name}")
    click.echo(f"Using amount: {amount}")
    click.echo(f"Using function: {function}")

    func = getattr(client.transactions, function, None)
    if func is None:
        click.echo(f"Function {function} not found in DeriveClient.")
        return
    if auto_confirm:
        click.echo(f"Auto-confirming transfer of {amount} {currency.name}.")
    else:
        click.echo(f"Transfer function: {function} will be executed manually.")
    if not auto_confirm and not click.confirm(
        f"Do you want to proceed with the transfer of {amount} {currency.name}?",
        default=True,
    ):
        click.echo("Transfer cancelled.")
        return
    try:
        response = func(
            subaccount_id=client._subaccount_id,
            asset_name=currency.name,
            amount=amount,
        )
        click.echo(f"Transfer response: {response}")
    except Exception as e:
        click.echo(f"An error occurred during the transfer: {e}")


if __name__ == "__main__":
    main()
