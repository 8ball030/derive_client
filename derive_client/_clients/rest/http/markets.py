"""Market data queries."""

from typing import Optional

from derive_client.data.generated.models import (
    CurrencyDetailedResponseSchema,
    InstrumentPublicResponseSchema,
    InstrumentType,
    PublicGetAllCurrenciesParamsSchema,
    PublicGetCurrencyParamsSchema,
    PublicGetCurrencyResultSchema,
    PublicGetInstrumentParamsSchema,
    PublicGetInstrumentResultSchema,
    PublicGetInstrumentsParamsSchema,
    PublicGetTickerParamsSchema,
    PublicGetTickerResultSchema,
    PublicGetAllInstrumentsParamsSchema,
    PublicGetAllInstrumentsResultSchema,
)


class MarketOperations:
    """Market data queries."""

    def __init__(self, client):
        """
        Initialize account operations.

        Args:
            client: HTTPClient instance providing access to public/private APIs
        """
        self._client = client

    def get_currency(self, currency: str) -> PublicGetCurrencyResultSchema:
        params = PublicGetCurrencyParamsSchema(currency=currency)
        response = self._client.public.get_currency(params)
        return response.result

    def get_all_currencies(self) -> list[CurrencyDetailedResponseSchema]:
        params = PublicGetAllCurrenciesParamsSchema()
        response = self._client.public.get_all_currencies(params)
        return response.result

    def get_instrument(self, instrument_name: str) -> PublicGetInstrumentResultSchema:
        params = PublicGetInstrumentParamsSchema(instrument_name=instrument_name)
        response = self._client.public.get_instrument(params)
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
        response = self._client.public.get_instruments(params)
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
        response = self._client.public.get_all_instruments(params)
        return response.result

    def get_ticker(self, instrument_name: str) -> PublicGetTickerResultSchema:
        params = PublicGetTickerParamsSchema(instrument_name=instrument_name)
        response = self._client.public.get_ticker(params)
        return response.result

    def get_tickers(
        self,
        currency: str,
        expired: bool,
        instrument_type: InstrumentType,
    ) -> list[PublicGetTickerResultSchema]:
        instruments = self.get_instruments(currency=currency, expired=expired, instrument_type=instrument_type)
        tickers = [self.get_ticker(instrument_name=instrument.instrument_name) for instrument in instruments]
        return tickers
