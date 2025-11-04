import asyncio
import heapq
import json
import statistics
import time
from logging import Logger
from typing import Any, AsyncGenerator, Callable, Coroutine, Literal, cast

from aiohttp import ClientResponseError
from eth_abi.abi import encode
from eth_account import Account
from eth_account.signers.local import LocalAccount
from eth_typing import HexStr
from requests import RequestException
from web3 import AsyncHTTPProvider, AsyncWeb3
from web3.contract.async_contract import AsyncContract, AsyncContractEvent, AsyncContractFunction
from web3.exceptions import TransactionNotFound
from web3.types import RPCEndpoint, RPCResponse

from derive_client.config import (
    ABI_DATA_DIR,
    ASSUMED_BRIDGE_GAS_LIMIT,
    DEFAULT_RPC_ENDPOINTS,
    GAS_FEE_BUFFER,
    MIN_PRIORITY_FEE,
)
from derive_client.data_types import (
    ChainID,
    ChecksumAddress,
    FeeEstimate,
    FeeEstimates,
    FeeHistory,
    GasPriority,
    RPCEndpoints,
    TxHash,
    TxStatus,
    TypedFilterParams,
    TypedLogReceipt,
    TypedSignedTransaction,
    TypedTransaction,
    TypedTxReceipt,
    Wei,
)
from derive_client.exceptions import (
    BridgeEventTimeout,
    FinalityTimeout,
    InsufficientNativeBalance,
    InsufficientTokenBalance,
    NoAvailableRPC,
    TransactionDropped,
    TxPendingTimeout,
)
from derive_client.utils.logger import get_logger
from derive_client.utils.retry import exp_backoff_retry
from derive_client.utils.w3 import EndpointState, load_rpc_endpoints

EVENT_LOG_RETRIES = 10


def make_rotating_provider_middleware(
    endpoints: list[AsyncHTTPProvider],
    *,
    initial_backoff: float = 1.0,
    max_backoff: float = 600.0,
    logger: Logger,
) -> Callable[[Callable[[RPCEndpoint, Any], RPCResponse], AsyncWeb3], Any]:
    """
    v6.11-style middleware:
     - round-robin via a min-heap of `next_available` times
     - on 429: exponential back-off for that endpoint, capped
    """

    heap: list[EndpointState] = [EndpointState(p) for p in endpoints]
    heapq.heapify(heap)
    lock = asyncio.Lock()

    async def middleware_factory(
        make_request: Callable[[RPCEndpoint, Any], RPCResponse],
        w3: AsyncWeb3,
    ) -> Callable[[RPCEndpoint, Any], Coroutine[Any, Any, RPCResponse]]:
        async def rotating_backoff(method: RPCEndpoint, params: Any) -> RPCResponse:
            now = time.monotonic()

            while True:
                # 1) grab the earlies-available endpoint
                async with lock:
                    state = heapq.heappop(heap)

                # 2) if it's not yet ready, push back and error out
                if state.next_available > now:
                    async with lock:
                        heapq.heappush(heap, state)
                    msg = "All RPC endpoints are cooling down. Try again in %.2f seconds."
                    logger.warning(msg, state.next_available - now)
                    raise NoAvailableRPC(msg)

                try:
                    # 3) attempt the request
                    provider = cast(AsyncHTTPProvider, state.provider)
                    resp = await provider.make_request(method, params)

                    # Json‑RPC error branch
                    if isinstance(resp, dict) and (error := resp.get("error")):
                        state.backoff = state.backoff * 2 if state.backoff else initial_backoff
                        state.backoff = min(state.backoff, max_backoff)
                        state.next_available = now + state.backoff
                        async with lock:
                            heapq.heappush(heap, state)

                        if isinstance(error, str):
                            msg = error
                        else:
                            err_msg = error.get("message", "")
                            err_code = error.get("code", "")
                            msg = "RPC error on %s: %s (code: %s)→ backing off %.2fs"

                        logger.info(msg, state.provider.endpoint_uri, err_msg, err_code, state.backoff)
                        continue

                    # 4) on success, reset its backoff and re-schedule immediately
                    state.backoff = 0.0
                    state.next_available = now
                    async with lock:
                        heapq.heappush(heap, state)
                    return resp

                except (ClientResponseError, RequestException) as e:
                    logger.debug("Endpoint %s failed: %s", state.provider.endpoint_uri, e)

                    if isinstance(e, RequestException) and e.response:
                        hdr = e.response.headers.get("Retry-After")
                    else:
                        hdr = None

                    # We retry on all exceptions
                    if hdr is not None:
                        backoff = float(hdr)
                    else:
                        backoff = state.backoff * 2 if state.backoff > 0 else initial_backoff

                    # cap backoff and schedule
                    state.backoff = min(backoff, max_backoff)
                    state.next_available = now + state.backoff
                    async with lock:
                        heapq.heappush(heap, state)
                    msg = "Backing off %s for %.2fs"
                    logger.info(msg, state.provider.endpoint_uri, backoff)
                    continue

                except Exception as e:
                    msg = "Unexpected error calling %s %s on %s; backing off %.2fs and continuing"
                    logger.exception(msg, method, params, state.provider.endpoint_uri, max_backoff, exc_info=e)
                    state.backoff = max_backoff
                    state.next_available = now + state.backoff
                    async with lock:
                        heapq.heappush(heap, state)
                    continue

        return rotating_backoff

    return middleware_factory


