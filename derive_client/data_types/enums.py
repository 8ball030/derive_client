"""Enums used in the derive_client module."""

from enum import Enum, IntEnum


class TxStatus(IntEnum):
    FAILED = 0  # confirmed and status == 0 (on-chain revert)
    SUCCESS = 1  # confirmed and status == 1
    PENDING = 2  # not yet confirmed, no receipt


class DeriveTxStatus(Enum):
    """Status code returned in DeriveClient.get_transaction."""

    REQUESTED = "requested"
    PENDING = "pending"
    SETTLED = "settled"
    REVERTED = "reverted"
    IGNORED = "ignored"
    TIMED_OUT = "timed_out"


class QuoteStatus(Enum):
    OPEN = "open"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class BridgeType(Enum):
    SOCKET = "socket"
    LAYERZERO = "layerzero"
    STANDARD = "standard"


class Direction(Enum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"


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


class GasPriority(IntEnum):
    SLOW = 25
    MEDIUM = 50
    FAST = 75


class SocketAddress(Enum):
    ETH = "0x943ac2775928318653e91d350574436a1b9b16f9"
    ARBITRUM = "0x37cc674582049b579571e2ffd890a4d99355f6ba"
    OPTIMISM = "0x301bD265F0b3C16A58CbDb886Ad87842E3A1c0a4"
    BASE = "0x12E6e58864cE4402cF2B4B8a8E9c75eAD7280156"
    DERIVE = "0x565810cbfa3Cf1390963E5aFa2fB953795686339"


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

    ETH = "ETH"

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


class LiquidityRole(Enum):
    MAKER = "maker"
    TAKER = "taker"


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
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class EthereumJSONRPCErrorCode(IntEnum):
    # https://ethereum-json-rpc.com/errors
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    INVALID_INPUT = -32000
    RESOURCE_NOT_FOUND = -32001
    RESOURCE_UNAVAILABLE = -32002
    TRANSACTION_REJECTED = -32003
    METHOD_NOT_SUPPORTED = -32004
    LIMIT_EXCEEDED = -32005
    JSONRPC_VERSION_NOT_SUPPORTED = -32006


class DeriveJSONRPCErrorCode(IntEnum):
    # https://docs.derive.xyz/reference/error-codes
    NO_ERROR = 0
    RATE_LIMIT_EXCEEDED = -32000
    CONCURRENT_WS_CLIENTS_LIMIT_EXCEEDED = -32100
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    ORDER_CONFIRMATION_TIMEOUT = 9000
    ENGINE_CONFIRMATION_TIMEOUT = 9001

    MANAGER_NOT_FOUND = 10000
    ASSET_NOT_ERC20 = 10001
    WALLET_MISMATCH = 10002
    SUBACCOUNT_MISMATCH = 10003
    MULTIPLE_CURRENCIES_NOT_SUPPORTED = 10004
    MAX_SUBACCOUNTS_REACHED = 10005
    MAX_SESSION_KEYS_REACHED = 10006
    MAX_ASSETS_PER_SUBACCOUNT = 10007
    MAX_EXPIRIES_PER_SUBACCOUNT = 10008
    INVALID_RECIPIENT_SUBACCOUNT_ID = 10009
    PMRM_USDC_ONLY_COLLATERAL = 10010
    ERC20_INSUFFICIENT_ALLOWANCE = 10011
    ERC20_INSUFFICIENT_BALANCE = 10012
    PENDING_DEPOSIT = 10013
    PENDING_WITHDRAWAL = 10014
    PM2_COLLATERAL_CONSTRAINT = 10015

    INSUFFICIENT_FUNDS_ORDER = 11000
    ORDER_REJECTED_FROM_QUEUE = 11002
    ALREADY_CANCELLED = 11003
    ALREADY_FILLED = 11004
    ALREADY_EXPIRED = 11005
    ORDER_NOT_EXIST = 11006
    SELF_CROSS_DISALLOWED = 11007
    POST_ONLY_REJECT = 11008
    ZERO_LIQUIDITY = 11009
    POST_ONLY_INVALID_TYPE = 11010
    INVALID_SIGNATURE_EXPIRY = 11011
    INVALID_AMOUNT = 11012
    INVALID_LIMIT_PRICE = 11013
    FOK_NOT_FILLED = 11014
    MMP_FROZEN = 11015
    ALREADY_CONSUMED = 11016
    NON_UNIQUE_NONCE = 11017
    INVALID_NONCE_DATE = 11018
    OPEN_ORDERS_LIMIT_EXCEEDED = 11019
    NEGATIVE_ERC20_BALANCE = 11020
    INSTRUMENT_NOT_LIVE = 11021
    TRIGGER_ORDER_CANCELLED = 11050
    INVALID_TRIGGER_PRICE = 11051
    TRIGGER_ORDER_LIMIT_EXCEEDED = 11052
    TRIGGER_PRICE_TYPE_UNSUPPORTED = 11053
    TRIGGER_ORDER_REPLACE_UNSUPPORTED = 11054
    MARKET_ORDER_INVALID_TRIGGER_PRICE = 11055
    LEG_INSTRUMENTS_NOT_UNIQUE = 11100
    RFQ_NOT_FOUND = 11101
    QUOTE_NOT_FOUND = 11102
    RFQ_LEG_MISMATCH = 11103
    RFQ_NOT_OPEN = 11104
    RFQ_ID_MISMATCH = 11105
    INVALID_RFQ_COUNTERPARTY = 11106
    QUOTE_COST_TOO_HIGH = 11107
    AUCTION_NOT_ONGOING = 11200
    OPEN_ORDERS_NOT_ALLOWED = 11201
    PRICE_LIMIT_EXCEEDED = 11202
    LAST_TRADE_ID_MISMATCH = 11203
    MAKER_PROGRAM_NOT_FOUND = 19000
    ASSET_NOT_FOUND = 12000
    INSTRUMENT_NOT_FOUND = 12001
    CURRENCY_NOT_FOUND = 12002
    USDC_NO_CAPS = 12003
    INVALID_CHANNELS = 13000
    ACCOUNT_NOT_FOUND = 14000
    SUBACCOUNT_NOT_FOUND = 14001
    SUBACCOUNT_WITHDRAWN = 14002
    SESSIONKEY_EXPIRY_TOO_LOW = 14009
    SESSIONKEY_ALREADY_REGISTERED = 14010
    SESSIONKEY_REGISTERED_OTHER_ACCOUNT = 14011
    ADDRESS_NOT_CHECKSUMMED = 14012
    INVALID_ETH_ADDRESS = 14013
    INVALID_SIGNATURE = 14014
    NONCE_MISMATCH = 14015
    RAWTX_FUNCTION_MISMATCH = 14016
    RAWTX_CONTRACT_MISMATCH = 14017
    RAWTX_PARAMS_MISMATCH = 14018
    RAWTX_PARAM_VALUES_MISMATCH = 14019
    HEADER_WALLET_MISMATCH = 14020
    HEADER_WALLET_MISSING = 14021
    PRIVATE_CHANNEL_SUBSCRIPTION_FAILED = 14022
    SIGNER_NOT_OWNER = 14023
    CHAINID_MISMATCH = 14024
    MISSING_PRIVATE_PARAM = 14025
    SESSIONKEY_NOT_FOUND = 14026
    UNAUTHORIZED_RQF_MAKER = 14027
    CROSS_CURRENCY_RFQ_NOT_SUPPORTED = 14028
    SESSIONKEY_IP_NOT_WHITELISTED = 14029
    SESSIONKEY_EXPIRED = 14030
    UNAUTHORIZED_KEY_SCOPE = 14031
    SCOPE_NOT_ADMIN = 14032
    ACCOUNT_NOT_WHITELISTED_ATOMIC_ORDERS = 14033
    REFERRAL_CODE_NOT_FOUND = 14034
    RESTRICTED_REGION = 16000
    ACCOUNT_DISABLED_COMPLIANCE = 16001
    SENTINEL_AUTH_INVALID = 16100
    INVALID_BLOCK_NUMBER = 18000
    BLOCK_ESTIMATION_FAILED = 18001
    LIGHTACCOUNT_OWNER_MISMATCH = 18002
    VAULT_ERC20_ASSET_NOT_EXISTS = 18003
    VAULT_ERC20_POOL_NOT_EXISTS = 18004
    VAULT_ADD_ASSET_BEFORE_BALANCE = 18005
    INVALID_SWELL_SEASON = 18006
    VAULT_NOT_FOUND = 18007
    MAKER_PROGRAM_NOT_FOUND_19000 = 19000
