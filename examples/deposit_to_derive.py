"""
Example of bridging funds from Base to a Derive smart contract funding account
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from enum import IntEnum, StrEnum, auto
from pathlib import Path
from typing import Callable

import requests
from eth_account import Account
from pydantic import BaseModel, ConfigDict
from web3 import Web3
from web3.contract import Contract
from web3.datastructures import AttributeDict

Address = str
MSG_GAS_LIMIT = 100_000
TARGET_SPEED = "FAST"
DEPOSIT_GAS_LIMIT = 420_000
PAYLOAD_SIZE = 161
PROD_LYRA_ADDRESSES = "https://raw.githubusercontent.com/0xdomrom/socket-plugs/refs/heads/main/deployments/superbridge/prod_lyra_addresses.json"  # noqa: E501


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


class DRPCEndPoints(StrEnum):
    ETH = "https://eth.drpc.org"
    OPTIMISM = "https://optimism.drpc.org"
    BASE = "https://base.drpc.org"
    MODE = "https://mode.drpc.org"
    ARBITRUM = "https://arbitrum.drpc.org"
    BLAST = "https://blast.drpc.org"


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


def get_repo_root() -> Path:
    return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode().strip())


def fetch_json(url: str, cache_path: Path, post_processer: Callable = None):
    if cache_path.exists():
        return json.loads(cache_path.read_text())

    cache_path.parent.mkdir(exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    if post_processer:
        data = post_processer(data)
    cache_path.write_text(json.dumps(data, indent=4))

    return data


def fetch_prod_lyra_addresses(url: str = PROD_LYRA_ADDRESSES) -> LyraAddresses:
    """Fetch the chain data JSON from chainid.network."""

    cache_path = get_repo_root() / "data" / "prod_lyra_addresses.json"

    return LyraAddresses(chains=fetch_json(url=url, cache_path=cache_path))


def wait_for_tx_receipt(tx_hash: str, timeout=120, poll_interval=1) -> AttributeDict:
    start_time = time.time()
    while True:
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
        except Exception:
            receipt = None
        if receipt is not None:
            return receipt
        if time.time() - start_time > timeout:
            raise TimeoutError("Timed out waiting for transaction receipt.")
        time.sleep(poll_interval)


def sign_and_send_tx(w3: Web3, tx, private_key: str) -> AttributeDict:
    """
    Sign a transaction, send it, and wait for the receipt.

    Exceptions (e.g. timeout) will propagate, so the caller may handle them.
    """

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    print(f"signed_tx: {signed_tx}")
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"tx_hash: 0x{tx_hash.hex()}")
    tx_receipt = wait_for_tx_receipt(tx_hash=tx_hash)
    print(f"tx_receipt: {tx_receipt}")
    return tx_receipt


def increase_allowance(
    w3: Web3,
    from_account: Account,
    erc20_contract: Contract,
    spender: Address,
    amount: int,
    private_key: str,
) -> None:
    func = erc20_contract.functions.approve(spender, amount)
    nonce = w3.eth.get_transaction_count(from_account.address)
    tx = func.build_transaction(
        {
            "from": from_account.address,
            "nonce": nonce,
            "gas": MSG_GAS_LIMIT,
            "gasPrice": w3.eth.gas_price,
        }
    )

    try:
        tx_receipt = sign_and_send_tx(w3, tx=tx, private_key=private_key)
        if tx_receipt.status == TxStatus.SUCCESS:
            print("Transaction succeeded!")
        else:
            raise Exception("Transaction reverted.")
    except Exception as error:
        raise error


def get_min_fees(bridge_contract: Contract, connector: Address) -> int:
    total_fees = bridge_contract.functions.getMinFees(
        connector_=Web3.to_checksum_address(connector),
        msgGasLimit_=MSG_GAS_LIMIT,
        payloadSize_=PAYLOAD_SIZE,
    ).call()
    return total_fees


def prepare_bridge_tx(
    w3: Web3,
    chain_id: ChainID,
    account: Account,
    contract: Contract,
    receiver: Address,
    amount: int,
    msg_gas_limit: int,
    connector: Address,
) -> dict:
    func = contract.functions.bridge(
        receiver_=w3.to_checksum_address(receiver),
        amount_=amount,
        msgGasLimit_=msg_gas_limit,
        connector_=w3.to_checksum_address(connector),
        extraData_=b"",
        options_=b"",
    )

    fees = get_min_fees(contract, connector=connector)
    func.call({"from": account.address, "value": fees})

    nonce = w3.eth.get_transaction_count(account.address)
    tx = func.build_transaction(
        {
            "chainId": chain_id,
            "from": account.address,
            "nonce": nonce,
            "gas": DEPOSIT_GAS_LIMIT,
            "gasPrice": w3.eth.gas_price,
            "value": fees + 1,
        }
    )

    return tx


def get_w3_connection(chain_id: ChainID) -> Web3:
    rpc_url = DRPCEndPoints[chain_id.name]
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise ConnectionError(f"Failed to connect to RPC at {rpc_url}")
    return w3


def get_contract(w3: Web3, address: str, abi: list) -> Contract:
    return w3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)


def get_erc20_contract(w3: Web3, token_address: str) -> Contract:
    erc20_abi_path = get_repo_root() / "data" / "erc20.json"
    abi = json.loads(erc20_abi_path.read_text())
    return get_contract(w3=w3, address=token_address, abi=abi)


def ensure_balance(token_contract: Contract, owner: Address, amount: int):
    balance = token_contract.functions.balanceOf(owner).call()
    if amount > balance:
        raise ValueError(f"Not enough funds: {balance}, tried to send: {amount}")


def ensure_allowance(
    w3: Web3,
    token_contract: Contract,
    owner: Address,
    spender: Address,
    amount: int,
    private_key: str,
):
    allowance = token_contract.functions.allowance(owner, spender).call()
    if amount > allowance:
        print(f"Increasing allowance from {allowance} to {amount}")
        increase_allowance(
            w3=w3,
            from_account=Account.from_key(private_key),
            erc20_contract=token_contract,
            spender=spender,
            amount=amount,
            private_key=private_key,
        )


def bridge(
    w3: Web3,
    chain_id: ChainID,
    account: Account,
    amount: int,
    receiver: Address,
    bridge_contract: Contract,
    connector: Address,
    token_data: NonMintableTokenData,
    private_key: str,
):
    token_contract = get_erc20_contract(w3, token_data.NonMintableToken)

    ensure_balance(token_contract, account.address, amount)

    spender = token_data.Vault
    ensure_allowance(
        w3=w3,
        token_contract=token_contract,
        owner=account.address,
        spender=spender,
        amount=amount,
        private_key=private_key,
    )

    tx = prepare_bridge_tx(
        w3=w3,
        chain_id=chain_id,
        account=account,
        contract=bridge_contract,
        receiver=receiver,
        amount=amount,
        msg_gas_limit=MSG_GAS_LIMIT,
        connector=connector,
    )

    try:
        tx_receipt = sign_and_send_tx(w3=w3, tx=tx, private_key=private_key)
        if tx_receipt.status == TxStatus.SUCCESS:
            print("Transaction succeeded!")
        else:
            raise Exception("Transaction reverted.")
    except Exception as error:
        raise error


if __name__ == "__main__":
    if (ethereum_private_key := os.environ.get("ETHEREUM_PRIVATE_KEY")) is None:
        raise ValueError("ETHEREUM_PRIVATE_KEY not found in environment variables.")
    if (smart_contract_wallet_address := os.environ.get("DERIVE_SMART_CONTRACT_WALLET_ADDRESS")) is None:
        raise ValueError("DERIVE_SMART_CONTRACT_WALLET_ADDRESS not found in env.")

    chain_id = ChainID.BASE

    w3 = get_w3_connection(chain_id=chain_id)

    account = Account.from_key(ethereum_private_key)
    lyra_addresses = fetch_prod_lyra_addresses()

    token_data = lyra_addresses.chains[chain_id][Currency.weETH]
    connector = token_data.connectors[ChainID.LYRA][TARGET_SPEED]

    vault_address = token_data.Vault
    receiver = smart_contract_wallet_address

    vault_abi_path = get_repo_root() / "data" / "socket_superbridge_vault.json"
    abi = json.loads(vault_abi_path.read_text())
    bridge_contract = get_contract(w3=w3, address=vault_address, abi=abi)

    amount_eth = 0.001
    amount = w3.to_wei(amount_eth, "ether")

    bridge(
        w3=w3,
        chain_id=chain_id,
        account=account,
        amount=amount,
        receiver=receiver,
        bridge_contract=bridge_contract,
        connector=connector,
        token_data=token_data,
        private_key=ethereum_private_key,
    )
