"""Auto-generated API classes from OpenAPI spec"""

from typing import List

from derive_client._clients.rest.async_http.session import AsyncHTTPSession
from derive_client._clients.rest.endpoints import PrivateEndpoints, PublicEndpoints
from derive_client._clients.utils import AuthContext, decode_envelope, decode_result, encode_json_exclude_none
from derive_client.config import PUBLIC_HEADERS
from derive_client.data_types import EnvConfig
from derive_client.data_types.generated_models import (
    AuctionResultSchema,
    CurrencyDetailedResponseSchema,
    InstrumentPublicResponseSchema,
    MMPConfigResultSchema,
    PrivateCancelAllParamsSchema,
    PrivateCancelAllTriggerOrdersParamsSchema,
    PrivateCancelBatchQuotesParamsSchema,
    PrivateCancelBatchQuotesResultSchema,
    PrivateCancelBatchRfqsParamsSchema,
    PrivateCancelBatchRfqsResultSchema,
    PrivateCancelByInstrumentParamsSchema,
    PrivateCancelByInstrumentResultSchema,
    PrivateCancelByLabelParamsSchema,
    PrivateCancelByLabelResultSchema,
    PrivateCancelByNonceParamsSchema,
    PrivateCancelByNonceResultSchema,
    PrivateCancelParamsSchema,
    PrivateCancelQuoteParamsSchema,
    PrivateCancelQuoteResultSchema,
    PrivateCancelResultSchema,
    PrivateCancelRfqParamsSchema,
    PrivateCancelTriggerOrderParamsSchema,
    PrivateCancelTriggerOrderResultSchema,
    PrivateChangeSubaccountLabelParamsSchema,
    PrivateChangeSubaccountLabelResultSchema,
    PrivateCreateSubaccountParamsSchema,
    PrivateCreateSubaccountResultSchema,
    PrivateDepositParamsSchema,
    PrivateDepositResultSchema,
    PrivateEditSessionKeyParamsSchema,
    PrivateEditSessionKeyResultSchema,
    PrivateExecuteQuoteParamsSchema,
    PrivateExecuteQuoteResultSchema,
    PrivateExpiredAndCancelledHistoryParamsSchema,
    PrivateExpiredAndCancelledHistoryResultSchema,
    PrivateGetAccountParamsSchema,
    PrivateGetAccountResultSchema,
    PrivateGetAllPortfoliosParamsSchema,
    PrivateGetCollateralsParamsSchema,
    PrivateGetCollateralsResultSchema,
    PrivateGetDepositHistoryParamsSchema,
    PrivateGetDepositHistoryResultSchema,
    PrivateGetErc20TransferHistoryParamsSchema,
    PrivateGetErc20TransferHistoryResultSchema,
    PrivateGetFundingHistoryParamsSchema,
    PrivateGetFundingHistoryResultSchema,
    PrivateGetInterestHistoryParamsSchema,
    PrivateGetInterestHistoryResultSchema,
    PrivateGetLiquidationHistoryParamsSchema,
    PrivateGetLiquidatorHistoryParamsSchema,
    PrivateGetLiquidatorHistoryResultSchema,
    PrivateGetMarginParamsSchema,
    PrivateGetMarginResultSchema,
    PrivateGetMmpConfigParamsSchema,
    PrivateGetNotificationsParamsSchema,
    PrivateGetNotificationsResultSchema,
    PrivateGetOpenOrdersParamsSchema,
    PrivateGetOpenOrdersResultSchema,
    PrivateGetOptionSettlementHistoryParamsSchema,
    PrivateGetOptionSettlementHistoryResultSchema,
    PrivateGetOrderHistoryParamsSchema,
    PrivateGetOrderHistoryResultSchema,
    PrivateGetOrderParamsSchema,
    PrivateGetOrderResultSchema,
    PrivateGetOrdersParamsSchema,
    PrivateGetOrdersResultSchema,
    PrivateGetPositionsParamsSchema,
    PrivateGetPositionsResultSchema,
    PrivateGetQuotesParamsSchema,
    PrivateGetQuotesResultSchema,
    PrivateGetRfqsParamsSchema,
    PrivateGetRfqsResultSchema,
    PrivateGetSubaccountParamsSchema,
    PrivateGetSubaccountResultSchema,
    PrivateGetSubaccountsParamsSchema,
    PrivateGetSubaccountsResultSchema,
    PrivateGetSubaccountValueHistoryParamsSchema,
    PrivateGetSubaccountValueHistoryResultSchema,
    PrivateGetTradeHistoryParamsSchema,
    PrivateGetTradeHistoryResultSchema,
    PrivateGetWithdrawalHistoryParamsSchema,
    PrivateGetWithdrawalHistoryResultSchema,
    PrivateLiquidateParamsSchema,
    PrivateLiquidateResultSchema,
    PrivateOrderDebugParamsSchema,
    PrivateOrderDebugResultSchema,
    PrivateOrderParamsSchema,
    PrivateOrderResultSchema,
    PrivatePollQuotesParamsSchema,
    PrivatePollQuotesResultSchema,
    PrivatePollRfqsParamsSchema,
    PrivatePollRfqsResultSchema,
    PrivateRegisterScopedSessionKeyParamsSchema,
    PrivateRegisterScopedSessionKeyResultSchema,
    PrivateReplaceParamsSchema,
    PrivateReplaceQuoteParamsSchema,
    PrivateReplaceQuoteResultSchema,
    PrivateReplaceResultSchema,
    PrivateResetMmpParamsSchema,
    PrivateRfqGetBestQuoteParamsSchema,
    PrivateRfqGetBestQuoteResultSchema,
    PrivateSendQuoteParamsSchema,
    PrivateSendQuoteResultSchema,
    PrivateSendRfqParamsSchema,
    PrivateSendRfqResultSchema,
    PrivateSessionKeysParamsSchema,
    PrivateSessionKeysResultSchema,
    PrivateSetCancelOnDisconnectParamsSchema,
    PrivateSetMmpConfigParamsSchema,
    PrivateSetMmpConfigResultSchema,
    PrivateTransferErc20ParamsSchema,
    PrivateTransferErc20ResultSchema,
    PrivateTransferPositionParamsSchema,
    PrivateTransferPositionResultSchema,
    PrivateTransferPositionsParamsSchema,
    PrivateTransferPositionsResultSchema,
    PrivateUpdateNotificationsParamsSchema,
    PrivateUpdateNotificationsResultSchema,
    PrivateWithdrawParamsSchema,
    PrivateWithdrawResultSchema,
    ProgramResponseSchema,
    PublicBuildRegisterSessionKeyTxParamsSchema,
    PublicBuildRegisterSessionKeyTxResultSchema,
    PublicCreateSubaccountDebugParamsSchema,
    PublicCreateSubaccountDebugResultSchema,
    PublicDepositDebugParamsSchema,
    PublicDepositDebugResultSchema,
    PublicDeregisterSessionKeyParamsSchema,
    PublicDeregisterSessionKeyResultSchema,
    PublicExecuteQuoteDebugParamsSchema,
    PublicExecuteQuoteDebugResultSchema,
    PublicGetAllCurrenciesParamsSchema,
    PublicGetAllInstrumentsParamsSchema,
    PublicGetAllInstrumentsResultSchema,
    PublicGetCurrencyParamsSchema,
    PublicGetCurrencyResultSchema,
    PublicGetFundingRateHistoryParamsSchema,
    PublicGetFundingRateHistoryResultSchema,
    PublicGetInstrumentParamsSchema,
    PublicGetInstrumentResultSchema,
    PublicGetInstrumentsParamsSchema,
    PublicGetInterestRateHistoryParamsSchema,
    PublicGetInterestRateHistoryResultSchema,
    PublicGetLatestSignedFeedsParamsSchema,
    PublicGetLatestSignedFeedsResultSchema,
    PublicGetLiquidationHistoryParamsSchema,
    PublicGetLiquidationHistoryResultSchema,
    PublicGetLiveIncidentsParamsSchema,
    PublicGetLiveIncidentsResultSchema,
    PublicGetMakerProgramScoresParamsSchema,
    PublicGetMakerProgramScoresResultSchema,
    PublicGetMakerProgramsParamsSchema,
    PublicGetMarginParamsSchema,
    PublicGetMarginResultSchema,
    PublicGetOptionSettlementHistoryParamsSchema,
    PublicGetOptionSettlementHistoryResultSchema,
    PublicGetOptionSettlementPricesParamsSchema,
    PublicGetOptionSettlementPricesResultSchema,
    PublicGetReferralPerformanceParamsSchema,
    PublicGetReferralPerformanceResultSchema,
    PublicGetSpotFeedHistoryCandlesParamsSchema,
    PublicGetSpotFeedHistoryCandlesResultSchema,
    PublicGetSpotFeedHistoryParamsSchema,
    PublicGetSpotFeedHistoryResultSchema,
    PublicGetTickerParamsSchema,
    PublicGetTickerResultSchema,
    PublicGetTickersParamsSchema,
    PublicGetTickersResultSchema,
    PublicGetTimeParamsSchema,
    PublicGetTradeHistoryParamsSchema,
    PublicGetTradeHistoryResultSchema,
    PublicGetTransactionParamsSchema,
    PublicGetTransactionResultSchema,
    PublicGetVaultBalancesParamsSchema,
    PublicGetVaultShareParamsSchema,
    PublicGetVaultShareResultSchema,
    PublicGetVaultStatisticsParamsSchema,
    PublicLoginParamsSchema,
    PublicMarginWatchParamsSchema,
    PublicMarginWatchResultSchema,
    PublicRegisterSessionKeyParamsSchema,
    PublicRegisterSessionKeyResultSchema,
    PublicSendQuoteDebugParamsSchema,
    PublicSendQuoteDebugResultSchema,
    PublicStatisticsParamsSchema,
    PublicStatisticsResultSchema,
    PublicWithdrawDebugParamsSchema,
    PublicWithdrawDebugResultSchema,
    Result,
    VaultBalanceResponseSchema,
    VaultStatisticsResponseSchema,
)


