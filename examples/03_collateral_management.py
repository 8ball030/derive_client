"""
Collateral Management: Deposits, Withdrawals, and Margin

This example demonstrates:
1. Viewing current collateral balances
2. Depositing assets from LightAccount to subaccount
3. Withdrawing assets from subaccount to LightAccount
4. Checking margin requirements
5. Simulating collateral changes (what-if scenarios)

Prerequisites:
- Funded LightAccount wallet (see 03_bridging_and_funding.py)
- At least some USDC in your LightAccount
"""

from decimal import Decimal
from pathlib import Path

from derive_client import HTTPClient
from derive_client.data_types.generated_models import SimulatedCollateralSchema

# Setup
env_file = Path(__file__).parent.parent / ".env.template"
client = HTTPClient.from_env(env_file=env_file)
client.connect()

print("=" * 60)
print("1. VIEW CURRENT COLLATERAL")
print("=" * 60)

# Get current subaccount collateral balances
collaterals = client.collateral.get()
print(f"\nSubaccount {client.active_subaccount.id} collateral:")

total_value = Decimal(0)
for collateral in collaterals.collaterals:
    value = collateral.amount * collateral.mark_price
    total_value += value
    print(f"  {collateral.asset_name}: {collateral.amount} (${value:.2f})")

print(f"\nTotal collateral value: ${total_value:.2f}")

print("\n" + "=" * 60)
print("2. CHECK MARGIN REQUIREMENTS")
print("=" * 60)

# Get margin details
margin = client.collateral.get_margin()
print("\nMargin requirements:")
print(f"  Initial margin: ${margin.post_initial_margin:.2f}")
print(f"  Maintenance margin: ${margin.post_maintenance_margin:.2f}")

# Calculate available margin (collateral - initial margin)
available_margin = total_value - margin.post_initial_margin
print(f"  Available margin: ${available_margin:.2f}")

# Calculate margin health
if margin.post_maintenance_margin > 0:
    health_ratio = (total_value / margin.post_maintenance_margin) * 100
    print(f"  Health ratio: {health_ratio:.1f}%")
    if health_ratio < 120:
        print("  ⚠️  Warning: Low margin health!")
    elif health_ratio > 200:
        print("  ✅ Good margin health")

print("\n" + "=" * 60)
print("3. WITHDRAW FROM SUBACCOUNT")
print("=" * 60)

# Withdraw back to LightAccount wallet
withdraw_amount = Decimal("15.0")
print(f"\nWithdrawing ${withdraw_amount} USDC from subaccount...")

withdrawal_result = client.collateral.withdraw_from_subaccount(
    amount=withdraw_amount,
    asset_name="USDC",
)

print("✅ Withdrawal submitted")
print(f"   Transaction ID: {withdrawal_result.transaction_id}")

# Verify final balances
collaterals_final = client.collateral.get()
usdc_final = next((c.amount for c in collaterals_final.collaterals if c.asset_name == "USDC"), Decimal(0))

print(f"\nFinal subaccount USDC: {usdc_final}")

print("\n" + "=" * 60)

# TODO: Feedback from Ksett / Josh
# print("\n" + "=" * 60)
# print("4. SIMULATE MARGIN IMPACT")
# print("=" * 60)
#
# # Current margin
# current_margin = client.collateral.get_margin()
# print("\nCurrent state:")
# print(f"  Initial margin required: ${current_margin.post_initial_margin:.2f}")
# print(f"  Available margin: ${total_value - current_margin.post_initial_margin:.2f}")
#
# # Simulate: What if I deposit more USDC?
# simulated_deposit = Decimal("100.0")
# simulated_collateral = [
#     SimulatedCollateralSchema(
#         amount=simulated_deposit,
#         asset_name="USDC",
#     )
# ]
#
# margin_with_deposit = client.collateral.get_margin(
#     simulated_collateral_changes=simulated_collateral,
# )
#
# new_total = total_value + simulated_deposit
# new_available = new_total - margin_with_deposit.post_initial_margin
#
# print(f"\nAfter ${simulated_deposit} USDC deposit:")
# print(f"  New available margin: ${margin_with_deposit.post_initial_margin:.2f}")
# print(f"  Available margin: ${new_available:.2f}")
# print(f"  Additional capacity: +${new_available - (total_value - current_margin.post_initial_margin):.2f}")

