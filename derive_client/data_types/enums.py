"""Enums used in the derive_client module."""

from enum import Enum, IntEnum


class TxStatus(IntEnum):
    FAILED = 0  # confirmed and status == 0 (on-chain revert)
    SUCCESS = 1  # confirmed and status == 1
    PENDING = 2  # not yet confirmed, no receipt
    ERROR = 3  # local error, e.g. connection, invalid tx


class ChainID(IntEnum):
    ETH = 1
    OPTIMISM = 10
    DERIVE = LYRA = 957
    BASE = 8453
    MODE = 34443
    ARBITRUM = 42161
    BLAST = 81457

    @classmethod
    def _missing_(cls, value):
        try:
            int_value = int(value)
            return next(member for member in cls if member == int_value)
        except (ValueError, TypeError, StopIteration):
            return super()._missing_(value)


class RPCEndPoints(Enum):
    ETH = "https://eth.drpc.org"
    OPTIMISM = "https://optimism.drpc.org"
    BASE = "https://base.drpc.org"
    MODE = "https://mode.drpc.org"
    ARBITRUM = "https://arbitrum.drpc.org"
    BLAST = "https://blast.drpc.org"
    DERIVE = LYRA = "https://rpc.lyra.finance"


class SessionKeyScope(Enum):
    ADMIN = "admin"
    ACCOUNT = "account"
    READ_ONLY = "read_only"


class MainnetCurrency(Enum):
    BTC = "BTC"
    ETH = "ETH"


class MarginType(Enum):
    SM = "SM"
    PM = "PM"
    PM2 = "PM2"


class InstrumentType(Enum):
    """Instrument types."""

    ERC20 = "erc20"
    OPTION = "option"
    PERP = "perp"


class UnderlyingCurrency(Enum):
    """Underlying currencies."""

    ETH = "eth"
    BTC = "btc"
    USDC = "usdc"
    LBTC = "lbtc"
    WEETH = "weeth"
    OP = "op"
    DRV = "drv"
    rswETH = "rseeth"
    rsETH = "rseth"
    DAI = "dai"
    USDT = "usdt"


class Currency(Enum):
    """Depositable currencies..."""

    weETH = "weETH"
    rswETH = "rswETH"
    rsETH = "rsETH"
    USDe = "USDe"
    deUSD = "deUSD"
    PYUSD = "PYUSD"
    sUSDe = "sUSDe"
    SolvBTC = "SolvBTC"
    SolvBTCBBN = "SolvBTCBBN"
    LBTC = "LBTC"
    OP = "OP"
    DAI = "DAI"
    sDAI = "sDAI"
    cbBTC = "cbBTC"
    eBTC = "eBTC"
    # old style deposits
    WBTC = "WBTC"
    WETH = "WETH"
    USDC = "USDC"
    USDT = "USDT"
    SNX = "SNX"
    wstETH = "wstETH"
    USDCe = "USDC.e"


class OrderSide(Enum):
    """Order sides."""

    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order types."""

    LIMIT = "limit"
    MARKET = "market"


class OrderStatus(Enum):
    """Order statuses."""

    OPEN = "open"
    FILLED = "filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class TimeInForce(Enum):
    """Time in force."""

    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"
    POST_ONLY = "post_only"


class Environment(Enum):
    """Environment."""

    PROD = "prod"
    TEST = "test"


class SubaccountType(Enum):
    """
    Type of sub account
    """

    STANDARD = "standard"
    PORTFOLIO = "portfolio"


class CollateralAsset(Enum):
    """Asset types."""

    USDC = "usdc"
    WEETH = "weeth"
    LBTC = "lbtc"


class ActionType(Enum):
    """Action types."""

    DEPOSIT = "deposit"
    TRANSFER = "transfer"


class RfqStatus(Enum):
    """RFQ statuses."""

    OPEN = "open"