class AsyncPublicAPI:
    """Async public API methods"""

    def __init__(self, session: AsyncHTTPSession, config: EnvConfig):
        self._session = session
        self._config = config
        self._endpoints = PublicEndpoints(config.base_url)

    @property
    def headers(self) -> dict:
        return PUBLIC_HEADERS

    async def build_register_session_key_tx(
        self,
        params: PublicBuildRegisterSessionKeyTxParamsSchema,
    ) -> PublicBuildRegisterSessionKeyTxResultSchema:
        """
        Build a signable transaction params dictionary.
        """

        url = self._endpoints.build_register_session_key_tx
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicBuildRegisterSessionKeyTxResultSchema)
        return result

    async def register_session_key(
        self,
        params: PublicRegisterSessionKeyParamsSchema,
    ) -> PublicRegisterSessionKeyResultSchema:
        """
        Register or update expiry of an existing session key.

        Currently, this only supports creating admin level session keys.

        Keys with fewer permissions are registered via `/register_scoped_session_key`

        Expiries updated on admin session keys may not happen immediately due to waiting
        for the onchain transaction to settle.
        """

        url = self._endpoints.register_session_key
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicRegisterSessionKeyResultSchema)
        return result

    async def deregister_session_key(
        self,
        params: PublicDeregisterSessionKeyParamsSchema,
    ) -> PublicDeregisterSessionKeyResultSchema:
        """
        Used for de-registering admin scoped keys. For other scopes, use
        `/edit_session_key`.
        """

        url = self._endpoints.deregister_session_key
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicDeregisterSessionKeyResultSchema)
        return result

    async def login(
        self,
        params: PublicLoginParamsSchema,
    ) -> List[int]:
        """
        Authenticate a websocket connection. Unavailable via HTTP.
        """

        url = self._endpoints.login
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, list[int])
        return result

    async def statistics(
        self,
        params: PublicStatisticsParamsSchema,
    ) -> PublicStatisticsResultSchema:
        """
        Get statistics for a specific instrument or instrument type
        """

        url = self._endpoints.statistics
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicStatisticsResultSchema)
        return result

    async def get_all_currencies(
        self,
        params: PublicGetAllCurrenciesParamsSchema,
    ) -> List[CurrencyDetailedResponseSchema]:
        """
        Get all active currencies with their spot price, spot price 24hrs ago.

        For real-time updates, recommend using channels -> ticker or orderbook.
        """

        url = self._endpoints.get_all_currencies
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, list[CurrencyDetailedResponseSchema])
        return result

    async def get_currency(
        self,
        params: PublicGetCurrencyParamsSchema,
    ) -> PublicGetCurrencyResultSchema:
        """
        Get currency related risk params, spot price 24hrs ago and lending details for a
        specific currency.
        """

        url = self._endpoints.get_currency
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicGetCurrencyResultSchema)
        return result

    async def get_instrument(
        self,
        params: PublicGetInstrumentParamsSchema,
    ) -> PublicGetInstrumentResultSchema:
        """
        Get single instrument by asset name
        """

        url = self._endpoints.get_instrument
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicGetInstrumentResultSchema)
        return result

    async def get_all_instruments(
        self,
        params: PublicGetAllInstrumentsParamsSchema,
    ) -> PublicGetAllInstrumentsResultSchema:
        """
        Get a paginated history of all instruments
        """

        url = self._endpoints.get_all_instruments
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicGetAllInstrumentsResultSchema)
        return result

    async def get_instruments(
        self,
        params: PublicGetInstrumentsParamsSchema,
    ) -> List[InstrumentPublicResponseSchema]:
        """
        Get all active instruments for a given `currency` and `type`.
        """

        url = self._endpoints.get_instruments
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, list[InstrumentPublicResponseSchema])
        return result

    async def get_ticker(
        self,
        params: PublicGetTickerParamsSchema,
    ) -> PublicGetTickerResultSchema:
        """
        Get ticker information (best bid / ask, instrument contraints, fees info, etc.)
        for a single instrument

        DEPRECATION NOTICE: This RPC is deprecated in favor of `get_tickers` on Dec 1,
        2025.
        """

        url = self._endpoints.get_ticker
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicGetTickerResultSchema)
        return result

    async def get_tickers(
        self,
        params: PublicGetTickersParamsSchema,
    ) -> PublicGetTickersResultSchema:
        """
        Get tickers information (best bid / ask, stats, etc.) for a multiple
        instruments.

        For options: currency is required and expiry_date is required.

        For perps: currency is optional, expiry_date will throw an error.

        For erc20s: currency is optional, expiry_date will throw an error.

        For most up to date stream of tickers, use the
        `ticker.<instrument_name>.<interval>` channels.
        """

        url = self._endpoints.get_tickers
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicGetTickersResultSchema)
        return result

    async def get_latest_signed_feeds(
        self,
        params: PublicGetLatestSignedFeedsParamsSchema,
    ) -> PublicGetLatestSignedFeedsResultSchema:
        """
        Get latest signed data feeds
        """

        url = self._endpoints.get_latest_signed_feeds
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicGetLatestSignedFeedsResultSchema)
        return result

    async def get_option_settlement_prices(
        self,
        params: PublicGetOptionSettlementPricesParamsSchema,
    ) -> PublicGetOptionSettlementPricesResultSchema:
        """
        Get settlement prices by expiry for each currency
        """

        url = self._endpoints.get_option_settlement_prices
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicGetOptionSettlementPricesResultSchema)
        return result

    async def get_spot_feed_history(
        self,
        params: PublicGetSpotFeedHistoryParamsSchema,
    ) -> PublicGetSpotFeedHistoryResultSchema:
        """
        Get spot feed history by currency

        DB: read replica
        """

        url = self._endpoints.get_spot_feed_history
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicGetSpotFeedHistoryResultSchema)
        return result

    async def get_spot_feed_history_candles(
        self,
        params: PublicGetSpotFeedHistoryCandlesParamsSchema,
    ) -> PublicGetSpotFeedHistoryCandlesResultSchema:
        """
        Get spot feed history candles by currency

        DB: read replica
        """

        url = self._endpoints.get_spot_feed_history_candles
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicGetSpotFeedHistoryCandlesResultSchema)
        return result

    async def get_funding_rate_history(
        self,
        params: PublicGetFundingRateHistoryParamsSchema,
    ) -> PublicGetFundingRateHistoryResultSchema:
        """
        Get funding rate history. Start timestamp is restricted to at most 30 days ago.

        End timestamp greater than current time will be truncated to current time.

        Zero start timestamp is allowed and will default to 30 days from the end
        timestamp.

        DB: read replica
        """

        url = self._endpoints.get_funding_rate_history
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicGetFundingRateHistoryResultSchema)
        return result

    async def get_trade_history(
        self,
        params: PublicGetTradeHistoryParamsSchema,
    ) -> PublicGetTradeHistoryResultSchema:
        """
        Get trade history for a subaccount, with filter parameters.
        """

        url = self._endpoints.get_trade_history
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicGetTradeHistoryResultSchema)
        return result

    async def get_option_settlement_history(
        self,
        params: PublicGetOptionSettlementHistoryParamsSchema,
    ) -> PublicGetOptionSettlementHistoryResultSchema:
        """
        Get expired option settlement history for a subaccount
        """

        url = self._endpoints.get_option_settlement_history
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicGetOptionSettlementHistoryResultSchema)
        return result

    async def get_liquidation_history(
        self,
        params: PublicGetLiquidationHistoryParamsSchema,
    ) -> PublicGetLiquidationHistoryResultSchema:
        """
        Returns a paginated liquidation history for all subaccounts. Note that the
        pagination is based on the number of

        raw events that include bids, auction start, and auction end events. This means
        that the count returned in the

        pagination info will be larger than the total number of auction events. This
        also means the number of returned

        auctions per page will be smaller than the supplied `page_size`.
        """

        url = self._endpoints.get_liquidation_history
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicGetLiquidationHistoryResultSchema)
        return result

    async def get_interest_rate_history(
        self,
        params: PublicGetInterestRateHistoryParamsSchema,
    ) -> PublicGetInterestRateHistoryResultSchema:
        """
        Get latest USDC interest rate history
        """

        url = self._endpoints.get_interest_rate_history
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicGetInterestRateHistoryResultSchema)
        return result

    async def get_transaction(
        self,
        params: PublicGetTransactionParamsSchema,
    ) -> PublicGetTransactionResultSchema:
        """
        Used for getting a transaction by its transaction id
        """

        url = self._endpoints.get_transaction
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicGetTransactionResultSchema)
        return result

    async def get_margin(
        self,
        params: PublicGetMarginParamsSchema,
    ) -> PublicGetMarginResultSchema:
        """
        Calculates margin for a given portfolio and (optionally) a simulated state
        change.

        Does not take into account open orders margin requirements.public/withdraw_debug
        """

        url = self._endpoints.get_margin
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicGetMarginResultSchema)
        return result

    async def margin_watch(
        self,
        params: PublicMarginWatchParamsSchema,
    ) -> PublicMarginWatchResultSchema:
        """
        Calculates MtM and maintenance margin for a given subaccount.
        """

        url = self._endpoints.margin_watch
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicMarginWatchResultSchema)
        return result

    async def get_vault_share(
        self,
        params: PublicGetVaultShareParamsSchema,
    ) -> PublicGetVaultShareResultSchema:
        """
        Gets the value of a vault's token against the base currency, underlying
        currency, and USD for a timestamp range.

        The name of the vault from the Vault proxy contract is used to fetch the vault's
        value.
        """

        url = self._endpoints.get_vault_share
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicGetVaultShareResultSchema)
        return result

    async def get_vault_statistics(
        self,
        params: PublicGetVaultStatisticsParamsSchema,
    ) -> List[VaultStatisticsResponseSchema]:
        """
        Gets all the latest vault shareRate, totalSupply and TVL values for all vaults.

        For data on shares across chains, use public/get_vault_assets.
        """

        url = self._endpoints.get_vault_statistics
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, list[VaultStatisticsResponseSchema])
        return result

    async def get_vault_balances(
        self,
        params: PublicGetVaultBalancesParamsSchema,
    ) -> List[VaultBalanceResponseSchema]:
        """
        Get all vault assets held by user. Can query by smart contract address or smart
        contract owner.

        Includes VaultERC20Pool balances
        """

        url = self._endpoints.get_vault_balances
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, list[VaultBalanceResponseSchema])
        return result

    async def create_subaccount_debug(
        self,
        params: PublicCreateSubaccountDebugParamsSchema,
    ) -> PublicCreateSubaccountDebugResultSchema:
        """
        Used for debugging only, do not use in production. Will return the incremental
        encoded and hashed data.

        See guides in Documentation for more.
        """

        url = self._endpoints.create_subaccount_debug
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicCreateSubaccountDebugResultSchema)
        return result

    async def deposit_debug(
        self,
        params: PublicDepositDebugParamsSchema,
    ) -> PublicDepositDebugResultSchema:
        """
        Used for debugging only, do not use in production. Will return the incremental
        encoded and hashed data.

        See guides in Documentation for more.
        """

        url = self._endpoints.deposit_debug
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicDepositDebugResultSchema)
        return result

    async def withdraw_debug(
        self,
        params: PublicWithdrawDebugParamsSchema,
    ) -> PublicWithdrawDebugResultSchema:
        """
        Used for debugging only, do not use in production. Will return the incremental
        encoded and hashed data.

        See guides in Documentation for more.
        """

        url = self._endpoints.withdraw_debug
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicWithdrawDebugResultSchema)
        return result

    async def send_quote_debug(
        self,
        params: PublicSendQuoteDebugParamsSchema,
    ) -> PublicSendQuoteDebugResultSchema:
        """
        Sends a quote in response to an RFQ request.

        The legs supplied in the parameters must exactly match those in the RFQ.
        """

        url = self._endpoints.send_quote_debug
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicSendQuoteDebugResultSchema)
        return result

    async def execute_quote_debug(
        self,
        params: PublicExecuteQuoteDebugParamsSchema,
    ) -> PublicExecuteQuoteDebugResultSchema:
        """
        Sends a quote in response to an RFQ request.

        The legs supplied in the parameters must exactly match those in the RFQ.
        """

        url = self._endpoints.execute_quote_debug
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicExecuteQuoteDebugResultSchema)
        return result

    async def get_time(
        self,
        params: PublicGetTimeParamsSchema,
    ) -> int:
        url = self._endpoints.get_time
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, int)
        return result

    async def get_live_incidents(
        self,
        params: PublicGetLiveIncidentsParamsSchema,
    ) -> PublicGetLiveIncidentsResultSchema:
        url = self._endpoints.get_live_incidents
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicGetLiveIncidentsResultSchema)
        return result

    async def get_maker_programs(
        self,
        params: PublicGetMakerProgramsParamsSchema,
    ) -> List[ProgramResponseSchema]:
        """
        Get all maker programs, including past / historical ones.
        """

        url = self._endpoints.get_maker_programs
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, list[ProgramResponseSchema])
        return result

    async def get_maker_program_scores(
        self,
        params: PublicGetMakerProgramScoresParamsSchema,
    ) -> PublicGetMakerProgramScoresResultSchema:
        """
        Get scores breakdown by maker program.
        """

        url = self._endpoints.get_maker_program_scores
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicGetMakerProgramScoresResultSchema)
        return result

    async def get_referral_performance(
        self,
        params: PublicGetReferralPerformanceParamsSchema,
    ) -> PublicGetReferralPerformanceResultSchema:
        """
        Get the broker program referral performance. Epochs are 28 days long.
        """

        url = self._endpoints.get_referral_performance
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PublicGetReferralPerformanceResultSchema)
        return result


