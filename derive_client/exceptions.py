"""Custom Exception classes."""

from typing import Any


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


class TxSubmissionError(Exception):
    """Raised when a transaction could not be signed or submitted."""


class BridgeEventParseError(Exception):
    """Raised when an expected cross-chain bridge event could not be parsed."""


class AlreadyFinalizedError(Exception):
    """Raised when attempting to poll a BridgeTxResult who'se status is not TxStatus.PENDING."""


class BridgeRouteError(Exception):
    """Raised when no bridge route exists for the given currency and chains."""


class NoAvailableRPC(Exception):
    """Raised when all configured RPC endpoints are temporarily unavailable due to backoff or failures."""


class InsufficientNativeBalance(Exception):
    """Raised when the native currency balance is insufficient for gas and/or value transfer."""


class InsufficientTokenBalance(Exception):
    """Raised when the token balance is insufficient for the requested operation."""


class BridgePrimarySignerRequiredError(Exception):
    """Raised when bridging is attempted with a secondary session-key signer."""


class EthGasFundingPending(Exception):
    """Raised after we detect lack of ETH on Derive to pay for gas."""


class DeriveFundingFailed(Exception):
    """Raised when funding the Derive wallet with gas fails."""


class DrvWithdrawAmountBelowFee(Exception):
    """Raised when the DRV withdrawal amount is less than the fee required to withdraw."""
