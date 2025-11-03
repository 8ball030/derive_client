"""
Example demonstrating multiple position transfers using transfer_positions method.

This script shows how to transfer multiple positions between subaccounts in a single transaction.
Based on the working debug_position_lifecycle patterns.
"""

import time

from derive_client.derive import DeriveClient
from rich import print

from derive_client.data_types import (
    DeriveTxResult,
    DeriveTxStatus,
    Environment,
    InstrumentType,
    OrderSide,
    OrderType,
    TransferPosition,
    UnderlyingCurrency,
)

# Configuration - update these values for your setup
WALLET = "0xA419f70C696a4b449a4A24F92e955D91482d44e9"
PRIVATE_KEY = "0x2ae8be44db8a590d20bffbe3b6872df9b569147d3bf6801a35a28281a4816bbd"
ENVIRONMENT = Environment.TEST


def create_guaranteed_position(
    client, instrument_name, instrument_type, from_subaccount_id, to_subaccount_id, target_amount
):
    """Create a position using guaranteed fill strategy."""
    ticker = client.fetch_ticker(instrument_name)
    mark_price = float(ticker["mark_price"])
    trade_price = round(mark_price, 2)

    print(f"Creating {target_amount} position in {instrument_name} at {trade_price}")

    # Create counterparty order first
    client.subaccount_id = to_subaccount_id
    counterparty_side = OrderSide.BUY if target_amount < 0 else OrderSide.SELL

    counterparty_order = client.create_order(
        price=trade_price,
        amount=abs(target_amount),
        instrument_name=instrument_name,
        side=counterparty_side,
        order_type=OrderType.LIMIT,
        instrument_type=instrument_type,
    )
    print(f"Counterparty order: {counterparty_order['order_id']}")
    time.sleep(1.0)

    # Create main order
    client.subaccount_id = from_subaccount_id
    main_side = OrderSide.SELL if target_amount < 0 else OrderSide.BUY

    main_order = client.create_order(
        price=trade_price,
        amount=abs(target_amount),
        instrument_name=instrument_name,
        side=main_side,
        order_type=OrderType.LIMIT,
        instrument_type=instrument_type,
    )
    print(f"Main order: {main_order['order_id']}")
    time.sleep(2.0)

    # Check position
    try:
        position = client.get_position_amount(instrument_name, from_subaccount_id)
        print(f"Position created: {position}")
        return position, trade_price
    except ValueError:
        print(f"Failed to create position in {instrument_name}")
        return 0, trade_price


