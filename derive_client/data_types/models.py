"""Models used in the bridge module."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal, cast

from eth_account.datastructures import SignedTransaction
from eth_typing import BlockNumber, HexStr
from eth_utils.address import is_address, to_checksum_address
from eth_utils.hexadecimal import is_0x_prefixed, is_hex
from hexbytes import HexBytes
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    RootModel,
)
from web3 import AsyncWeb3
from web3.contract.async_contract import AsyncContract, AsyncContractEvent
from web3.types import ChecksumAddress as ETHChecksumAddress
from web3.types import FilterParams, LogReceipt, TxReceipt
from web3.types import Wei as ETHWei

from derive_client.exceptions import TxReceiptMissing

if TYPE_CHECKING:
    from derive_client.constants import ChainID

    from .enums import (
        BridgeType,
        Currency,
        GasPriority,
        TxStatus,
    )


class ChecksumAddress(str):
    """ChecksumAddress with validation."""

    def __new__(cls, v: str) -> ChecksumAddress:
        if not is_address(v):
            raise ValueError(f"Invalid Ethereum address: {v}")
        return cast(ChecksumAddress, to_checksum_address(v))


class TxHash(str):
    """Transaction hash with validation."""

    def __new__(cls, value: str | HexBytes) -> TxHash:
        if isinstance(value, HexBytes):
            value = value.hex()
        if not isinstance(value, str):
            raise TypeError(f"Expected string or HexBytes, got {type(value)}")
        if not is_0x_prefixed(value) or not is_hex(value) or len(value) != 66:
            raise ValueError(f"Invalid transaction hash: {value}")
        return cast(TxHash, value)


class Wei(int):
    """Wei with validation."""

    def __new__(cls, value: str | int) -> Wei:
        if isinstance(value, str) and is_hex(value):
            value = int(value, 16)
        return cast(Wei, value)


class TypedFilterParams(BaseModel):
    """Typed filter params for eth_getLogs that we actually use.

    Unlike web3.types.FilterParams which has overly-broad unions,
    this reflects our actual runtime behavior:
    - We work with int block numbers internally
    - We convert to hex strings right before RPC calls
    - We use 'latest' as a special case for open-ended queries
    """

    model_config = ConfigDict(frozen=True)

    address: ChecksumAddress | list[ChecksumAddress]
    topics: tuple[HexBytes | None, ...] | None = None

    # Block range - we use int internally, convert to hex for RPC
    # 'latest' is used as sentinel for open-ended queries
    fromBlock: int | Literal["latest"]
    toBlock: int | Literal["latest"]
    blockHash: HexBytes | None = None

    def to_rpc_params(self) -> FilterParams:
        """Convert to RPC-compatible filter params with hex block numbers."""

        address: ETHChecksumAddress | list[ETHChecksumAddress]
        if isinstance(self.address, list):
            address = [cast(ETHChecksumAddress, addr) for addr in self.address]
        else:
            address = cast(ETHChecksumAddress, self.address)

        from_block = cast(HexStr, hex(self.fromBlock)) if self.fromBlock != "latest" else self.fromBlock
        to_block = cast(HexStr, hex(self.toBlock)) if self.toBlock != "latest" else self.toBlock

        params: FilterParams = {
            "address": address,
            "fromBlock": from_block,
            "toBlock": to_block,
        }

        if self.topics is not None:
            params["topics"] = list(self.topics)
        if self.blockHash is not None:
            params["blockHash"] = self.blockHash

        return params


class TypedLogReceipt(BaseModel):
    """Typed log entry from transaction receipt."""

    address: ChecksumAddress
    blockHash: HexBytes
    blockNumber: int
    data: HexBytes
    logIndex: int
    removed: bool
    topics: list[HexBytes]
    transactionHash: HexBytes
    transactionIndex: int

    def to_w3(self) -> LogReceipt:
        """Convert to web3.py LogReceipt dict."""

        return LogReceipt(
            address=cast(ETHChecksumAddress, self.address),
            blockHash=self.blockHash,
            blockNumber=cast(BlockNumber, self.blockNumber),
            data=self.data,
            logIndex=self.logIndex,
            removed=self.removed,
            topics=self.topics,
            transactionHash=self.transactionHash,
            transactionIndex=self.transactionIndex,
        )


class TypedTxReceipt(BaseModel):
    """Fully typed transaction receipt with attribute access.

    Based on web3.types.TxReceipt but actually usable with type checkers.
    All fields from EIP-658 and common extensions included.
    """

    model_config = ConfigDict(populate_by_name=True)

    blockHash: HexBytes
    blockNumber: int
    contractAddress: ChecksumAddress | None
    cumulativeGasUsed: int
    effectiveGasPrice: int
    from_: ChecksumAddress = Field(alias='from')
    gasUsed: int
    logs: list[TypedLogReceipt]
    logsBloom: HexBytes
    status: int  # 0 or 1 per EIP-658
    to: ChecksumAddress
    transactionHash: HexBytes
    transactionIndex: int
    type: int = Field(alias='type')  # Transaction type (0=legacy, 1=EIP-2930, 2=EIP-1559)

    # Optional fields (depending on chain/tx type)
    root: HexStr  # Pre-EIP-658 state root
    # blobGasPrice: int | None = None  # EIP-4844
    # blobGasUsed: int | None = None  # EIP-4844

    def to_w3(self) -> TxReceipt:
        """Convert to web3.py TxReceipt dict."""

        return {
            'blockHash': self.blockHash,
            'blockNumber': cast(BlockNumber, self.blockNumber),
            'contractAddress': cast(ETHChecksumAddress, self.contractAddress) if self.contractAddress else None,
            'cumulativeGasUsed': self.cumulativeGasUsed,
            'effectiveGasPrice': cast(ETHWei, self.effectiveGasPrice),
            'from': cast(ETHChecksumAddress, self.from_),
            'gasUsed': self.gasUsed,
            'logs': [log.to_w3() for log in self.logs],
            'logsBloom': self.logsBloom,
            'status': self.status,
            'to': cast(ETHChecksumAddress, self.to),
            'transactionHash': self.transactionHash,
            'transactionIndex': self.transactionIndex,
            'type': self.type,
            'root': self.root,
        }

        # return tx_receipt


class TypedSignedTransaction(BaseModel):
    """Properly typed signed transaction.

    Immutable replacement for eth_account.datastructures.SignedTransaction.
    """

    model_config = ConfigDict(frozen=True)

    raw_transaction: HexBytes
    hash: HexBytes
    r: int
    s: int
    v: int

    def to_w3(self) -> SignedTransaction:
        """Convert to eth_account SignedTransaction."""

        return SignedTransaction(
            raw_transaction=self.raw_transaction,
            hash=self.hash,
            r=self.r,
            s=self.s,
            v=self.v,
        )


class TypedTransaction(BaseModel):
    """Fully typed transaction data retrieved from the blockchain.

    Based on web3.types.TxData but with proper attribute access.
    This represents a transaction that has been retrieved from a node,
    which may or may not be mined yet.
    """

    model_config = ConfigDict(populate_by_name=True)

    blockHash: HexBytes | None
    blockNumber: int | None  # None if pending
    from_: ChecksumAddress = Field(alias='from')
    gas: int
    gasPrice: int | None = None  # Legacy transactions
    maxFeePerGas: int | None = None  # EIP-1559
    maxPriorityFeePerGas: int | None = None  # EIP-1559
    hash: HexBytes
    input: HexBytes
    nonce: int
    to: ChecksumAddress | None  # None for contract creation
    transactionIndex: int | None  # None if pending
    value: int
    type: int  # 0=legacy, 1=EIP-2930, 2=EIP-1559
    chainId: int | None = None
    v: int
    r: HexBytes
    s: HexBytes

    # EIP-2930 (optional)
    accessList: list[dict[str, Any]] | None = None

    # EIP-4844 (optional)
    maxFeePerBlobGas: int | None = None
    blobVersionedHashes: list[HexBytes] | None = None


class TokenData(BaseModel):
    isAppChain: bool
    connectors: dict[ChainID, dict[str, ChecksumAddress]]
    LyraTSAShareHandlerDepositHook: ChecksumAddress | None = None
    LyraTSADepositHook: ChecksumAddress | None = None
    isNewBridge: bool


class MintableTokenData(TokenData):
    Controller: ChecksumAddress
    MintableToken: ChecksumAddress


class NonMintableTokenData(TokenData):
    Vault: ChecksumAddress
    NonMintableToken: ChecksumAddress


class DeriveAddresses(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    chains: dict[ChainID, dict[Currency, MintableTokenData | NonMintableTokenData]]


@dataclass
class BridgeContext:
    currency: Currency
    source_w3: AsyncWeb3
    target_w3: AsyncWeb3
    source_token: AsyncContract
    source_event: AsyncContractEvent
    target_event: AsyncContractEvent
    source_chain: ChainID
    target_chain: ChainID

    @property
    def bridge_type(self) -> BridgeType:
        return BridgeType.LAYERZERO if self.currency == Currency.DRV else BridgeType.SOCKET


class BridgeTxDetails(BaseModel):
    contract: ChecksumAddress
    fn_name: str
    fn_kwargs: dict[str, Any]
    tx: dict[str, Any]
    signed_tx: TypedSignedTransaction

    @property
    def tx_hash(self) -> str:
        """Pre-computed transaction hash."""
        return self.signed_tx.hash.to_0x_hex()

    @property
    def nonce(self) -> int:
        """Transaction nonce."""
        return self.tx["nonce"]

    @property
    def gas(self) -> Wei:
        """Gas limit"""
        return self.tx["gas"]

    @property
    def max_fee_per_gas(self) -> Wei:
        return self.tx["maxFeePerGas"]


class PreparedBridgeTx(BaseModel):
    amount: int
    value: int
    currency: Currency
    source_chain: ChainID
    target_chain: ChainID
    bridge_type: BridgeType
    tx_details: BridgeTxDetails

    fee_value: int
    fee_in_token: int

    def __post_init_post_parse__(self) -> None:
        # rule 1: don't allow both amount (erc20) and value (native) to be non-zero
        if self.amount and self.value:
            raise ValueError(
                f"Both amount ({self.amount}) and value ({self.value}) are non-zero; "
                "use `prepare_erc20_tx` or `prepare_eth_tx` instead."
            )

        # rule 2: don't allow both fee types to be non-zero simultaneously
        if self.fee_value and self.fee_in_token:
            raise ValueError(
                f"Both fee_value ({self.fee_value}) and fee_in_token ({self.fee_in_token}) are non-zero; "
                "fees must be expressed in only one currency."
            )

    @property
    def tx_hash(self) -> str:
        """Pre-computed transaction hash."""
        return self.tx_details.tx_hash

    @property
    def nonce(self) -> int:
        """Transaction nonce."""
        return self.tx_details.nonce

    @property
    def gas(self) -> Wei:
        return self.tx_details.gas

    @property
    def max_fee_per_gas(self) -> int:
        return self.tx_details.max_fee_per_gas

    @property
    def max_total_fee(self) -> int:
        return self.gas * self.max_fee_per_gas


class TxResult(BaseModel):
    tx_hash: TxHash
    tx_receipt: TypedTxReceipt | None = None

    @property
    def status(self) -> TxStatus:
        if self.tx_receipt is not None:
            return TxStatus(int(self.tx_receipt.status))  # ∈ {0, 1} (EIP-658)
        return TxStatus.PENDING


class BridgeTxResult(BaseModel):
    prepared_tx: PreparedBridgeTx
    source_tx: TxResult
    target_from_block: int
    event_id: str | None = None
    target_tx: TxResult | None = None

    @property
    def status(self) -> TxStatus:
        if self.source_tx.status is not TxStatus.SUCCESS:
            return self.source_tx.status
        return self.target_tx.status if self.target_tx is not None else TxStatus.PENDING

    @property
    def currency(self) -> Currency:
        return self.prepared_tx.currency

    @property
    def source_chain(self) -> ChainID:
        return self.prepared_tx.source_chain

    @property
    def target_chain(self) -> ChainID:
        return self.prepared_tx.target_chain

    @property
    def bridge_type(self) -> BridgeType:
        return self.prepared_tx.bridge_type

    @property
    def gas_used(self) -> int:
        if not self.source_tx.tx_receipt:
            raise TxReceiptMissing("Source tx receipt not available")
        return self.source_tx.tx_receipt.gasUsed

    @property
    def effective_gas_price(self) -> int:
        if not self.source_tx.tx_receipt:
            raise TxReceiptMissing("Source tx receipt not available")
        return self.source_tx.tx_receipt.effectiveGasPrice

    @property
    def total_fee(self) -> int:
        return self.gas_used * self.effective_gas_price


class RPCEndpoints(BaseModel, frozen=True):
    ETH: list[HttpUrl] = Field(default_factory=list)
    OPTIMISM: list[HttpUrl] = Field(default_factory=list)
    BASE: list[HttpUrl] = Field(default_factory=list)
    ARBITRUM: list[HttpUrl] = Field(default_factory=list)
    DERIVE: list[HttpUrl] = Field(default_factory=list)
    MODE: list[HttpUrl] = Field(default_factory=list)
    BLAST: list[HttpUrl] = Field(default_factory=list)

    def __getitem__(self, key: ChainID | int | str) -> list[HttpUrl]:
        chain = ChainID[key.upper()] if isinstance(key, str) else ChainID(key)
        if not (urls := getattr(self, chain.name, [])):
            raise ValueError(f"No RPC URLs configured for {chain.name}")
        return urls


class FeeHistory(BaseModel):
    base_fee_per_gas: list[Wei] = Field(alias="baseFeePerGas")
    gas_used_ratio: list[float] = Field(alias="gasUsedRatio")
    base_fee_per_blob_gas: list[Wei] | None = Field(default=None, alias="baseFeePerBlobGas")
    blob_gas_used_ratio: list[float] | None = Field(default=None, alias="blobGasUsedRatio")
    oldest_block: int = Field(alias="oldestBlock")
    reward: list[list[Wei]]


@dataclass
class FeeEstimate:
    max_fee_per_gas: int
    max_priority_fee_per_gas: int


class FeeEstimates(RootModel):
    root: dict[GasPriority, FeeEstimate]

    def __getitem__(self, key: GasPriority):
        return self.root[key]

    def items(self):
        return self.root.items()


@dataclass
class PositionTransfer:
    """Position to transfer between subaccounts."""

    instrument_name: str
    amount: Decimal  # Can be negative (sign indicates long/short)
