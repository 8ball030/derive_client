from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from msgspec import Struct

from derive_client.data_types.channels.enums import Direction, LiquidityRole
from derive_client.data_types.generated_models import TxStatus as TxStatus


class SubaccountIdTradesChannelSchema(Struct):
    subaccount_id: int


class TradeResponseSchema(Struct):
    direction: Direction
    expected_rebate: Decimal
    index_price: Decimal
    instrument_name: str
    is_transfer: bool
    label: str
    liquidity_role: LiquidityRole
    mark_price: Decimal
    order_id: str
    realized_pnl: Decimal
    realized_pnl_excl_fees: Decimal
    subaccount_id: int
    timestamp: int
    trade_amount: Decimal
    trade_fee: Decimal
    trade_id: str
    trade_price: Decimal
    transaction_id: str
    tx_status: TxStatus
    quote_id: Optional[str] = None
    tx_hash: Optional[str] = None


class SubaccountIdTradesNotificationParamsSchema(Struct):
    channel: str
    data: List[TradeResponseSchema]


class SubaccountIdTradesNotificationSchema(Struct):
    method: str
    params: SubaccountIdTradesNotificationParamsSchema


class SubaccountIdTradesPubSubSchema(Struct):
    channel_params: SubaccountIdTradesChannelSchema
    notification: SubaccountIdTradesNotificationSchema


class SubaccountIdTrades(SubaccountIdTradesPubSubSchema):
    pass