class AsyncPrivateAPI:
    """Async private API methods"""

    def __init__(self, session: AsyncHTTPSession, config: EnvConfig, auth: AuthContext):
        self._session = session
        self._config = config
        self._auth = auth
        self._endpoints = PrivateEndpoints(config.base_url)

    @property
    def headers(self) -> dict:
        return {**PUBLIC_HEADERS, **self._auth.signed_headers}

    async def get_account(
        self,
        params: PrivateGetAccountParamsSchema,
    ) -> PrivateGetAccountResultSchema:
        """
        Account details getter

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_account
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetAccountResultSchema)
        return result

    async def create_subaccount(
        self,
        params: PrivateCreateSubaccountParamsSchema,
    ) -> PrivateCreateSubaccountResultSchema:
        """
        Create a new subaccount under a given wallet, and deposit an asset into that
        subaccount.

        See `public/create_subaccount_debug` for debugging invalid signature issues or
        go to guides in Documentation.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.create_subaccount
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateCreateSubaccountResultSchema)
        return result

    async def get_subaccount(
        self,
        params: PrivateGetSubaccountParamsSchema,
    ) -> PrivateGetSubaccountResultSchema:
        """
        Get open orders, active positions, and collaterals of a subaccount

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_subaccount
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetSubaccountResultSchema)
        return result

    async def get_subaccounts(
        self,
        params: PrivateGetSubaccountsParamsSchema,
    ) -> PrivateGetSubaccountsResultSchema:
        """
        Get all subaccounts of an account / wallet

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_subaccounts
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetSubaccountsResultSchema)
        return result

    async def get_all_portfolios(
        self,
        params: PrivateGetAllPortfoliosParamsSchema,
    ) -> List[PrivateGetSubaccountResultSchema]:
        """
        Get all portfolios of a wallet

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_all_portfolios
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, list[PrivateGetSubaccountResultSchema])
        return result

    async def change_subaccount_label(
        self,
        params: PrivateChangeSubaccountLabelParamsSchema,
    ) -> PrivateChangeSubaccountLabelResultSchema:
        """
        Change a user defined label for given subaccount

        Required minimum session key permission level is `account`
        """

        url = self._endpoints.change_subaccount_label
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateChangeSubaccountLabelResultSchema)
        return result

    async def get_notifications(
        self,
        params: PrivateGetNotificationsParamsSchema,
    ) -> PrivateGetNotificationsResultSchema:
        """
        Get the notifications related to a subaccount.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_notifications
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetNotificationsResultSchema)
        return result

    async def update_notifications(
        self,
        params: PrivateUpdateNotificationsParamsSchema,
    ) -> PrivateUpdateNotificationsResultSchema:
        """
        RPC to mark specified notifications as seen for a given subaccount.

        Required minimum session key permission level is `account`
        """

        url = self._endpoints.update_notifications
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateUpdateNotificationsResultSchema)
        return result

    async def deposit(
        self,
        params: PrivateDepositParamsSchema,
    ) -> PrivateDepositResultSchema:
        """
        Deposit an asset to a subaccount.

        See `public/deposit_debug' for debugging invalid signature issues or go to
        guides in Documentation.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.deposit
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateDepositResultSchema)
        return result

    async def withdraw(
        self,
        params: PrivateWithdrawParamsSchema,
    ) -> PrivateWithdrawResultSchema:
        """
        Withdraw an asset to wallet.

        See `public/withdraw_debug` for debugging invalid signature issues or go to
        guides in Documentation.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.withdraw
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateWithdrawResultSchema)
        return result

    async def transfer_erc20(
        self,
        params: PrivateTransferErc20ParamsSchema,
    ) -> PrivateTransferErc20ResultSchema:
        """
        Transfer ERC20 assets from one subaccount to another (e.g. USDC or ETH).

        For transfering positions (e.g. options or perps), use
        `private/transfer_position` instead.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.transfer_erc20
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateTransferErc20ResultSchema)
        return result

    async def transfer_position(
        self,
        params: PrivateTransferPositionParamsSchema,
    ) -> PrivateTransferPositionResultSchema:
        """
        Transfers a positions from one subaccount to another, owned by the same wallet.

        The transfer is executed as a pair of orders crossing each other.

        The maker order is created first, followed by a taker order crossing it.

        The order amounts, limit prices and instrument name must be the same for both
        orders.

        Fee is not charged and a zero `max_fee` must be signed.

        The maker order is forcibly considered to be `reduce_only`, meaning it can only
        reduce the position size.

        History: For position transfer history, use the `private/get_trade_history` RPC
        (not `private/get_erc20_transfer_history`).

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.transfer_position
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateTransferPositionResultSchema)
        return result

    async def transfer_positions(
        self,
        params: PrivateTransferPositionsParamsSchema,
    ) -> PrivateTransferPositionsResultSchema:
        """
        Transfers multiple positions from one subaccount to another, owned by the same
        wallet.

        The transfer is executed as a an RFQ. A mock RFQ is first created from the taker
        parameters, followed by a maker quote and a taker execute.

        The leg amounts, prices and instrument name must be the same in both param
        payloads.

        Fee is not charged and a zero `max_fee` must be signed.

        Every leg in the transfer must be a position reduction for either maker or taker
        (or both).

        History: for position transfer history, use the `private/get_trade_history` RPC
        (not `private/get_erc20_transfer_history`).

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.transfer_positions
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateTransferPositionsResultSchema)
        return result

    async def order(
        self,
        params: PrivateOrderParamsSchema,
    ) -> PrivateOrderResultSchema:
        """
        Create a new order.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.order
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateOrderResultSchema)
        return result

    async def replace(
        self,
        params: PrivateReplaceParamsSchema,
    ) -> PrivateReplaceResultSchema:
        """
        Cancel an existing order with nonce or order_id and create new order with
        different order_id in a single RPC call.

        If the cancel fails, the new order will not be created.

        If the cancel succeeds but the new order fails, the old order will still be
        cancelled.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.replace
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateReplaceResultSchema)
        return result

    async def order_debug(
        self,
        params: PrivateOrderDebugParamsSchema,
    ) -> PrivateOrderDebugResultSchema:
        """
        Debug a new order

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.order_debug
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateOrderDebugResultSchema)
        return result

    async def get_order(
        self,
        params: PrivateGetOrderParamsSchema,
    ) -> PrivateGetOrderResultSchema:
        """
        Get state of an order by order id.  If the order is an MMP order, it will not
        show up if cancelled/expired.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_order
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetOrderResultSchema)
        return result

    async def get_orders(
        self,
        params: PrivateGetOrdersParamsSchema,
    ) -> PrivateGetOrdersResultSchema:
        """
        Get orders for a subaccount, with optional filtering.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_orders
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetOrdersResultSchema)
        return result

    async def get_open_orders(
        self,
        params: PrivateGetOpenOrdersParamsSchema,
    ) -> PrivateGetOpenOrdersResultSchema:
        """
        Get all open orders of a subacccount

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_open_orders
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetOpenOrdersResultSchema)
        return result

    async def cancel(
        self,
        params: PrivateCancelParamsSchema,
    ) -> PrivateCancelResultSchema:
        """
        Cancel a single order.

        Other `private/cancel_*` routes are available through both REST and WebSocket.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.cancel
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateCancelResultSchema)
        return result

    async def cancel_all(
        self,
        params: PrivateCancelAllParamsSchema,
    ) -> Result:
        """
        Cancel all orders for this instrument.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.cancel_all
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, Result)
        return result

    async def cancel_by_label(
        self,
        params: PrivateCancelByLabelParamsSchema,
    ) -> PrivateCancelByLabelResultSchema:
        """
        Cancel all open orders for a given subaccount and a given label.  If
        instrument_name is provided, only orders for that instrument will be cancelled.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.cancel_by_label
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateCancelByLabelResultSchema)
        return result

    async def cancel_by_nonce(
        self,
        params: PrivateCancelByNonceParamsSchema,
    ) -> PrivateCancelByNonceResultSchema:
        """
        Cancel a single order by nonce. Uses up that nonce if the order does not exist,
        so any future orders with that nonce will fail

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.cancel_by_nonce
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateCancelByNonceResultSchema)
        return result

    async def cancel_by_instrument(
        self,
        params: PrivateCancelByInstrumentParamsSchema,
    ) -> PrivateCancelByInstrumentResultSchema:
        """
        Cancel all orders for this instrument.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.cancel_by_instrument
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateCancelByInstrumentResultSchema)
        return result

    async def cancel_trigger_order(
        self,
        params: PrivateCancelTriggerOrderParamsSchema,
    ) -> PrivateCancelTriggerOrderResultSchema:
        """
        Cancels a trigger order.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.cancel_trigger_order
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateCancelTriggerOrderResultSchema)
        return result

    async def cancel_all_trigger_orders(
        self,
        params: PrivateCancelAllTriggerOrdersParamsSchema,
    ) -> Result:
        """
        Cancel all trigger orders for this subaccount.

        Also used by cancel_all in WS.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.cancel_all_trigger_orders
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, Result)
        return result

    async def get_order_history(
        self,
        params: PrivateGetOrderHistoryParamsSchema,
    ) -> PrivateGetOrderHistoryResultSchema:
        """
        Get order history for a subaccount

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_order_history
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetOrderHistoryResultSchema)
        return result

    async def get_trade_history(
        self,
        params: PrivateGetTradeHistoryParamsSchema,
    ) -> PrivateGetTradeHistoryResultSchema:
        """
        Get trade history for a subaccount, with filter parameters.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_trade_history
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetTradeHistoryResultSchema)
        return result

    async def get_deposit_history(
        self,
        params: PrivateGetDepositHistoryParamsSchema,
    ) -> PrivateGetDepositHistoryResultSchema:
        """
        Get subaccount deposit history.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_deposit_history
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetDepositHistoryResultSchema)
        return result

    async def get_withdrawal_history(
        self,
        params: PrivateGetWithdrawalHistoryParamsSchema,
    ) -> PrivateGetWithdrawalHistoryResultSchema:
        """
        Get subaccount withdrawal history.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_withdrawal_history
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetWithdrawalHistoryResultSchema)
        return result

    async def send_rfq(
        self,
        params: PrivateSendRfqParamsSchema,
    ) -> PrivateSendRfqResultSchema:
        """
        Requests two-sided quotes from participating market makers.

        Required minimum session key permission level is `account`
        """

        url = self._endpoints.send_rfq
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateSendRfqResultSchema)
        return result

    async def cancel_rfq(
        self,
        params: PrivateCancelRfqParamsSchema,
    ) -> Result:
        """
        Cancels a single RFQ by id.

        Required minimum session key permission level is `account`
        """

        url = self._endpoints.cancel_rfq
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, Result)
        return result

    async def cancel_batch_rfqs(
        self,
        params: PrivateCancelBatchRfqsParamsSchema,
    ) -> PrivateCancelBatchRfqsResultSchema:
        """
        Cancels RFQs given optional filters.

        If no filters are provided, all RFQs for the subaccount are cancelled.

        All filters are combined using `AND` logic, so mutually exclusive filters will
        result in no RFQs being cancelled.

        Required minimum session key permission level is `account`
        """

        url = self._endpoints.cancel_batch_rfqs
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateCancelBatchRfqsResultSchema)
        return result

    async def get_rfqs(
        self,
        params: PrivateGetRfqsParamsSchema,
    ) -> PrivateGetRfqsResultSchema:
        """
        Retrieves a list of RFQs matching filter criteria. Takers can use this to get
        their open RFQs, RFQ history, etc.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_rfqs
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetRfqsResultSchema)
        return result

    async def poll_rfqs(
        self,
        params: PrivatePollRfqsParamsSchema,
    ) -> PrivatePollRfqsResultSchema:
        """
        Retrieves a list of RFQs matching filter criteria. Market makers can use this to
        poll RFQs directed to them.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.poll_rfqs
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivatePollRfqsResultSchema)
        return result

    async def send_quote(
        self,
        params: PrivateSendQuoteParamsSchema,
    ) -> PrivateSendQuoteResultSchema:
        """
        Sends a quote in response to an RFQ request.

        The legs supplied in the parameters must exactly match those in the RFQ.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.send_quote
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateSendQuoteResultSchema)
        return result

    async def replace_quote(
        self,
        params: PrivateReplaceQuoteParamsSchema,
    ) -> PrivateReplaceQuoteResultSchema:
        """
        Cancel an existing quote with nonce or quote_id and create new quote with
        different quote_id in a single RPC call.

        If the cancel fails, the new quote will not be created.

        If the cancel succeeds but the new quote fails, the old quote will still be
        cancelled.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.replace_quote
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateReplaceQuoteResultSchema)
        return result

    async def cancel_quote(
        self,
        params: PrivateCancelQuoteParamsSchema,
    ) -> PrivateCancelQuoteResultSchema:
        """
        Cancels an open quote.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.cancel_quote
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateCancelQuoteResultSchema)
        return result

    async def cancel_batch_quotes(
        self,
        params: PrivateCancelBatchQuotesParamsSchema,
    ) -> PrivateCancelBatchQuotesResultSchema:
        """
        Cancels quotes given optional filters. If no filters are provided, all quotes by
        the subaccount are cancelled.

        All filters are combined using `AND` logic, so mutually exclusive filters will
        result in no quotes being cancelled.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.cancel_batch_quotes
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateCancelBatchQuotesResultSchema)
        return result

    async def get_quotes(
        self,
        params: PrivateGetQuotesParamsSchema,
    ) -> PrivateGetQuotesResultSchema:
        """
        Retrieves a list of quotes matching filter criteria.

        Market makers can use this to get their open quotes, quote history, etc.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_quotes
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetQuotesResultSchema)
        return result

    async def poll_quotes(
        self,
        params: PrivatePollQuotesParamsSchema,
    ) -> PrivatePollQuotesResultSchema:
        """
        Retrieves a list of quotes matching filter criteria.

        Takers can use this to poll open quotes that they can fill against their open
        RFQs.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.poll_quotes
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivatePollQuotesResultSchema)
        return result

    async def execute_quote(
        self,
        params: PrivateExecuteQuoteParamsSchema,
    ) -> PrivateExecuteQuoteResultSchema:
        """
        Executes a quote.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.execute_quote
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateExecuteQuoteResultSchema)
        return result

    async def rfq_get_best_quote(
        self,
        params: PrivateRfqGetBestQuoteParamsSchema,
    ) -> PrivateRfqGetBestQuoteResultSchema:
        """
        Performs a "dry run" on an RFQ, returning the estimated fee and whether the
        trade is expected to pass.

        Should any exception be raised in the process of evaluating the trade, a
        standard RPC error will be returned

        with the error details.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.rfq_get_best_quote
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateRfqGetBestQuoteResultSchema)
        return result

    async def get_margin(
        self,
        params: PrivateGetMarginParamsSchema,
    ) -> PrivateGetMarginResultSchema:
        """
        Calculates margin for a given subaccount and (optionally) a simulated state
        change. Does not take into account

        open orders margin requirements.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_margin
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetMarginResultSchema)
        return result

    async def get_collaterals(
        self,
        params: PrivateGetCollateralsParamsSchema,
    ) -> PrivateGetCollateralsResultSchema:
        """
        Get collaterals of a subaccount

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_collaterals
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetCollateralsResultSchema)
        return result

    async def get_positions(
        self,
        params: PrivateGetPositionsParamsSchema,
    ) -> PrivateGetPositionsResultSchema:
        """
        Get active positions of a subaccount

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_positions
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetPositionsResultSchema)
        return result

    async def get_option_settlement_history(
        self,
        params: PrivateGetOptionSettlementHistoryParamsSchema,
    ) -> PrivateGetOptionSettlementHistoryResultSchema:
        """
        Get expired option settlement history for a subaccount

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_option_settlement_history
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetOptionSettlementHistoryResultSchema)
        return result

    async def get_subaccount_value_history(
        self,
        params: PrivateGetSubaccountValueHistoryParamsSchema,
    ) -> PrivateGetSubaccountValueHistoryResultSchema:
        """
        Get the value history of a subaccount

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_subaccount_value_history
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetSubaccountValueHistoryResultSchema)
        return result

    async def expired_and_cancelled_history(
        self,
        params: PrivateExpiredAndCancelledHistoryParamsSchema,
    ) -> PrivateExpiredAndCancelledHistoryResultSchema:
        """
        Generate a list of URLs to retrieve archived orders

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.expired_and_cancelled_history
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateExpiredAndCancelledHistoryResultSchema)
        return result

    async def get_funding_history(
        self,
        params: PrivateGetFundingHistoryParamsSchema,
    ) -> PrivateGetFundingHistoryResultSchema:
        """
        Get subaccount funding history.

        DB: read replica

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_funding_history
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetFundingHistoryResultSchema)
        return result

    async def get_interest_history(
        self,
        params: PrivateGetInterestHistoryParamsSchema,
    ) -> PrivateGetInterestHistoryResultSchema:
        """
        Get subaccount interest payment history.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_interest_history
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetInterestHistoryResultSchema)
        return result

    async def get_erc20_transfer_history(
        self,
        params: PrivateGetErc20TransferHistoryParamsSchema,
    ) -> PrivateGetErc20TransferHistoryResultSchema:
        """
        Get subaccount erc20 transfer history.

        Position transfers (e.g. options or perps) are treated as trades. Use
        `private/get_trade_history` for position transfer history.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_erc20_transfer_history
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetErc20TransferHistoryResultSchema)
        return result

    async def get_liquidation_history(
        self,
        params: PrivateGetLiquidationHistoryParamsSchema,
    ) -> List[AuctionResultSchema]:
        """
        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_liquidation_history
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, list[AuctionResultSchema])
        return result

    async def liquidate(
        self,
        params: PrivateLiquidateParamsSchema,
    ) -> PrivateLiquidateResultSchema:
        """
        Liquidates a given subaccount using funds from another subaccount. This endpoint
        has a few limitations:

        1. If succesful, the RPC will freeze the caller's subaccount until the bid is
        settled or is reverted on chain.

        2. The caller's subaccount must not have any open orders.

        3. The caller's subaccount must have enough withdrawable cash to cover the bid
        and the buffer margin requirements.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.liquidate
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateLiquidateResultSchema)
        return result

    async def get_liquidator_history(
        self,
        params: PrivateGetLiquidatorHistoryParamsSchema,
    ) -> PrivateGetLiquidatorHistoryResultSchema:
        """
        Returns a paginated history of auctions that the subaccount has participated in
        as a liquidator.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_liquidator_history
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateGetLiquidatorHistoryResultSchema)
        return result

    async def session_keys(
        self,
        params: PrivateSessionKeysParamsSchema,
    ) -> PrivateSessionKeysResultSchema:
        """
        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.session_keys
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateSessionKeysResultSchema)
        return result

    async def edit_session_key(
        self,
        params: PrivateEditSessionKeyParamsSchema,
    ) -> PrivateEditSessionKeyResultSchema:
        """
        Edits session key parameters such as label and IP whitelist.

        For non-admin keys you can also toggle whether to disable a particular key.

        Disabling non-admin keys must be done through /deregister_session_key

        Required minimum session key permission level is `account`
        """

        url = self._endpoints.edit_session_key
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateEditSessionKeyResultSchema)
        return result

    async def register_scoped_session_key(
        self,
        params: PrivateRegisterScopedSessionKeyParamsSchema,
    ) -> PrivateRegisterScopedSessionKeyResultSchema:
        """
        Registers a new session key bounded to a scope without a transaction attached.

        If you want to register an admin key, you must provide a signed raw transaction.

        Required minimum session key permission level is `account`
        """

        url = self._endpoints.register_scoped_session_key
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateRegisterScopedSessionKeyResultSchema)
        return result

    async def get_mmp_config(
        self,
        params: PrivateGetMmpConfigParamsSchema,
    ) -> List[MMPConfigResultSchema]:
        """
        Get the current mmp config for a subaccount (optionally filtered by currency)

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_mmp_config
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, list[MMPConfigResultSchema])
        return result

    async def set_mmp_config(
        self,
        params: PrivateSetMmpConfigParamsSchema,
    ) -> PrivateSetMmpConfigResultSchema:
        """
        Set the mmp config for the subaccount and currency

        Required minimum session key permission level is `account`
        """

        url = self._endpoints.set_mmp_config
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, PrivateSetMmpConfigResultSchema)
        return result

    async def reset_mmp(
        self,
        params: PrivateResetMmpParamsSchema,
    ) -> Result:
        """
        Resets (unfreezes) the mmp state for a subaccount (optionally filtered by
        currency)

        Required minimum session key permission level is `account`
        """

        url = self._endpoints.reset_mmp
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, Result)
        return result

    async def set_cancel_on_disconnect(
        self,
        params: PrivateSetCancelOnDisconnectParamsSchema,
    ) -> Result:
        """
        Enables cancel on disconnect for the account

        Required minimum session key permission level is `account`
        """

        url = self._endpoints.set_cancel_on_disconnect
        data = encode_json_exclude_none(params)
        message = await self._session._send_request(url, data, headers=self.headers)
        envelope = decode_envelope(message)
        result = decode_result(envelope, Result)
        return result
