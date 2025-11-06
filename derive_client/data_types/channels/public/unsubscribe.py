from __future__ import annotations

from typing import Dict, List, Literal, Optional, Union

from msgspec import Struct


class UnsubscribeParamsSchema(Struct):
    channels: Optional[List[str]] = None


class UnsubscribeResultSchema(Struct):
    remaining_subscriptions: List[str]
    status: Dict[str, str]


class UnsubscribeRequestSchema(Struct):
    httpMethod: str
    method: Literal['unsubscribe']
    params: UnsubscribeParamsSchema
    id: Optional[Union[str, int]] = None


class UnsubscribeResponseSchema(Struct):
    id: Union[str, int]
    result: UnsubscribeResultSchema


class UnsubscribeJSONRPCSchema(Struct):
    request: UnsubscribeRequestSchema
    response: UnsubscribeResponseSchema


class Unsubscribe(UnsubscribeJSONRPCSchema):
    pass
