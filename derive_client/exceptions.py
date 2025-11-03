"""Custom Exception classes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from derive_client.data_types import BridgeTxResult, ChainID, FeeEstimate, TypedLogReceipt


class NotConnectedError(RuntimeError):
    """Raised when the client hasn't connected (call connect())."""


class ApiException(Exception):
    """Raised when an API request fails or returns an error response."""


class EthereumJSONRPCException(ApiException):
    """Raised when an Ethereum JSON-RPC error payload is returned."""

    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(message)
        self.code = code
        self.data = data

    def __str__(self):
        base = f"Ethereum RPC {self.code}: {self.args[0]}"
        return f"{base}  [data={self.data!r}]" if self.data is not None else base


class DeriveJSONRPCException(ApiException):
    """Raised when a Derive JSON-RPC error payload is returned."""

    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(message)
        self.code = code
        self.data = data

    def __str__(self):
        base = f"Derive RPC {self.code}: {self.args[0]}"
        return f"{base}  [data={self.data!r}]" if self.data is not None else base


class BridgeEventParseError(Exception):
    """Raised when an expected cross-chain bridge event could not be parsed."""


class BridgeRouteError(Exception):
    """Raised when no bridge route exists for the given currency and chains."""


class NoAvailableRPC(Exception):
    """Raised when all configured RPC endpoints are temporarily unavailable due to backoff or failures."""


class InsufficientNativeBalance(Exception):
    """Raised when the native currency balance is insufficient for gas and/or value transfer."""

    def __init__(
        self,
        message: str,
        *,
        chain_id: ChainID,
        balance: int,
        assumed_gas_limit: int,
        fee_estimate: FeeEstimate,
    ):
        super().__init__(message)
        self.chain_id = chain_id
        self.balance = balance
        self.assumed_gas_limit = assumed_gas_limit
        self.fee_estimate = fee_estimate


class InsufficientTokenBalance(Exception):
    """Raised when the token balance is insufficient for the requested operation."""


class BridgePrimarySignerRequiredError(Exception):
    """Raised when bridging is attempted with a secondary session-key signer."""


class TxReceiptMissing(Exception):
    """Raised when a transaction receipt is required but not available."""


class FinalityTimeout(Exception):
    """Raised when the transaction was mined but did not reach the required finality within the timeout."""


class TxPendingTimeout(Exception):
    """Raised when the transaction receipt does not materialize and the transaction remains in the mempool."""


class TransactionDropped(Exception):
    """Raised when the transaction the transaction is no longer in the mempool, likely dropped."""


class BridgeEventTimeout(Exception):
    """Raised when no matching bridge event was seen before deadline."""


class PartialBridgeResult(Exception):
    """Raised after submission when the bridge pipeline fails"""

    def __init__(self, message: str, *, tx_result: BridgeTxResult):
        super().__init__(message)
        self.tx_result = tx_result

    @property
    def cause(self) -> BaseException | None:
        """Provides access to the orignal Exception."""
        return self.__cause__


class StandardBridgeRelayFailed(Exception):
    """Raised when the L2 messenger emits FailedRelayedMessage."""

    def __init__(self, message: str, *, event_log: TypedLogReceipt):
        super().__init__(message)
        self.event_log = event_log