def get_w3_connection(
    chain_id: ChainID,
    *,
    rpc_endpoints: RPCEndpoints | None = None,
    logger: Logger | None = None,
) -> AsyncWeb3:
    rpc_endpoints = rpc_endpoints or load_rpc_endpoints(DEFAULT_RPC_ENDPOINTS)
    providers = [AsyncHTTPProvider(str(url)) for url in rpc_endpoints[chain_id]]

    logger = logger or get_logger()

    # NOTE: Initial provider is a no-op once middleware is in place
    # NOTE: If you don't set a dummy provider, bad things will happen!
    provider = AsyncHTTPProvider()
    w3 = AsyncWeb3(provider)

    rotator = make_rotating_provider_middleware(
        providers,
        initial_backoff=1.0,
        max_backoff=600.0,
        logger=logger,
    )
    w3.middleware_onion.add(rotator, name="rotating_provider")

    return w3


def get_w3_connections(logger) -> dict[ChainID, AsyncWeb3]:
    return {chain_id: get_w3_connection(chain_id, logger=logger) for chain_id in ChainID}


def get_contract(w3: AsyncWeb3, address: ChecksumAddress, abi: list) -> AsyncContract:
    return w3.eth.contract(address=AsyncWeb3.to_checksum_address(address), abi=abi)


def get_erc20_contract(w3: AsyncWeb3, token_address: ChecksumAddress) -> AsyncContract:
    erc20_abi_path = ABI_DATA_DIR / "erc20.json"
    abi = json.loads(erc20_abi_path.read_text())
    return get_contract(w3=w3, address=token_address, abi=abi)


async def ensure_token_balance(
    token_contract: AsyncContract,
    owner: ChecksumAddress,
    amount: int,
    fee_in_token: int = 0,
):
    balance = await token_contract.functions.balanceOf(owner).call()
    required = amount + fee_in_token
    if amount > balance:
        raise InsufficientTokenBalance(
            f"Not enough tokens for withdraw: required={required} (amount={amount} + fee={fee_in_token}), "
            f"balance={balance} ({(balance / required * 100):.2f}% of required)"
        )


async def ensure_token_allowance(
    w3: AsyncWeb3,
    token_contract: AsyncContract,
    owner: ChecksumAddress,
    spender: ChecksumAddress,
    amount: int,
    private_key: str,
    logger: Logger,
):
    allowance = await token_contract.functions.allowance(owner, spender).call()
    if amount > allowance:
        logger.info(f"Increasing allowance from {allowance} to {amount}")
        await _increase_token_allowance(
            w3=w3,
            from_account=Account.from_key(private_key),
            erc20_contract=token_contract,
            spender=spender,
            amount=amount,
            private_key=private_key,
            logger=logger,
        )


async def _increase_token_allowance(
    w3: AsyncWeb3,
    from_account: LocalAccount,
    erc20_contract: AsyncContract,
    spender: ChecksumAddress,
    amount: int,
    private_key: str,
    logger: Logger,
) -> None:
    func = erc20_contract.functions.approve(spender, amount)
    tx = await build_standard_transaction(func=func, account=from_account, w3=w3, logger=logger)
    signed_tx = sign_tx(w3=w3, tx=tx, private_key=private_key)
    tx_hash = await send_tx(w3=w3, signed_tx=signed_tx)
    tx_receipt = await wait_for_tx_finality(w3=w3, tx_hash=tx_hash, logger=logger)
    if tx_receipt.status != TxStatus.SUCCESS:
        raise RuntimeError("approve() failed")


