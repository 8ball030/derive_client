"""Pure constants without dependencies."""

from pathlib import Path
from typing import Final

INT32_MAX: Final[int] = (1 << 31) - 1
UINT32_MAX: Final[int] = (1 << 32) - 1
INT64_MAX: Final[int] = (1 << 63) - 1
UINT64_MAX: Final[int] = (1 << 64) - 1


PKG_ROOT = Path(__file__).parent.parent
DATA_DIR = PKG_ROOT / "data"
ABI_DATA_DIR = DATA_DIR / "abi"

PUBLIC_HEADERS = {"accept": "application/json", "content-type": "application/json"}


GAS_FEE_BUFFER = 1.1  # buffer multiplier to pad maxFeePerGas
GAS_LIMIT_BUFFER = 1.1  # buffer multiplier to pad gas limit
MSG_GAS_LIMIT = 200_000
ASSUMED_BRIDGE_GAS_LIMIT = 1_000_000
MIN_PRIORITY_FEE = 10_000
PAYLOAD_SIZE = 161
TARGET_SPEED = "FAST"

DEFAULT_RPC_ENDPOINTS = DATA_DIR / "rpc_endpoints.yaml"
