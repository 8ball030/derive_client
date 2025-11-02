"""Network and chain configurations."""

from enum import Enum, IntEnum

from derive_client.data_types import ChecksumAddress, Currency, UnderlyingCurrency


class LayerZeroChainIDv2(IntEnum):
    # https://docs.layerzero.network/v2/deployments/deployed-contracts
    ETH = 30101
    ARBITRUM = 30110
    OPTIMISM = 30111
    BASE = 30184
    DERIVE = 30311


class SocketAddress(Enum):
    ETH = ChecksumAddress("0x943ac2775928318653e91d350574436a1b9b16f9")
    ARBITRUM = ChecksumAddress("0x37cc674582049b579571e2ffd890a4d99355f6ba")
    OPTIMISM = ChecksumAddress("0x301bD265F0b3C16A58CbDb886Ad87842E3A1c0a4")
    BASE = ChecksumAddress("0x12E6e58864cE4402cF2B4B8a8E9c75eAD7280156")
    DERIVE = ChecksumAddress("0x565810cbfa3Cf1390963E5aFa2fB953795686339")


class DeriveTokenAddress(Enum):
    # https://www.coingecko.com/en/coins/derive

    # impl: 0x4909ad99441ea5311b90a94650c394cea4a881b8 (Derive)
    ETH = ChecksumAddress("0xb1d1eae60eea9525032a6dcb4c1ce336a1de71be")

    # impl: 0x1eda1f6e04ae37255067c064ae783349cf10bdc5 (DeriveL2)
    OPTIMISM = ChecksumAddress("0x33800de7e817a70a694f31476313a7c572bba100")

    # impl: 0x01259207a40925b794c8ac320456f7f6c8fe2636 (DeriveL2)
    BASE = ChecksumAddress("0x9d0e8f5b25384c7310cb8c6ae32c8fbeb645d083")

    # impl: 0x5d22b63d83a9be5e054df0e3882592ceffcef097 (DeriveL2)
    ARBITRUM = ChecksumAddress("0x77b7787a09818502305c95d68a2571f090abb135")

    # impl: 0x340B51Cb46DBF63B55deD80a78a40aa75Dd4ceDF (DeriveL2)
    DERIVE = ChecksumAddress("0x2EE0fd70756EDC663AcC9676658A1497C247693A")


DEFAULT_REFERER = "0x9135BA0f495244dc0A5F029b25CDE95157Db89AD"

GAS_FEE_BUFFER = 1.1  # buffer multiplier to pad maxFeePerGas
GAS_LIMIT_BUFFER = 1.1  # buffer multiplier to pad gas limit
MSG_GAS_LIMIT = 200_000
ASSUMED_BRIDGE_GAS_LIMIT = 1_000_000
MIN_PRIORITY_FEE = 10_000
PAYLOAD_SIZE = 161
TARGET_SPEED = "FAST"

DEFAULT_GAS_FUNDING_AMOUNT = int(0.0001 * 1e18)  # 0.0001 ETH

TOKEN_DECIMALS = {
    UnderlyingCurrency.ETH: 18,
    UnderlyingCurrency.BTC: 8,
    UnderlyingCurrency.USDC: 6,
    UnderlyingCurrency.LBTC: 8,
    UnderlyingCurrency.WEETH: 18,
    UnderlyingCurrency.OP: 18,
    UnderlyingCurrency.DRV: 18,
    UnderlyingCurrency.rswETH: 18,
    UnderlyingCurrency.rsETH: 18,
    UnderlyingCurrency.DAI: 18,
    UnderlyingCurrency.USDT: 6,
    UnderlyingCurrency.OLAS: 18,
    UnderlyingCurrency.DRV: 18,
}

CURRENCY_DECIMALS = {
    Currency.ETH: 18,
    Currency.weETH: 18,
    Currency.rswETH: 18,
    Currency.rsETH: 18,
    Currency.USDe: 18,
    Currency.deUSD: 18,
    Currency.PYUSD: 6,
    Currency.sUSDe: 18,
    Currency.SolvBTC: 18,
    Currency.SolvBTCBBN: 18,
    Currency.LBTC: 8,
    Currency.OP: 18,
    Currency.DAI: 18,
    Currency.sDAI: 18,
    Currency.cbBTC: 8,
    Currency.eBTC: 8,
    Currency.AAVE: 18,
    Currency.OLAS: 18,
    Currency.DRV: 18,
    Currency.WBTC: 8,
    Currency.WETH: 18,
    Currency.USDC: 6,
    Currency.USDT: 6,
    Currency.wstETH: 18,
    Currency.USDCe: 6,
    Currency.SNX: 18,
}
