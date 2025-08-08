"""Models used in the bridge module."""

from derive_action_signing.module_data import ModuleData
from derive_action_signing.utils import decimal_to_big_int
from eth_abi.abi import encode
from eth_utils import is_0x_prefixed, is_address, is_hex, to_checksum_address
from pydantic import BaseModel, ConfigDict, Field, GetCoreSchemaHandler, GetJsonSchemaHandler, HttpUrl
from pydantic.dataclasses import dataclass
from pydantic_core import core_schema
from web3 import Web3
from web3.contract import Contract
from web3.contract.contract import ContractEvent
from web3.datastructures import AttributeDict

from .enums import BridgeType, ChainID, Currency, DeriveTxStatus, MainnetCurrency, MarginType, SessionKeyScope, TxStatus


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


class Address(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source, _handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.no_info_before_validator_function(cls._validate, core_schema.str_schema())

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
    def _validate(cls, v: str) -> str:
        if not isinstance(v, str):
            raise TypeError("Expected a string for TxHash")
        if not is_0x_prefixed(v) or not is_hex(v) or len(v) != 66:
            raise ValueError(f"Invalid Ethereum transaction hash: {v}")
        return v


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
    source_w3: Web3
    target_w3: Web3
    source_token: Contract
    source_event: ContractEvent
    target_event: ContractEvent

    @property
    def source_chain(self) -> ChainID:
        return ChainID(self.source_w3.eth.chain_id)

    @property
    def target_chain(self) -> ChainID:
        return ChainID(self.target_w3.eth.chain_id)


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
    currency: Currency
    bridge: BridgeType
    source_chain: ChainID
    target_chain: ChainID
    source_tx: TxResult
    target_from_block: int
    event_id: str | None = None
    target_tx: TxResult | None = None

    @property
    def status(self) -> TxStatus:
        if self.source_tx.status is not TxStatus.SUCCESS:
            return self.source_tx.status
        return self.target_tx.status if self.target_tx is not None else TxStatus.PENDING


class DepositResult(BaseModel):
    status: DeriveTxStatus  # should be "REQUESTED"
    transaction_id: str


class WithdrawResult(BaseModel):
    status: DeriveTxStatus  # should be "REQUESTED"
    transaction_id: str


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
