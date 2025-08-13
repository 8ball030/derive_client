"""Utils for the Derive Client package."""

from .abi import download_prod_address_abis
from .logger import get_logger
from .prod_addresses import get_prod_derive_addresses
from .retry import exp_backoff_retry, get_retry_session, wait_until
from .unwrap import unwrap_or_raise
from .w3 import (
    build_standard_transaction,
    estimate_fees,
    get_contract,
    get_erc20_contract,
    get_w3_connection,
    iter_events,
    load_rpc_endpoints,
    make_filter_params,
    make_rotating_provider_middleware,
    send_and_confirm_tx,
    sign_and_send_tx,
    wait_for_event,
    wait_for_tx_receipt,
)

__all__ = [
    "estimate_fees",
    "get_logger",
    "get_prod_derive_addresses",
    "exp_backoff_retry",
    "get_retry_session",
    "make_filter_params",
    "make_rotating_provider_middleware",
    "wait_until",
    "get_w3_connection",
    "get_contract",
    "get_erc20_contract",
    "load_rpc_endpoints",
    "wait_for_tx_receipt",
    "sign_and_send_tx",
    "send_and_confirm_tx",
    "download_prod_address_abis",
    "build_standard_transaction",
    "iter_events",
    "wait_for_event",
    "unwrap_or_raise",
]
