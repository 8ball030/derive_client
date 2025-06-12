import json

from derive_client.constants import DATA_DIR
from derive_client.data_types import ChainID, Currency

prod_lyra_addresses = DATA_DIR / "prod_lyra_addresses.json"


def test_prod_lyra_addresses():
    raw_data = json.loads(prod_lyra_addresses.read_text())
    chain_ids = set()
    currencies = set()
    for chain_id, data in raw_data.items():
        chain_ids.add(int(chain_id))
        for currency, item in data.items():
            currencies.add(currency)

    missing_chains = chain_ids.difference(ChainID.__members__.values())
    missing_currencies = currencies.difference(Currency.__members__)
    assert not missing_chains
    assert not missing_currencies
