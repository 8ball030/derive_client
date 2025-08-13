import functools
import heapq
import json
import threading
import time
from logging import Logger
from pathlib import Path
from typing import Any, Callable, Generator, Literal

import yaml
from eth_account import Account
from eth_account.datastructures import SignedTransaction
from requests import RequestException
from web3 import Web3
from web3.contract import Contract
from web3.contract.contract import ContractEvent
from web3.datastructures import AttributeDict
from web3.providers.rpc import HTTPProvider

from derive_client.constants import ABI_DATA_DIR, DEFAULT_RPC_ENDPOINTS, GAS_FEE_BUFFER, GAS_LIMIT_BUFFER
from derive_client.data_types import ChainID, RPCEndpoints
from derive_client.exceptions import (
    FinalityTimeout,
    InsufficientNativeBalance,
    NoAvailableRPC,
    TransactionDropped,
    TxPendingTimeout,
)
from derive_client.utils.logger import get_logger
from derive_client.utils.retry import exp_backoff_retry

EVENT_LOG_RETRIES = 10


class EndpointState:
    __slots__ = ("provider", "backoff", "next_available")

    def __init__(self, provider: HTTPProvider):
        self.provider = provider
        self.backoff = 0.0
        self.next_available = 0.0

    def __lt__(self, other: "EndpointState") -> bool:
        return self.next_available < other.next_available

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.provider.endpoint_uri})"


def make_rotating_provider_middleware(
    endpoints: list[HTTPProvider],
    *,
    initial_backoff: float = 1.0,
    max_backoff: float = 600.0,
    logger: Logger,
) -> Callable[[Callable[[str, Any], Any], Web3], Callable[[str, Any], Any]]:
    """
    v6.11-style middleware:
     - round-robin via a min-heap of `next_available` times
     - on 429: exponential back-off for that endpoint, capped
    """

    heap: list[EndpointState] = [EndpointState(p) for p in endpoints]
    heapq.heapify(heap)
    lock = threading.Lock()

    def middleware_factory(make_request: Callable[[str, Any], Any], w3: Web3) -> Callable[[str, Any], Any]:
        def rotating_backoff(method: str, params: Any) -> Any:
            now = time.monotonic()

            while True:
                # 1) grab the earlies-available endpoint
                with lock:
                    state = heapq.heappop(heap)

                # 2) if it's not yet ready, push back and error out
                if state.next_available > now:
                    with lock:
                        heapq.heappush(heap, state)
                    msg = "All RPC endpoints are cooling down. Try again in %.2f seconds."
                    logger.warning(msg, state.next_available - now)
                    raise NoAvailableRPC(msg)

                try:
                    # 3) attempt the request
                    resp = state.provider.make_request(method, params)

                    # Json‑RPC error branch
                    if isinstance(resp, dict) and (error := resp.get("error")):
                        state.backoff = state.backoff * 2 if state.backoff else initial_backoff
                        state.backoff = min(state.backoff, max_backoff)
                        state.next_available = now + state.backoff
                        with lock:
                            heapq.heappush(heap, state)
                        err_msg = error.get("message", "")
                        msg = "RPC error on %s: %s → backing off %.2fs"
                        logger.info(msg, state.provider.endpoint_uri, err_msg, state.backoff, extra=resp)
                        continue

                    # 4) on success, reset its backoff and re-schedule immediately
                    state.backoff = 0.0
                    state.next_available = now
                    with lock:
                        heapq.heappush(heap, state)
                    return resp

                except RequestException as e:
                    logger.debug("Endpoint %s failed: %s", state.provider.endpoint_uri, e)

                    # We retry on all exceptions
                    hdr = (e.response and e.response.headers or {}).get("Retry-After")
                    try:
                        backoff = float(hdr)
                    except (ValueError, TypeError):
                        backoff = state.backoff * 2 if state.backoff > 0 else initial_backoff

                    # cap backoff and schedule
                    state.backoff = min(backoff, max_backoff)
                    state.next_available = now + state.backoff
                    with lock:
                        heapq.heappush(heap, state)
                    msg = "Backing off %s for %.2fs"
                    logger.info(msg, state.provider.endpoint_uri, backoff)
                    continue
                except Exception as e:
                    msg = "Unexpected error calling %s %s on %s; backing off %.2fs and continuing"
                    logger.exception(msg, method, params, state.provider.endpoint_uri, max_backoff, exc_info=e)
                    state.backoff = max_backoff
                    state.next_available = now + state.backoff
                    with lock:
                        heapq.heappush(heap, state)
                    continue

        return rotating_backoff

    return middleware_factory


