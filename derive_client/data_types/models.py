"""Models used in the bridge module."""

from typing import Any

from derive_action_signing.module_data import ModuleData
from derive_action_signing.utils import decimal_to_big_int
from eth_abi.abi import encode
from eth_account.datastructures import SignedTransaction
from eth_utils import is_0x_prefixed, is_address, is_hex, to_checksum_address
from hexbytes import HexBytes
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    HttpUrl,
    PositiveFloat,
    RootModel,
)
from pydantic.dataclasses import dataclass
from pydantic_core import core_schema
from web3 import AsyncWeb3, Web3
from web3.contract import AsyncContract
from web3.contract.async_contract import AsyncContractEvent
from web3.datastructures import AttributeDict

from derive_client.exceptions import TxReceiptMissing

from .enums import (
    BridgeType,
    ChainID,
    Currency,
    DeriveTxStatus,
    GasPriority,
    LiquidityRole,
    MainnetCurrency,
    MarginType,
    OrderSide,
    OrderStatus,
    QuoteStatus,
    SessionKeyScope,
    TimeInForce,
    TxStatus,
)


class PAttributeDict(AttributeDict):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source, _handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(lambda v, **kwargs: cls._validate(v))

    @classmethod
    def __get_pydantic_json_schema__(cls, _schema, _handler: GetJsonSchemaHandler) -> dict:
        return {"type": "object", "additionalProperties": True}

    @classmethod
    def _validate(cls, v) -> AttributeDict:
        if not isinstance(v, (dict, AttributeDict)):
            raise TypeError(f"Expected AttributeDict, got {v!r}")
        return AttributeDict(v)


class PHexBytes(HexBytes):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source: Any, _handler: Any) -> core_schema.CoreSchema:
        # Allow either HexBytes or bytes/hex strings to be parsed into HexBytes
        return core_schema.no_info_before_validator_function(
            cls._validate,
            core_schema.union_schema(
                [
                    core_schema.is_instance_schema(HexBytes),
                    core_schema.bytes_schema(),
                    core_schema.str_schema(),
                ]
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, _schema: core_schema.CoreSchema, _handler: Any) -> dict:
        return {"type": "string", "format": "hex"}

    @classmethod
    def _validate(cls, v: Any) -> HexBytes:
        if isinstance(v, HexBytes):
            return v
        if isinstance(v, (bytes, bytearray)):
            return HexBytes(v)
        if isinstance(v, str):
            return HexBytes(v)
        raise TypeError(f"Expected HexBytes-compatible type, got {type(v).__name__}")


class PSignedTransaction(SignedTransaction):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source: Any, _handler: Any) -> core_schema.CoreSchema:
        # Accept existing SignedTransaction or a tuple/dict of its fields
        return core_schema.no_info_plain_validator_function(cls._validate)

    @classmethod
    def __get_pydantic_json_schema__(cls, _schema: core_schema.CoreSchema, _handler: Any) -> dict:
        return {
            "type": "object",
            "properties": {
                "raw_transaction": {"type": "string", "format": "hex"},
                "hash": {"type": "string", "format": "hex"},
                "r": {"type": "integer"},
                "s": {"type": "integer"},
                "v": {"type": "integer"},
            },
        }

    @classmethod
    def _validate(cls, v: Any) -> SignedTransaction:
        if isinstance(v, SignedTransaction):
            return v
        if isinstance(v, dict):
            return SignedTransaction(
                raw_transaction=PHexBytes(v["raw_transaction"]),
                hash=PHexBytes(v["hash"]),
                r=int(v["r"]),
                s=int(v["s"]),
                v=int(v["v"]),
            )
        raise TypeError(f"Expected SignedTransaction or dict, got {type(v).__name__}")


