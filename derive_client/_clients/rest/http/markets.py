"""Market data queries."""

from __future__ import annotations

from typing import Optional

from derive_client._clients.rest.http.api import PublicAPI
from derive_client._clients.utils import fetch_all_pages_of_instrument_type
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
        self._active_instrument_cache: dict[str, InstrumentPublicResponseSchema] = {}

    def fetch_instruments(self, expired: bool = False) -> dict[str, InstrumentPublicResponseSchema]:
        """
        Fetch all instruments from API:
        - If expired == False (default): build cache of active instruments and replace persistent cache.
        - If expired == True: return a mapping of expired instruments without modifying persistent cache.
        """

        instruments = {}
        for instrument_type in InstrumentType:
            for instrument in fetch_all_pages_of_instrument_type(
                markets=self,
                instrument_type=instrument_type,
                expired=expired,
            ):
                if instrument.instrument_name in instruments:
                    msg = f"Duplicate instrument_name '{instrument.instrument_name}' found while building instrument mapping."
                    raise RuntimeError(msg)
                instruments[instrument.instrument_name] = instrument

        if expired:
            return instruments

        self._active_instrument_cache.clear()
        self._active_instrument_cache.update(instruments)
        return self._active_instrument_cache

    @property
    def cached_active_instruments(self) -> dict[str, InstrumentPublicResponseSchema]:
        return self._active_instrument_cache

    def get_cached_instrument(self, instrument_name: str) -> InstrumentPublicResponseSchema:
        """Lookup an instrument from the active cache; avoids API calls in performance-critical paths."""

        if (instrument := self.cached_active_instruments.get(instrument_name)) is None:
            raise RuntimeError(
                f"Instrument '{instrument_name}' not found in active instrument cache. "
                "Either the name is incorrect, or the local cache is stale. "
                "Call fetch_instruments() to refresh the cache."
            )
        return instrument

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
        """Collect tickers by calling get_ticker for each instrument. May issue many HTTP requests; use with care."""

        instruments = self.get_instruments(currency=currency, expired=expired, instrument_type=instrument_type)
        tickers = [self.get_ticker(instrument_name=instrument.instrument_name) for instrument in instruments]
        return tickers
