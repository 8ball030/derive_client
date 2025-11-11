from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from msgspec import Struct

from derive_client.data_types.generated_models import Direction


class TradesInstrumentNameChannelSchema(Struct):
    instrument_name: str


class TradePublicResponseSchema(Struct):
    direction: Direction
    index_price: Decimal
    instrument_name: str
    mark_price: Decimal
    timestamp: int
    trade_amount: Decimal
    trade_id: str
    trade_price: Decimal
    quote_id: Optional[str] = None


class TradesInstrumentNameNotificationParamsSchema(Struct):
    channel: str
    data: List[TradePublicResponseSchema]


class TradesInstrumentNameNotificationSchema(Struct):
    method: str
    params: TradesInstrumentNameNotificationParamsSchema


class TradesInstrumentNamePubSubSchema(Struct):
    channel_params: TradesInstrumentNameChannelSchema
    notification: TradesInstrumentNameNotificationSchema


class TradesInstrumentName(TradesInstrumentNamePubSubSchema):
    pass
