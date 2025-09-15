"""
Complete RFQ (Request for Quote) trading flow demonstration.

This example shows:
1. Maker creating and posting quotes
2. Taker discovering and requesting quotes  
3. Price comparison with Deribit
4. Complete trade execution
"""

from rich import print
from derive_client.data_types import Environment, OrderSide, InstrumentType, Currency
from derive_client.derive import DeriveClient
from tests.conftest import TEST_PRIVATE_KEY, TEST_WALLET


def setup_clients():
    """Setup separate clients for maker and taker roles"""

    maker_client = DeriveClient(wallet=TEST_WALLET, private_key=TEST_PRIVATE_KEY, env=Environment.TEST)
    taker_client = DeriveClient(wallet=TEST_WALLET, private_key=TEST_PRIVATE_KEY, env=Environment.TEST)

    maker_client.subaccount_id = maker_client.subaccount_ids[0]
    taker_client.subaccount_id = taker_client.subaccount_ids[1]

    return maker_client, taker_client


def create_demo_rfq(client):
    """Helper function to create a demo RFQ for maker flow demonstration"""
    print("   Creating demo RFQ...")

    # Get some active ETH options
    markets = client.fetch_instruments(instrument_type=InstrumentType.OPTION, currency=Currency.ETH)
    active_markets = [m for m in markets if m.get('is_active')]

    if len(active_markets) < 2:
        raise ValueError("Need at least 2 active markets for demo")

    breakpoint()

    # Create simple two-leg RFQ
    leg_1 = {
        'instrument_name': active_markets[0]['instrument_name'],
        'amount': 0.5,  # Smaller amount for demo
        'direction': OrderSide.BUY.value,
    }
    leg_2 = {'instrument_name': active_markets[1]['instrument_name'], 'amount': 0.5, 'direction': OrderSide.SELL.value}

    rfq_data = {
        'subaccount_id': client.subaccount_id,
        'legs': sorted([leg_1, leg_2], key=lambda x: x['instrument_name']),  # Sort by name
    }

    rfq_result = client.send_rfq(rfq_data)
    print(f"   Demo RFQ created: {rfq_result['rfq_id'][:8]}...")

    return rfq_result


def demonstrate_maker_flow(client):
    """Show maker creating and posting quotes for incoming RFQs"""
    print("\n[bold blue]MAKER FLOW - Market Making Operations[/bold blue]")

    # Step 1: Check for incoming RFQs
    print("1. Polling for incoming RFQs...")
    rfq_response = client.poll_rfqs()
    rfqs = rfq_response.get('rfqs', [])

    if not rfqs:
        print("   [yellow]No active RFQs found. In a real scenario, you would wait for RFQs.[/yellow]")
        print("   [dim]For demonstration, we'll create our own RFQ first...[/dim]")

        # Create a sample RFQ for demo purposes
        demo_rfq = create_demo_rfq(client)
        rfqs = [demo_rfq]

    print(f"   Found {len(rfqs)} active RFQ(s)")

    # Step 2: Analyze the first RFQ
    target_rfq = rfqs[0]
    print(f"\n2. Analyzing RFQ {target_rfq['rfq_id'][:8]}...")
    print(f"   - Legs: {len(target_rfq['legs'])}")
    for i, leg in enumerate(target_rfq['legs']):
        print(f"     Leg {i+1}: {leg['direction']} {leg['amount']} {leg['instrument_name']}")

    # Step 3: Calculate fair prices for each leg
    print("\n3. Calculating fair prices based on market data...")
    legs_with_prices = []

    for leg in target_rfq['legs']:
        # Get current market data
        ticker = client.fetch_ticker(leg['instrument_name'])
        mark_price = float(ticker['mark_price'])

        # Simple pricing logic (in practice, this would be more sophisticated)
        if leg['direction'] == 'buy':
            # If RFQ wants to buy, we sell - price slightly above mark
            our_price = mark_price * 1.02  # 2% markup
        else:
            # If RFQ wants to sell, we buy - price slightly below mark
            our_price = mark_price * 0.98  # 2% discount

        # Round to tick size
        tick_size = float(ticker['tick_size'])
        our_price = round(our_price / tick_size) * tick_size

        leg_with_price = {
            'instrument_name': leg['instrument_name'],
            'amount': leg['amount'],
            'direction': leg['direction'],
            'price': our_price,
        }
        legs_with_prices.append(leg_with_price)

        print(f"   {leg['instrument_name']}: Mark ${mark_price:.2f} → Our Quote ${our_price:.2f}")

    # Step 4: Create and submit quote
    print(f"\n4. Submitting quote for RFQ {target_rfq['rfq_id'][:8]}...")

    try:
        quote = client.create_quote(
            rfq_id=target_rfq['rfq_id'], legs=legs_with_prices, direction="sell"  # We're selling to the RFQ creator
        )

        print(f"   [green]✓[/green] Quote created successfully!")
        print(f"   Quote ID: {quote['quote_id'][:8]}...")
        print(f"   Status: {quote['status']}")
        print(f"   Direction: {quote['direction']}")

        # Step 5: Monitor quote status
        print("\n5. Quote submitted - waiting for potential execution...")
        print("   [dim]In practice, you would monitor for execution or expiry[/dim]")

        return quote

    except Exception as e:
        raise
        print(f"   [red]✗[/red] Failed to create quote: {e}")
        return None


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
