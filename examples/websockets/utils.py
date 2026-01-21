"""
Utility functions for WebSocket examples.
"""

from decimal import Decimal

from derive_client.data_types.generated_models import AssetType, PositionResponseSchema


def get_default_position(instrument_name: str) -> PositionResponseSchema:
    return PositionResponseSchema(
        instrument_name=instrument_name,
        amount=Decimal(0),
        average_price=Decimal(0),
        unrealized_pnl=Decimal(0),
        realized_pnl=Decimal(0),
        leverage=Decimal(0),
        maintenance_margin=Decimal(0),
        initial_margin=Decimal(0),
        liquidation_price=None,
        amount_step=Decimal(0),
        average_price_excl_fees=Decimal(0),
        creation_timestamp=0,
        cumulative_funding=Decimal(0),
        delta=Decimal(0),
        gamma=Decimal(0),
        vega=Decimal(0),
        theta=Decimal(0),
        unrealized_pnl_excl_fees=Decimal(0),
        index_price=Decimal(0),
        mark_price=Decimal(0),
        instrument_type=AssetType.perp,
        mark_value=Decimal(0),
        total_fees=Decimal(0),
        net_settlements=Decimal(0),
        open_orders_margin=Decimal(0),
        pending_funding=Decimal(0),
        realized_pnl_excl_fees=Decimal(0),
    )
