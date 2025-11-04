"""Internal: Standard bridge implementation."""

import asyncio
import json
from decimal import Decimal
from logging import Logger
from typing import cast

from eth_account.signers.local import LocalAccount
from eth_utils.crypto import keccak
from returns.future import future_safe
from web3 import AsyncWeb3
from web3.contract.async_contract import AsyncContract, AsyncContractEvent

from derive_client.config import (
    L1_CHUG_SPLASH_PROXY,
    L1_CROSS_DOMAIN_MESSENGER_ABI_PATH,
    L1_STANDARD_BRIDGE_ABI_PATH,
    L2_CROSS_DOMAIN_MESSENGER_ABI_PATH,
    L2_CROSS_DOMAIN_MESSENGER_PROXY,
    L2_STANDARD_BRIDGE_ABI_PATH,
    L2_STANDARD_BRIDGE_PROXY,
    MSG_GAS_LIMIT,
    RESOLVED_DELEGATE_PROXY,
)
from derive_client.data_types import (
    BridgeTxDetails,
    BridgeTxResult,
    BridgeType,
    ChainID,
    ChecksumAddress,
    Currency,
    PreparedBridgeTx,
    TxHash,
    TxResult,
    TypedLogReceipt,
    TypedTxReceipt,
)
from derive_client.exceptions import BridgeEventParseError, PartialBridgeResult, StandardBridgeRelayFailed
from derive_client.utils.w3 import to_base_units

from .w3 import (
    build_standard_transaction,
    encode_abi,
    get_contract,
    get_w3_connections,
    make_filter_params,
    send_tx,
    sign_tx,
    wait_for_bridge_event,
    wait_for_tx_finality,
)


def _load_l1_contract(w3: AsyncWeb3) -> AsyncContract:
    address = L1_CHUG_SPLASH_PROXY
    abi = json.loads(L1_STANDARD_BRIDGE_ABI_PATH.read_text())
    return get_contract(w3=w3, address=address, abi=abi)


def _load_l2_contract(w3: AsyncWeb3) -> AsyncContract:
    address = L2_STANDARD_BRIDGE_PROXY
    abi = json.loads(L2_STANDARD_BRIDGE_ABI_PATH.read_text())
    return get_contract(w3=w3, address=address, abi=abi)


def _load_l2_contracts(w3s: dict[ChainID, AsyncWeb3]) -> dict[ChainID, AsyncContract]:
    return {chain_id: _load_l2_contract(w3) for chain_id, w3 in w3s.items() if chain_id is not ChainID.ETH}


def _load_l1_cross_domain_messenger_proxy(w3: AsyncWeb3) -> AsyncContract:
    address = RESOLVED_DELEGATE_PROXY
    abi = json.loads(L1_CROSS_DOMAIN_MESSENGER_ABI_PATH.read_text())
    return get_contract(w3=w3, address=address, abi=abi)


def _load_l2_cross_domain_messenger_proxy(w3: AsyncWeb3) -> AsyncContract:
    address = L2_CROSS_DOMAIN_MESSENGER_PROXY
    abi = json.loads(L2_CROSS_DOMAIN_MESSENGER_ABI_PATH.read_text())
    return get_contract(w3=w3, address=address, abi=abi)


