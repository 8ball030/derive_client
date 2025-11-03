import functools
import heapq
import threading
import time
from decimal import Decimal
from logging import Logger
from pathlib import Path
from typing import Any, Callable

import yaml
from requests import RequestException
from web3 import AsyncHTTPProvider, HTTPProvider, Web3
from web3.types import RPCEndpoint, RPCResponse

from derive_client.config import CURRENCY_DECIMALS, DEFAULT_RPC_ENDPOINTS
from derive_client.data_types import ChainID, Currency, RPCEndpoints
from derive_client.exceptions import NoAvailableRPC
from derive_client.utils.logger import get_logger


class EndpointState:
    __slots__ = ("provider", "backoff", "next_available")

    def __init__(self, provider: HTTPProvider | AsyncHTTPProvider):
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
) -> Callable[[Callable[[RPCEndpoint, Any], RPCResponse], Web3], Callable[[RPCEndpoint, Any], RPCResponse]]:
    """
    v6.11-style middleware:
     - round-robin via a min-heap of `next_available` times
     - on 429: exponential back-off for that endpoint, capped
    """

    heap: list[EndpointState] = [EndpointState(p) for p in endpoints]
    heapq.heapify(heap)
    lock = threading.Lock()

    def middleware_factory(
        make_request: Callable[[RPCEndpoint, Any], RPCResponse],
        w3: Web3,
    ) -> Callable[[RPCEndpoint, Any], Any]:
        def rotating_backoff(method: RPCEndpoint, params: Any) -> Any:
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
                    with lock:
                        heapq.heappush(heap, state)
                    return resp

                except RequestException as e:
                    logger.debug("Endpoint %s failed: %s", state.provider.endpoint_uri, e)

                    # We retry on all exceptions
                    retry_after_header = None
                    if e.response is not None and e.response.headers is not None:
                        retry_after_header = e.response.headers.get("Retry-After")

                    if retry_after_header is not None and isinstance(retry_after_header, str):
                        try:
                            backoff = float(retry_after_header)
                        except (ValueError, TypeError):
                            backoff = state.backoff * 2 if state.backoff > 0 else initial_backoff
                    else:
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
    providers = [HTTPProvider(str(url)) for url in rpc_endpoints[chain_id]]

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


def to_base_units(decimal_amount: Decimal, currency: Currency) -> int:
    """Convert a human-readable token amount to base units using the currency's decimals."""

    return int(decimal_amount * 10 ** CURRENCY_DECIMALS[currency])


def from_base_units(amount: int, currency: Currency) -> Decimal:
    """Convert base units to human-readable amount using the currency's decimals."""

    return Decimal(amount) / Decimal(10) ** CURRENCY_DECIMALS[currency]
