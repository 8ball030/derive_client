from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Optional

from msgspec import Struct

from derive_client.data_types.channels.enums import MarginType, State


class AuctionsWatchChannelSchema(Struct):
    pass


class AuctionDetailsSchema(Struct):
    estimated_bid_price: Decimal
    estimated_discount_pnl: Decimal
    estimated_mtm: Decimal
    estimated_percent_bid: Decimal
    last_seen_trade_id: int
    margin_type: MarginType
    min_cash_transfer: Decimal
    min_price_limit: Decimal
    subaccount_balances: Dict[str, Decimal]
    currency: Optional[str] = None


class AuctionResultSchema(Struct):
    state: State
    subaccount_id: int
    timestamp: int
    details: Optional[AuctionDetailsSchema] = None


class AuctionsWatchNotificationParamsSchema(Struct):
    channel: str
    data: List[AuctionResultSchema]


class AuctionsWatchNotificationSchema(Struct):
    method: str
    params: AuctionsWatchNotificationParamsSchema


class AuctionsWatchPubSubSchema(Struct):
    channel_params: AuctionsWatchChannelSchema
    notification: AuctionsWatchNotificationSchema


class AuctionsWatch(AuctionsWatchPubSubSchema):
    pass