class StandardBridge:
    """Bridge tokens using Optimism's native standard bridge."""

    def __init__(self, account: LocalAccount, logger: Logger):
        """
        Initialize Standard bridge.

        Args:
            account: Account object containing the private key of the owner of the smart contract funding account
            logger: Logger instance for logging
        """

        self.account = account
        self.logger = logger
        self.w3s = get_w3_connections(logger=logger)
        self.l1_contract = _load_l1_contract(self.w3s[ChainID.ETH])
        self.l2_contracts = _load_l2_contracts(self.w3s)
        self.l1_messenger_proxy = _load_l1_cross_domain_messenger_proxy(self.w3s[ChainID.ETH])
        self.l2_messenger_proxy = _load_l2_cross_domain_messenger_proxy(self.w3s[ChainID.DERIVE])

    @future_safe
    async def prepare_eth_tx(
        self,
        amount: Decimal,
        to: ChecksumAddress,
        source_chain: ChainID,
        target_chain: ChainID,
    ) -> PreparedBridgeTx:
        currency = Currency.ETH

        if source_chain is not ChainID.ETH or target_chain is not ChainID.DERIVE or to != self.account.address:
            raise NotImplementedError("Only ETH transfers from Ethereum to Derive EOA are currently supported.")

        value: int = to_base_units(decimal_amount=amount, currency=currency)
        prepared_tx = await self._prepare_eth_tx(
            value=value,
            to=to,
            source_chain=source_chain,
            target_chain=target_chain,
        )

        return prepared_tx

    @property
    def private_key(self) -> str:
        """Private key of the owner (EOA)."""
        return self.account.key.to_0x_hex()  # type: ignore[attr-defined]

    @future_safe
    async def submit_bridge_tx(self, prepared_tx: PreparedBridgeTx) -> BridgeTxResult:
        tx_result = await self._send_bridge_tx(prepared_tx=prepared_tx)

        return tx_result

    @future_safe
    async def poll_bridge_progress(self, tx_result: BridgeTxResult) -> BridgeTxResult:
        try:
            tx_result.source_tx.tx_receipt = await self._confirm_source_tx(tx_result=tx_result)
            tx_result.target_tx = TxResult(tx_hash=await self._wait_for_target_event(tx_result=tx_result))
            tx_result.target_tx.tx_receipt = await self._confirm_target_tx(tx_result=tx_result)
        except Exception as e:
            raise PartialBridgeResult(f"Bridge pipeline failed: {e}", tx_result=tx_result) from e

        return tx_result

    async def _prepare_eth_tx(
        self,
        value: int,
        to: ChecksumAddress,
        source_chain: ChainID,
        target_chain: ChainID,
    ) -> PreparedBridgeTx:
        w3 = self.w3s[source_chain]

        proxy_contract = self.l1_contract
        func = proxy_contract.functions.bridgeETHTo(
            _to=to,
            _minGasLimit=MSG_GAS_LIMIT,
            _extraData=b"",
        )

        tx = await build_standard_transaction(func=func, account=self.account, w3=w3, value=value, logger=self.logger)

        tx_gas_cost = tx["gas"] * tx["maxFeePerGas"]
        if value < tx_gas_cost:
            msg = f"⚠️ Bridge tx value {value} is smaller than max gas cost {tx_gas_cost} (~{tx_gas_cost / value:.2f}x value)"  # noqa: E501
            self.logger.warning(msg)

        signed_tx = sign_tx(w3=w3, tx=tx, private_key=self.private_key)

        tx_details = BridgeTxDetails(
            contract=ChecksumAddress(func.address),
            fn_name=func.fn_name,
            fn_kwargs=func.kwargs,
            tx=tx,
            signed_tx=signed_tx,
        )

        prepared_tx = PreparedBridgeTx(
            amount=0,
            value=value,
            fee_value=0,
            fee_in_token=0,
            currency=Currency.ETH,
            source_chain=source_chain,
            target_chain=target_chain,
            bridge_type=BridgeType.STANDARD,
            tx_details=tx_details,
        )

        return prepared_tx

    async def _send_bridge_tx(self, prepared_tx: PreparedBridgeTx) -> BridgeTxResult:
        source_w3 = self.w3s[prepared_tx.source_chain]
        target_w3 = self.w3s[prepared_tx.target_chain]

        # record on target chain where we should start polling
        target_from_block = await target_w3.eth.block_number

        signed_tx = prepared_tx.tx_details.signed_tx
        tx_hash = await send_tx(w3=source_w3, signed_tx=signed_tx)
        source_tx = TxResult(tx_hash=tx_hash)

        tx_result = BridgeTxResult(
            prepared_tx=prepared_tx,
            source_tx=source_tx,
            target_from_block=target_from_block,
        )

        return tx_result

    async def _confirm_source_tx(self, tx_result: BridgeTxResult) -> TypedTxReceipt:
        msg = "⏳ Checking source chain [%s] tx receipt for %s"
        self.logger.info(msg, tx_result.source_chain.name, tx_result.source_tx.tx_hash)

        w3 = self.w3s[tx_result.source_chain]
        tx_receipt = await wait_for_tx_finality(
            w3=w3,
            tx_hash=tx_result.source_tx.tx_hash,
            logger=self.logger,
        )

        return tx_receipt

    async def _wait_for_target_event(self, tx_result: BridgeTxResult) -> TxHash:
        event_log = await self._fetch_standard_event_log(tx_result)
        tx_hash = event_log.transactionHash
        self.logger.info(f"Target event tx_hash found: {tx_hash.to_0x_hex()}")

        return TxHash(tx_hash)

    async def _confirm_target_tx(self, tx_result: BridgeTxResult) -> TypedTxReceipt:
        assert tx_result.target_tx is not None, "Expected tx_result.target_tx to exist"

        msg = "⏳ Checking target chain [%s] tx receipt for %s"
        self.logger.info(msg, tx_result.target_chain.name, tx_result.target_tx.tx_hash)

        w3 = self.w3s[tx_result.target_chain]
        tx_receipt = await wait_for_tx_finality(
            w3=w3,
            tx_hash=tx_result.target_tx.tx_hash,
            logger=self.logger,
        )

        return tx_receipt

    async def _fetch_standard_event_log(self, tx_result: BridgeTxResult) -> TypedLogReceipt:
        assert tx_result.source_tx.tx_receipt, "Expected source_tx.receipt to exist"

        source_event = self.l1_messenger_proxy.events.SentMessage()

        target_w3 = self.w3s[tx_result.target_chain]
        try:
            source_event_log = source_event.process_log(tx_result.source_tx.tx_receipt.logs[3].to_w3())
            nonce = source_event_log["args"]["messageNonce"]
        except Exception as e:
            raise BridgeEventParseError(f"Could not decode StandardBridge messageNonce: {e}") from e

        self.logger.info(f"🔖 Source [{tx_result.source_chain.name}] messageNonce: {nonce}")

        args = source_event_log["args"]
        gas_limit = args["gasLimit"]
        sender = AsyncWeb3.to_checksum_address(args["sender"])
        target = AsyncWeb3.to_checksum_address(args["target"])
        message = args["message"]
        value = tx_result.prepared_tx.amount

        func = self.l1_messenger_proxy.functions.relayMessage(
            _nonce=nonce,
            _sender=sender,
            _target=target,
            _value=value,
            _minGasLimit=gas_limit,
            _message=message,
        )

        msg_hash = keccak(encode_abi(func))
        tx_result.event_id = msg_hash.hex()
        self.logger.info(f"🗝️ Computed msgHash: {tx_result.event_id}")

        target_event = cast(AsyncContractEvent, self.l2_messenger_proxy.events.RelayedMessage())
        failed_target_event = cast(AsyncContractEvent, self.l2_messenger_proxy.events.FailedRelayedMessage())

        filter_params = make_filter_params(
            event=target_event,
            from_block=tx_result.target_from_block,
            argument_filters={"msgHash": msg_hash},
        )
        failed_filter_params = make_filter_params(
            event=failed_target_event,
            from_block=tx_result.target_from_block,
            argument_filters={"msgHash": msg_hash},
        )

        self.logger.info(f"🔍 Listening for msgHash on [{tx_result.target_chain.name}] at {target_event.address}")

        relayed_task = asyncio.create_task(wait_for_bridge_event(target_w3, filter_params, logger=self.logger))
        failed_task = asyncio.create_task(wait_for_bridge_event(target_w3, failed_filter_params, logger=self.logger))
        done, pending = await asyncio.wait([relayed_task, failed_task], return_when=asyncio.FIRST_COMPLETED)

        for task in pending:
            task.cancel()
        if failed_task in done:
            # reraises Exceptions (i.e. BridgeEventTimeout), and in this scenario not raise StandardBridgeRelayFailed
            event_log = done.pop().result()
            raise StandardBridgeRelayFailed(
                "The relay was attempted but reverted on L2. "
                "Likely causes are out-of-gas, non-standard token implementation, or target contract reversion.\n"
                "Action:\n"
                "- Inspect the L2 tx receipt logs for the revert reason.\n"
                "- If out-of-gas, resubmit with higher _minGasLimit.\n"
                "- If token mismatch, check that the L2 token contract matches the expected bridgeable ERC20.\n"
                "- If paused/reverted, retry after resolving the underlying contract state.",
                event_log=event_log,
            )

        event_log = done.pop().result()

        return event_log
