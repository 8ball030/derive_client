import pytest

from derive_client._clients.rest.http.client import HTTPClient
from derive_client.data.generated.models import (
    CurrencyDetailedResponseSchema,
    InstrumentPublicResponseSchema,
    InstrumentType,
    PrivateGetAccountResultSchema,
    PrivateGetOrdersParamsSchema,
    PrivateGetOrdersResponseSchema,
    PrivateGetSubaccountResultSchema,
    PrivateGetSubaccountsParamsSchema,
    PrivateGetSubaccountsResponseSchema,
    PrivateGetSubaccountsResultSchema,
    PrivateSessionKeysResultSchema,
    PublicGetAllInstrumentsResultSchema,
    PublicGetCurrencyResultSchema,
    PublicGetInstrumentResultSchema,
    PublicGetTickerParamsSchema,
    PublicGetTickerResponseSchema,
    PublicGetTickerResultSchema,
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


def test_account_session_keys(client):
    session_keys = client.account.session_keys()
    assert isinstance(session_keys, PrivateSessionKeysResultSchema)


def test_account_get_all_portfolios(client):
    all_portfolios = client.account.get_all_portfolios()
    assert isinstance(all_portfolios, list)
    assert all(isinstance(item, PrivateGetSubaccountResultSchema) for item in all_portfolios)


def test_account_get_subaccounts(client):
    subaccounts = client.account.get_subaccounts()
    assert isinstance(subaccounts, PrivateGetSubaccountsResultSchema)


def test_account_get(client):
    account = client.account.get()
    assert isinstance(account, PrivateGetAccountResultSchema)


def test_markets_get_currency(client):
    currency = "ETH"
    currency = client.markets.get_currency(currency=currency)
    assert isinstance(currency, PublicGetCurrencyResultSchema)


def test_markets_get_all_currencies(client):
    currencies = client.markets.get_all_currencies()
    assert isinstance(currencies, list)
    assert all(isinstance(item, CurrencyDetailedResponseSchema) for item in currencies)


def test_markets_get_instrument(client):
    instrument_name = "ETH-PERP"
    instrument = client.markets.get_instrument(instrument_name=instrument_name)
    assert isinstance(instrument, PublicGetInstrumentResultSchema)


def test_markets_get_instruments(client):
    currency = "ETH"
    expired = False
    instrument_type = InstrumentType.option
    instruments = client.markets.get_instruments(
        currency=currency,
        expired=expired,
        instrument_type=instrument_type,
    )
    assert isinstance(instruments, list)
    assert all(isinstance(item, InstrumentPublicResponseSchema) for item in instruments)


def test_markets_get_all_instruments(client):
    expired = False
    instrument_type = InstrumentType.perp
    currency = None
    page = 1
    page_size = 100
    all_instruments = client.markets.get_all_instruments(
        expired=expired,
        instrument_type=instrument_type,
        currency=currency,
        page=page,
        page_size=page_size,
    )
    assert isinstance(all_instruments, PublicGetAllInstrumentsResultSchema)


def test_markets_get_ticker(client):
    instrument_name = "ETH-PERP"
    ticker = client.markets.get_ticker(instrument_name=instrument_name)
    assert isinstance(ticker, PublicGetTickerResultSchema)


def test_markets_get_tickers(client):
    currency = "ETH"
    expired = False
    instrument_type = InstrumentType.perp
    tickers = client.markets.get_tickers(
        currency=currency,
        expired=expired,
        instrument_type=instrument_type,
    )
    assert isinstance(tickers, list)
    assert all(isinstance(item, PublicGetTickerResultSchema) for item in tickers)
