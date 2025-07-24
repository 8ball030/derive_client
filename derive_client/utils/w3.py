import heapq
import json
import threading
import time
from http import HTTPStatus
from typing import Any, Callable, Generator, Literal

from eth_account import Account
from hexbytes import HexBytes
from requests import ConnectTimeout, ReadTimeout, RequestException
from web3 import Web3
from web3.contract import Contract
from web3.contract.contract import ContractEvent
from web3.datastructures import AttributeDict
from web3.providers.rpc import HTTPProvider

from derive_client.constants import ABI_DATA_DIR, GAS_FEE_BUFFER
from derive_client.data_types import ChainID, RPCEndPoints, TxResult, TxStatus
from derive_client.exceptions import TxSubmissionError
from derive_client.utils.retry import exp_backoff_retry


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
    initial_backoff: float = 1.0,
    max_backoff: float = 300.0,
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
            now = time.time()

            while True:
                # 1) grab the earlies-available endpoint
                with lock:
                    state = heapq.heappop(heap)

                # 2) if it's not yet ready, push back and error out
                if state.next_available > now:
                    with lock:
                        heapq.heappush(heap, state)
                    raise TimeoutError("All available RPC endpoints are on timeout")

                try:
                    # 3) attempt the request
                    resp = state.provider.make_request(method, params)
                    # 4) on success, reset its backoff and re-schedule immediately
                    state.backoff = 0.0
                    state.next_available = now
                    with lock:
                        heapq.heappush(heap, state)
                    print(f"State: {state} = SUCCESS")
                    return resp

                except RequestException as e:
                    print(f"State: {state} = FAILED: {e}")
                    # decide if this error is retryable
                    retryable = False

                    # a) HTTP 429 Too Many Requests
                    status = getattr(e.response, "status_code", None)
                    if status == HTTPStatus.TOO_MANY_REQUESTS:
                        retryable = True
                        # parse Retry-After header if present
                        hdr = e.response.headers.get("Retry-After")
                        try:
                            backoff = float(hdr)
                        except (ValueError, TypeError):
                            backoff = state.backoff * 2 if state.backoff > 0 else initial_backoff
                    # b) network‐level timeouts or connection errors
                    elif isinstance(e, (ReadTimeout, ConnectTimeout, ConnectionError)):
                        retryable = True
                        backoff = state.backoff * 2 if state.backoff > 0 else initial_backoff
                    # c) non‑retryable error
                    else:
                        backoff = 0.0

                    if retryable:
                        # cap backoff and schedule
                        state.backoff = min(backoff, max_backoff)
                        state.next_available = now + state.backoff
                        with lock:
                            heapq.heappush(heap, state)
                        # try the next endpoint in the heap
                        continue
                    else:
                        # push back immediately and propagate
                        state.next_available = now
                        with lock:
                            heapq.heappush(heap, state)
                        raise

        return rotating_backoff

    return middleware_factory


def get_w3_connection(chain_id: ChainID) -> Web3:
    rpc_url = RPCEndPoints[chain_id.name].value
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise ConnectionError(f"Failed to connect to RPC at {rpc_url}")
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
        raise ValueError(f"Insufficient gas balance, have {balance}, need {total_cost}: ({ratio:.2f})")

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

    tx["gas"] = w3.eth.estimate_gas(tx)
    return simulate_tx(w3, tx, account)


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


def sign_and_send_tx(w3: Web3, tx: dict, private_key: str) -> HexBytes:
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    print(f"signed_tx: {signed_tx}")
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"tx_hash: 0x{tx_hash.hex()}")
    return tx_hash


def send_and_confirm_tx(
    w3: Web3,
    tx: dict,
    private_key: str,
    *,
    action: str,  # e.g. "approve()", "deposit()", "withdraw()"
) -> TxResult:
    """Send and confirm transactions."""

    try:
        tx_hash = sign_and_send_tx(w3=w3, tx=tx, private_key=private_key)
        tx_result = TxResult(tx_hash=tx_hash.to_0x_hex(), tx_receipt=None, exception=None)
    except Exception as send_err:
        msg = f"❌ Failed to send tx for {action}, error: {send_err!r}"
        print(msg)
        raise TxSubmissionError(msg) from send_err

    try:
        tx_receipt = wait_for_tx_receipt(w3=w3, tx_hash=tx_hash)
        tx_result.tx_receipt = tx_receipt
    except TimeoutError as timeout_err:
        print(f"⏱️ Timeout waiting for tx receipt of {tx_hash.hex()}")
        tx_result.exception = timeout_err
        return tx_result

    if tx_receipt.status == TxStatus.SUCCESS:
        print(f"✅ {action} succeeded for tx {tx_hash.hex()}")
    else:
        print(f"❌ {action} reverted for tx {tx_hash.hex()}")

    return tx_result


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
) -> Generator[AttributeDict, None, None]:
    """Stream matching logs over a fixed or live block window. Optionally raises TimeoutError."""

    original_filter_params = filter_params.copy()  # return original in TimeoutError
    if (cursor := filter_params["fromBlock"]) == "latest":
        cursor = w3.eth.block_number

    start_block = cursor
    filter_params["toBlock"] = filter_params.get("toBlock", "latest")
    fixed_ceiling = None if filter_params["toBlock"] == "latest" else filter_params["toBlock"]

    deadline = None if timeout is None else time.time() + timeout
    while True:
        if deadline and time.time() > deadline:
            msg = f"Timed out waiting for events after scanning blocks {start_block}-{cursor}"
            raise TimeoutError(f"{msg}: filter_params: {original_filter_params}")
        upper = fixed_ceiling or w3.eth.block_number
        if cursor <= upper:
            end = min(upper, cursor + max_block_range - 1)
            filter_params["fromBlock"] = hex(cursor)
            filter_params["toBlock"] = hex(end)
            logs = w3.eth.get_logs(filter_params=filter_params)
            print(f"Scanned {cursor} - {end}: {len(logs)} logs")
            yield from filter(condition, logs)
            cursor = end + 1  # bounds are inclusive

        if fixed_ceiling and cursor > fixed_ceiling:
            return

        time.sleep(poll_interval)


def wait_for_event(
    w3: Web3,
    filter_params: dict,
    *,
    condition: Callable[[AttributeDict], bool] = lambda _: True,
    max_block_range: int = 10_000,
    poll_interval: float = 5.0,
    timeout: float = 300.0,
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
