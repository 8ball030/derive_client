from __future__ import annotations

from typing import Dict, List, Literal, Optional, Union

from msgspec import Struct


class SubscribeParamsSchema(Struct):
    channels: List[str]


class SubscribeResultSchema(Struct):
    current_subscriptions: List[str]
    status: Dict[str, str]


class SubscribeRequestSchema(Struct):
    httpMethod: str
    method: Literal['subscribe']
    params: SubscribeParamsSchema
    id: Optional[Union[str, int]] = None


class SubscribeResponseSchema(Struct):
    id: Union[str, int]
    result: SubscribeResultSchema


class SubscribeJSONRPCSchema(Struct):
    request: SubscribeRequestSchema
    response: SubscribeResponseSchema


class Subscribe(SubscribeJSONRPCSchema):
    pass
