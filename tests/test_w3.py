import threading
import time
import warnings
from http import HTTPStatus

import pytest
from requests.exceptions import RequestException
from web3 import Web3 as BaseWeb3
from web3.exceptions import MethodUnavailable
from web3.providers.rpc import HTTPProvider
from web3.types import (
    RPCEndpoint,
)

from derive_client.config import DEFAULT_RPC_ENDPOINTS
from derive_client.data_types import ChainID, EthereumJSONRPCErrorCode
from derive_client.utils import get_logger, load_rpc_endpoints
from derive_client.utils.w3 import make_rotating_provider_middleware

RPC_ENDPOINTS = list(load_rpc_endpoints(DEFAULT_RPC_ENDPOINTS).model_dump().items())

REQUIRED_METHODS = {
    "eth_blockNumber": [],
    "eth_chainId": [],
    "eth_getBalance": ["0x0000000000000000000000000000000000000000", "latest"],
    "eth_call": [{"to": "0x0000000000000000000000000000000000000000", "data": "0x"}, "latest"],
    "eth_sendRawTransaction": ["0x"],
    "eth_getLogs": [
        {"fromBlock": "latest", "toBlock": "latest"},
    ],
}


class TrackingHTTPProvider(HTTPProvider):
    def __init__(self, endpoint_uri: str, used: set):
        super().__init__(endpoint_uri)
        self.used = used
        self.lock = threading.Lock()

    def make_request(self, method, params):
        with self.lock:
            self.used.add(self.endpoint_uri)
        # No-op, no call to super(), we only use this to test provider rotation
        return {"result": {}}


class Web3(BaseWeb3):
    provider: HTTPProvider


@pytest.mark.flaky(reruns=3, reruns_delay=1)
@pytest.mark.parametrize("chain, rpc_endpoints", RPC_ENDPOINTS)
def test_rpc_endpoints_reachability_and_chain_id(chain, rpc_endpoints):
    success = {}
    failed = {}
    rate_limited = set()

    request_kwargs = {"timeout": 1}
    providers = [HTTPProvider(url, request_kwargs) for url in rpc_endpoints]
    for provider in providers:
        w3 = Web3(provider)
        if not w3.is_connected:
            continue
        try:
            success[w3.provider.endpoint_uri] = w3.eth.chain_id
        except RequestException as e:
            status = getattr(e.response, "status_code", None)
            if status == HTTPStatus.TOO_MANY_REQUESTS:
                rate_limited.add(w3.provider.endpoint_uri)
                continue
            failed[w3.provider.endpoint_uri] = e
        except Exception as e:
            failed[w3.provider.endpoint_uri] = e

    not_connected = set(rpc_endpoints) - set(success) - set(failed) - set(rate_limited)
    assert not not_connected, f"Not connected: {not_connected}"

    if failed:
        details = "\n".join(f"  {u} → chain_id {cid}" for u, cid in failed.items())
        pytest.fail(f"[{chain}] endpoints failures:\n{details}")

    expected = ChainID[chain]
    incorrect_chains = {k: v for k, v in success.items() if v != expected}
    assert not incorrect_chains, f"Incorrect chain, expected {expected.name} ({expected}) got: {incorrect_chains}"

    if rate_limited:
        warnings.warn(f"[{chain}] endpoints rate-limited: {rate_limited}", UserWarning)

    max_unresponsive = len(rpc_endpoints) // 3
    if len(rate_limited) > max_unresponsive:
        msg = "\n".join(f"  {url}" for url in rate_limited)
        pytest.fail(f"[{chain}] Too many unresponsive endpoints ({len(rate_limited)}/{len(rpc_endpoints)}):\n{msg}")


@pytest.mark.flaky(reruns=3, reruns_delay=1)
@pytest.mark.parametrize("chain, rpc_endpoints", RPC_ENDPOINTS)
def test_rpc_methods_supported(chain, rpc_endpoints):
    missing = {}
    exceptions = {}
    request_kwargs = {"timeout": 1}
    for url in rpc_endpoints:
        prov = HTTPProvider(url, request_kwargs=request_kwargs)
        w3 = Web3(prov)

        for method, params in REQUIRED_METHODS.items():
            try:
                # use manager.request_blocking to hit exactly that method
                w3.manager.request_blocking(RPCEndpoint(method), params)
            except MethodUnavailable:
                missing.setdefault(url, []).append(method)
            except RequestException as e:
                # the method exists (we're hitting the RPC path)
                # but the provider is choking on our dummy TX payload
                if method != "eth_sendRawTransaction":
                    exceptions.setdefault(url, []).append((method, e))
            except ValueError as e:
                err = e.args[0]
                if isinstance(err, dict) and err.get("code") == EthereumJSONRPCErrorCode.METHOD_NOT_FOUND:
                    # still missing
                    missing.setdefault(url, []).append(method)
                # else: other error codes (-32000, -32603, etc.) => method exists
            except AttributeError as e:
                # RPC endpoints is returning a plain text error message instead of a proper JSON-RPC
                if "'str' object has no attribute 'get'" in str(e):
                    print(f"Malformed response from {url} for method {method}")
                else:
                    exceptions.setdefault(url, []).append((method, e))

    assert not missing, f"Some RPC endpoints lack required methods: {missing}"
    assert not exceptions, f"Some RPC endpoints could not be reached: {exceptions}"


@pytest.mark.parametrize("chain, rpc_endpoints", RPC_ENDPOINTS)
def test_rotating_middelware(chain, rpc_endpoints):
    # --------------------
    # -- USAGE in v6.11 --
    # --------------------

    # 1) Build your list of HTTPProvider, based on your RPCEndpoints
    used = set()
    providers: list[HTTPProvider] = [TrackingHTTPProvider(url, used) for url in rpc_endpoints]

    # 2) Create Web3 (initial provider is a no-op once middleware is in place)
    w3 = Web3()

    # 3) Register the rotating-backoff middleware
    rotator = make_rotating_provider_middleware(
        providers,
        initial_backoff=2.0,
        max_backoff=30.0,
        logger=get_logger(),
    )
    w3.middleware_onion.add(rotator)

    # 4) Test: rotation through all providers
    expected = {p.endpoint_uri for p in providers}
    timeout = time.monotonic() + len(providers)
    while used != expected and time.monotonic() < timeout:
        _ = w3.eth.get_block("latest")

    unused = expected - used
    assert not unused, f"Unused {chain} endpoints:\n{unused}"
