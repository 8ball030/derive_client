from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from msgspec import Struct

from derive_client.data_types.channels.enums import Direction, InvalidReason, LiquidityRole, Status
from derive_client.data_types.generated_models import CancelReason1 as CancelReason
from derive_client.data_types.generated_models import TxStatus as TxStatus


class SubaccountIdBestQuotesChannelSchema(Struct):
    subaccount_id: int


class RPCErrorFormatSchema(Struct):
    code: int
    message: str
    data: Optional[str] = None


class LegPricedSchema(Struct):
    amount: Decimal
    direction: Direction
    instrument_name: str
    price: Decimal


class QuoteResultPublicSchema(Struct):
    cancel_reason: CancelReason
    creation_timestamp: int
    direction: Direction
    fill_pct: Decimal
    last_update_timestamp: int
    legs: List[LegPricedSchema]
    legs_hash: str
    liquidity_role: LiquidityRole
    quote_id: str
    rfq_id: str
    status: Status
    subaccount_id: int
    tx_status: TxStatus
    wallet: str
    tx_hash: Optional[str] = None


class RFQGetBestQuoteResultSchema(Struct):
    direction: Direction
    estimated_fee: Decimal
    estimated_realized_pnl: Decimal
    estimated_realized_pnl_excl_fees: Decimal
    estimated_total_cost: Decimal
    filled_pct: Decimal
    invalid_reason: InvalidReason
    is_valid: bool
    post_initial_margin: Decimal
    pre_initial_margin: Decimal
    suggested_max_fee: Decimal
    best_quote: Optional[QuoteResultPublicSchema] = None
    down_liquidation_price: Optional[Decimal] = None
    orderbook_total_cost: Optional[Decimal] = None
    post_liquidation_price: Optional[Decimal] = None
    up_liquidation_price: Optional[Decimal] = None


class BestQuoteChannelResultSchema(Struct):
    rfq_id: str
    error: Optional[RPCErrorFormatSchema] = None
    result: Optional[RFQGetBestQuoteResultSchema] = None


class SubaccountIdBestQuotesNotificationParamsSchema(Struct):
    channel: str
    data: List[BestQuoteChannelResultSchema]


class SubaccountIdBestQuotesNotificationSchema(Struct):
    method: str
    params: SubaccountIdBestQuotesNotificationParamsSchema


class SubaccountIdBestQuotesPubSubSchema(Struct):
    channel_params: SubaccountIdBestQuotesChannelSchema
    notification: SubaccountIdBestQuotesNotificationSchema


class SubaccountIdBestQuotes(SubaccountIdBestQuotesPubSubSchema):
    pass
