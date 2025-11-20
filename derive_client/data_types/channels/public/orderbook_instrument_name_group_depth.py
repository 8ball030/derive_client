from __future__ import annotations

from decimal import Decimal
from typing import List

from msgspec import Struct

from derive_client.data_types.channels.enums import Depth, Group


class OrderbookInstrumentNameGroupDepthChannelSchema(Struct):
    depth: Depth
    group: Group
    instrument_name: str


class OrderbookInstrumentNameGroupDepthPublisherDataSchema(Struct):
    asks: List[List[Decimal]]
    bids: List[List[Decimal]]
    instrument_name: str
    publish_id: int
    timestamp: int


class OrderbookInstrumentNameGroupDepthNotificationParamsSchema(Struct):
    channel: str
    data: OrderbookInstrumentNameGroupDepthPublisherDataSchema


class OrderbookInstrumentNameGroupDepthNotificationSchema(Struct):
    method: str
    params: OrderbookInstrumentNameGroupDepthNotificationParamsSchema


class OrderbookInstrumentNameGroupDepthPubSubSchema(Struct):
    channel_params: OrderbookInstrumentNameGroupDepthChannelSchema
    notification: OrderbookInstrumentNameGroupDepthNotificationSchema


class OrderbookInstrumentNameGroupDepth(OrderbookInstrumentNameGroupDepthPubSubSchema):
    pass