async def estimate_fees(w3, blocks: int = 20) -> FeeEstimates:
    """Estimate EIP-1559 maxFeePerGas and maxPriorityFeePerGas from recent blocks for GasPriority percentiles."""

    percentiles = tuple(map(int, GasPriority))
    fee_history = FeeHistory(**await w3.eth.fee_history(blocks, "pending", percentiles))
    latest_base_fee = fee_history.base_fee_per_gas[-1]

    percentile_rewards: dict[int, list[Wei]] = {p: [] for p in percentiles}
    for block_rewards in fee_history.reward:
        for percentile, reward in zip(percentiles, block_rewards):
            percentile_rewards[percentile].append(reward)

    estimates = {}
    for percentile in percentiles:
        rewards = percentile_rewards[percentile]
        non_zero_rewards = list(filter(lambda x: x, rewards))
        estimated_priority_fee = int(statistics.median(non_zero_rewards)) if non_zero_rewards else MIN_PRIORITY_FEE

        buffered_base_fee = int(latest_base_fee * GAS_FEE_BUFFER)
        estimated_max_fee = buffered_base_fee + estimated_priority_fee
        estimates[GasPriority(percentile)] = FeeEstimate(estimated_max_fee, estimated_priority_fee)

    return FeeEstimates(estimates)


async def preflight_native_balance_check(
    w3: AsyncWeb3,
    fee_estimate: FeeEstimate,
    account: LocalAccount,
    value: int,
) -> None:
    balance = await w3.eth.get_balance(account.address)
    max_fee_per_gas = fee_estimate.max_fee_per_gas

    max_gas_cost = ASSUMED_BRIDGE_GAS_LIMIT * max_fee_per_gas
    total_cost = max_gas_cost + value

    if not balance >= total_cost:
        chain_id = ChainID(await w3.eth.chain_id)
        ratio = balance / total_cost * 100
        raise InsufficientNativeBalance(
            f"Insufficient funds on {chain_id.name} ({chain_id}): "
            f"balance={balance}, required={total_cost} {ratio:.2f}% available "
            f"(includes value={value} and assumed gas limit={ASSUMED_BRIDGE_GAS_LIMIT} at {max_fee_per_gas} wei/gas)",
            balance=balance,
            chain_id=chain_id,
            assumed_gas_limit=ASSUMED_BRIDGE_GAS_LIMIT,
            fee_estimate=fee_estimate,
        )


@exp_backoff_retry
async def build_standard_transaction(
    func,
    account: LocalAccount,
    w3: AsyncWeb3,
    logger: Logger,
    value: int = 0,
    gas_blocks: int = 30,
    gas_priority: GasPriority = GasPriority.MEDIUM,
) -> dict:
    """Standardized transaction building with EIP-1559 and gas estimation"""

    nonce = await w3.eth.get_transaction_count(account.address)
    fee_estimations = await estimate_fees(w3, blocks=gas_blocks)

    for percentile, fee_estimation in fee_estimations.items():
        logger.debug(f"{fee_estimation} [{percentile}% Percentile]")

    fee_estimate = fee_estimations[gas_priority]
    logger.info(f"Fee estimate: {fee_estimate} [Gas priority {gas_priority.name} | {gas_priority.value}% Percentile]")

    await preflight_native_balance_check(w3=w3, account=account, fee_estimate=fee_estimate, value=value)

    tx = await func.build_transaction(
        {
            "from": account.address,
            "nonce": nonce,
            "maxFeePerGas": fee_estimate.max_fee_per_gas,
            "maxPriorityFeePerGas": fee_estimate.max_priority_fee_per_gas,
            "chainId": await w3.eth.chain_id,
            "value": value,
        }
    )

    # Warn if actual gas exceeds ASSUMED_BRIDGE_GAS_LIMIT; may indicate the limit is too low
    # and could cause unhandled RPC errors instead of raising InsufficientNativeBalance
    if tx["gas"] > ASSUMED_BRIDGE_GAS_LIMIT:
        logger.warning(f"Bridge tx gas {tx['gas']} exceeds assumed limit {ASSUMED_BRIDGE_GAS_LIMIT}")

    # simulate the tx
    await w3.eth.call(tx)
    return tx


