"""
Bridge client to deposit funds to the Derive smart contract funding account
"""

from __future__ import annotations

import json

from eth_account import Account
from web3 import Web3
from web3.contract import Contract

from derive_client.bridge.constants import MSG_GAS_LIMIT
from derive_client.bridge.enums import ChainID, TxStatus
from derive_client.bridge.models import Address, NonMintableTokenData
from derive_client.bridge.transaction import ensure_allowance, ensure_balance, prepare_bridge_tx
from derive_client.bridge.utils import get_contract, get_erc20_contract, get_repo_root, sign_and_send_tx

VAULT_ABI_PATH = get_repo_root() / "data" / "socket_superbridge_vault.json"


class BridgeClient:
    def __init__(self, w3: Web3, account: Account, chain_id: ChainID):
        self.w3 = w3
        self.account = account
        self.chain_id = chain_id
        self.bridge_contract: Contract | None = None

    def load_bridge_contract(self, vault_address: str) -> None:
        """Instantiate the bridge contract."""

        abi = json.loads(VAULT_ABI_PATH.read_text())
        address = self.w3.to_checksum_address(vault_address)
        self.bridge_contract = get_contract(w3=self.w3, address=address, abi=abi)

    def deposit(
        self, amount: int, receiver: Address, connector: Address, token_data: NonMintableTokenData, private_key: str
    ):
        """
        Deposit funds by preparing, signing, and sending a bridging transaction.
        """

        token_contract = get_erc20_contract(self.w3, token_data.NonMintableToken)

        ensure_balance(token_contract, self.account.address, amount)
        ensure_allowance(self.w3, token_contract, self.account.address, token_data.Vault, amount, private_key)

        tx = prepare_bridge_tx(
            w3=self.w3,
            chain_id=self.chain_id,
            account=self.account,
            contract=self.bridge_contract,
            receiver=receiver,
            amount=amount,
            msg_gas_limit=MSG_GAS_LIMIT,
            connector=connector,
        )

        tx_receipt = sign_and_send_tx(self.w3, tx, private_key)
        if tx_receipt.status == TxStatus.SUCCESS:
            print("Deposit successful!")
            return tx_receipt
        else:
            raise Exception("Deposit transaction reverted.")
