from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from msgspec import Struct

from derive_client.data_types.generated_models import CancelReason1 as CancelReason
from derive_client.data_types.generated_models import Direction as FilledDirection
from derive_client.data_types.generated_models import Status


class WalletRfqsChannelSchema(Struct):
    wallet: str


class LegUnpricedSchema(Struct):
    amount: Decimal
    direction: FilledDirection
    instrument_name: str


class RFQResultPublicSchema(Struct):
    cancel_reason: CancelReason
    creation_timestamp: int
    filled_direction: FilledDirection
    filled_pct: Decimal
    last_update_timestamp: int
    legs: List[LegUnpricedSchema]
    partial_fill_step: Decimal
    rfq_id: str
    status: Status
    subaccount_id: int
    valid_until: int
    total_cost: Optional[Decimal] = None


class WalletRfqsNotificationParamsSchema(Struct):
    channel: str
    data: List[RFQResultPublicSchema]


class WalletRfqsNotificationSchema(Struct):
    method: str
    params: WalletRfqsNotificationParamsSchema


class WalletRfqsPubSubSchema(Struct):
    channel_params: WalletRfqsChannelSchema
    notification: WalletRfqsNotificationSchema


class WalletRfqs(WalletRfqsPubSubSchema):
    pass
