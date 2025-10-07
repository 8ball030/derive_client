import pytest

from derive_client._clients.rest.http.client import HTTPClient
from derive_client.data.generated.models import (
    PrivateGetOrdersParamsSchema,
    PrivateGetOrdersResponseSchema,
    PrivateGetSubaccountsParamsSchema,
    PrivateGetSubaccountsResponseSchema,
    PublicGetTickerParamsSchema,
    PublicGetTickerResponseSchema,
)
from derive_client.data_types import Environment

TEST_WALLET = "0x8772185a1516f0d61fC1c2524926BfC69F95d698"
TEST_SESSION_KEY = "0x2ae8be44db8a590d20bffbe3b6872df9b569147d3bf6801a35a28281a4816bbd"
SUBACCOUNT_IDS = [31049, 30769]


@pytest.fixture
def client():
    client = HTTPClient(
        wallet=TEST_WALLET,
        session_key=TEST_SESSION_KEY,
        env=Environment.TEST,
    )
    return client


def test_public_get_ticker(client):
    instrument_name = "ETH-PERP"
    params = PublicGetTickerParamsSchema(instrument_name=instrument_name)
    response = client.public.get_ticker(params=params)
    assert isinstance(response, PublicGetTickerResponseSchema)


def test_get_private_get_subaccounts(client):
    wallet = TEST_WALLET
    params = PrivateGetSubaccountsParamsSchema(wallet=wallet)
    response = client.private.get_subaccounts(params=params)
    assert isinstance(response, PrivateGetSubaccountsResponseSchema)


def test_get_private_get_orders(client):
    subaccount_id = SUBACCOUNT_IDS[0]
    params = PrivateGetOrdersParamsSchema(subaccount_id=subaccount_id)
    response = client.private.get_orders(params=params)
    assert isinstance(response, PrivateGetOrdersResponseSchema)
