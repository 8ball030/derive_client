from __future__ import annotations

from decimal import Decimal
from typing import List

from msgspec import Struct

from derive_client.data_types.channels.enums import UpdateType


class SubaccountIdBalancesChannelSchema(Struct):
    subaccount_id: int


class BalanceUpdateSchema(Struct):
    name: str
    new_balance: Decimal
    previous_balance: Decimal
    update_type: UpdateType


class SubaccountIdBalancesNotificationParamsSchema(Struct):
    channel: str
    data: List[BalanceUpdateSchema]


class SubaccountIdBalancesNotificationSchema(Struct):
    method: str
    params: SubaccountIdBalancesNotificationParamsSchema


class SubaccountIdBalancesPubSubSchema(Struct):
    channel_params: SubaccountIdBalancesChannelSchema
    notification: SubaccountIdBalancesNotificationSchema


class SubaccountIdBalances(SubaccountIdBalancesPubSubSchema):
    pass