@functools.lru_cache
def load_rpc_endpoints(path: Path) -> RPCEndpoints:
    return RPCEndpoints(**yaml.safe_load(path.read_text()))


def get_w3_connection(
    chain_id: ChainID,
    *,
    rpc_endpoints: RPCEndpoints | None = None,
    logger: Logger | None = None,
) -> Web3:
    rpc_endpoints = rpc_endpoints or load_rpc_endpoints(DEFAULT_RPC_ENDPOINTS)
    providers = [HTTPProvider(url) for url in rpc_endpoints[chain_id]]

    logger = logger or get_logger()

    # NOTE: Initial provider is a no-op once middleware is in place
    w3 = Web3()
    rotator = make_rotating_provider_middleware(
        providers,
        initial_backoff=1.0,
        max_backoff=600.0,
        logger=logger,
    )
    w3.middleware_onion.add(rotator)
    return w3


def get_contract(w3: Web3, address: str, abi: list) -> Contract:
    return w3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)


def get_erc20_contract(w3: Web3, token_address: str) -> Contract:
    erc20_abi_path = ABI_DATA_DIR / "erc20.json"
    abi = json.loads(erc20_abi_path.read_text())
    return get_contract(w3=w3, address=token_address, abi=abi)


def simulate_tx(w3: Web3, tx: dict, account: Account) -> dict:
    balance = w3.eth.get_balance(account.address)
    max_fee_per_gas = tx["maxFeePerGas"]
    gas_limit = tx["gas"]
    value = tx.get("value", 0)

    max_gas_cost = gas_limit * max_fee_per_gas
    total_cost = max_gas_cost + value
    if not balance >= total_cost:
        ratio = balance / total_cost * 100
        raise InsufficientNativeBalance(f"available: {balance} < required: {total_cost} ({ratio:.2f}%)")

    w3.eth.call(tx)
    return tx


@exp_backoff_retry
def build_standard_transaction(
    func,
    account: Account,
    w3: Web3,
    value: int = 0,
    gas_blocks: int = 100,
    gas_percentile: int = 99,
) -> dict:
    """Standardized transaction building with EIP-1559 and gas estimation"""

    nonce = w3.eth.get_transaction_count(account.address)
    fee_estimations = estimate_fees(w3, blocks=gas_blocks, percentiles=[gas_percentile])
    max_fee = fee_estimations[0]["maxFeePerGas"]
    priority_fee = fee_estimations[0]["maxPriorityFeePerGas"]

    tx = func.build_transaction(
        {
            "from": account.address,
            "nonce": nonce,
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": priority_fee,
            "chainId": w3.eth.chain_id,
            "value": value,
        }
    )

    tx["gas"] = int(w3.eth.estimate_gas(tx) * GAS_LIMIT_BUFFER)
    return simulate_tx(w3, tx, account)


def wait_for_tx_finality(
    w3: Web3,
    tx_hash: str,
    logger: Logger,
    finality_blocks: int = 120,
    timeout: float = 300.0,
    poll_interval: float = 1.0,
) -> AttributeDict:
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

    start_time = time.monotonic()

    while True:
        try:
            receipt = AttributeDict(w3.eth.get_transaction_receipt(tx_hash))
        # receipt can disappear temporarily during reorgs, or if RPC provider is not synced
        except Exception as exc:
            receipt = None
            logger.debug("No tx receipt for tx_hash=%s", tx_hash, extra={"exc": exc})

        # blockNumber can change as tx gets reorged into different blocks
        try:
            if receipt is not None and (block_number := w3.eth.block_number) >= receipt.blockNumber + finality_blocks:
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
                tx = AttributeDict(w3.eth.get_transaction(tx_hash))
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
        time.sleep(poll_interval)


def sign_tx(w3: Web3, tx: dict, private_key: str) -> SignedTransaction:
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    return signed_tx


def send_tx(w3: Web3, signed_tx: SignedTransaction) -> str:
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return tx_hash.to_0x_hex()


