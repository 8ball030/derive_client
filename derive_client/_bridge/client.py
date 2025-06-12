"""
Bridge client to deposit funds to the Derive smart contract funding account
"""

from __future__ import annotations

import json

from eth_account import Account
from web3 import Web3
from web3.contract import Contract

from derive_client._bridge.transaction import ensure_allowance, ensure_balance, prepare_mainnet_to_derive_gas_tx
from derive_client.constants import (
    CONFIGS,
    CONTROLLER_ABI_PATH,
    CONTROLLER_V0_ABI_PATH,
    DEFAULT_GAS_FUNDING_AMOUNT,
    DEPOSIT_GAS_LIMIT,
    DEPOSIT_HELPER_ABI_PATH,
    DEPOSIT_HOOK_ABI_PATH,
    L1_STANDARD_BRIDGE_ABI_PATH,
    LIGHT_ACCOUNT_ABI_PATH,
    MSG_GAS_LIMIT,
    NEW_VAULT_ABI_PATH,
    OLD_VAULT_ABI_PATH,
    PAYLOAD_SIZE,
    TARGET_SPEED,
    WITHDRAW_WRAPPER_V2_ABI_PATH,
)
from derive_client.data_types import (
    Address,
    ChainID,
    DeriveTokenAddresses,
    Environment,
    LayerZeroChainIDv2,
    MintableTokenData,
    NonMintableTokenData,
    RPCEndPoints,
    TxResult,
)
from derive_client.utils import build_standard_transaction, get_contract, get_erc20_contract, send_and_confirm_tx


def _load_vault_contract(w3: Web3, token_data: NonMintableTokenData) -> Contract:
    path = NEW_VAULT_ABI_PATH if token_data.isNewBridge else OLD_VAULT_ABI_PATH
    abi = json.loads(path.read_text())
    return get_contract(w3=w3, address=token_data.Vault, abi=abi)


def _load_controller_contract(w3: Web3, token_data: MintableTokenData) -> Contract:
    path = CONTROLLER_ABI_PATH if token_data.isNewBridge else CONTROLLER_V0_ABI_PATH
    abi = json.loads(path.read_text())
    return get_contract(w3=w3, address=token_data.Controller, abi=abi)


def _load_deposit_contract(w3: Web3, token_data: MintableTokenData) -> Contract:
    address = token_data.LyraTSAShareHandlerDepositHook
    abi = json.loads(DEPOSIT_HOOK_ABI_PATH.read_text())
    return get_contract(w3=w3, address=address, abi=abi)


def _load_light_account(w3: Web3, wallet: Address) -> Contract:
    abi = json.loads(LIGHT_ACCOUNT_ABI_PATH.read_text())
    return get_contract(w3=w3, address=wallet, abi=abi)


def _get_min_fees(
    bridge_contract: Contract,
    connector: Address,
    token_data: NonMintableTokenData | MintableTokenData,
) -> int:
    params = {
        "connector_": connector,
        "msgGasLimit_": MSG_GAS_LIMIT,
    }
    if token_data.isNewBridge:
        params["payloadSize_"] = PAYLOAD_SIZE

    return bridge_contract.functions.getMinFees(**params).call()