async def wait_for_tx_finality(
    w3: AsyncWeb3,
    tx_hash: str,
    logger: Logger,
    finality_blocks: int = 10,
    timeout: float = 300.0,
    poll_interval: float = 1.0,
) -> TypedTxReceipt:
    """
    Wait until tx is mined and has `finality_blocks` confirmations.
    On timeout this raises one of:
      - FinalityTimeout: receipt exists but not enough confirmations
      - TxPendingTimeout: no receipt, but tx present and pending in mempool
      - TransactionDropped: no receipt and tx not known to node (likely dropped)

    Notes on reorgs and provider inconsistency:
      - A chain reorg can cause a previously-seen receipt to disappear (tx becomes "unmined").
        In that case the tx will often reappear as pending in the mempool (TxPendingTimeout),
        but it can also be dropped entirely (TransactionDropped) or re-mined later.
      - With rotating RPC providers you may observe receipts, tx entries, and block numbers
        from different nodes that disagree. This function classifies a timeout based on a
        single get_transaction probe and is intentionally conservative; callers should
        interpret exceptions as:
          * FinalityTimeout: node reports mined or we observed a receipt but not enough confirms:
            wait longer; invoke this function again.
          * TxPendingTimeout: node knows the tx and reports it pending:
            either wait/poll longer or resubmit (reuse the nonce to prevent duplication).
          * TransactionDropped: node has no record (likely dropped or node out-of-sync):
            either wait/poll longer or resubmit (reuse the nonce to prevent duplication).
    """

    block_number = -1
    tx_hash = cast(HexStr, tx_hash)
    start_time = time.monotonic()

    while True:
        try:
            raw_receipt = await w3.eth.get_transaction_receipt(tx_hash)
            receipt = TypedTxReceipt.model_validate(raw_receipt)
        # receipt can disappear temporarily during reorgs, or if RPC provider is not synced
        except TransactionNotFound as exc:
            receipt = None
            logger.debug("No tx receipt for tx_hash=%s", tx_hash, extra={"exc": exc})

        # blockNumber can change as tx gets reorged into different blocks
        try:
            if receipt is not None:
                block_number = await w3.eth.block_number
                if block_number >= receipt.blockNumber + finality_blocks:
                    return receipt
        except Exception as exc:
            msg = "Failed to fetch block_number trying to assess finality of tx_hash=%s"
            logger.debug(msg, tx_hash, extra={"exc": exc})

        if time.monotonic() - start_time > timeout:
            # 1) We have a receipt but did not reach required confirmations
            if receipt is not None:
                raise FinalityTimeout(
                    f"Timed out waiting for finality: tx={tx_hash!r}, timeout_s={timeout}r ",
                    f"required confirmations={finality_blocks}."
                    f"\nreceipt_block={receipt.blockNumber!r}, current_block={block_number!r}.",
                    "\nAction: wait longer / poll for finality again.",
                )
            # 2) No receipt: check if tx is known to node (mempool) or dropped
            try:
                tx = TypedTransaction.model_validate(await w3.eth.get_transaction(tx_hash))
            except Exception as exc:
                tx = None
                logger.debug("get_transaction probe failed for tx_hash=%s", tx_hash, extra={"exc": exc})

            # still pending in mempool
            if tx is not None and tx.blockNumber is None:
                raise TxPendingTimeout(
                    f"No receipt within timeout: tx={tx_hash!r}, timeout_s={timeout}.",
                    "\nNode reports transaction present and pending in mempool.",
                    "\nAction: either wait/poll longer or resubmit (reuse the nonce to prevent duplication).",
                )
            # node reports tx mined, but no receipt
            elif tx is not None:
                raise FinalityTimeout(
                    f"Timed out waiting for finality: tx={tx_hash!r}, timeout_s={timeout}, "
                    f"required confirmations={finality_blocks}."
                    f"\nNode reports tx mined at block {tx.blockNumber!r} but receipt not observed by this verifier."
                    "\nAction: wait longer / poll for finality again.",
                )
            # tx dropped or node no longer knows about it
            else:
                raise TransactionDropped(
                    f"Transaction not found after timeout: tx={tx_hash!r}, timeout_s={timeout}.",
                    "\nNode does not report a receipt or pending transaction (likely dropped).",
                    "\nAction: either wait/poll longer or resubmit (reuse the nonce to prevent duplication).",
                )

        logger.debug("Waiting for finality: tx=%s sleeping=%.1fs", tx_hash, poll_interval)
        await asyncio.sleep(poll_interval)


def sign_tx(w3: AsyncWeb3, tx: dict, private_key: str) -> TypedSignedTransaction:
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    return TypedSignedTransaction(**signed_tx._asdict())