def estimate_fees(w3, percentiles: list[int], blocks=20, default_tip=10_000):
    fee_history = w3.eth.fee_history(blocks, "pending", percentiles)
    base_fees = fee_history["baseFeePerGas"]
    rewards = fee_history["reward"]

    # Calculate average priority fees for each percentile
    avg_priority_fees = []
    for i in range(len(percentiles)):
        nonzero_rewards = [r[i] for r in rewards if len(r) > i and r[i] > 0]
        if nonzero_rewards:
            estimated_tip = sum(nonzero_rewards) // len(nonzero_rewards)
        else:
            estimated_tip = default_tip
        avg_priority_fees.append(estimated_tip)

    # Use the latest base fee
    latest_base_fee = base_fees[-1]

    # Calculate max fees
    fee_estimations = []
    for priority_fee in avg_priority_fees:
        max_fee = int((latest_base_fee + priority_fee) * GAS_FEE_BUFFER)
        fee_estimations.append({"maxFeePerGas": max_fee, "maxPriorityFeePerGas": priority_fee})

    return fee_estimations


def iter_events(
    w3: Web3,
    filter_params: dict,
    *,
    condition: Callable[[AttributeDict], bool] = lambda _: True,
    max_block_range: int = 10_000,
    poll_interval: float = 5.0,
    timeout: float | None = None,
    logger: Logger,
) -> Generator[AttributeDict, None, None]:
    """Stream matching logs over a fixed or live block window. Optionally raises TimeoutError."""

    original_filter_params = filter_params.copy()  # return original in TimeoutError
    if (cursor := filter_params["fromBlock"]) == "latest":
        cursor = w3.eth.block_number

    start_block = cursor
    filter_params["toBlock"] = filter_params.get("toBlock", "latest")
    fixed_ceiling = None if filter_params["toBlock"] == "latest" else filter_params["toBlock"]

    deadline = None if timeout is None else time.monotonic() + timeout
    while True:
        if deadline and time.monotonic() > deadline:
            msg = f"Timed out waiting for events after scanning blocks {start_block}-{cursor}"
            logger.warning(msg)
            raise TimeoutError(f"{msg}: filter_params: {original_filter_params}")
        upper = fixed_ceiling or w3.eth.block_number
        if cursor <= upper:
            end = min(upper, cursor + max_block_range - 1)
            filter_params["fromBlock"] = hex(cursor)
            filter_params["toBlock"] = hex(end)
            # For example, when rotating providers are out of sync
            retry_get_logs = exp_backoff_retry(w3.eth.get_logs, attempts=EVENT_LOG_RETRIES)
            logs = retry_get_logs(filter_params=filter_params)
            logger.debug(f"Scanned {cursor} - {end}: {len(logs)} logs")
            yield from filter(condition, logs)
            cursor = end + 1  # bounds are inclusive

        if fixed_ceiling and cursor > fixed_ceiling:
            raise StopIteration

        time.sleep(poll_interval)


def wait_for_event(
    w3: Web3,
    filter_params: dict,
    *,
    condition: Callable[[AttributeDict], bool] = lambda _: True,
    max_block_range: int = 10_000,
    poll_interval: float = 5.0,
    timeout: float = 300.0,
    logger: Logger,
) -> AttributeDict:
    """Return the first log from iter_events, or raise TimeoutError after `timeout` seconds."""

    return next(iter_events(**locals()))


def make_filter_params(
    event: ContractEvent,
    from_block: int | Literal["latest"],
    to_block: int | Literal["latest"] = "latest",
    argument_filters: dict | None = None,
) -> dict:
    """
    Function to create an eth_getLogs compatible filter_params for this event without using .create_filter.
    event.create_filter uses eth_newFilter (a "push"), which not all RPC endpoints support.
    """

    argument_filters = argument_filters or {}
    filter_params = event._get_event_filter_params(
        fromBlock=from_block,
        toBlock=to_block,
        argument_filters=argument_filters,
        abi=event.abi,
    )
    filter_params["topics"] = tuple(filter_params["topics"])
    address = filter_params["address"]
    if isinstance(address, str):
        filter_params["address"] = Web3.to_checksum_address(address)
    elif isinstance(address, (list, tuple)) and len(address) == 1:
        filter_params["address"] = Web3.to_checksum_address(address[0])
    else:
        raise ValueError(f"Unexpected address filter: {address!r}")

    return filter_params
