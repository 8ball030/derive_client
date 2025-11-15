"""
Market Data: Exploring Available Markets and Price Information

This example demonstrates:
1. Discovering available currencies and instruments
2. Finding trading opportunities (bid-ask spreads)
3. Monitoring market conditions across assets
4. Comparing perpetual vs option markets
5. Using cached vs fresh data

Prerequisites:
- None! Market data is public and doesn't require authentication
"""

from decimal import Decimal
from pathlib import Path

from derive_client import HTTPClient
from derive_client.data_types import InstrumentType

# Setup
env_file = Path(__file__).parent.parent / ".env.template"
client = HTTPClient.from_env(env_file=env_file)
client.connect()

print("=" * 60)
print("1. DISCOVER AVAILABLE MARKETS")
print("=" * 60)

# Get all currencies
currencies = client.markets.get_all_currencies()
print(f"\nAvailable currencies: {len(currencies)}")
for curr in currencies[:5]:  # Show first 5
    print(f"  {curr.currency}: ${curr.spot_price:.2f}")
print("  ...")

# Get instruments for ETH
eth_perps = client.markets.get_instruments(
    currency="ETH",
    expired=False,
    instrument_type=InstrumentType.perp,
)
print(f"\nETH perpetuals: {len(eth_perps)}")
for perp in eth_perps:
    print(f"  {perp.instrument_name}")

eth_options = client.markets.get_instruments(
    currency="ETH",
    expired=False,
    instrument_type=InstrumentType.option,
)
print(f"\nETH options: {len(eth_options)} active")

print("\n" + "=" * 60)
print("2. FIND TIGHT SPREADS (Best Trading Conditions)")
print("=" * 60)

# Compare spreads across major perpetuals
perp_names = ["ETH-PERP", "BTC-PERP"]
spreads = []

print("\nBid-Ask Spreads (lower = better liquidity):")
for instrument in perp_names:
    ticker = client.markets.get_ticker(instrument_name=instrument)

    bid = Decimal(ticker.best_bid_price)
    ask = Decimal(ticker.best_ask_price)
    mid = (bid + ask) / 2
    spread_bps = ((ask - bid) / mid) * 10_000  # Basis points

    spreads.append((instrument, spread_bps, mid))
    print(f"\n  {instrument}:")
    print(f"    Bid: ${bid:.2f}")
    print(f"    Ask: ${ask:.2f}")
    print(f"    Spread: {spread_bps:.2f} bps")

# Find tightest spread
best_spread = min(spreads, key=lambda x: x[1])
print(f"\n✅ Tightest spread: {best_spread[0]} ({best_spread[1]:.2f} bps)")
print("   → Best market for large orders")

print("\n" + "=" * 60)
print("3. MARKET MOMENTUM (24h Price Changes)")
print("=" * 60)

# Compare 24h performance
print("\n24h Performance:")
for curr in currencies[:5]:
    change = curr.spot_price - curr.spot_price_24h
    change_pct = (change / curr.spot_price_24h) * 100 if curr.spot_price_24h else Decimal("0")
    arrow = "📈" if change_pct > 0 else "📉"
    print(f"  {arrow} {curr.currency}: {change_pct:+.2f}% (${curr.spot_price:.2f})")

print("\n" + "=" * 60)
print("4. INSTRUMENT DETAILS & CONSTRAINTS")
print("=" * 60)

# Deep dive on specific instrument
eth_perp = client.markets.get_instrument(instrument_name="ETH-PERP")
ticker = client.markets.get_ticker(instrument_name="ETH-PERP")

print(f"\n{eth_perp.instrument_name} Details:")
print(f"  Base currency: {eth_perp.base_currency}")
print(f"  Quote currency: {eth_perp.quote_currency}")
print(f"  Tick size: ${eth_perp.tick_size}")
print(f"  Min trade size: {eth_perp.minimum_amount}")
print(f"  Max trade size: {eth_perp.maximum_amount}")

print("\n  Current state:")
print(f"    Mark price: ${ticker.mark_price:.2f}")
print(f"    Index price: ${ticker.index_price}")
print(f"    Funding rate: {ticker.perp_details.funding_rate * 100:.4f}%")
print(f"    24h volume: ${ticker.stats.contract_volume:,.0f}")
print(f"    Open interest: {ticker.stats.open_interest:.4f}")

# Check if funding is favorable
funding_rate = Decimal(ticker.perp_details.funding_rate)
if funding_rate > 0:
    print(f"\n  💡 Funding: Longs pay shorts ({funding_rate * 100:.4f}%)")
    print("     → Consider shorting for positive carry")
elif funding_rate < 0:
    print(f"\n  💡 Funding: Shorts pay longs ({abs(funding_rate) * 100:.4f}%)")
    print("     → Consider longing for positive carry")

print("\n" + "=" * 60)
print("5. OPTIONS MARKET OVERVIEW")
print("=" * 60)

# Get ETH options expiring soon
if eth_options:
    print(f"\nETH Options: {len(eth_options)} available")

    # Group by expiry
    expiries = {}
    for opt in eth_options:
        expiry = opt.option_details.expiry
        if expiry not in expiries:
            expiries[expiry] = []
        expiries[expiry].append(opt)

    print(f"Expiry dates: {len(expiries)}")
    for expiry in sorted(expiries.keys())[:3]:  # Next 3 expiries
        opts = expiries[expiry]
        calls = [o for o in opts if "C" in o.instrument_name]
        puts = [o for o in opts if "P" in o.instrument_name]
        print(f"  {expiry}: {len(calls)} calls, {len(puts)} puts")

    # Show sample option
    sample = eth_options[0]
    print(f"\nSample option: {sample.instrument_name}")
    print(f"  Strike: ${sample.option_details.strike}")
    print(f"  Type: {'Call' if 'C' in sample.instrument_name else 'Put'}")
    print(f"  Expiry: {sample.option_details.expiry}")

print("\n" + "=" * 60)
print("6. CACHING FOR PERFORMANCE")
print("=" * 60)

client.disconnect()

print("\n✅ Market data exploration complete!")
print("\nKey insights:")
print("  • Check spreads before large orders (tight = better)")
print("  • Monitor funding rates for carry opportunities")
print("  • Use caching to reduce API calls and improve performance")
print("  • 24h price changes help identify momentum")
