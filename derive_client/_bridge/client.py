"""
Bridge client to deposit funds to the Derive smart contract funding account
"""

from __future__ import annotations

import functools
import json
from logging import Logger

from eth_account import Account
from returns.future import future_safe
from returns.io import IOResult
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
from derive_client.utils.w3 import to_base_units

from .w3 import (
    build_standard_transaction,
    ensure_token_allowance,
    ensure_token_balance,
    get_contract,
    get_w3_connections,
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
    def __init__(self, env: Environment, account: Account, wallet: Address, logger: Logger):
        """Synchronous constructor that performs minimal, non-blocking setup."""

        if not env == Environment.PROD:
            raise RuntimeError(f"Bridging is not supported in the {env.name} environment.")

        self.config = CONFIGS[env]
        self.account = account
        self.owner = account.address
        self.wallet = wallet
        self.derive_addresses = get_prod_derive_addresses()
        self.w3s = get_w3_connections(logger=logger)
        self.logger = logger

    @property
    def derive_w3(self):
        return self.w3s[ChainID.DERIVE]

    @property
    def private_key(self) -> str:
        """Private key of the owner (EOA) of the smart contract funding account."""
        return self.account._private_key

    @functools.cached_property
    def light_account(self):
        """Smart contract funding wallet."""
        return _load_light_account(w3=self.derive_w3, wallet=self.wallet)

    async def verify_owner(self):
        """We verify the wallet owner on each prepare_deposit and prepare_withdrawal."""

        owner = await self.light_account.functions.owner().call()
        if owner != self.owner:
            raise BridgePrimarySignerRequiredError(
                "Bridging disabled for secondary session-key signers: old-style assets "
                "(USDC, USDT) on Derive cannot specify a custom receiver. Using a "
                "secondary signer routes funds to the session key's contract instead of "
                "the primary owner's. Please run all bridge operations with the "
                "primary wallet owner."
            )

    def get_deposit_helper(self, context: BridgeContext) -> Contract:

        match context.source_chain:
            case ChainID.ARBITRUM:
                address = self.config.contracts.ARBITRUM_DEPOSIT_WRAPPER
            case ChainID.OPTIMISM:
                address = self.config.contracts.OPTIMISM_DEPOSIT_WRAPPER
            case _:
                address = self.config.contracts.DEPOSIT_WRAPPER

        abi = json.loads(DEPOSIT_HELPER_ABI_PATH.read_text())
        return get_contract(w3=self.w3s[context.source_chain], address=address, abi=abi)

    @functools.cached_property
    def withdraw_wrapper(self) -> Contract:
        address = self.config.contracts.WITHDRAW_WRAPPER_V2
        abi = json.loads(WITHDRAW_WRAPPER_V2_ABI_PATH.read_text())
        return get_contract(w3=self.derive_w3, address=address, abi=abi)

    @functools.lru_cache
    def _make_bridge_context(
        self,
        direction: Direction,
        currency: Currency,
        remote_chain_id: ChainID,
    ) -> BridgeContext:

        is_deposit = direction == Direction.DEPOSIT

        if is_deposit:
            src_w3, tgt_w3 = self.w3s[remote_chain_id], self.derive_w3
            src_chain, tgt_chain = remote_chain_id, ChainID.DERIVE
        else:
            src_w3, tgt_w3 = self.derive_w3, self.w3s[remote_chain_id]
            src_chain, tgt_chain = ChainID.DERIVE, remote_chain_id

        if currency is Currency.DRV:
            src_addr = DeriveTokenAddresses[src_chain.name].value
            tgt_addr = DeriveTokenAddresses[tgt_chain.name].value
            derive_abi = json.loads(DERIVE_L2_ABI_PATH.read_text())
            remote_abi_path = DERIVE_ABI_PATH if remote_chain_id == ChainID.ETH else DERIVE_L2_ABI_PATH
            remote_abi = json.loads(remote_abi_path.read_text())
            src_abi, tgt_abi = (remote_abi, derive_abi) if is_deposit else (derive_abi, remote_abi)
            src = get_contract(src_w3, src_addr, abi=src_abi)
            tgt = get_contract(tgt_w3, tgt_addr, abi=tgt_abi)
            src_event, tgt_event = src.events.OFTSent(), tgt.events.OFTReceived()
            context = BridgeContext(currency, src_w3, tgt_w3, src, src_event, tgt_event, src_chain, tgt_chain)
            return context

        erc20_abi = json.loads(ERC20_ABI_PATH.read_text())
        socket_abi = json.loads(SOCKET_ABI_PATH.read_text())

        if is_deposit:
            token_data: NonMintableTokenData = self.derive_addresses.chains[src_chain][currency]
            token_contract = get_contract(src_w3, token_data.NonMintableToken, abi=erc20_abi)
        else:
            token_data: MintableTokenData = self.derive_addresses.chains[src_chain][currency]
            token_contract = get_contract(src_w3, token_data.MintableToken, abi=erc20_abi)

        src_addr = SocketAddress[src_chain.name].value
        tgt_addr = SocketAddress[tgt_chain.name].value
        src_socket = get_contract(src_w3, address=src_addr, abi=socket_abi)
        tgt_socket = get_contract(tgt_w3, address=tgt_addr, abi=socket_abi)
        src_event, tgt_event = src_socket.events.MessageOutbound(), tgt_socket.events.ExecutionSuccess()
        context = BridgeContext(currency, src_w3, tgt_w3, token_contract, src_event, tgt_event, src_chain, tgt_chain)
        return context

    def _get_context(self, state: PreparedBridgeTx | BridgeTxResult) -> BridgeContext:

        direction = Direction.WITHDRAW if state.source_chain == ChainID.DERIVE else Direction.DEPOSIT
        remote_chain_id = state.target_chain if direction == Direction.WITHDRAW else state.source_chain
        context = self._make_bridge_context(
            direction=direction,
            currency=state.currency,
            remote_chain_id=remote_chain_id,
        )

        return context

    def _resolve_socket_route(
        self,
        context: BridgeContext,
    ) -> tuple[MintableTokenData | NonMintableTokenData, Address]:

        currency = context.currency
        src_chain, tgt_chain = context.source_chain, context.target_chain

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
        context: BridgeContext,
    ) -> PreparedBridgeTx:

        w3 = context.source_w3
        tx = await build_standard_transaction(func=func, account=self.account, w3=w3, value=value, logger=self.logger)
        signed_tx = sign_tx(w3=context.source_w3, tx=tx, private_key=self.private_key)

        tx_details = BridgeTxDetails(
            contract=func.address,
            method=func.fn_name,
            kwargs=func.kwargs,
            tx=tx,
            signed_tx=signed_tx,
        )

        prepared_tx = PreparedBridgeTx(
            currency=context.currency,
            source_chain=context.source_chain,
            target_chain=context.target_chain,
            tx_details=tx_details,
        )

        return prepared_tx

    @future_safe
    async def prepare_deposit(
        self,
        token_amount: float,
        currency: Currency,
        chain_id: ChainID,
    ) -> IOResult[PreparedBridgeTx, Exception]:

        amount: int = to_base_units(token_amount=token_amount, currency=currency)
        await self.verify_owner()

        direction = Direction.DEPOSIT

        if currency == Currency.DRV:
            context = self._make_bridge_context(direction, currency=currency, remote_chain_id=chain_id)
            prepared_tx = await self._prepare_layerzero_deposit(amount=amount, context=context)
        else:
            context = self._make_bridge_context(direction, currency=currency, remote_chain_id=chain_id)
            prepared_tx = await self._prepare_socket_deposit(amount=amount, context=context)

        return prepared_tx

    @future_safe
    async def prepare_withdrawal(
        self,
        token_amount: float,
        currency: Currency,
        chain_id: ChainID,
    ) -> IOResult[PreparedBridgeTx, Exception]:

        amount: int = to_base_units(token_amount=token_amount, currency=currency)
        await self.verify_owner()

        direction = Direction.WITHDRAW

        if currency == Currency.DRV:
            context = self._make_bridge_context(direction, currency=currency, remote_chain_id=chain_id)
            prepared_tx = await self._prepare_layerzero_withdrawal(amount=amount, context=context)
        else:
            context = self._make_bridge_context(direction, currency=currency, remote_chain_id=chain_id)
            prepared_tx = await self._prepare_socket_withdrawal(amount=amount, context=context)

        return prepared_tx

    @future_safe
    async def submit_bridge_tx(self, prepared_tx: PreparedBridgeTx) -> IOResult[BridgeTxResult, Exception]:

        tx_result = await self._send_bridge_tx(prepared_tx=prepared_tx)

        return tx_result

    @future_safe
    async def poll_bridge_progress(self, tx_result: BridgeTxResult) -> IOResult[BridgeTxResult, Exception]:

        try:
            tx_result.source_tx.tx_receipt = await self._confirm_source_tx(tx_result=tx_result)
            tx_result.target_tx = TxResult(tx_hash=await self._wait_for_target_event(tx_result=tx_result))
            tx_result.target_tx.tx_receipt = await self._confirm_target_tx(tx_result=tx_result)
        except Exception as e:
            raise PartialBridgeResult(f"Bridge pipeline failed: {e}", tx_result=tx_result) from e

        return tx_result

    async def _prepare_socket_deposit(self, amount: int, context: BridgeContext) -> PreparedBridgeTx:

        token_data, _connector = self._resolve_socket_route(context=context)

        spender = token_data.Vault if token_data.isNewBridge else self.get_deposit_helper(context).address
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
            func, fees_func = self._prepare_new_style_deposit(token_data, amount, context)
        else:
            func, fees_func = self._prepare_old_style_deposit(token_data, amount, context)

        fees = await fees_func.call()
        prepared_tx = await self._prepare_tx(func=func, value=fees + 1, context=context)

        return prepared_tx

    async def _prepare_socket_withdrawal(self, amount: int, context: BridgeContext) -> PreparedBridgeTx:

        token_data, connector = self._resolve_socket_route(context=context)

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
        prepared_tx = await self._prepare_tx(func=func, value=0, context=context)

        return prepared_tx

    async def _prepare_layerzero_deposit(self, amount: int, context: BridgeContext) -> PreparedBridgeTx:

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

        func = context.source_token.functions.send(send_params, fees, refund_address)
        prepared_tx = await self._prepare_tx(func=func, value=native_fee, context=context)

        return prepared_tx

    async def _prepare_layerzero_withdrawal(self, amount: int, context: BridgeContext) -> PreparedBridgeTx:

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
        prepared_tx = await self._prepare_tx(func=func, value=0, context=context)

        return prepared_tx

    async def _send_bridge_tx(self, prepared_tx: PreparedBridgeTx) -> BridgeTxResult:

        context = self._get_context(prepared_tx)

        # record on target chain where we should start polling
        target_from_block = await context.target_w3.eth.block_number

        signed_tx = prepared_tx.tx_details.signed_tx
        tx_hash = await send_tx(w3=context.source_w3, signed_tx=signed_tx)
        source_tx = TxResult(tx_hash=tx_hash)

        tx_result = BridgeTxResult(
            currency=prepared_tx.currency,
            bridge=context.bridge_type,
            source_chain=context.source_chain,
            target_chain=context.target_chain,
            source_tx=source_tx,
            target_from_block=target_from_block,
            tx_details=prepared_tx.tx_details,
        )

        return tx_result

    async def _confirm_source_tx(self, tx_result: BridgeTxResult) -> TxReceipt:

        context = self._get_context(tx_result)
        msg = "⏳ Checking source chain [%s] tx receipt for %s"
        self.logger.info(msg, tx_result.source_chain.name, tx_result.source_tx.tx_hash)
        tx_receipt = await wait_for_tx_finality(
            w3=context.source_w3,
            tx_hash=tx_result.source_tx.tx_hash,
            logger=self.logger,
        )

        return tx_receipt

    async def _wait_for_target_event(self, tx_result: BridgeTxResult) -> HexBytes:

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

    async def _confirm_target_tx(self, tx_result: BridgeTxResult) -> TxReceipt:

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

    def _prepare_new_style_deposit(
        self, token_data: NonMintableTokenData, amount: int, context: BridgeContext
    ) -> tuple[ContractFunction, int]:

        vault_contract = _load_vault_contract(w3=self.w3s[context.source_chain], token_data=token_data)
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

    def _prepare_old_style_deposit(
        self, token_data: NonMintableTokenData, amount: int, context: BridgeContext
    ) -> tuple[ContractFunction, int]:

        vault_contract = _load_vault_contract(w3=self.w3s[context.source_chain], token_data=token_data)
        connector = token_data.connectors[ChainID.DERIVE][TARGET_SPEED]
        fees_func = _get_min_fees(bridge_contract=vault_contract, connector=connector, token_data=token_data)
        func = self.get_deposit_helper(context).functions.depositToLyra(
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
