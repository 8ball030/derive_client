from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from msgspec import Struct

from derive_client.data_types.channels.enums import (
    Direction,
    OrderStatus,
    OrderType,
    TimeInForce,
    TriggerPriceType,
    TriggerType,
)
from derive_client.data_types.generated_models import CancelReason as CancelReason


class SubaccountIdOrdersChannelSchema(Struct):
    subaccount_id: int


class OrderResponseSchema(Struct):
    amount: Decimal
    average_price: Decimal
    cancel_reason: CancelReason
    creation_timestamp: int
    direction: Direction
    filled_amount: Decimal
    instrument_name: str
    is_transfer: bool
    label: str
    last_update_timestamp: int
    limit_price: Decimal
    max_fee: Decimal
    mmp: bool
    nonce: int
    order_fee: Decimal
    order_id: str
    order_status: OrderStatus
    order_type: OrderType
    signature: str
    signature_expiry_sec: int
    signer: str
    subaccount_id: int
    time_in_force: TimeInForce
    quote_id: Optional[str] = None
    replaced_order_id: Optional[str] = None
    trigger_price: Optional[Decimal] = None
    trigger_price_type: Optional[TriggerPriceType] = None
    trigger_reject_message: Optional[str] = None
    trigger_type: Optional[TriggerType] = None


class SubaccountIdOrdersNotificationParamsSchema(Struct):
    channel: str
    data: List[OrderResponseSchema]


class SubaccountIdOrdersNotificationSchema(Struct):
    method: str
    params: SubaccountIdOrdersNotificationParamsSchema


class SubaccountIdOrdersPubSubSchema(Struct):
    channel_params: SubaccountIdOrdersChannelSchema
    notification: SubaccountIdOrdersNotificationSchema


class SubaccountIdOrders(SubaccountIdOrdersPubSubSchema):
    pass
