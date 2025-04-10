"""
Tests for the DeriveClient deposit and withdrawal methods for subaccounts.
"""

from derive_client.enums import CollateralAsset


def test_transfer_from_subaccount_to_funding(derive_client):
    """Test transfer from subaccount to funding."""
    # freeze_time(derive_client)
    amount = 1
    from_subaccount_id = derive_client.fetch_subaccounts()['subaccount_ids'][0]
    result = derive_client.transfer_from_subaccount_to_funding(
        amount=amount,
        subaccount_id=from_subaccount_id,
        asset_name=CollateralAsset.USDC.name,
    )
    assert result


def test_transfer_from_funding_to_subaccount(derive_client):
    """Test transfer from funding to subaccount."""
    # freeze_time(derive_client)
    amount = 1
    to_subaccount_id = derive_client.fetch_subaccounts()['subaccount_ids'][0]
    result = derive_client.transfer_from_funding_to_subaccount(
        amount=amount,
        subaccount_id=to_subaccount_id,
        asset_name=CollateralAsset.USDC.name,
    )
    assert result
