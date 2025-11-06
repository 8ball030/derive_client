from __future__ import annotations

from decimal import Decimal
from typing import Dict

from msgspec import Struct


class SpotFeedCurrencyChannelSchema(Struct):
    currency: str


class SpotFeedSnapshotSchema(Struct):
    confidence: Decimal
    confidence_prev_daily: Decimal
    price: Decimal
    price_prev_daily: Decimal
    timestamp_prev_daily: int


class SpotFeedCurrencyPublisherDataSchema(Struct):
    feeds: Dict[str, SpotFeedSnapshotSchema]
    timestamp: int


class SpotFeedCurrencyNotificationParamsSchema(Struct):
    channel: str
    data: SpotFeedCurrencyPublisherDataSchema


class SpotFeedCurrencyNotificationSchema(Struct):
    method: str
    params: SpotFeedCurrencyNotificationParamsSchema


class SpotFeedCurrencyPubSubSchema(Struct):
    channel_params: SpotFeedCurrencyChannelSchema
    notification: SpotFeedCurrencyNotificationSchema


class SpotFeedCurrency(SpotFeedCurrencyPubSubSchema):
    pass
