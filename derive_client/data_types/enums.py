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


class LayerZeroChainIDv2(IntEnum):
    # https://docs.layerzero.network/v2/deployments/deployed-contracts
    ETH = 30101
    ARBITRUM = 30110
    OPTIMISM = 30111
    BASE = 30184
    DERIVE = 30311


class DeriveTokenAddresses(Enum):
    # https://www.coingecko.com/en/coins/derive
    ETH = "0xb1d1eae60eea9525032a6dcb4c1ce336a1de71be"  # impl: 0x4909ad99441ea5311b90a94650c394cea4a881b8 (Derive)
    OPTIMISM = (
        "0x33800de7e817a70a694f31476313a7c572bba100"  # impl: 0x1eda1f6e04ae37255067c064ae783349cf10bdc5 (DeriveL2)
    )
    BASE = "0x9d0e8f5b25384c7310cb8c6ae32c8fbeb645d083"  # impl: 0x01259207a40925b794c8ac320456f7f6c8fe2636 (DeriveL2)
    ARBITRUM = (
        "0x77b7787a09818502305c95d68a2571f090abb135"  # impl: 0x5d22b63d83a9be5e054df0e3882592ceffcef097 (DeriveL2)
    )
    DERIVE = "0x2EE0fd70756EDC663AcC9676658A1497C247693A"  # impl: 0x340B51Cb46DBF63B55deD80a78a40aa75Dd4ceDF (DeriveL2)


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
    OLAS = "olas"


class Currency(Enum):
    """Depositable currencies"""

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
    AAVE = "AAVE"
    OLAS = "OLAS"

    # not in prod_lyra_addresses.json
    DRV = "DRV"

    # old style deposits
    WBTC = "WBTC"
    WETH = "WETH"
    USDC = "USDC"
    USDT = "USDT"
    wstETH = "wstETH"
    USDCe = "USDC.e"
    SNX = "SNX"


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
