"""Models used in the bridge module."""

from pydantic import BaseModel, ConfigDict

from derive_client.bridge.enums import ChainID, Currency

Address = str


class TokenData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    isAppChain: bool
    connectors: dict[ChainID, dict[str, str]]
    LyraTSAShareHandlerDepositHook: Address | None = None
    LyraTSADepositHook: Address | None = None


class MintableTokenData(TokenData):
    Controller: Address
    MintableToken: Address


class NonMintableTokenData(TokenData):
    Vault: Address
    NonMintableToken: Address


class LyraAddresses(BaseModel):
    chains: dict[ChainID, dict[Currency, MintableTokenData | NonMintableTokenData]]
