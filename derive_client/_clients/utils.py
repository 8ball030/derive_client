from __future__ import annotations

import json
import time
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, Optional

import msgspec
from derive_action_signing import ModuleData, SignedAction
from derive_action_signing.utils import sign_rest_auth_header
from eth_account import Account
from pydantic import BaseModel
from web3 import AsyncWeb3, Web3

from derive_client.constants import EnvConfig
from derive_client.data.generated.models import InstrumentPublicResponseSchema, InstrumentType, RPCErrorFormatSchema
from derive_client.data_types import Address

if TYPE_CHECKING:
    from derive_client._clients.rest.http.markets import MarketOperations


def get_default_signature_expiry_sec() -> int:
    """
    Compute a conservative default signature_expiry_sec (Unix epoch seconds)

    Rationale:
    - RFQ send/execute docs require expiry >= 310 seconds from now and mark the quote
      expired once time-to-expiry <= 300 seconds.
    - We choose 330 seconds from current local time (310 + 20s margin) to cover:
      - small local/server clock skew
      - signing and network transmission latency
      - brief processing/queue delays on client or server
    """
    utc_time_now_s = int(time.time())
    return utc_time_now_s + 330


@dataclass
class AuthContext:
    wallet: Address
    w3: Web3 | AsyncWeb3
    account: Account
    config: EnvConfig

    @property
    def signer(self) -> Address:
        return self.account.address

    @property
    def signed_headers(self):
        return sign_rest_auth_header(
            web3_client=self.w3,
            smart_contract_wallet=self.wallet,
            session_key_or_wallet_private_key=self.account.key,
        )

    def sign_action(
        self,
        module_address: Address,
        module_data: ModuleData,
        subaccount_id: int,
        signature_expiry_sec: Optional[int] = None,
        nonce: Optional[int] = None,
    ) -> SignedAction:
        module_address = self.w3.to_checksum_address(module_address)

        nonce = nonce or time.time_ns()
        signature_expiry_sec = signature_expiry_sec or get_default_signature_expiry_sec()

        action = SignedAction(
            subaccount_id=subaccount_id,
            owner=self.wallet,
            signer=self.signer,
            signature_expiry_sec=signature_expiry_sec,
            nonce=nonce,
            module_address=module_address,
            module_data=module_data,
            DOMAIN_SEPARATOR=self.config.DOMAIN_SEPARATOR,
            ACTION_TYPEHASH=self.config.ACTION_TYPEHASH,
        )
        action.sign(self.account.key)
        return action


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
        raise DeriveJSONRPCError(message_id=message.get("id", ""), rpc_error=rpc_error)
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


def encode_json_exclude_none(obj: msgspec.Struct) -> bytes:
    """
    Encode msgspec Struct omitting None values.

    The Derive API requires optional fields to be omitted entirely
    rather than sent as null.
    """
    data = msgspec.structs.asdict(obj)
    filtered = {k: v for k, v in data.items() if v is not None}
    return msgspec.json.encode(filtered)


@dataclass
class PositionTransfer:
    """Position to transfer between subaccounts."""

    instrument_name: str
    amount: Decimal  # Can be negative (sign indicates long/short)


def fetch_all_pages_of_instrument_type(
    markets: MarketOperations,
    instrument_type: InstrumentType,
    expired: bool,
) -> list[InstrumentPublicResponseSchema]:
    """Fetch all instruments of a type, handling pagination."""

    page = 1
    page_size = 1000
    instruments = []

    while True:
        result = markets.get_all_instruments(
            expired=expired,
            instrument_type=instrument_type,
            page=page,
            page_size=page_size,
        )
        instruments.extend(result.instruments)
        if page >= result.pagination.num_pages:
            break
        page += 1

    return instruments
