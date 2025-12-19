from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from msgspec import Struct

from derive_client.data_types.generated_models import Direction, InstrumentType


class TradesInstrumentTypeCurrencyChannelSchema(Struct):
    currency: str
    instrument_type: InstrumentType


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


class TradesInstrumentTypeCurrencyNotificationParamsSchema(Struct):
    channel: str
    data: List[TradePublicResponseSchema]


class TradesInstrumentTypeCurrencyNotificationSchema(Struct):
    method: str
    params: TradesInstrumentTypeCurrencyNotificationParamsSchema


class TradesInstrumentTypeCurrencyPubSubSchema(Struct):
    channel_params: TradesInstrumentTypeCurrencyChannelSchema
    notification: TradesInstrumentTypeCurrencyNotificationSchema


class TradesInstrumentTypeCurrency(TradesInstrumentTypeCurrencyPubSubSchema):
    pass
