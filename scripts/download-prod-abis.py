#!/usr/bin/env python3

"""
Download ABIs for all Derive production contract addresses.

This script fetches ABIs from block explorers for all contracts used in production,
including handling EIP1967 proxy contracts by detecting and downloading their
implementation ABIs as well.
"""

import json
import sys
import time

from web3 import Web3

from derive_client.config import ABI_DATA_DIR
from derive_client.data_types import ChainID, ChecksumAddress, Currency, MintableTokenData, NonMintableTokenData
from derive_client.utils.logger import get_logger
from derive_client.utils.prod_addresses import get_prod_derive_addresses
from derive_client.utils.retry import get_retry_session
from derive_client.utils.w3 import get_w3_connection

TIMEOUT = 10
REQUEST_DELAY = 0.5
RATE_LIMIT_DELAY = 300  # 5 minutes
EIP1967_SLOT = (int.from_bytes(Web3.keccak(text="eip1967.proxy.implementation")[:32], "big") - 1).to_bytes(32, "big")


CHAIN_ID_TO_URL = {
    ChainID.ETH: "https://abidata.net/{address}",
    ChainID.OPTIMISM: "https://abidata.net/{address}?network=optimism",
    ChainID.ARBITRUM: "https://abidata.net/{address}?network=arbitrum",
    ChainID.BASE: "https://abidata.net/{address}?network=base",
    ChainID.DERIVE: "https://explorer.derive.xyz/api?module=contract&action=getabi&address={address}",
}


def get_abi(chain_id, contract_address: str, logger):
    url = CHAIN_ID_TO_URL[chain_id].format(address=contract_address)
    session = get_retry_session()

    for attempt in range(2):
        try:
            response = session.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            if chain_id == ChainID.DERIVE:
                return json.loads(response.json()["result"])
            return response.json()["abi"]
        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str or "429" in error_str:
                logger.warning(
                    f"Rate limit hit for {url}. ",
                    f"Waiting {RATE_LIMIT_DELAY}s before retry.",
                )
                time.sleep(RATE_LIMIT_DELAY)


def collect_prod_addresses(
    currencies: dict[Currency, NonMintableTokenData | MintableTokenData],
):
    contract_addresses = []
    for currency, token_data in currencies.items():
        if isinstance(token_data, MintableTokenData):
            contract_addresses.append(token_data.Controller)
            contract_addresses.append(token_data.MintableToken)
        else:  # NonMintableTokenData
            contract_addresses.append(token_data.Vault)
            contract_addresses.append(token_data.NonMintableToken)

        if token_data.LyraTSADepositHook is not None:
            contract_addresses.append(token_data.LyraTSADepositHook)
        if token_data.LyraTSAShareHandlerDepositHook is not None:
            contract_addresses.append(token_data.LyraTSAShareHandlerDepositHook)

        for connector_chain_id, connectors in token_data.connectors.items():
            contract_addresses.append(connectors["FAST"])

    return contract_addresses


def get_impl_address(w3: Web3, address: ChecksumAddress) -> ChecksumAddress | None:
    """Get EIP1967 Proxy implementation address, if any."""

    data = w3.eth.get_storage_at(address, EIP1967_SLOT)
    impl_address = Web3.to_checksum_address(data[-20:])

    if int(impl_address, 16) == 0:
        return None

    return ChecksumAddress(impl_address)


def main() -> int:
    """Main entry point for the script."""
    logger = get_logger()
    prod_addresses = get_prod_derive_addresses()

    # Collect all addresses by chain
    chain_addresses: dict[ChainID, list[ChecksumAddress]] = {}
    for chain_id, currencies in prod_addresses.chains.items():
        chain_addresses[chain_id] = collect_prod_addresses(currencies)

    failures: list[str] = []
    abi_path = ABI_DATA_DIR.parent / "abis"

    for chain_id, addresses in chain_addresses.items():
        if chain_id not in CHAIN_ID_TO_URL:
            logger.info(f"Network not supported by abidata.net: {chain_id.name}")
            continue

        proxy_mapping: dict[str, str] = {}
        w3 = get_w3_connection(chain_id=chain_id)

        while addresses:
            address = addresses.pop()
            contract_abi_path = abi_path / chain_id.name.lower() / f"{address}.json"

            if impl_address := get_impl_address(w3=w3, address=address):
                logger.info(f"EIP1967 Proxy detected: {address} -> {impl_address}")
                addresses.append(impl_address)
                proxy_mapping[address] = impl_address

            if not contract_abi_path.exists():
                try:
                    abi = get_abi(chain_id=chain_id, contract_address=address, logger=logger)
                except Exception as e:
                    failures.append(f"{chain_id.name}: {address}: {e}")
                    logger.warning(f"Failed to fetch ABI for {address}: {e}")
                    continue
                if addresses:
                    time.sleep(REQUEST_DELAY)
            else:
                logger.info(f"Already present: {contract_abi_path}")
                continue

            contract_abi_path = abi_path / chain_id.name.lower() / f"{address}.json"
            contract_abi_path.parent.mkdir(exist_ok=True, parents=True)
            contract_abi_path.write_text(json.dumps(abi, indent=4))
            logger.info(f"Saved ABI: {contract_abi_path}")

        if proxy_mapping:
            proxy_mapping_path = abi_path / chain_id.name.lower() / "proxy_mapping.json"
            proxy_mapping_path.write_text(json.dumps(proxy_mapping, indent=4))
            logger.info(f"Saved proxy mapping: {proxy_mapping_path}")

    if failures:
        logger.error(f"Failed to fetch {len(failures)} ABIs:")
        for failure in failures:
            logger.error(f"  {failure}")
        return 1

    logger.info("Successfully downloaded all ABIs!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
