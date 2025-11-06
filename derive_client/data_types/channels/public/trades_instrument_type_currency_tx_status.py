from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from msgspec import Struct

from derive_client.data_types.channels.enums import Direction, InstrumentType, LiquidityRole
from derive_client.data_types.generated_models import TxStatus2 as TxStatus


class TradesInstrumentTypeCurrencyTxStatusChannelSchema(Struct):
    currency: str
    instrument_type: InstrumentType
    tx_status: TxStatus


class TradeSettledPublicResponseSchema(Struct):
    direction: Direction
    expected_rebate: Decimal
    index_price: Decimal
    instrument_name: str
    liquidity_role: LiquidityRole
    mark_price: Decimal
    realized_pnl: Decimal
    realized_pnl_excl_fees: Decimal
    subaccount_id: int
    timestamp: int
    trade_amount: Decimal
    trade_fee: Decimal
    trade_id: str
    trade_price: Decimal
    tx_hash: str
    tx_status: TxStatus
    wallet: str
    quote_id: Optional[str] = None


class TradesInstrumentTypeCurrencyTxStatusNotificationParamsSchema(Struct):
    channel: str
    data: List[TradeSettledPublicResponseSchema]


class TradesInstrumentTypeCurrencyTxStatusNotificationSchema(Struct):
    method: str
    params: TradesInstrumentTypeCurrencyTxStatusNotificationParamsSchema


class TradesInstrumentTypeCurrencyTxStatusPubSubSchema(Struct):
    channel_params: TradesInstrumentTypeCurrencyTxStatusChannelSchema
    notification: TradesInstrumentTypeCurrencyTxStatusNotificationSchema


class TradesInstrumentTypeCurrencyTxStatus(TradesInstrumentTypeCurrencyTxStatusPubSubSchema):
    pass