class Address(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source, _handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.no_info_before_validator_function(cls._validate, core_schema.any_schema())

    @classmethod
    def __get_pydantic_json_schema__(cls, _schema, _handler: GetJsonSchemaHandler) -> dict:
        return {"type": "string", "format": "ethereum-address"}

    @classmethod
    def _validate(cls, v: str) -> str:
        if not is_address(v):
            raise ValueError(f"Invalid Ethereum address: {v}")
        return to_checksum_address(v)


class TxHash(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source, _handler: GetCoreSchemaHandler):
        return core_schema.no_info_before_validator_function(cls._validate, core_schema.str_schema())

    @classmethod
    def __get_pydantic_json_schema__(cls, _schema, _handler: GetJsonSchemaHandler):
        return {"type": "string", "format": "ethereum-tx-hash"}

    @classmethod
    def _validate(cls, v: str | HexBytes) -> str:
        if isinstance(v, HexBytes):
            v = v.to_0x_hex()
        if not isinstance(v, str):
            raise TypeError("Expected a string or HexBytes for TxHash")
        if not is_0x_prefixed(v) or not is_hex(v) or len(v) != 66:
            raise ValueError(f"Invalid Ethereum transaction hash: {v}")
        return v


class Wei(int):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source, _handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.no_info_before_validator_function(cls._validate, core_schema.int_schema())

    @classmethod
    def __get_pydantic_json_schema__(cls, _schema, _handler: GetJsonSchemaHandler) -> dict:
        return {"type": ["string", "integer"], "title": "Wei"}

    @classmethod
    def _validate(cls, v: str | int) -> int:
        if isinstance(v, int):
            return v
        if isinstance(v, str) and is_hex(v):
            return int(v, 16)
        raise TypeError(f"Invalid type for Wei: {type(v)}")


@dataclass
class CreateSubAccountDetails:
    amount: int
    base_asset_address: str
    sub_asset_address: str

    def to_eth_tx_params(self):
        return (
            decimal_to_big_int(self.amount),
            Web3.to_checksum_address(self.base_asset_address),
            Web3.to_checksum_address(self.sub_asset_address),
        )


@dataclass
class CreateSubAccountData(ModuleData):
    amount: int
    asset_name: str
    margin_type: str
    create_account_details: CreateSubAccountDetails

    def to_abi_encoded(self):
        return encode(
            ['uint256', 'address', 'address'],
            self.create_account_details.to_eth_tx_params(),
        )

    def to_json(self):
        return {}


class TokenData(BaseModel):
    isAppChain: bool
    connectors: dict[ChainID, dict[str, str]]
    LyraTSAShareHandlerDepositHook: Address | None = None
    LyraTSADepositHook: Address | None = None
    isNewBridge: bool


class MintableTokenData(TokenData):
    Controller: Address
    MintableToken: Address


class NonMintableTokenData(TokenData):
    Vault: Address
    NonMintableToken: Address


class DeriveAddresses(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    chains: dict[ChainID, dict[Currency, MintableTokenData | NonMintableTokenData]]


class SessionKey(BaseModel):
    public_session_key: Address
    expiry_sec: int
    ip_whitelist: list
    label: str
    scope: SessionKeyScope


class ManagerAddress(BaseModel):
    address: Address
    margin_type: MarginType
    currency: MainnetCurrency | None


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
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


@dataclass
class BridgeTxDetails:
    contract: Address
    method: str
    kwargs: dict[str, Any]
    tx: dict[str, Any]
    signed_tx: PSignedTransaction

    @property
    def tx_hash(self) -> str:
        """Pre-computed transaction hash."""
        return self.signed_tx.hash.to_0x_hex()

    @property
    def nonce(self) -> int:
        """Transaction nonce."""
        return self.tx["nonce"]

    @property
    def gas(self) -> int:
        """Gas limit"""
        return self.tx["gas"]

    @property
    def max_fee_per_gas(self) -> Wei:
        return self.tx["maxFeePerGas"]


@dataclass
class PreparedBridgeTx:
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
    def gas(self) -> int:
        return self.tx_details.gas

    @property
    def max_fee_per_gas(self) -> Wei:
        return self.tx_details.max_fee_per_gas

    @property
    def max_total_fee(self) -> Wei:
        return self.gas * self.max_fee_per_gas


@dataclass(config=ConfigDict(validate_assignment=True))
class TxResult:
    tx_hash: TxHash
    tx_receipt: PAttributeDict | None = None

    @property
    def status(self) -> TxStatus:
        if self.tx_receipt is not None:
            return TxStatus(int(self.tx_receipt.status))  # ∈ {0, 1} (EIP-658)
        return TxStatus.PENDING


@dataclass(config=ConfigDict(validate_assignment=True))
class BridgeTxResult:
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
        return self.source_tx.tx_receipt["gasUsed"]

    @property
    def effective_gas_price(self) -> Wei:
        if not self.source_tx.tx_receipt:
            raise TxReceiptMissing("Source tx receipt not available")
        return self.source_tx.tx_receipt["effectiveGasPrice"]

    @property
    def total_fee(self) -> Wei:
        return self.gas_used * self.effective_gas_price


class DepositResult(BaseModel):
    status: DeriveTxStatus  # should be "REQUESTED"
    transaction_id: str


class WithdrawResult(BaseModel):
    status: DeriveTxStatus  # should be "REQUESTED"
    transaction_id: str


class TransferPosition(BaseModel):
    """Model for position transfer data."""

    # Ref: https://docs.pydantic.dev/2.3/usage/types/number_types/#constrained-types
    instrument_name: str
    amount: PositiveFloat
    limit_price: PositiveFloat


class DeriveTxResult(BaseModel):
    data: dict  # Data used to create transaction
    status: DeriveTxStatus
    error_log: dict
    transaction_id: str
    tx_hash: str | None = Field(alias="transaction_hash")


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


class Order(BaseModel):
    amount: float
    average_price: float
    cancel_reason: str
    creation_timestamp: int
    direction: OrderSide
    filled_amount: float
    instrument_name: str
    is_transfer: bool
    label: str
    last_update_timestamp: int
    limit_price: float
    max_fee: float
    mmp: bool
    nonce: int
    order_fee: float
    order_id: str
    order_status: OrderStatus
    order_type: str
    quote_id: None
    replaced_order_id: str | None
    signature: str
    signature_expiry_sec: int
    signer: str
    subaccount_id: int
    time_in_force: TimeInForce
    trigger_price: float | None
    trigger_price_type: str | None
    trigger_reject_message: str | None
    trigger_type: str | None


class Trade(BaseModel):
    direction: OrderSide
    expected_rebate: float
    index_price: float
    instrument_name: str
    is_transfer: bool
    label: str
    liquidity_role: LiquidityRole
    mark_price: float
    order_id: str
    quote_id: None
    realized_pnl: float
    realized_pnl_excl_fees: float
    subaccount_id: int
    timestamp: int
    trade_amount: float
    trade_fee: float
    trade_id: str
    trade_price: float
    transaction_id: str
    tx_hash: str | None
    tx_status: DeriveTxStatus


class PositionSpec(BaseModel):
    amount: float  # negative allowed to indicate direction
    instrument_name: str


class PositionTransfer(BaseModel):
    maker_order: Order
    taker_order: Order
    maker_trade: Trade
    taker_trade: Trade


class Leg(BaseModel):
    amount: float
    direction: OrderSide  # TODO: PositionSide
    instrument_name: str
    price: float = 0.0


class Quote(BaseModel):
    cancel_reason: str
    creation_timestamp: int
    direction: OrderSide
    fee: float
    fill_pct: int
    is_transfer: bool
    label: str
    last_update_timestamp: int
    legs: list[Leg]
    legs_hash: str
    liquidity_role: LiquidityRole
    max_fee: float
    mmp: bool
    nonce: int
    quote_id: str
    rfq_id: str
    signature: str
    signature_expiry_sec: int
    signer: Address
    status: QuoteStatus


class PositionsTransfer(BaseModel):
    maker_quote: Quote
    taker_quote: Quote
