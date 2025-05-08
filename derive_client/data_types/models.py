"""Models used in the bridge module."""

from dataclasses import dataclass

from derive_action_signing.module_data import ModuleData
from derive_action_signing.utils import decimal_to_big_int
from eth_abi.abi import encode
from eth_utils import is_address, to_checksum_address
from pydantic import BaseModel, ConfigDict, GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic_core import core_schema
from web3 import Web3
from web3.datastructures import AttributeDict

from .enums import ChainID, Currency, MainnetCurrency, MarginType, SessionKeyScope, TxStatus


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


@dataclass
class TxResult:
    tx_hash: str
    tx_receipt: AttributeDict | None
    exception: Exception | None

    @property
    def status(self) -> TxStatus:
        if self.tx_receipt is not None:
            return TxStatus(int(self.tx_receipt.status))  # ∈ {0, 1} (EIP-658)
        if isinstance(self.exception, TimeoutError):
            return TxStatus.PENDING
        return TxStatus.ERROR
