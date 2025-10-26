"""Tests for MMP module."""

import pytest

from derive_client.data.generated.models import (
    MMPConfigResultSchema,
    PrivateSetMmpConfigResultSchema,
    Result,
)


@pytest.mark.asyncio
async def test_mmp_get_config(client_owner_wallet):
    currency = None
    mmp_configs = await client_owner_wallet.mmp.get_config(currency=currency)
    assert isinstance(mmp_configs, list)
    assert all(isinstance(item, MMPConfigResultSchema) for item in mmp_configs)


@pytest.mark.asyncio
async def test_mmp_set_config(client_owner_wallet):
    currency = "BTC"
    mmp_configs = await client_owner_wallet.mmp.get_config(currency=currency)
    mmp_config = mmp_configs[0]
    set_mmp_config = await client_owner_wallet.mmp.set_config(
        currency=currency,
        mmp_frozen_time=mmp_config.mmp_frozen_time,
        mmp_interval=mmp_config.mmp_interval,
        mmp_amount_limit=mmp_config.mmp_amount_limit,
        mmp_delta_limit=mmp_config.mmp_delta_limit,
    )
    assert isinstance(set_mmp_config, PrivateSetMmpConfigResultSchema)


@pytest.mark.asyncio
async def test_mmp_reset(client_owner_wallet):
    currency = "ETH"
    result = await client_owner_wallet.mmp.reset(currency=currency)
    assert isinstance(result, Result)
