"""Tests for Market module."""

from derive_client.data_types.generated_models import (
    AssetType,
    CurrencyDetailedResponseSchema,
    InstrumentPublicResponseSchema,
    PublicGetAllInstrumentsResultSchema,
    PublicGetCurrencyResultSchema,
    PublicGetInstrumentResultSchema,
    PublicGetTickerResultSchema,
    TickerSlimSchema,
)


def test_markets_get_currency(client_admin_wallet):
    currency = "ETH"
    currency = client_admin_wallet.markets.get_currency(currency=currency)
    assert isinstance(currency, PublicGetCurrencyResultSchema)


def test_markets_get_all_currencies(client_admin_wallet):
    currencies = client_admin_wallet.markets.get_all_currencies()
    assert isinstance(currencies, list)
    assert all(isinstance(item, CurrencyDetailedResponseSchema) for item in currencies)


def test_markets_get_instrument(client_admin_wallet):
    instrument_name = "ETH-PERP"
    instrument = client_admin_wallet.markets.get_instrument(instrument_name=instrument_name)
    assert isinstance(instrument, PublicGetInstrumentResultSchema)


def test_markets_get_instruments(client_admin_wallet):
    currency = "ETH"
    expired = False
    instrument_type = AssetType.option
    instruments = client_admin_wallet.markets.get_instruments(
        currency=currency,
        expired=expired,
        instrument_type=instrument_type,
    )
    assert isinstance(instruments, list)
    assert all(isinstance(item, InstrumentPublicResponseSchema) for item in instruments)


def test_markets_get_all_instruments(client_admin_wallet):
    expired = False
    instrument_type = AssetType.perp
    currency = None
    all_instruments = client_admin_wallet.markets.get_all_instruments(
        expired=expired,
        instrument_type=instrument_type,
        currency=currency,
    )
    assert isinstance(all_instruments, PublicGetAllInstrumentsResultSchema)


def test_markets_get_ticker(client_admin_wallet):
    instrument_name = "ETH-PERP"
    ticker = client_admin_wallet.markets.get_ticker(instrument_name=instrument_name)
    assert isinstance(ticker, PublicGetTickerResultSchema)


def test_markets_get_tickers(client_admin_wallet):
    currency = "ETH"
    expired = False
    instrument_type = AssetType.option
    instruments = client_admin_wallet.markets.get_instruments(
        currency=currency,
        expired=expired,
        instrument_type=instrument_type,
    )

    _, expiry_date, _, _ = instruments[0].instrument_name.split("-")
    tickers = client_admin_wallet.markets.get_tickers(
        currency=currency,
        expiry_date=expiry_date,
        instrument_type=instrument_type,
    )

    assert isinstance(tickers, dict)
    assert all(isinstance(ticker, TickerSlimSchema) for ticker in tickers.values())
