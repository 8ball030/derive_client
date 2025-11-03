"""
Example: Transfer a single position using derive_client

This example shows how to use the derive_client to transfer a single position
between subaccounts using the transfer_position method.
"""

import time

from derive_client.derive import DeriveClient
from rich import print

from derive_client.data_types import Environment, InstrumentType, OrderSide, OrderType, UnderlyingCurrency

# Configuration - update these values for your setup
WALLET = "0xA419f70C696a4b449a4A24F92e955D91482d44e9"
PRIVATE_KEY = "0x2ae8be44db8a590d20bffbe3b6872df9b569147d3bf6801a35a28281a4816bbd"
ENVIRONMENT = Environment.TEST


def main():
    """Example of transferring a single position between subaccounts."""
    print("[blue]=== Single Position Transfer Example ===[/blue]\n")

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

    # Find an active instrument
    instruments = client.fetch_instruments(
        instrument_type=InstrumentType.PERP, currency=UnderlyingCurrency.ETH, expired=False
    )

    active_instruments = [inst for inst in instruments if inst.get("is_active", True)]
    if not active_instruments:
        print("No active instruments found")
        return

    instrument_name = active_instruments[0]["instrument_name"]
    print(f"Using instrument: {instrument_name}")

    # Check if we have a position to transfer
    client.subaccount_id = from_subaccount_id
    try:
        position_amount = client.get_position_amount(instrument_name, from_subaccount_id)
        print(f"Found existing position: {position_amount}")
    except ValueError:
        # Create a small position for demonstration
        print("No existing position - creating one for demo...")

        ticker = client.fetch_ticker(instrument_name)
        mark_price = float(ticker["mark_price"])
        trade_price = round(mark_price, 2)

        # Create a small short position
        order_result = client.create_order(
            price=trade_price,
            amount=1.0,
            instrument_name=instrument_name,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            instrument_type=InstrumentType.PERP,
        )
        print(f"Created order: {order_result['order_id']}")

        time.sleep(3)  # Wait for fill

        try:
            position_amount = client.get_position_amount(instrument_name, from_subaccount_id)
            print(f"Position after trade: {position_amount}")
        except ValueError:
            print("Failed to create position")
            return

    if abs(position_amount) < 0.01:
        print("No meaningful position to transfer")
        return

    # Get current market price for transfer
    ticker = client.fetch_ticker(instrument_name)
    transfer_price = float(ticker["mark_price"])
    # beacuse of `must not have more than 2 decimal places` error from the derive API
    transfer_price = round(transfer_price, 2)

    print("\nTransferring position...")
    print(f"  Amount: {abs(position_amount)}")
    print(f"  Price: {transfer_price}")
    print(f"  From: {from_subaccount_id}")
    print(f"  To: {to_subaccount_id}")

    # Execute the transfer
    transfer_result = client.transfer_position(
        instrument_name=instrument_name,
        amount=abs(position_amount),
        limit_price=transfer_price,
        from_subaccount_id=from_subaccount_id,
        to_subaccount_id=to_subaccount_id,
        position_amount=position_amount,
        instrument_type=InstrumentType.PERP,
        currency=UnderlyingCurrency.ETH,
    )

    print("\nTransfer completed!")
    print(f"Transaction ID: {transfer_result.transaction_id}")
    print(f"Status: {transfer_result.status.value}")

    # Wait for settlement
    time.sleep(3)

    # Verify the transfer
    print("\nVerifying transfer...")

    # Check source position
    client.subaccount_id = from_subaccount_id
    try:
        source_position = client.get_position_amount(instrument_name, from_subaccount_id)
        print(f"Source position: {source_position}")
    except ValueError:
        print("Source position: 0")

    # Check target position
    client.subaccount_id = to_subaccount_id
    try:
        target_position = client.get_position_amount(instrument_name, to_subaccount_id)
        print(f"Target position: {target_position}")
    except ValueError:
        print("Target position: 0")

    print("\nTransfer example completed!")


if __name__ == "__main__":
    main()
