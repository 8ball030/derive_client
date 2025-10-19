from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

import msgspec
from derive_action_signing import ModuleData, SignedAction
from derive_action_signing.utils import sign_rest_auth_header
from eth_account import Account
from pydantic import BaseModel
from web3 import AsyncWeb3, Web3

from derive_client.constants import EnvConfig
from derive_client.data.generated.models import RPCErrorFormatSchema
from derive_client.data_types import Address


@dataclass
class AuthContext:
    wallet: Address
    w3: Web3 | AsyncWeb3
    account: Account
    config: EnvConfig
    nonce_generator: NonceGenerator

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
        signature_expiry_sec: int,
        subaccount_id: int,
        nonce: int | None = None,
    ) -> SignedAction:
        module_address = self.w3.to_checksum_address(module_address)
        nonce = nonce if nonce is not None else self.nonce_generator.next()
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


class NonceExhaustedError(Exception):
    """Raised when nonce counter is exhausted within a millisecond."""


class NonceGenerator:
    """
    Thread-safe nonce generator for Derive L2 trading.
    Generates nonces as: <13-digit UTC ms timestamp><3-digit counter>
    Guarantees up to 1000 unique nonces per millisecond.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._last_ms = 0
        self._counter = 0

    def next(self) -> int:
        """
        Generate a unique 16-digit nonce.
        Format: <UTC timestamp in ms (13 digits)><counter (3 digits)>

        Returns:
            int: Unique nonce (e.g., 1695836058725001)
        """
        with self._lock:
            utc_now_ms = time.time_ns() // 1_000_000
            if utc_now_ms > self._last_ms:
                self._last_ms = utc_now_ms
                self._counter = 0
            else:
                if self._counter > 999:
                    raise NonceExhaustedError(
                        f"Exhausted 1000 nonces in millisecond {utc_now_ms}. "
                        f"Cannot generate more than 1000 nonces per millisecond. "
                        f"Consider rate limiting your requests."
                    )
                self._counter += 1

        return utc_now_ms * 1000 + self._counter


@dataclass
class PositionTransfer:
    """Position to transfer between subaccounts."""

    instrument_name: str
    amount: Decimal  # Can be negative (sign indicates long/short)
