"""Tests for Market module."""

import pytest

from derive_client.data_types.generated_models import (
    CurrencyDetailedResponseSchema,
    InstrumentPublicResponseSchema,
    InstrumentType,
    PublicGetAllInstrumentsResultSchema,
    PublicGetCurrencyResultSchema,
    PublicGetInstrumentResultSchema,
    PublicGetTickerResultSchema,
)


@pytest.mark.asyncio
async def test_markets_get_currency(client_admin_wallet):
    currency = "ETH"
    currency = await client_admin_wallet.markets.get_currency(currency=currency)
    assert isinstance(currency, PublicGetCurrencyResultSchema)


@pytest.mark.asyncio
async def test_markets_get_all_currencies(client_admin_wallet):
    currencies = await client_admin_wallet.markets.get_all_currencies()
    assert isinstance(currencies, list)
    assert all(isinstance(item, CurrencyDetailedResponseSchema) for item in currencies)


@pytest.mark.asyncio
async def test_markets_get_instrument(client_admin_wallet):
    instrument_name = "ETH-PERP"
    instrument = await client_admin_wallet.markets.get_instrument(instrument_name=instrument_name)
    assert isinstance(instrument, PublicGetInstrumentResultSchema)


@pytest.mark.asyncio
async def test_markets_get_instruments(client_admin_wallet):
    currency = "ETH"
    expired = False
    instrument_type = InstrumentType.option
    instruments = await client_admin_wallet.markets.get_instruments(
        currency=currency,
        expired=expired,
        instrument_type=instrument_type,
    )
    assert isinstance(instruments, list)
    assert all(isinstance(item, InstrumentPublicResponseSchema) for item in instruments)


@pytest.mark.asyncio
async def test_markets_get_all_instruments(client_admin_wallet):
    expired = False
    instrument_type = InstrumentType.perp
    currency = None
    all_instruments = await client_admin_wallet.markets.get_all_instruments(
        expired=expired,
        instrument_type=instrument_type,
        currency=currency,
    )
    assert isinstance(all_instruments, PublicGetAllInstrumentsResultSchema)


@pytest.mark.asyncio
async def test_markets_get_ticker(client_admin_wallet):
    instrument_name = "ETH-PERP"
    ticker = await client_admin_wallet.markets.get_ticker(instrument_name=instrument_name)
    assert isinstance(ticker, PublicGetTickerResultSchema)


@pytest.mark.asyncio
async def test_markets_get_all_tickers(client_admin_wallet):
    currency = "ETH"
    expired = False
    instrument_type = InstrumentType.perp
    tickers = await client_admin_wallet.markets.get_all_tickers(
        currency=currency,
        expired=expired,
        instrument_type=instrument_type,
    )
    assert isinstance(tickers, list)
    assert all(isinstance(item, PublicGetTickerResultSchema) for item in tickers)
