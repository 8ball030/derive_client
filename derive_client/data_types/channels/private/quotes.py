from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from msgspec import Struct

from derive_client.data_types.generated_models import CancelReason1 as CancelReason
from derive_client.data_types.generated_models import Direction, LiquidityRole, Status
from derive_client.data_types.generated_models import TxStatus as TxStatus


class SubaccountIdQuotesChannelSchema(Struct):
    subaccount_id: int


class LegPricedSchema(Struct):
    amount: Decimal
    direction: Direction
    instrument_name: str
    price: Decimal


class QuoteResultSchema(Struct):
    cancel_reason: CancelReason
    creation_timestamp: int
    direction: Direction
    fee: Decimal
    fill_pct: Decimal
    is_transfer: bool
    label: str
    last_update_timestamp: int
    legs: List[LegPricedSchema]
    legs_hash: str
    liquidity_role: LiquidityRole
    max_fee: Decimal
    mmp: bool
    nonce: int
    quote_id: str
    rfq_id: str
    signature: str
    signature_expiry_sec: int
    signer: str
    status: Status
    subaccount_id: int
    tx_status: TxStatus
    tx_hash: Optional[str] = None


class SubaccountIdQuotesNotificationParamsSchema(Struct):
    channel: str
    data: List[QuoteResultSchema]


class SubaccountIdQuotesNotificationSchema(Struct):
    method: str
    params: SubaccountIdQuotesNotificationParamsSchema


class SubaccountIdQuotesPubSubSchema(Struct):
    channel_params: SubaccountIdQuotesChannelSchema
    notification: SubaccountIdQuotesNotificationSchema


class SubaccountIdQuotes(SubaccountIdQuotesPubSubSchema):
    pass
