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

TEST_PRIVATE_KEY = "0xc14f53ee466dd3fc5fa356897ab276acbef4f020486ec253a23b0d1c3f89d4f4"
DEFAULT_SPOT_QUOTE_TOKEN = "USDC"

DEFAULT_REFERER = "0x9135BA0f495244dc0A5F029b25CDE95157Db89AD"

GAS_FEE_BUFFER = 1.1  # buffer multiplier to pad maxFeePerGas
GAS_LIMIT_BUFFER = 1.1  # buffer multiplier to pad gas limit
MSG_GAS_LIMIT = 200_000
ASSUMED_BRIDGE_GAS_LIMIT = 1_000_000
MIN_PRIORITY_FEE = 10_000
PAYLOAD_SIZE = 161
TARGET_SPEED = "FAST"

DEFAULT_GAS_FUNDING_AMOUNT = int(0.0001 * 1e18)  # 0.0001 ETH

DEFAULT_RPC_ENDPOINTS = DATA_DIR / "rpc_endpoints.yaml"
