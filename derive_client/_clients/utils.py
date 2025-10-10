import json
from dataclasses import dataclass
from enum import StrEnum

import msgspec
from derive_action_signing.utils import sign_rest_auth_header
from eth_account import Account
from pydantic import BaseModel
from web3 import AsyncWeb3, Web3

from derive_client.data.generated.models import RPCErrorFormatSchema


@dataclass
class AuthContext:
    wallet: str
    w3: Web3 | AsyncWeb3
    account: Account

    @property
    def signed_headers(self):
        return sign_rest_auth_header(
            web3_client=self.w3,
            smart_contract_wallet=self.wallet,
            session_key_or_wallet_private_key=self.account.key,
        )


class DeriveJSONRPCError(Exception):
    """Raised when a Derive JSON-RPC error payload is returned."""

    def __init__(self, message_id: str | int, rpc_error: RPCErrorFormatSchema):
        super().__init__(f"{rpc_error.code}: {rpc_error.message} (message_id={message_id})")
        self.message_id = message_id
        self.rpc_error = rpc_error

    def __str__(self):
        base = f"Derive RPC {self.rpc_error.code}: {self.rpc_error.message}"
        return f"{base}  [data={self.rpc_error.data!r}]" if self.rpc_error.data is not None else base


def try_cast_response(response: bytes, response_schema: type[msgspec.Struct]) -> msgspec.Struct:
    try:
        return msgspec.json.decode(response, type=response_schema)
    except msgspec.ValidationError:
        message = json.loads(response)
        rpc_error = RPCErrorFormatSchema(**message["error"])
        raise DeriveJSONRPCError(message_id=message["id"], rpc_error=rpc_error)
    raise ValueError(f"Failed to decode response data: {response}")


class RateLimitConfig(BaseModel, frozen=True):
    name: str
    matching_tps: int
    per_instrument_tps: int
    non_matching_tps: int
    connections_per_ip: int
    burst_multiplier: int
    burst_reset_seconds: int


class RateLimitProfile(StrEnum):
    TRADER = "trader"
    MARKET_MAKER = "market_maker"


RATE_LIMIT: dict[RateLimitProfile, RateLimitConfig] = {
    RateLimitProfile.TRADER: RateLimitConfig(
        name="Trader",
        matching_tps=1,
        per_instrument_tps=1,
        non_matching_tps=5,
        connections_per_ip=4,
        burst_multiplier=5,
        burst_reset_seconds=5,
    ),
    RateLimitProfile.MARKET_MAKER: RateLimitConfig(
        name="Market Maker",
        matching_tps=500,
        per_instrument_tps=10,
        non_matching_tps=500,
        connections_per_ip=64,
        burst_multiplier=5,
        burst_reset_seconds=5,
    ),
}
