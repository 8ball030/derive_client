"""Enums used in the bridge module."""

from enum import IntEnum, StrEnum, auto


class TxStatus(IntEnum):
    FAILED = 0
    SUCCESS = 1


class ChainID(IntEnum):
    ETH = 1
    OPTIMISM = 10
    LYRA = 957
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


class Currency(StrEnum):
    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[str]):
        return name

    weETH = auto()
    rswETH = auto()
    rsETH = auto()
    USDe = auto()
    deUSD = auto()
    PYUSD = auto()
    sUSDe = auto()
    SolvBTC = auto()
    SolvBTCBBN = auto()
    LBTC = auto()
    OP = auto()
    DAI = auto()
    sDAI = auto()
    cbBTC = auto()
    eBTC = auto()


class DRPCEndPoints(StrEnum):
    ETH = "https://eth.drpc.org"
    OPTIMISM = "https://optimism.drpc.org"
    BASE = "https://base.drpc.org"
    MODE = "https://mode.drpc.org"
    ARBITRUM = "https://arbitrum.drpc.org"
    BLAST = "https://blast.drpc.org"
