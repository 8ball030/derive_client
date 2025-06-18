import json

from web3 import Web3

from derive_client.constants import ABI_DATA_DIR
from derive_client.data_types import ChainID, Currency, MintableTokenData, NonMintableTokenData
from derive_client.utils.logger import get_logger
from derive_client.utils.prod_addresses import get_prod_derive_addresses
from derive_client.utils.retry import get_retry_session
from derive_client.utils.w3 import get_w3_connection

TIMEOUT = 10
EIP1967_SLOT = (int.from_bytes(Web3.keccak(text="eip1967.proxy.implementation")[:32], "big") - 1).to_bytes(32, "big")


CHAIN_ID_TO_URL = {
    ChainID.ETH: "https://abidata.net/{address}",
    ChainID.OPTIMISM: "https://abidata.net/{address}?network=optimism",
    ChainID.ARBITRUM: "https://abidata.net/{address}?network=arbitrum",
    ChainID.BASE: "https://abidata.net/{address}?network=base",
    ChainID.DERIVE: "https://explorer.derive.xyz/api?module=contract&action=getabi&address={address}",
}


def _get_abi(chain_id, contract_address: str):
    url = CHAIN_ID_TO_URL[chain_id].format(address=contract_address)
    session = get_retry_session()
    response = session.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    if chain_id == ChainID.DERIVE:
        return json.loads(response.json()["result"])
    return response.json()["abi"]


def _collect_prod_addresses(
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


def get_impl_address(w3: Web3, address: str) -> str | None:
    """Get EIP1967 Proxy implementation address"""

    data = w3.eth.get_storage_at(address, EIP1967_SLOT)
    impl_address = Web3.to_checksum_address(data[-20:])
    if int(impl_address, 16) == 0:
        return
    return impl_address


def download_prod_address_abis():
    """Download Derive production addresses ABIs."""

    logger = get_logger()
    prod_addresses = get_prod_derive_addresses()

    chain_addresses = {}
    for chain_id, currencies in prod_addresses.chains.items():
        chain_addresses[chain_id] = _collect_prod_addresses(currencies)

    failures = []
    abi_path = ABI_DATA_DIR.parent / "abis"

    for chain_id, addresses in chain_addresses.items():
        proxy_mapping = {}
        w3 = get_w3_connection(chain_id=chain_id)

        if chain_id not in CHAIN_ID_TO_URL:
            logger.info(f"Network not supported by abidata.net: {chain_id.name}")
            continue

        while addresses:
            address = addresses.pop()
            if impl_address := get_impl_address(w3=w3, address=address):
                logger.info(f"EIP1967 Proxy implementation found: {address} -> {impl_address}")
                addresses.append(impl_address)
                proxy_mapping[address] = impl_address
            try:
                abi = _get_abi(chain_id=chain_id, contract_address=address)
            except Exception as e:
                failures.append(f"{chain_id.name}: {address}: {e}")
                continue

            contract_abi_path = abi_path / chain_id.name.lower() / f"{address}.json"
            contract_abi_path.parent.mkdir(exist_ok=True, parents=True)
            contract_abi_path.write_text(json.dumps(abi, indent=4))

        proxy_mapping_path = abi_path / chain_id.name.lower() / "proxy_mapping.json"
        proxy_mapping_path.write_text(json.dumps(proxy_mapping, indent=4))

    if failures:
        unattained = "\n".join(failures)
        logger.error(f"Failed to fetch:\n{unattained}")
