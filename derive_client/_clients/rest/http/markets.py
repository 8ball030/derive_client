"""Market data queries."""

from __future__ import annotations

from typing import Optional

from derive_client._clients.rest.http.api import PublicAPI
from derive_client.data.generated.models import (
    CurrencyDetailedResponseSchema,
    InstrumentPublicResponseSchema,
    InstrumentType,
    PublicGetAllCurrenciesParamsSchema,
    PublicGetAllInstrumentsParamsSchema,
    PublicGetAllInstrumentsResultSchema,
    PublicGetCurrencyParamsSchema,
    PublicGetCurrencyResultSchema,
    PublicGetInstrumentParamsSchema,
    PublicGetInstrumentResultSchema,
    PublicGetInstrumentsParamsSchema,
    PublicGetTickerParamsSchema,
    PublicGetTickerResultSchema,
)


class MarketOperations:
    """Market data queries."""

    def __init__(self, public_api: PublicAPI):
        """
        Initialize market data queries.

        Args:
            public_api: PublicAPI instance providing access to public APIs
        """
        self._public_api = public_api

    def get_currency(self, currency: str) -> PublicGetCurrencyResultSchema:
        params = PublicGetCurrencyParamsSchema(currency=currency)
        response = self._public_api.get_currency(params)
        return response.result

    def get_all_currencies(self) -> list[CurrencyDetailedResponseSchema]:
        params = PublicGetAllCurrenciesParamsSchema()
        response = self._public_api.get_all_currencies(params)
        return response.result

    def get_instrument(self, instrument_name: str) -> PublicGetInstrumentResultSchema:
        params = PublicGetInstrumentParamsSchema(instrument_name=instrument_name)
        response = self._public_api.get_instrument(params)
        return response.result

    def get_instruments(
        self,
        currency: str,
        expired: bool,
        instrument_type: InstrumentType,
    ) -> list[InstrumentPublicResponseSchema]:
        params = PublicGetInstrumentsParamsSchema(
            currency=currency,
            expired=expired,
            instrument_type=instrument_type,
        )
        response = self._public_api.get_instruments(params)
        return response.result

    def get_all_instruments(
        self,
        expired: bool,
        instrument_type: InstrumentType,
        currency: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> PublicGetAllInstrumentsResultSchema:
        params = PublicGetAllInstrumentsParamsSchema(
            expired=expired,
            instrument_type=instrument_type,
            currency=currency,
            page=page,
            page_size=page_size,
        )
        response = self._public_api.get_all_instruments(params)
        return response.result

    def get_ticker(self, instrument_name: str) -> PublicGetTickerResultSchema:
        params = PublicGetTickerParamsSchema(instrument_name=instrument_name)
        response = self._public_api.get_ticker(params)
        return response.result

    def get_all_tickers(
        self,
        currency: str,
        expired: bool,
        instrument_type: InstrumentType,
    ) -> list[PublicGetTickerResultSchema]:
        instruments = self.get_instruments(currency=currency, expired=expired, instrument_type=instrument_type)
        tickers = [self.get_ticker(instrument_name=instrument.instrument_name) for instrument in instruments]
        return tickers
