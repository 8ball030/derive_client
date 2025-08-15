"""
Bridge client to deposit funds to the Derive smart contract funding account
"""

from __future__ import annotations

import functools
import json
from logging import Logger

from eth_account import Account
from web3 import Web3
from web3.contract import Contract
from web3.contract.contract import ContractFunction
from web3.datastructures import AttributeDict
from web3.types import HexBytes, LogReceipt, TxReceipt

from derive_client.constants import (
    CONFIGS,
    CONTROLLER_ABI_PATH,
    CONTROLLER_V0_ABI_PATH,
    DEPOSIT_HELPER_ABI_PATH,
    DEPOSIT_HOOK_ABI_PATH,
    DERIVE_ABI_PATH,
    DERIVE_L2_ABI_PATH,
    ERC20_ABI_PATH,
    LIGHT_ACCOUNT_ABI_PATH,
    LYRA_OFT_WITHDRAW_WRAPPER_ABI_PATH,
    LYRA_OFT_WITHDRAW_WRAPPER_ADDRESS,
    MSG_GAS_LIMIT,
    NEW_VAULT_ABI_PATH,
    OLD_VAULT_ABI_PATH,
    PAYLOAD_SIZE,
    SOCKET_ABI_PATH,
    TARGET_SPEED,
    WITHDRAW_WRAPPER_V2_ABI_PATH,
)
from derive_client.data_types import (
    Address,
    BridgeContext,
    BridgeTxDetails,
    BridgeTxResult,
    BridgeType,
    ChainID,
    Currency,
    DeriveTokenAddresses,
    Direction,
    Environment,
    LayerZeroChainIDv2,
    MintableTokenData,
    NonMintableTokenData,
    PreparedBridgeTx,
    SocketAddress,
    TxResult,
)
from derive_client.exceptions import (
    BridgeEventParseError,
    BridgePrimarySignerRequiredError,
    BridgeRouteError,
    DrvWithdrawAmountBelowFee,
    PartialBridgeResult,
)
from derive_client.utils import get_prod_derive_addresses

from .w3 import (
    build_standard_transaction,
    ensure_token_allowance,
    ensure_token_balance,
    get_contract,
    get_w3_connection,
    make_filter_params,
    send_tx,
    sign_tx,
    wait_for_event,
    wait_for_tx_finality,
)


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

    return bridge_contract.functions.getMinFees(**params)


