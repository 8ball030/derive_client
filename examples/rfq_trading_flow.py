"""
Complete RFQ (Request for Quote) trading flow demonstration.

This example shows:
1. Maker creating and posting quotes
2. Taker discovering and requesting quotes  
3. Price comparison with Deribit
4. Complete trade execution
"""

from rich import print
from derive_client.data_types import Environment
from derive_client.derive import DeriveClient
from tests.conftest import TEST_PRIVATE_KEY, TEST_WALLET


def setup_clients():
    """Setup separate clients for maker and taker roles"""

    maker_client = DeriveClient(wallet=TEST_WALLET, private_key=TEST_PRIVATE_KEY, env=Environment.TEST)
    taker_client = DeriveClient(wallet=TEST_WALLET, private_key=TEST_PRIVATE_KEY, env=Environment.TEST)

    maker_client.subaccount_id = maker_client.subaccount_ids[0] 
    taker_client.subaccount_id = taker_client.subaccount_ids[1]
    
    return maker_client, taker_client


def demonstrate_maker_flow(client):
    """Show maker creating and posting quotes"""
    print("\n[bold blue]MAKER FLOW[/bold blue]")


def demonstrate_taker_flow(client, quote_id):
    """Show taker requesting and accepting quotes"""
    print("\n[bold green]TAKER FLOW[/bold green]")


def compare_with_deribit(instrument_name):
    """Compare pricing with Deribit for reference"""
    print("\n[bold yellow]PRICE COMPARISON[/bold yellow]")


def main():
    """
    Complete RFQ trading demonstration
    """
    print("[bold]RFQ Trading Flow Demonstration[/bold]")
    
    maker_client, taker_client = setup_clients()
    
    # 1. Maker creates quote
    quote = demonstrate_maker_flow(maker_client)
    
    # 2. Price comparison
    compare_with_deribit(quote['instrument_name'])
    
    # 3. Taker accepts quote
    trade = demonstrate_taker_flow(taker_client, quote['quote_id'])
    
    print(f"\n[bold green]Trade completed: {trade}[/bold green]")


if __name__ == "__main__":
    main()
