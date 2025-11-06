from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from msgspec import Struct

from derive_client.data_types.channels.enums import AssetType, MarginType


class MarginWatchChannelSchema(Struct):
    pass


class CollateralPublicResponseSchema(Struct):
    amount: Decimal
    asset_name: str
    asset_type: AssetType
    initial_margin: Decimal
    maintenance_margin: Decimal
    mark_price: Decimal
    mark_value: Decimal


class PositionPublicResponseSchema(Struct):
    amount: Decimal
    delta: Decimal
    gamma: Decimal
    index_price: Decimal
    initial_margin: Decimal
    instrument_name: str
    instrument_type: AssetType
    maintenance_margin: Decimal
    mark_price: Decimal
    mark_value: Decimal
    theta: Decimal
    vega: Decimal
    liquidation_price: Optional[Decimal] = None


class MarginWatchResultSchema(Struct):
    collaterals: List[CollateralPublicResponseSchema]
    currency: str
    initial_margin: Decimal
    maintenance_margin: Decimal
    margin_type: MarginType
    positions: List[PositionPublicResponseSchema]
    subaccount_id: int
    subaccount_value: Decimal
    valuation_timestamp: int


class MarginWatchNotificationParamsSchema(Struct):
    channel: str
    data: List[MarginWatchResultSchema]


class MarginWatchNotificationSchema(Struct):
    method: str
    params: MarginWatchNotificationParamsSchema


class MarginWatchPubSubSchema(Struct):
    channel_params: MarginWatchChannelSchema
    notification: MarginWatchNotificationSchema


class MarginWatch(MarginWatchPubSubSchema):
    pass
