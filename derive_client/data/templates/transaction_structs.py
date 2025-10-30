"""Struct definitions for PublicGetTransactionResultSchema nested types."""

from msgspec import Struct


class TransactionDataInner(Struct):
    asset: str
    amount: str
    decimals: int


class TransactionData(Struct):
    data: TransactionDataInner
    nonce: int
    owner: str
    expiry: int
    module: str
    signer: str
    asset_id: str
    signature: str
    asset_name: str
    subaccount_id: int
    is_atomic_signing: bool


class TransactionErrorLog(Struct):
    error: str
