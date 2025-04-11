import json
import subprocess
import time
from pathlib import Path

from web3 import Web3
from web3.contract import Contract
from web3.datastructures import AttributeDict

from derive_client.bridge.enums import ChainID, DRPCEndPoints
from derive_client.bridge.models import LyraAddresses


def get_repo_root() -> Path:
    return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode().strip())


def get_prod_lyra_addresses() -> LyraAddresses:
    """Fetch the socket superbridge JSON data."""
    prod_lyra_addresses = get_repo_root() / "data" / "prod_lyra_addresses.json"
    return LyraAddresses(chains=json.loads(prod_lyra_addresses.read_text()))


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


def wait_for_tx_receipt(w3: Web3, tx_hash: str, timeout=120, poll_interval=1) -> AttributeDict:
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


def sign_and_send_tx(w3: Web3, tx: dict, private_key: str) -> AttributeDict:
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    print(f"signed_tx: {signed_tx}")
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"tx_hash: 0x{tx_hash.hex()}")
    receipt = wait_for_tx_receipt(w3, tx_hash)
    print(f"tx_receipt: {receipt}")
    return receipt
