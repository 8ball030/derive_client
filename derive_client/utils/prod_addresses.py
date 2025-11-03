from __future__ import annotations

import json

from derive_client.config import DATA_DIR
from derive_client.data_types import DeriveAddresses


def get_prod_derive_addresses() -> DeriveAddresses:
    """Fetch the socket superbridge JSON data."""
    prod_lyra_addresses = DATA_DIR / "prod_lyra_addresses.json"
    old_prod_lyra_addresses = DATA_DIR / "prod_lyra-old_addresses.json"
    chains = {}
    for chain_id, data in json.loads(prod_lyra_addresses.read_text()).items():
        chain_data = {}
        for currency, item in data.items():
            item["isNewBridge"] = True
            chain_data[currency] = item
        chains[chain_id] = chain_data

    for chain_id, data in json.loads(old_prod_lyra_addresses.read_text()).items():
        current_chain_data = chains[chain_id]
        for currency, item in data.items():
            item["isNewBridge"] = False
            current_chain_data[currency] = item
    return DeriveAddresses(chains=chains)
