"""Market data queries."""

from __future__ import annotations

import warnings
from logging import Logger
from typing import Optional

from derive_client._clients.rest.async_http.api import AsyncPublicAPI
from derive_client._clients.utils import async_fetch_all_pages_of_instrument_type, infer_instrument_type
from derive_client.data_types.generated_models import (
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
    PublicGetTickersParamsSchema,
    TickerSlimSchema,
)


class MarketOperations:
    """Market data queries."""

    def __init__(self, *, public_api: AsyncPublicAPI, logger: Logger):
        """
        Initialize market data queries.

        Args:
            public_api: PublicAPI instance providing access to public APIs
        """
        self._public_api = public_api
        self._logger = logger

        self._erc20_instruments_cache: dict[str, InstrumentPublicResponseSchema] = {}
        self._perp_instruments_cache: dict[str, InstrumentPublicResponseSchema] = {}
        self._option_instruments_cache: dict[str, InstrumentPublicResponseSchema] = {}

    @property
    def erc20_instruments_cache(self) -> dict[str, InstrumentPublicResponseSchema]:
        """Get cached ERC20 instruments."""

        if not self._erc20_instruments_cache:
            raise RuntimeError(
                "Call fetch_instruments() or fetch_all_instruments() to create the erc20_instruments_cache."
            )
        return self._erc20_instruments_cache

    @property
    def perp_instruments_cache(self) -> dict[str, InstrumentPublicResponseSchema]:
        """Get cached perpetual instruments."""

        if not self._perp_instruments_cache:
            raise RuntimeError(
                "Call fetch_instruments() or fetch_all_instruments() to create the perp_instruments_cache."
            )
        return self._perp_instruments_cache

    @property
    def option_instruments_cache(self) -> dict[str, InstrumentPublicResponseSchema]:
        """Get cached option instruments."""

        if not self._option_instruments_cache:
            raise RuntimeError(
                "Call fetch_instruments() or fetch_all_instruments() to create the option_instruments_cache."
            )
        return self._option_instruments_cache

    async def fetch_instruments(
        self,
        *,
        instrument_type: InstrumentType,
        expired: bool = False,
    ) -> dict[str, InstrumentPublicResponseSchema]:
        """
        Fetch instruments for a specific instrument type from API.

        Args:
            instrument_type: The type of instruments to fetch (erc20, perp, or option)
            expired: If False (default), update cache with active instruments.
                     If True, return expired instruments without caching.

        Returns:
            Dictionary mapping instrument_name to instrument data
        """

        instruments = {}
        for instrument in await async_fetch_all_pages_of_instrument_type(
            markets=self,
            instrument_type=instrument_type,
            expired=expired,
        ):
            instruments[instrument.instrument_name] = instrument

        if expired:
            return instruments

        cache = self._get_cache_for_type(instrument_type)
        cache.clear()
        cache.update(instruments)
        self._logger.debug(f"Cached {len(cache)} {instrument_type.name.upper()} instruments")
        return cache

    async def fetch_all_instruments(self, *, expired: bool = False) -> dict[str, InstrumentPublicResponseSchema]:
        """
        Fetch all instrument types from API.

        Args:
            expired: If False (default), update all caches with active instruments.
                     If True, return expired instruments without caching.

        Returns:
            Dictionary mapping instrument_name to instrument data for all types
        """

        all_instruments = {}
        for instrument_type in InstrumentType:
            instruments = await self.fetch_instruments(instrument_type=instrument_type, expired=expired)
            all_instruments.update(instruments)

        return all_instruments

    def _get_cache_for_type(self, instrument_type: InstrumentType) -> dict[str, InstrumentPublicResponseSchema]:
        """Get the cache for a specific instrument type."""

        match instrument_type:
            case InstrumentType.erc20:
                return self._erc20_instruments_cache
            case InstrumentType.perp:
                return self._perp_instruments_cache
            case InstrumentType.option:
                return self._option_instruments_cache
            case _:
                raise TypeError(f"Unsupported instrument_type: {instrument_type!r}")

    def _get_cached_instrument(self, *, instrument_name: str) -> InstrumentPublicResponseSchema:
        """Internal helper to retrieve an instrument from cache."""

        instrument_type = infer_instrument_type(instrument_name=instrument_name)

        cache = self._get_cache_for_type(instrument_type)

        if (instrument := cache.get(instrument_name)) is None:
            raise RuntimeError(
                f"Instrument '{instrument_name}' not found in {instrument_type} instrument cache. "
                "Either the name is incorrect, or the local cache is stale. "
                "Call fetch_instruments() or fetch_all_instruments() to refresh the cache."
            )

        return instrument

    async def get_currency(self, *, currency: str) -> PublicGetCurrencyResultSchema:
        """Get currency related risk params, spot price 24hrs ago and lending details for a specific currency."""

        params = PublicGetCurrencyParamsSchema(currency=currency)
        response = await self._public_api.get_currency(params)
        return response.result

    async def get_all_currencies(self) -> list[CurrencyDetailedResponseSchema]:
        """Get all active currencies with their spot price, spot price 24hrs ago."""

        params = PublicGetAllCurrenciesParamsSchema()
        response = await self._public_api.get_all_currencies(params)
        return response.result

    async def get_instrument(self, *, instrument_name: str) -> PublicGetInstrumentResultSchema:
        """Get single instrument by asset name."""

        params = PublicGetInstrumentParamsSchema(instrument_name=instrument_name)
        response = await self._public_api.get_instrument(params)
        return response.result

    async def get_instruments(
        self,
        *,
        currency: str,
        expired: bool,
        instrument_type: InstrumentType,
    ) -> list[InstrumentPublicResponseSchema]:
        """Get all active instruments for a given `currency` and `type`."""

        params = PublicGetInstrumentsParamsSchema(
            currency=currency,
            expired=expired,
            instrument_type=instrument_type,
        )
        response = await self._public_api.get_instruments(params)
        return response.result

    async def get_all_instruments(
        self,
        *,
        expired: bool,
        instrument_type: InstrumentType,
        currency: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> PublicGetAllInstrumentsResultSchema:
        """Get a paginated history of all instruments."""

        params = PublicGetAllInstrumentsParamsSchema(
            expired=expired,
            instrument_type=instrument_type,
            currency=currency,
            page=page,
            page_size=page_size,
        )
        response = await self._public_api.get_all_instruments(params)
        return response.result

    async def get_ticker(self, *, instrument_name: str) -> PublicGetTickerResultSchema:
        """
        Get ticker information (best bid / ask, instrument contraints, fees info, etc.) for a single instrument

        DEPRECATION NOTICE: This RPC is deprecated in favor of `get_tickers` on Dec 1, 2025.
        """

        warnings.warn(
            "get_ticker is deprecated and will be removed on Dec 1, 2025. Use get_tickers instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        params = PublicGetTickerParamsSchema(instrument_name=instrument_name)
        response = await self._public_api.get_ticker(params)
        return response.result

    async def get_tickers(
        self,
        *,
        currency: str,
        instrument_type: InstrumentType,
        expiry_date: Optional[str] = None,
    ) -> dict[str, TickerSlimSchema]:
        """Get tickers information (best bid / ask, stats, etc.) for multiple instruments."""

        params = PublicGetTickersParamsSchema(
            currency=currency,
            instrument_type=instrument_type,
            expiry_date=expiry_date,
        )
        response = await self._public_api.get_tickers(params)
        return response.result.tickers
