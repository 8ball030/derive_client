from __future__ import annotations

from derive_client.data_types import ChainID, Currency
from derive_client.utils.prod_addresses import get_prod_derive_addresses


def test_get_prod_derive_addresses():
    """Test to ensure our enums cover all chain ids and currencies listed."""

    prod_addresses = get_prod_derive_addresses()
    chain_ids = set(prod_addresses.chains)
    currencies = {currency for value in prod_addresses.chains.values() for currency in value}
    missing_chains = chain_ids - set(ChainID)
    missing_currencies = currencies - set(Currency)
    assert not missing_chains
    assert not missing_currencies