async def send_tx(w3: AsyncWeb3, signed_tx: TypedSignedTransaction) -> TxHash:
    tx_hash = await w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return TxHash(tx_hash)


async def iter_events(
    w3: AsyncWeb3,
    filter_params: TypedFilterParams,
    *,
    condition: Callable[[TypedLogReceipt], bool] = lambda _: True,
    max_block_range: int = 10_000,
    poll_interval: float = 5.0,
    timeout: float | None = None,
    logger: Logger,
) -> AsyncGenerator[TypedLogReceipt, None]:
    """Stream matching logs over a fixed or live block window. Optionally raises TimeoutError."""

    if (cursor := filter_params.fromBlock) == "latest":
        cursor = await w3.eth.block_number

    start_block = cursor
    fixed_ceiling = None if filter_params.toBlock == "latest" else filter_params.toBlock

    rpc_filter_params = filter_params.to_rpc_params()
    deadline = None if timeout is None else time.monotonic() + timeout

    while True:
        if deadline and time.monotonic() > deadline:
            msg = f"Timed out waiting for events after scanning blocks {start_block}-{cursor}"
            logger.warning(msg)
            raise TimeoutError(f"{msg}: filter_params: {filter_params}")

        upper = fixed_ceiling or await w3.eth.block_number
        if cursor <= upper:
            end = min(upper, cursor + max_block_range - 1)

            # Convert to hex strings for RPC call - some providers require this
            rpc_filter_params["fromBlock"] = cast(HexStr, hex(cursor))
            rpc_filter_params["toBlock"] = cast(HexStr, hex(end))

            # For example, when rotating providers are out of sync
            retry_get_logs = exp_backoff_retry(w3.eth.get_logs, attempts=EVENT_LOG_RETRIES)
            logs_raw = await retry_get_logs(filter_params=rpc_filter_params)
            logger.debug(f"Scanned {cursor} - {end}: {len(logs_raw)} logs")

            for log in filter(condition, map(TypedLogReceipt.model_validate, logs_raw)):
                yield log

            cursor = end + 1  # bounds are inclusive

        if fixed_ceiling and cursor > fixed_ceiling:
            raise StopIteration

        await asyncio.sleep(poll_interval)


async def wait_for_bridge_event(
    w3: AsyncWeb3,
    filter_params: TypedFilterParams,
    *,
    condition: Callable[[TypedLogReceipt], bool] = lambda _: True,
    max_block_range: int = 10_000,
    poll_interval: float = 5.0,
    timeout: float = 300.0,
    logger: Logger,
) -> TypedLogReceipt:
    """Wait for the first matching bridge-related log on the target chain or raise BridgeEventTimeout."""

    try:
        return await anext(iter_events(**locals()))
    except TimeoutError as e:
        raise BridgeEventTimeout("Timed out waiting for target chain bridge event") from e


def make_filter_params(
    event: AsyncContractEvent,
    from_block: int | Literal["latest"],
    to_block: int | Literal["latest"] = "latest",
    argument_filters: dict[str, Any] | None = None,
) -> TypedFilterParams:
    """
    Function to create an eth_getLogs compatible filter_params for this event without using .create_filter.
    event.create_filter uses eth_newFilter (a "push"), which not all RPC endpoints support.
    """

    argument_filters = argument_filters or {}

    filter_params_raw = event._get_event_filter_params(
        fromBlock=from_block,
        toBlock=to_block,
        argument_filters=argument_filters,
        abi=event.abi,
    )

    address_raw = filter_params_raw["address"]
    address: ChecksumAddress | list[ChecksumAddress]

    address = filter_params_raw["address"]
    if isinstance(address_raw, str):
        address = ChecksumAddress(address_raw)
    elif isinstance(address_raw, (list, tuple)) and len(address_raw) == 1:
        address = ChecksumAddress(address_raw[0])
    else:
        raise ValueError(f"Unexpected address filter: {address!r}")

    return TypedFilterParams(
        address=address,
        topics=tuple(filter_params_raw["topics"]),
        fromBlock=from_block,
        toBlock=to_block,
    )


def encode_abi(func: AsyncContractFunction) -> bytes:
    """Get the ABI-encoded data (including 4-byte selector)."""

    types = [str(arg.get("internalType")) for arg in func.abi.get("inputs", [])]
    selector = bytes.fromhex(func.selector.removeprefix("0x"))

    return selector + encode(types, func.arguments)