class BridgeClient:
    def __init__(self, env: Environment, w3: Web3, account: Account):
        if not env == Environment.PROD:
            raise RuntimeError(f"Bridging is not supported in the {env.name} environment.")
        self.config = CONFIGS[env]
        self.w3 = w3
        self.account = account
        self.withdraw_wrapper = self._load_withdraw_wrapper()
        self.deposit_helper = self._load_deposit_helper()

    def _load_deposit_helper(self) -> Contract:
        address = (
            self.config.contracts.DEPOSIT_WRAPPER
            if self.w3.eth.chain_id
            not in [
                ChainID.ARBITRUM,
                ChainID.OPTIMISM,
            ]
            else getattr(self.config.contracts, f"{ChainID(self.w3.eth.chain_id).name}_DEPOSIT_WRAPPER")
        )
        abi = json.loads(DEPOSIT_HELPER_ABI_PATH.read_text())
        return get_contract(w3=self.w3, address=address, abi=abi)

    def _load_withdraw_wrapper(self) -> Contract:
        address = self.config.contracts.WITHDRAW_WRAPPER_V2
        abi = json.loads(WITHDRAW_WRAPPER_V2_ABI_PATH.read_text())
        return get_contract(w3=self.w3, address=address, abi=abi)

    def deposit_drv(
        self,
        amount: int,
        receiver: Address,
        chain_id: ChainID,
    ) -> TxResult:
        """
        Deposit funds by preparing, signing, and sending a bridging transaction.
        """

        spender = Web3.to_checksum_address(DeriveTokenAddresses[chain_id.name])
        if chain_id == ChainID.ETH:
            abi_path = CONTROLLER_ABI_PATH.parent / "Derive.json"
        else:
            abi_path = CONTROLLER_ABI_PATH.parent / "DeriveL2.json"

        abi = json.loads(abi_path.read_text())
        token_contract = get_contract(self.w3, spender, abi=abi)

        ensure_balance(token_contract, self.account.address, amount)
        ensure_allowance(
            w3=self.w3,
            token_contract=token_contract,
            owner=self.account.address,
            spender=spender,
            amount=amount,
            private_key=self.account._private_key,
        )

        receiver_bytes32 = Web3.to_bytes(hexstr=self.account.address).rjust(32, b"\x00")

        params = (
            LayerZeroChainIDv2.DERIVE.value,  # dstEid
            receiver_bytes32,  # receiver
            amount,  # amountLD
            amount,  # minAmountLD
            b"",  # extraOptions
            b"",  # composeMsg
            b"",  # oftCmd
        )
        fees = token_contract.functions.quoteSend(
            params,
            False,  # payInLzToken
        ).call()

        native_fee, lz_token_fee = fees
        _refundAddress = self.account.address
        func = token_contract.functions.send(params, fees, _refundAddress)

        tx = build_standard_transaction(func=func, account=self.account, w3=self.w3, value=native_fee)

        tx_result = send_and_confirm_tx(w3=self.w3, tx=tx, private_key=self.account._private_key, action="bridge()")
        return tx_result

    def deposit(
        self,
        amount: int,
        receiver: Address,
        token_data: NonMintableTokenData | MintableTokenData,
    ) -> TxResult:
        """
        Deposit funds by preparing, signing, and sending a bridging transaction.
        """

        spender = token_data.Vault if token_data.isNewBridge else self.deposit_helper.address
        token_contract = get_erc20_contract(self.w3, token_data.NonMintableToken)
        ensure_balance(token_contract, self.account.address, amount)
        ensure_allowance(
            w3=self.w3,
            token_contract=token_contract,
            owner=self.account.address,
            spender=spender,
            amount=amount,
            private_key=self.account._private_key,
        )

        if token_data.isNewBridge:
            tx = self._prepare_new_style_deposit(token_data, amount, receiver)
        else:
            tx = self._prepare_old_style_deposit(token_data, amount)

        tx_result = send_and_confirm_tx(w3=self.w3, tx=tx, private_key=self.account._private_key, action="bridge()")
        return tx_result

    def withdraw_drv(
        self,
        amount: int,
        receiver: Address,
        wallet: Address,
        private_key: str,
        target_chain: int,
    ):
        # proxy contract address for DRV token contract on Derive chain
        mintable_token = Web3.to_checksum_address("0x2EE0fd70756EDC663AcC9676658A1497C247693A")

        token_contract = get_erc20_contract(self.w3, mintable_token)
        light_account = _load_light_account(w3=self.w3, wallet=wallet)

        ABI_PATH = CONTROLLER_ABI_PATH.parent / "LyraOFTWithdrawWrapper.json"
        address = "0x9400cc156dad38a716047a67c897973A29A06710"
        abi = json.loads(ABI_PATH.read_text())
        withdraw_wrapper = get_contract(self.w3, address, abi=abi)

        balance = token_contract.functions.balanceOf(wallet).call()
        if balance < amount:
            raise ValueError(f"Not enough tokens to withdraw: {amount} < {balance} ({(balance / amount * 100):.2f}%) ")

        destEID = LayerZeroChainIDv2[target_chain.name]
        fee = withdraw_wrapper.functions.getFeeInToken(token_contract.address, amount, destEID).call()
        if amount < fee:
            raise ValueError(f"Withdraw amount < fee: {amount} < {fee} ({(fee / amount * 100):.2f}%)")

        kwargs = {
            "token": token_contract.address,
            "amount": amount,
            "toAddress": receiver,
            "destEID": destEID,
        }

        approve_data = token_contract.encodeABI(fn_name="approve", args=[withdraw_wrapper.address, amount])
        bridge_data = withdraw_wrapper.encodeABI(fn_name="withdrawToChain", args=list(kwargs.values()))

        func = light_account.functions.executeBatch(
            dest=[token_contract.address, withdraw_wrapper.address],
            func=[approve_data, bridge_data],
        )

        tx = build_standard_transaction(func=func, account=self.account, w3=self.w3, value=0)

        tx_result = send_and_confirm_tx(w3=self.w3, tx=tx, private_key=private_key, action="executeBatch()")
        return tx_result

    def withdraw_with_wrapper(
        self,
        amount: int,
        receiver: Address,
        token_data: MintableTokenData,
        wallet: Address,
        private_key: str,
        target_chain: int,
    ) -> TxResult:
        """
        Checks if sufficent gas is available in derive, if not funds the wallet.
        Prepares, signs, and sends a withdrawal transaction using the withdraw wrapper.
        """

        if not self.w3.eth.chain_id == ChainID.DERIVE:
            raise ValueError(
                f"Connected to chain ID {self.w3.eth.chain_id}, but expected Derive chain ({ChainID.DERIVE})."
            )

        derive_w3 = Web3(Web3.HTTPProvider(RPCEndPoints.DERIVE.value))
        balance_of_owner = derive_w3.eth.get_balance(self.account.address)
        if balance_of_owner < DEPOSIT_GAS_LIMIT:
            print(f"Funding Derive EOA wallet with {DEFAULT_GAS_FUNDING_AMOUNT} ETH")
            self.bridge_mainnet_eth_to_derive(DEFAULT_GAS_FUNDING_AMOUNT)

        connector = token_data.connectors[target_chain][TARGET_SPEED]

        # Get the token contract and Light Account contract instances.
        token_contract = get_erc20_contract(self.w3, token_data.MintableToken)
        light_account = _load_light_account(w3=self.w3, wallet=wallet)

        owner = light_account.functions.owner().call()
        if not receiver == owner:
            raise NotImplementedError(f"Withdraw to receiver {receiver} other than wallet owner {owner}")

        self._check_bridge_funds(token_data, connector, amount)

        kwargs = {
            "token": token_contract.address,
            "amount": amount,
            "recipient": receiver,
            "socketController": token_data.Controller,
            "connector": connector,
            "gasLimit": MSG_GAS_LIMIT,
        }

        # Encode the token approval and withdrawToChain for the withdraw wrapper.
        approve_data = token_contract.encodeABI(fn_name="approve", args=[self.withdraw_wrapper.address, amount])
        bridge_data = self.withdraw_wrapper.encodeABI(fn_name="withdrawToChain", args=list(kwargs.values()))

        # Build the batch execution call via the Light Account.
        func = light_account.functions.executeBatch(
            dest=[token_contract.address, self.withdraw_wrapper.address],
            func=[approve_data, bridge_data],
        )

        tx = build_standard_transaction(func=func, account=self.account, w3=self.w3, value=0)

        tx_result = send_and_confirm_tx(w3=self.w3, tx=tx, private_key=private_key, action="executeBatch()")
        return tx_result

    def bridge_mainnet_eth_to_derive(self, amount: int) -> TxResult:
        """
        Prepares, signs, and sends a transaction to bridge ETH from mainnet to Derive.
        This is the "socket superbridge" method; not required when using the withdraw wrapper.
        """

        w3 = Web3(Web3.HTTPProvider(RPCEndPoints.ETH.value))

        address = self.config.contracts.L1_CHUG_SPLASH_PROXY
        bridge_abi = json.loads(L1_STANDARD_BRIDGE_ABI_PATH.read_text())
        proxy_contract = get_contract(w3=w3, address=address, abi=bridge_abi)

        tx = prepare_mainnet_to_derive_gas_tx(w3=w3, account=self.account, amount=amount, proxy_contract=proxy_contract)
        tx_result = send_and_confirm_tx(w3=w3, tx=tx, private_key=self.account._private_key, action="bridgeETH()")
        return tx_result

    def _prepare_new_style_deposit(
        self,
        token_data: NonMintableTokenData,
        amount: int,
        receiver: Address,
    ) -> dict:
        vault_contract = _load_vault_contract(w3=self.w3, token_data=token_data)
        connector = token_data.connectors[ChainID.DERIVE][TARGET_SPEED]
        fees = _get_min_fees(bridge_contract=vault_contract, connector=connector, token_data=token_data)
        func = vault_contract.functions.bridge(
            receiver_=receiver,
            amount_=amount,
            msgGasLimit_=MSG_GAS_LIMIT,
            connector_=connector,
            extraData_=b"",
            options_=b"",
        )
        return build_standard_transaction(func=func, account=self.account, w3=self.w3, value=fees + 1)

    def _prepare_old_style_deposit(self, token_data: NonMintableTokenData, amount: int) -> dict:
        vault_contract = _load_vault_contract(w3=self.w3, token_data=token_data)
        connector = token_data.connectors[ChainID.DERIVE][TARGET_SPEED]
        fees = _get_min_fees(bridge_contract=vault_contract, connector=connector, token_data=token_data)
        func = self.deposit_helper.functions.depositToLyra(
            token=token_data.NonMintableToken,
            socketVault=token_data.Vault,
            isSCW=True,
            amount=amount,
            gasLimit=MSG_GAS_LIMIT,
            connector=connector,
        )
        return build_standard_transaction(func=func, account=self.account, w3=self.w3, value=fees + 1)

    def _check_bridge_funds(self, token_data, connector: Address, amount: int):
        controller = _load_controller_contract(w3=self.w3, token_data=token_data)
        if token_data.isNewBridge:
            deposit_hook = controller.functions.hook__().call()
            expected_hook = token_data.LyraTSAShareHandlerDepositHook
            if not deposit_hook == token_data.LyraTSAShareHandlerDepositHook:
                raise ValueError(
                    f"Controller deposit hook {deposit_hook} does not match expected address {expected_hook}"
                )
            deposit_contract = _load_deposit_contract(w3=self.w3, token_data=token_data)
            pool_id = deposit_contract.functions.connectorPoolIds(connector).call()
            locked = deposit_contract.functions.poolLockedAmounts(pool_id).call()
        else:
            pool_id = controller.functions.connectorPoolIds(connector).call()
            locked = controller.functions.poolLockedAmounts(pool_id).call()

        if amount > locked:
            raise RuntimeError(
                f"Insufficient funds locked in pool: has {locked}, want {amount} ({(locked / amount * 100):.2f}%)"
            )