def main():
    """Example of transferring multiple positions between subaccounts."""
    print("[yellow]=== Multiple Position Transfer Example ===\n")

    # Initialize client
    client = DeriveClient(
        wallet=WALLET,
        private_key=PRIVATE_KEY,
        env=ENVIRONMENT,
    )

    # Get subaccounts
    subaccounts = client.fetch_subaccounts()
    subaccount_ids = subaccounts.get("subaccount_ids", [])

    if len(subaccount_ids) < 2:
        print("Error: Need at least 2 subaccounts for transfer")
        return

    from_subaccount_id = subaccount_ids[0]
    to_subaccount_id = subaccount_ids[1]

    print(f"Using subaccounts: {from_subaccount_id} -> {to_subaccount_id}")

    # Find active instruments - focus on ETH-PERP first
    try:
        eth_instruments = client.fetch_instruments(
            instrument_type=InstrumentType.PERP, currency=UnderlyingCurrency.ETH, expired=False
        )
        eth_active = [inst for inst in eth_instruments if inst.get("is_active", True)]

        if not eth_active:
            print("No active ETH instruments found")
            return

        # Use ETH-PERP as primary instrument
        primary_instrument = eth_active[0]["instrument_name"]
        print(f"Using primary instrument: {primary_instrument}")

    except Exception as e:
        print(f"Error fetching instruments: {e}")
        return

    # Check for existing positions first
    client.subaccount_id = from_subaccount_id
    existing_positions = []

    try:
        eth_position = client.get_position_amount(primary_instrument, from_subaccount_id)
        if abs(eth_position) > 0.1:  # Meaningful position
            existing_positions.append(
                {'instrument_name': primary_instrument, 'amount': eth_position, 'instrument_type': InstrumentType.PERP}
            )
            print(f"Found existing position in {primary_instrument}: {eth_position}")
    except ValueError:
        pass

    # If no existing positions, create one using guaranteed fill
    if not existing_positions:
        print("No existing positions - creating one for demonstration...")
        target_amount = -1.5  # Short position

        position_amount, trade_price = create_guaranteed_position(
            client, primary_instrument, InstrumentType.PERP, from_subaccount_id, to_subaccount_id, target_amount
        )

        if abs(position_amount) > 0.01:
            existing_positions.append(
                {
                    'instrument_name': primary_instrument,
                    'amount': position_amount,
                    'instrument_type': InstrumentType.PERP,
                }
            )

    if not existing_positions:
        print("No positions available for transfer")
        return

    print(f"\nPreparing to transfer {len(existing_positions)} positions:")
    for pos in existing_positions:
        print(f"  {pos['instrument_name']}: {pos['amount']}")

    # Create transfer list
    transfer_list = []
    for pos in existing_positions:
        ticker = client.fetch_ticker(pos['instrument_name'])
        transfer_price = float(ticker["mark_price"])

        transfer_position = TransferPosition(
            instrument_name=pos['instrument_name'],
            amount=abs(pos['amount']),
            limit_price=transfer_price,
        )
        transfer_list.append(transfer_position)
        print(f"Transfer: {pos['instrument_name']} amount={abs(pos['amount'])} price={transfer_price}")

    # Determine global direction based on first position
    # For short positions (negative), use "buy" direction when transferring
    first_position = existing_positions[0]
    global_direction = "buy" if first_position['amount'] < 0 else "sell"

    print(f"\nExecuting transfer with global_direction='{global_direction}'...")
    print("(For short positions, we use 'buy' direction as we're covering/buying back the short)")

    try:
        # Execute the transfer
        transfer_result = client.transfer_positions(
            positions=transfer_list,
            from_subaccount_id=from_subaccount_id,
            to_subaccount_id=to_subaccount_id,
            global_direction=global_direction,
        )

        print("Transfer completed!")
        print(f"Transaction ID: {transfer_result.transaction_id}")
        print(f"Status: {transfer_result.status.value}")

    except ValueError as e:
        if "No valid transaction ID found in response" in str(e):
            print(f"Warning: Transaction ID extraction failed: {e}")
            print("This is a known issue with transfer_positions - continuing with verification...")

            # Create dummy result for verification
            transfer_result = DeriveTxResult(
                data={"note": "transaction_id_extraction_failed"},
                status=DeriveTxStatus.SETTLED,
                error_log={},
                transaction_id="unknown",
                transaction_hash=None,
            )
        else:
            print(f"Error during transfer: {e}")
            print("This might be due to insufficient balance or invalid transfer direction")
            return
    except Exception as e:
        print(f"Error during transfer: {e}")
        return

    # Wait for settlement
    time.sleep(4)

    # Verify transfers
    print("\nVerifying transfers...")

    for pos in existing_positions:
        instrument_name = pos['instrument_name']
        original_amount = pos['amount']

        # Check source position
        client.subaccount_id = from_subaccount_id
        try:
            source_position = client.get_position_amount(instrument_name, from_subaccount_id)
        except ValueError:
            source_position = 0

        # Check target position
        client.subaccount_id = to_subaccount_id
        try:
            target_position = client.get_position_amount(instrument_name, to_subaccount_id)
        except ValueError:
            target_position = 0

        print(f"\n{instrument_name}:")
        print(f"  Original: {original_amount}")
        print(f"  Source after: {source_position}")
        print(f"  Target after: {target_position}")

        if abs(source_position) < abs(original_amount):
            print("  Status: Transfer successful (source position reduced)")
        elif abs(target_position) > 0:
            print("  Status: Position found in target (may include existing positions)")
        else:
            print("  Status: Verification inconclusive")

    print("\nMultiple position transfer example completed!")
    print("Note: Transfers add to existing positions in target account")


if __name__ == "__main__":
    main()