# Simulate: What if I withdraw?
simulated_withdrawal = Decimal("-50.0")  # Negative = withdrawal
simulated_withdrawal_change = [
    SimulatedCollateralSchema(
        amount=simulated_withdrawal,
        asset_name="USDC",
    )
]

margin_after_withdrawal = client.collateral.get_margin(
    simulated_collateral_changes=simulated_withdrawal_change,
)

withdrawn_total = total_value + simulated_withdrawal  # Add negative = subtract
withdrawn_available = withdrawn_total - margin_after_withdrawal.post_initial_margin

print(f"\nAfter ${abs(simulated_withdrawal)} USDC withdrawal:")
print(f"  Initial margin required: ${margin_after_withdrawal.post_initial_margin:.2f}")
print(f"  Available margin: ${withdrawn_available:.2f}")

if withdrawn_available < 0:
    print("  ⚠️  Warning: This would put you in margin call!")
else:
    print("  ✅ Safe to withdraw")

print("\n" + "=" * 60)
print("5. DEPOSIT TO SUBACCOUNT")
print("=" * 60)

# Check LightAccount balance before deposit
# account_state = client.account.get()
# usdc_in_wallet = next((b.amount for b in account_state.balances if b.currency == "USDC"), Decimal(0))
# print(f"\nLightAccount USDC balance: {usdc_in_wallet}")

# Get initial USDC in subaccount
collaterals = client.collateral.get()
usdc_before = next((c.amount for c in collaterals.collaterals if c.asset_name == "USDC"), Decimal(0))
print(f"Subaccount USDC balance: {usdc_before}")

# Deposit USDC to subaccount
deposit_amount = Decimal("10.0")
print(f"\nDepositing ${deposit_amount} USDC to subaccount...")

deposit_result = client.collateral.deposit_to_subaccount(
    amount=deposit_amount,
    asset_name="USDC",
)

print("✅ Deposit submitted")
print(f"   Transaction ID: {deposit_result.transaction_id}")

# Check updated subaccount collateral
collaterals_after = client.collateral.get()
usdc_after = next((c.amount for c in collaterals_after.collaterals if c.asset_name == "USDC"), Decimal(0))
print(f"\nSubaccount USDC after deposit: {usdc_after}")
print(f"Change: +{usdc_after - usdc_before}")
print("\n" + "=" * 60)
print("6. FINAL SUMMARY")
print("=" * 60)

# Final overview
final_collaterals = client.collateral.get()
final_margin = client.collateral.get_margin()

final_total = sum(c.amount * c.mark_price for c in final_collaterals.collaterals)
final_available = final_total - final_margin.post_initial_margin

print("\nCollateral breakdown:")
for c in final_collaterals.collaterals:
    if c.amount > 0:
        value = c.amount * c.mark_price
        pct = (value / final_total * 100) if final_total > 0 else 0
        print(f"  {c.asset_name}: {c.amount} (${value:.2f}, {pct:.1f}%)")

print("\nMargin status:")
print(f"  Total collateral: ${final_total:.2f}")
print(f"  Initial margin: ${final_margin.post_initial_margin:.2f}")
print(f"  Maintenance margin: ${final_margin.post_maintenance_margin:.2f}")
print(f"  Available: ${final_available:.2f}")

if final_margin.post_maintenance_margin > 0:
    health = (final_total / final_margin.post_maintenance_margin) * 100
    print(f"  Health: {health:.1f}%")

client.disconnect()

print("\n✅ Collateral management complete!")
print("\nKey takeaways:")
print("  • Deposit: LightAccount → Subaccount (deposit_to_subaccount)")
print("  • Withdraw: Subaccount → LightAccount (withdraw_from_subaccount)")
print("  • Always simulate margin impact before large withdrawals")
print("  • Maintain health ratio > 120% to avoid liquidation risk")
