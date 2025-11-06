from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from msgspec import Struct

from derive_client.data_types.generated_models import Direction, LiquidityRole
from derive_client.data_types.generated_models import TxStatus as TxStatus1
from derive_client.data_types.generated_models import TxStatus2 as TxStatus


class SubaccountIdTradesTxStatusChannelSchema(Struct):
    subaccount_id: int
    tx_status: TxStatus


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
    tx_status: TxStatus1
    quote_id: Optional[str] = None
    tx_hash: Optional[str] = None


class SubaccountIdTradesTxStatusNotificationParamsSchema(Struct):
    channel: str
    data: List[TradeResponseSchema]


class SubaccountIdTradesTxStatusNotificationSchema(Struct):
    method: str
    params: SubaccountIdTradesTxStatusNotificationParamsSchema


class SubaccountIdTradesTxStatusPubSubSchema(Struct):
    channel_params: SubaccountIdTradesTxStatusChannelSchema
    notification: SubaccountIdTradesTxStatusNotificationSchema


class SubaccountIdTradesTxStatus(SubaccountIdTradesTxStatusPubSubSchema):
    pass