class BridgeClient:
    def __init__(self, env: Environment, chain_id: ChainID, account: Account, wallet: Address, logger: Logger):
        """Private init - use Bridge.create() instead."""
        raise RuntimeError("Use Bridge.create() async factory method instead of direct instantiation.")

    @classmethod
    async def create(cls, env: Environment, chain_id: ChainID, account: Account, wallet: Address, logger: Logger):
        """Async factory method to create and validate a Bridge instance."""
        if not env == Environment.PROD:
            raise RuntimeError(f"Bridging is not supported in the {env.name} environment.")

        instance = cls.__new__(cls)
        instance.config = CONFIGS[env]
        instance.derive_w3 = get_w3_connection(chain_id=ChainID.DERIVE, logger=logger)
        instance.remote_w3 = get_w3_connection(chain_id=chain_id, logger=logger)
        instance.account = account
        instance.derive_addresses = get_prod_derive_addresses()
        instance.light_account = _load_light_account(w3=instance.derive_w3, wallet=wallet)
        instance.logger = logger
        instance.remote_chain_id = chain_id

        owner = await instance.light_account.functions.owner().call()
        if owner != account.address:
            raise BridgePrimarySignerRequiredError(
                "Bridging disabled for secondary session-key signers: old-style assets "
                "(USDC, USDT) on Derive cannot specify a custom receiver. Using a "
                "secondary signer routes funds to the session key's contract instead of "
                "the primary owner's. Please run all bridge operations with the "
                "primary wallet owner."
            )
        instance.owner = owner

        return instance

    @property
    def wallet(self) -> Address:
        """Smart contract funding wallet."""
        return self.light_account.address

    @property
    def private_key(self) -> str:
        """Private key of the owner (EOA) of the smart contract funding account."""
        return self.account._private_key

    @functools.cached_property
    def deposit_helper(self) -> Contract:

        match self.remote_chain_id:
            case ChainID.ARBITRUM:
                address = self.config.contracts.ARBITRUM_DEPOSIT_WRAPPER
            case ChainID.OPTIMISM:
                address = self.config.contracts.OPTIMISM_DEPOSIT_WRAPPER
            case _:
                address = self.config.contracts.DEPOSIT_WRAPPER

        abi = json.loads(DEPOSIT_HELPER_ABI_PATH.read_text())
        return get_contract(w3=self.remote_w3, address=address, abi=abi)

    @functools.cached_property
    def withdraw_wrapper(self) -> Contract:
        address = self.config.contracts.WITHDRAW_WRAPPER_V2
        abi = json.loads(WITHDRAW_WRAPPER_V2_ABI_PATH.read_text())
        return get_contract(w3=self.derive_w3, address=address, abi=abi)

    @functools.lru_cache
    def _make_bridge_context(
        self,
        direction: Direction,
        bridge_type: BridgeType,
        currency: Currency,
    ) -> BridgeContext:

        is_deposit = direction == Direction.DEPOSIT
        src_w3, tgt_w3 = (self.remote_w3, self.derive_w3) if is_deposit else (self.derive_w3, self.remote_w3)
        src_chain, tgt_chain = (
            (self.remote_chain_id, ChainID.DERIVE) if is_deposit else (ChainID.DERIVE, self.remote_chain_id)
        )

        if bridge_type == BridgeType.LAYERZERO and currency is Currency.DRV:
            src_addr = DeriveTokenAddresses[src_chain.name].value
            tgt_addr = DeriveTokenAddresses[tgt_chain.name].value
            derive_abi = json.loads(DERIVE_L2_ABI_PATH.read_text())
            remote_abi_path = DERIVE_ABI_PATH if self.remote_chain_id == ChainID.ETH else DERIVE_L2_ABI_PATH
            remote_abi = json.loads(remote_abi_path.read_text())
            src_abi, tgt_abi = (remote_abi, derive_abi) if is_deposit else (derive_abi, remote_abi)
            src = get_contract(src_w3, src_addr, abi=src_abi)
            tgt = get_contract(tgt_w3, tgt_addr, abi=tgt_abi)
            src_event, tgt_event = src.events.OFTSent(), tgt.events.OFTReceived()
            context = BridgeContext(src_w3, tgt_w3, src, src_event, tgt_event, src_chain, tgt_chain)
            return context

        elif bridge_type == BridgeType.SOCKET and currency is not Currency.DRV:
            erc20_abi = json.loads(ERC20_ABI_PATH.read_text())
            socket_abi = json.loads(SOCKET_ABI_PATH.read_text())

            if is_deposit:
                token_data: NonMintableTokenData = self.derive_addresses.chains[self.remote_chain_id][currency]
                token_contract = get_contract(src_w3, token_data.NonMintableToken, abi=erc20_abi)
            else:
                token_data: MintableTokenData = self.derive_addresses.chains[ChainID.DERIVE][currency]
                token_contract = get_contract(src_w3, token_data.MintableToken, abi=erc20_abi)

            src_addr = SocketAddress[src_chain.name].value
            tgt_addr = SocketAddress[tgt_chain.name].value
            src_socket = get_contract(src_w3, address=src_addr, abi=socket_abi)
            tgt_socket = get_contract(tgt_w3, address=tgt_addr, abi=socket_abi)
            src_event, tgt_event = src_socket.events.MessageOutbound(), tgt_socket.events.ExecutionSuccess()
            context = BridgeContext(src_w3, tgt_w3, token_contract, src_event, tgt_event, src_chain, tgt_chain)
            return context

        raise BridgeRouteError(f"Unsupported bridge_type={bridge_type} for currency={currency}.")

    def _get_context(self, state: PreparedBridgeTx | BridgeTxResult) -> BridgeContext:

        direction = Direction.WITHDRAW if state.source_chain == ChainID.DERIVE else Direction.DEPOSIT
        context = self._make_bridge_context(
            direction=direction,
            bridge_type=state.bridge,
            currency=state.currency,
        )

        return context

    def _resolve_socket_route(
        self,
        direction: Direction,
        currency: Currency,
    ) -> tuple[MintableTokenData | NonMintableTokenData, Address]:

        src_chain, tgt_chain = (
            (self.remote_chain_id, ChainID.DERIVE)
            if direction == Direction.DEPOSIT
            else (ChainID.DERIVE, self.remote_chain_id)
        )

        if (src_token_data := self.derive_addresses.chains[src_chain].get(currency)) is None:
            msg = f"No bridge path for {currency.name} from {src_chain.name} to {tgt_chain.name}."
            raise BridgeRouteError(msg)
        if (tgt_token_data := self.derive_addresses.chains[tgt_chain].get(currency)) is None:
            msg = f"No bridge path for {currency.name} from {tgt_chain.name} to {src_chain.name}."
            raise BridgeRouteError(msg)

        if tgt_chain not in src_token_data.connectors:
            msg = f"Target chain {tgt_chain.name} not found in {src_chain.name} connectors."
            raise BridgeRouteError(msg)
        if src_chain not in tgt_token_data.connectors:
            msg = f"Source chain {src_chain.name} not found in {tgt_chain.name} connectors."
            raise BridgeRouteError(msg)

        return src_token_data, src_token_data.connectors[tgt_chain][TARGET_SPEED]

    async def _prepare_tx(
        self,
        func: ContractFunction,
        value: int,
        currency: Currency,
        context: BridgeContext,
    ) -> PreparedBridgeTx:

        tx = await build_standard_transaction(func=func, account=self.account, w3=context.source_w3, value=value)
        signed_tx = sign_tx(w3=context.source_w3, tx=tx, private_key=self.private_key)

        tx_details = BridgeTxDetails(
            contract=func.address,
            method=func.fn_name,
            kwargs=func.kwargs,
            tx=tx,
            signed_tx=signed_tx,
        )

        bridge = BridgeType.LAYERZERO if currency == Currency.DRV else BridgeType.SOCKET
        prepared_tx = PreparedBridgeTx(
            currency=currency,
            bridge=bridge,
            source_chain=context.source_chain,
            target_chain=context.target_chain,
            tx_details=tx_details,
        )

        return prepared_tx

    async def prepare_deposit(self, amount: int, currency: Currency) -> PreparedBridgeTx:

        if currency == Currency.DRV:
            prepared_tx = await self._prepare_layerzero_deposit(amount=amount, currency=currency)
        else:
            prepared_tx = await self._prepare_socket_deposit(amount=amount, currency=currency)

        return prepared_tx

    async def prepare_withdrawal(self, amount: int, currency: Currency) -> PreparedBridgeTx:

        if currency == Currency.DRV:
            prepared_tx = await self._prepare_layerzero_withdrawal(amount=amount, currency=currency)
        else:
            prepared_tx = await self._prepare_socket_withdrawal(amount=amount, currency=currency)

        return prepared_tx

    async def submit_bridge_tx(self, prepared_tx: PreparedBridgeTx) -> BridgeTxResult:

        tx_result = await self.send_bridge_tx(prepared_tx=prepared_tx)

        return tx_result

    async def poll_bridge_progress(self, tx_result: BridgeTxResult) -> BridgeTxResult:

        try:
            tx_result.source_tx.tx_receipt = await self.confirm_source_tx(tx_result=tx_result)
            tx_result.target_tx = TxResult(tx_hash=await self.wait_for_target_event(tx_result=tx_result))
            tx_result.target_tx.tx_receipt = await self.confirm_target_tx(tx_result=tx_result)
        except Exception as e:
            raise PartialBridgeResult("Bridge pipeline failed", tx_result=tx_result) from e

        return tx_result

    async def _prepare_socket_deposit(self, amount: int, currency: Currency) -> PreparedBridgeTx:

        direction = Direction.DEPOSIT
        bridge_type = BridgeType.SOCKET
        token_data, _connector = self._resolve_socket_route(direction, currency=currency)
        context = self._make_bridge_context(direction, bridge_type=bridge_type, currency=currency)

        spender = token_data.Vault if token_data.isNewBridge else self.deposit_helper.address
        await ensure_token_balance(context.source_token, self.owner, amount)
        await ensure_token_allowance(
            w3=context.source_w3,
            token_contract=context.source_token,
            owner=self.owner,
            spender=spender,
            amount=amount,
            private_key=self.private_key,
            logger=self.logger,
        )

        if token_data.isNewBridge:
            func, fees_func = self._prepare_new_style_deposit(token_data, amount)
        else:
            func, fees_func = self._prepare_old_style_deposit(token_data, amount)

        fees = await fees_func.call()
        prepared_tx = await self._prepare_tx(func=func, value=fees + 1, currency=currency, context=context)

        return prepared_tx

    async def _prepare_socket_withdrawal(self, amount: int, currency: Currency) -> PreparedBridgeTx:

        direction = Direction.WITHDRAW
        bridge_type = BridgeType.SOCKET
        token_data, connector = self._resolve_socket_route(direction, currency=currency)
        context = self._make_bridge_context(direction, bridge_type=bridge_type, currency=currency)

        # ensure_token_balance(context.source_token, self.wallet, amount)
        # self._check_bridge_funds(token_data, connector, amount)

        kwargs = {
            "token": context.source_token.address,
            "amount": amount,
            "recipient": self.owner,
            "socketController": token_data.Controller,
            "connector": connector,
            "gasLimit": MSG_GAS_LIMIT,
        }

        # Encode the token approval and withdrawToChain for the withdraw wrapper.
        approve_data = context.source_token.encodeABI(fn_name="approve", args=[self.withdraw_wrapper.address, amount])
        bridge_data = self.withdraw_wrapper.encodeABI(fn_name="withdrawToChain", args=list(kwargs.values()))

        # Build the batch execution call via the Light Account.
        func = self.light_account.functions.executeBatch(
            dest=[context.source_token.address, self.withdraw_wrapper.address],
            func=[approve_data, bridge_data],
        )
        prepared_tx = await self._prepare_tx(func=func, value=0, currency=currency, context=context)

        return prepared_tx

    async def _prepare_layerzero_deposit(self, amount: int, currency: Currency) -> PreparedBridgeTx:

        direction = Direction.DEPOSIT
        bridge_type = BridgeType.LAYERZERO
        context = self._make_bridge_context(direction, bridge_type=bridge_type, currency=currency)

        # check allowance, if needed approve
        await ensure_token_balance(context.source_token, self.owner, amount)
        await ensure_token_allowance(
            w3=context.source_w3,
            token_contract=context.source_token,
            owner=self.owner,
            spender=context.source_token.address,
            amount=amount,
            private_key=self.private_key,
            logger=self.logger,
        )

        # build the send tx
        receiver_bytes32 = Web3.to_bytes(hexstr=self.wallet).rjust(32, b"\x00")

        kwargs = {
            "dstEid": LayerZeroChainIDv2.DERIVE.value,
            "receiver": receiver_bytes32,
            "amountLD": amount,
            "minAmountLD": 0,
            "extraOptions": b"",
            "composeMsg": b"",
            "oftCmd": b"",
        }

        pay_in_lz_token = False
        send_params = tuple(kwargs.values())
        fees = await context.source_token.functions.quoteSend(send_params, pay_in_lz_token).call()
        native_fee, lz_token_fee = fees
        refund_address = self.owner

        func = await context.source_token.functions.send(send_params, fees, refund_address)
        prepared_tx = await self._prepare_tx(func=func, value=native_fee, currency=currency, context=context)

        return prepared_tx

    async def _prepare_layerzero_withdrawal(self, amount: int, currency: Currency) -> PreparedBridgeTx:

        direction = Direction.WITHDRAW
        bridge_type = BridgeType.LAYERZERO
        context = self._make_bridge_context(direction, bridge_type=bridge_type, currency=currency)

        abi = json.loads(LYRA_OFT_WITHDRAW_WRAPPER_ABI_PATH.read_text())
        withdraw_wrapper = get_contract(context.source_w3, LYRA_OFT_WITHDRAW_WRAPPER_ADDRESS, abi=abi)

        await ensure_token_balance(context.source_token, self.wallet, amount)

        destEID = LayerZeroChainIDv2[context.target_chain.name]
        fee = await withdraw_wrapper.functions.getFeeInToken(context.source_token.address, amount, destEID).call()
        if amount < fee:
            raise DrvWithdrawAmountBelowFee(f"Withdraw amount < fee: {amount} < {fee} ({(fee / amount * 100):.2f}%)")

        kwargs = {
            "token": context.source_token.address,
            "amount": amount,
            "toAddress": self.owner,
            "destEID": destEID,
        }

        approve_data = context.source_token.encodeABI(fn_name="approve", args=[withdraw_wrapper.address, amount])
        bridge_data = withdraw_wrapper.encodeABI(fn_name="withdrawToChain", args=list(kwargs.values()))

        func = self.light_account.functions.executeBatch(
            dest=[context.source_token.address, withdraw_wrapper.address],
            func=[approve_data, bridge_data],
        )
        prepared_tx = await self._prepare_tx(func=func, value=0, currency=currency, context=context)

        return prepared_tx

    async def send_bridge_tx(self, prepared_tx: PreparedBridgeTx) -> BridgeTxResult:

        context = self._get_context(prepared_tx)

        # record on target chain where we should start polling
        target_from_block = await context.target_w3.eth.block_number

        signed_tx = prepared_tx.tx_details.signed_tx
        tx_hash = await send_tx(w3=context.source_w3, signed_tx=signed_tx)
        source_tx = TxResult(tx_hash=tx_hash)

        tx_result = BridgeTxResult(
            currency=prepared_tx.currency,
            bridge=prepared_tx.bridge,
            source_chain=context.source_chain,
            target_chain=context.target_chain,
            source_tx=source_tx,
            target_from_block=target_from_block,
            tx_details=prepared_tx.tx_details,
        )

        return tx_result

    async def confirm_source_tx(self, tx_result: BridgeTxResult) -> TxReceipt:

        context = self._get_context(tx_result)
        msg = "⏳ Checking source chain [%s] tx receipt for %s"
        self.logger.info(msg, tx_result.source_chain.name, tx_result.source_tx.tx_hash)
        tx_receipt = await wait_for_tx_finality(
            w3=context.source_w3,
            tx_hash=tx_result.source_tx.tx_hash,
            logger=self.logger,
        )

        return tx_receipt

    async def wait_for_target_event(self, tx_result: BridgeTxResult) -> HexBytes:

        bridge_event_fetchers = {
            BridgeType.SOCKET: self._fetch_socket_event_log,
            BridgeType.LAYERZERO: self._fetch_lz_event_log,
        }
        if (fetch_event := bridge_event_fetchers.get(tx_result.bridge)) is None:
            raise BridgeRouteError(f"Invalid bridge_type: {tx_result.bridge}")

        context = self._get_context(tx_result)
        event_log = await fetch_event(tx_result, context)
        tx_hash = event_log["transactionHash"]
        self.logger.info(f"Target event tx_hash found: {tx_hash.to_0x_hex()}")

        return tx_hash

    async def confirm_target_tx(self, tx_result: BridgeTxResult) -> TxReceipt:

        context = self._get_context(tx_result)
        msg = "⏳ Checking target chain [%s] tx receipt for %s"
        self.logger.info(msg, tx_result.target_chain.name, tx_result.target_tx.tx_hash)
        tx_receipt = await wait_for_tx_finality(
            w3=context.target_w3,
            tx_hash=tx_result.target_tx.tx_hash,
            logger=self.logger,
        )

        return tx_receipt

    async def _fetch_lz_event_log(self, tx_result: BridgeTxResult, context: BridgeContext) -> LogReceipt:

        try:
            source_event = context.source_event.process_log(tx_result.source_tx.tx_receipt.logs[-1])
            guid = source_event["args"]["guid"]
        except Exception as e:
            raise BridgeEventParseError(f"Could not decode LayerZero OFTSent guid: {e}") from e

        tx_result.event_id = guid.hex()
        self.logger.info(f"🔖 Source [{tx_result.source_chain.name}] OFTSent GUID: {tx_result.event_id}")

        filter_params = make_filter_params(
            event=context.target_event,
            from_block=tx_result.target_from_block,
            argument_filters={"guid": guid},
        )

        self.logger.info(
            f"🔍 Listening for OFTReceived on [{tx_result.target_chain.name}] at {context.target_event.address}"
        )

        return await wait_for_event(context.target_w3, filter_params, logger=self.logger)

    async def _fetch_socket_event_log(self, tx_result: BridgeTxResult, context: BridgeContext) -> LogReceipt:

        try:
            source_event = context.source_event.process_log(tx_result.source_tx.tx_receipt.logs[-2])
            message_id = source_event["args"]["msgId"]
        except Exception as e:
            raise BridgeEventParseError(f"Could not decode Socket MessageOutbound event: {e}") from e

        tx_result.event_id = message_id.hex()
        self.logger.info(f"🔖 Source [{tx_result.source_chain.name}] MessageOutbound msgId: {tx_result.event_id}")
        filter_params = context.target_event._get_event_filter_params(
            fromBlock=tx_result.target_from_block, abi=context.target_event.abi
        )

        def matching_message_id(log: AttributeDict) -> bool:
            decoded = context.target_event.process_log(log)
            return decoded.get("args", {}).get("msgId") == message_id

        self.logger.info(
            f"🔍 Listening for ExecutionSuccess on [{tx_result.target_chain.name}] at {context.target_event.address}"
        )

        return await wait_for_event(context.target_w3, filter_params, condition=matching_message_id, logger=self.logger)

    def _prepare_new_style_deposit(self, token_data: NonMintableTokenData, amount: int) -> tuple[ContractFunction, int]:

        vault_contract = _load_vault_contract(w3=self.remote_w3, token_data=token_data)
        connector = token_data.connectors[ChainID.DERIVE][TARGET_SPEED]
        fees_func = _get_min_fees(bridge_contract=vault_contract, connector=connector, token_data=token_data)
        func = vault_contract.functions.bridge(
            receiver_=self.wallet,
            amount_=amount,
            msgGasLimit_=MSG_GAS_LIMIT,
            connector_=connector,
            extraData_=b"",
            options_=b"",
        )

        return func, fees_func

    def _prepare_old_style_deposit(self, token_data: NonMintableTokenData, amount: int) -> tuple[ContractFunction, int]:

        vault_contract = _load_vault_contract(w3=self.remote_w3, token_data=token_data)
        connector = token_data.connectors[ChainID.DERIVE][TARGET_SPEED]
        fees_func = _get_min_fees(bridge_contract=vault_contract, connector=connector, token_data=token_data)
        func = self.deposit_helper.functions.depositToLyra(
            token=token_data.NonMintableToken,
            socketVault=token_data.Vault,
            isSCW=True,
            amount=amount,
            gasLimit=MSG_GAS_LIMIT,
            connector=connector,
        )

        return func, fees_func

    def _check_bridge_funds(self, token_data, connector: Address, amount: int) -> None:

        controller = _load_controller_contract(w3=self.derive_w3, token_data=token_data)
        if token_data.isNewBridge:
            deposit_hook = controller.functions.hook__().call()
            expected_hook = token_data.LyraTSAShareHandlerDepositHook
            if not deposit_hook == token_data.LyraTSAShareHandlerDepositHook:
                msg = f"Controller deposit hook {deposit_hook} does not match expected address {expected_hook}"
                raise ValueError(msg)
            deposit_contract = _load_deposit_contract(w3=self.derive_w3, token_data=token_data)
            pool_id = deposit_contract.functions.connectorPoolIds(connector).call()
            locked = deposit_contract.functions.poolLockedAmounts(pool_id).call()
        else:
            pool_id = controller.functions.connectorPoolIds(connector).call()
            locked = controller.functions.poolLockedAmounts(pool_id).call()

        if amount > locked:
            raise RuntimeError(
                f"Insufficient funds locked in pool: has {locked}, want {amount} ({(locked / amount * 100):.2f}%)"
            )
