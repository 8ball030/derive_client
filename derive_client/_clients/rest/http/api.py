"""Auto-generated API classes from OpenAPI spec"""

from derive_client._clients.rest.endpoints import PrivateEndpoints, PublicEndpoints
from derive_client._clients.rest.http.session import HTTPSession
from derive_client._clients.utils import AuthContext, encode_json_exclude_none, try_cast_response
from derive_client.config import PUBLIC_HEADERS
from derive_client.data_types import EnvConfig
from derive_client.data_types.generated_models import (
    PrivateCancelAllParamsSchema,
    PrivateCancelAllResponseSchema,
    PrivateCancelAllTriggerOrdersParamsSchema,
    PrivateCancelAllTriggerOrdersResponseSchema,
    PrivateCancelBatchQuotesParamsSchema,
    PrivateCancelBatchQuotesResponseSchema,
    PrivateCancelBatchRfqsParamsSchema,
    PrivateCancelBatchRfqsResponseSchema,
    PrivateCancelByInstrumentParamsSchema,
    PrivateCancelByInstrumentResponseSchema,
    PrivateCancelByLabelParamsSchema,
    PrivateCancelByLabelResponseSchema,
    PrivateCancelByNonceParamsSchema,
    PrivateCancelByNonceResponseSchema,
    PrivateCancelParamsSchema,
    PrivateCancelQuoteParamsSchema,
    PrivateCancelQuoteResponseSchema,
    PrivateCancelResponseSchema,
    PrivateCancelRfqParamsSchema,
    PrivateCancelRfqResponseSchema,
    PrivateCancelTriggerOrderParamsSchema,
    PrivateCancelTriggerOrderResponseSchema,
    PrivateChangeSubaccountLabelParamsSchema,
    PrivateChangeSubaccountLabelResponseSchema,
    PrivateCreateSubaccountParamsSchema,
    PrivateCreateSubaccountResponseSchema,
    PrivateDepositParamsSchema,
    PrivateDepositResponseSchema,
    PrivateEditSessionKeyParamsSchema,
    PrivateEditSessionKeyResponseSchema,
    PrivateExecuteQuoteParamsSchema,
    PrivateExecuteQuoteResponseSchema,
    PrivateExpiredAndCancelledHistoryParamsSchema,
    PrivateExpiredAndCancelledHistoryResponseSchema,
    PrivateGetAccountParamsSchema,
    PrivateGetAccountResponseSchema,
    PrivateGetAllPortfoliosParamsSchema,
    PrivateGetAllPortfoliosResponseSchema,
    PrivateGetCollateralsParamsSchema,
    PrivateGetCollateralsResponseSchema,
    PrivateGetDepositHistoryParamsSchema,
    PrivateGetDepositHistoryResponseSchema,
    PrivateGetErc20TransferHistoryParamsSchema,
    PrivateGetErc20TransferHistoryResponseSchema,
    PrivateGetFundingHistoryParamsSchema,
    PrivateGetFundingHistoryResponseSchema,
    PrivateGetInterestHistoryParamsSchema,
    PrivateGetInterestHistoryResponseSchema,
    PrivateGetLiquidationHistoryParamsSchema,
    PrivateGetLiquidationHistoryResponseSchema,
    PrivateGetLiquidatorHistoryParamsSchema,
    PrivateGetLiquidatorHistoryResponseSchema,
    PrivateGetMarginParamsSchema,
    PrivateGetMarginResponseSchema,
    PrivateGetMmpConfigParamsSchema,
    PrivateGetMmpConfigResponseSchema,
    PrivateGetNotificationsParamsSchema,
    PrivateGetNotificationsResponseSchema,
    PrivateGetOpenOrdersParamsSchema,
    PrivateGetOpenOrdersResponseSchema,
    PrivateGetOptionSettlementHistoryParamsSchema,
    PrivateGetOptionSettlementHistoryResponseSchema,
    PrivateGetOrderHistoryParamsSchema,
    PrivateGetOrderHistoryResponseSchema,
    PrivateGetOrderParamsSchema,
    PrivateGetOrderResponseSchema,
    PrivateGetOrdersParamsSchema,
    PrivateGetOrdersResponseSchema,
    PrivateGetPositionsParamsSchema,
    PrivateGetPositionsResponseSchema,
    PrivateGetQuotesParamsSchema,
    PrivateGetQuotesResponseSchema,
    PrivateGetRfqsParamsSchema,
    PrivateGetRfqsResponseSchema,
    PrivateGetSubaccountParamsSchema,
    PrivateGetSubaccountResponseSchema,
    PrivateGetSubaccountsParamsSchema,
    PrivateGetSubaccountsResponseSchema,
    PrivateGetSubaccountValueHistoryParamsSchema,
    PrivateGetSubaccountValueHistoryResponseSchema,
    PrivateGetTradeHistoryParamsSchema,
    PrivateGetTradeHistoryResponseSchema,
    PrivateGetWithdrawalHistoryParamsSchema,
    PrivateGetWithdrawalHistoryResponseSchema,
    PrivateLiquidateParamsSchema,
    PrivateLiquidateResponseSchema,
    PrivateOrderDebugParamsSchema,
    PrivateOrderDebugResponseSchema,
    PrivateOrderParamsSchema,
    PrivateOrderResponseSchema,
    PrivatePollQuotesParamsSchema,
    PrivatePollQuotesResponseSchema,
    PrivatePollRfqsParamsSchema,
    PrivatePollRfqsResponseSchema,
    PrivateRegisterScopedSessionKeyParamsSchema,
    PrivateRegisterScopedSessionKeyResponseSchema,
    PrivateReplaceParamsSchema,
    PrivateReplaceQuoteParamsSchema,
    PrivateReplaceQuoteResponseSchema,
    PrivateReplaceResponseSchema,
    PrivateResetMmpParamsSchema,
    PrivateResetMmpResponseSchema,
    PrivateRfqGetBestQuoteParamsSchema,
    PrivateRfqGetBestQuoteResponseSchema,
    PrivateSendQuoteParamsSchema,
    PrivateSendQuoteResponseSchema,
    PrivateSendRfqParamsSchema,
    PrivateSendRfqResponseSchema,
    PrivateSessionKeysParamsSchema,
    PrivateSessionKeysResponseSchema,
    PrivateSetCancelOnDisconnectParamsSchema,
    PrivateSetCancelOnDisconnectResponseSchema,
    PrivateSetMmpConfigParamsSchema,
    PrivateSetMmpConfigResponseSchema,
    PrivateTransferErc20ParamsSchema,
    PrivateTransferErc20ResponseSchema,
    PrivateTransferPositionParamsSchema,
    PrivateTransferPositionResponseSchema,
    PrivateTransferPositionsParamsSchema,
    PrivateTransferPositionsResponseSchema,
    PrivateUpdateNotificationsParamsSchema,
    PrivateUpdateNotificationsResponseSchema,
    PrivateWithdrawParamsSchema,
    PrivateWithdrawResponseSchema,
    PublicBuildRegisterSessionKeyTxParamsSchema,
    PublicBuildRegisterSessionKeyTxResponseSchema,
    PublicCreateSubaccountDebugParamsSchema,
    PublicCreateSubaccountDebugResponseSchema,
    PublicDepositDebugParamsSchema,
    PublicDepositDebugResponseSchema,
    PublicDeregisterSessionKeyParamsSchema,
    PublicDeregisterSessionKeyResponseSchema,
    PublicExecuteQuoteDebugParamsSchema,
    PublicExecuteQuoteDebugResponseSchema,
    PublicGetAllCurrenciesParamsSchema,
    PublicGetAllCurrenciesResponseSchema,
    PublicGetAllInstrumentsParamsSchema,
    PublicGetAllInstrumentsResponseSchema,
    PublicGetCurrencyParamsSchema,
    PublicGetCurrencyResponseSchema,
    PublicGetFundingRateHistoryParamsSchema,
    PublicGetFundingRateHistoryResponseSchema,
    PublicGetInstrumentParamsSchema,
    PublicGetInstrumentResponseSchema,
    PublicGetInstrumentsParamsSchema,
    PublicGetInstrumentsResponseSchema,
    PublicGetInterestRateHistoryParamsSchema,
    PublicGetInterestRateHistoryResponseSchema,
    PublicGetLatestSignedFeedsParamsSchema,
    PublicGetLatestSignedFeedsResponseSchema,
    PublicGetLiquidationHistoryParamsSchema,
    PublicGetLiquidationHistoryResponseSchema,
    PublicGetLiveIncidentsParamsSchema,
    PublicGetLiveIncidentsResponseSchema,
    PublicGetMakerProgramScoresParamsSchema,
    PublicGetMakerProgramScoresResponseSchema,
    PublicGetMakerProgramsParamsSchema,
    PublicGetMakerProgramsResponseSchema,
    PublicGetMarginParamsSchema,
    PublicGetMarginResponseSchema,
    PublicGetOptionSettlementHistoryParamsSchema,
    PublicGetOptionSettlementHistoryResponseSchema,
    PublicGetOptionSettlementPricesParamsSchema,
    PublicGetOptionSettlementPricesResponseSchema,
    PublicGetReferralPerformanceParamsSchema,
    PublicGetReferralPerformanceResponseSchema,
    PublicGetSpotFeedHistoryCandlesParamsSchema,
    PublicGetSpotFeedHistoryCandlesResponseSchema,
    PublicGetSpotFeedHistoryParamsSchema,
    PublicGetSpotFeedHistoryResponseSchema,
    PublicGetTickerParamsSchema,
    PublicGetTickerResponseSchema,
    PublicGetTickersParamsSchema,
    PublicGetTickersResponseSchema,
    PublicGetTimeParamsSchema,
    PublicGetTimeResponseSchema,
    PublicGetTradeHistoryParamsSchema,
    PublicGetTradeHistoryResponseSchema,
    PublicGetTransactionParamsSchema,
    PublicGetTransactionResponseSchema,
    PublicGetVaultBalancesParamsSchema,
    PublicGetVaultBalancesResponseSchema,
    PublicGetVaultShareParamsSchema,
    PublicGetVaultShareResponseSchema,
    PublicGetVaultStatisticsParamsSchema,
    PublicGetVaultStatisticsResponseSchema,
    PublicLoginParamsSchema,
    PublicLoginResponseSchema,
    PublicMarginWatchParamsSchema,
    PublicMarginWatchResponseSchema,
    PublicRegisterSessionKeyParamsSchema,
    PublicRegisterSessionKeyResponseSchema,
    PublicSendQuoteDebugParamsSchema,
    PublicSendQuoteDebugResponseSchema,
    PublicStatisticsParamsSchema,
    PublicStatisticsResponseSchema,
    PublicWithdrawDebugParamsSchema,
    PublicWithdrawDebugResponseSchema,
)


class PublicAPI:
    """public API methods"""

    def __init__(self, session: HTTPSession, config: EnvConfig):
        self._session = session
        self._config = config
        self._endpoints = PublicEndpoints(config.base_url)

    @property
    def headers(self) -> dict:
        return PUBLIC_HEADERS

    def build_register_session_key_tx(
        self,
        params: PublicBuildRegisterSessionKeyTxParamsSchema,
    ) -> PublicBuildRegisterSessionKeyTxResponseSchema:
        """
        Build a signable transaction params dictionary.
        """

        url = self._endpoints.build_register_session_key_tx
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicBuildRegisterSessionKeyTxResponseSchema)
        return response

    def register_session_key(
        self,
        params: PublicRegisterSessionKeyParamsSchema,
    ) -> PublicRegisterSessionKeyResponseSchema:
        """
        Register or update expiry of an existing session key.

        Currently, this only supports creating admin level session keys.

        Keys with fewer permissions are registered via `/register_scoped_session_key`

        Expiries updated on admin session keys may not happen immediately due to waiting
        for the onchain transaction to settle.
        """

        url = self._endpoints.register_session_key
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicRegisterSessionKeyResponseSchema)
        return response

    def deregister_session_key(
        self,
        params: PublicDeregisterSessionKeyParamsSchema,
    ) -> PublicDeregisterSessionKeyResponseSchema:
        """
        Used for de-registering admin scoped keys. For other scopes, use
        `/edit_session_key`.
        """

        url = self._endpoints.deregister_session_key
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicDeregisterSessionKeyResponseSchema)
        return response

    def login(
        self,
        params: PublicLoginParamsSchema,
    ) -> PublicLoginResponseSchema:
        """
        Authenticate a websocket connection. Unavailable via HTTP.
        """

        url = self._endpoints.login
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicLoginResponseSchema)
        return response

    def statistics(
        self,
        params: PublicStatisticsParamsSchema,
    ) -> PublicStatisticsResponseSchema:
        """
        Get statistics for a specific instrument or instrument type
        """

        url = self._endpoints.statistics
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicStatisticsResponseSchema)
        return response

    def get_all_currencies(
        self,
        params: PublicGetAllCurrenciesParamsSchema,
    ) -> PublicGetAllCurrenciesResponseSchema:
        """
        Get all active currencies with their spot price, spot price 24hrs ago.

        For real-time updates, recommend using channels -> ticker or orderbook.
        """

        url = self._endpoints.get_all_currencies
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetAllCurrenciesResponseSchema)
        return response

    def get_currency(
        self,
        params: PublicGetCurrencyParamsSchema,
    ) -> PublicGetCurrencyResponseSchema:
        """
        Get currency related risk params, spot price 24hrs ago and lending details for a
        specific currency.
        """

        url = self._endpoints.get_currency
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetCurrencyResponseSchema)
        return response

    def get_instrument(
        self,
        params: PublicGetInstrumentParamsSchema,
    ) -> PublicGetInstrumentResponseSchema:
        """
        Get single instrument by asset name
        """

        url = self._endpoints.get_instrument
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetInstrumentResponseSchema)
        return response

    def get_all_instruments(
        self,
        params: PublicGetAllInstrumentsParamsSchema,
    ) -> PublicGetAllInstrumentsResponseSchema:
        """
        Get a paginated history of all instruments
        """

        url = self._endpoints.get_all_instruments
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetAllInstrumentsResponseSchema)
        return response

    def get_instruments(
        self,
        params: PublicGetInstrumentsParamsSchema,
    ) -> PublicGetInstrumentsResponseSchema:
        """
        Get all active instruments for a given `currency` and `type`.
        """

        url = self._endpoints.get_instruments
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetInstrumentsResponseSchema)
        return response

    def get_ticker(
        self,
        params: PublicGetTickerParamsSchema,
    ) -> PublicGetTickerResponseSchema:
        """
        Get ticker information (best bid / ask, instrument contraints, fees info, etc.)
        for a single instrument

        DEPRECATION NOTICE: This RPC is deprecated in favor of `get_tickers` on Dec 1,
        2025.
        """

        url = self._endpoints.get_ticker
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetTickerResponseSchema)
        return response

    def get_tickers(
        self,
        params: PublicGetTickersParamsSchema,
    ) -> PublicGetTickersResponseSchema:
        """
        Get tickers information (best bid / ask, stats, etc.) for a multiple
        instruments.

        For most up to date stream of tickers, use the
        `ticker.<instrument_name>.<interval>` channels.
        """

        url = self._endpoints.get_tickers
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetTickersResponseSchema)
        return response

    def get_latest_signed_feeds(
        self,
        params: PublicGetLatestSignedFeedsParamsSchema,
    ) -> PublicGetLatestSignedFeedsResponseSchema:
        """
        Get latest signed data feeds
        """

        url = self._endpoints.get_latest_signed_feeds
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetLatestSignedFeedsResponseSchema)
        return response

    def get_option_settlement_prices(
        self,
        params: PublicGetOptionSettlementPricesParamsSchema,
    ) -> PublicGetOptionSettlementPricesResponseSchema:
        """
        Get settlement prices by expiry for each currency
        """

        url = self._endpoints.get_option_settlement_prices
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetOptionSettlementPricesResponseSchema)
        return response

    def get_spot_feed_history(
        self,
        params: PublicGetSpotFeedHistoryParamsSchema,
    ) -> PublicGetSpotFeedHistoryResponseSchema:
        """
        Get spot feed history by currency

        DB: read replica
        """

        url = self._endpoints.get_spot_feed_history
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetSpotFeedHistoryResponseSchema)
        return response

    def get_spot_feed_history_candles(
        self,
        params: PublicGetSpotFeedHistoryCandlesParamsSchema,
    ) -> PublicGetSpotFeedHistoryCandlesResponseSchema:
        """
        Get spot feed history candles by currency

        DB: read replica
        """

        url = self._endpoints.get_spot_feed_history_candles
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetSpotFeedHistoryCandlesResponseSchema)
        return response

    def get_funding_rate_history(
        self,
        params: PublicGetFundingRateHistoryParamsSchema,
    ) -> PublicGetFundingRateHistoryResponseSchema:
        """
        Get funding rate history. Start timestamp is restricted to at most 30 days ago.

        End timestamp greater than current time will be truncated to current time.

        Zero start timestamp is allowed and will default to 30 days from the end
        timestamp.

        DB: read replica
        """

        url = self._endpoints.get_funding_rate_history
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetFundingRateHistoryResponseSchema)
        return response

    def get_trade_history(
        self,
        params: PublicGetTradeHistoryParamsSchema,
    ) -> PublicGetTradeHistoryResponseSchema:
        """
        Get trade history for a subaccount, with filter parameters.
        """

        url = self._endpoints.get_trade_history
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetTradeHistoryResponseSchema)
        return response

    def get_option_settlement_history(
        self,
        params: PublicGetOptionSettlementHistoryParamsSchema,
    ) -> PublicGetOptionSettlementHistoryResponseSchema:
        """
        Get expired option settlement history for a subaccount
        """

        url = self._endpoints.get_option_settlement_history
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetOptionSettlementHistoryResponseSchema)
        return response

    def get_liquidation_history(
        self,
        params: PublicGetLiquidationHistoryParamsSchema,
    ) -> PublicGetLiquidationHistoryResponseSchema:
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
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetLiquidationHistoryResponseSchema)
        return response

    def get_interest_rate_history(
        self,
        params: PublicGetInterestRateHistoryParamsSchema,
    ) -> PublicGetInterestRateHistoryResponseSchema:
        """
        Get latest USDC interest rate history
        """

        url = self._endpoints.get_interest_rate_history
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetInterestRateHistoryResponseSchema)
        return response

    def get_transaction(
        self,
        params: PublicGetTransactionParamsSchema,
    ) -> PublicGetTransactionResponseSchema:
        """
        Used for getting a transaction by its transaction id
        """

        url = self._endpoints.get_transaction
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetTransactionResponseSchema)
        return response

    def get_margin(
        self,
        params: PublicGetMarginParamsSchema,
    ) -> PublicGetMarginResponseSchema:
        """
        Calculates margin for a given portfolio and (optionally) a simulated state
        change.

        Does not take into account open orders margin requirements.public/withdraw_debug
        """

        url = self._endpoints.get_margin
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetMarginResponseSchema)
        return response

    def margin_watch(
        self,
        params: PublicMarginWatchParamsSchema,
    ) -> PublicMarginWatchResponseSchema:
        """
        Calculates MtM and maintenance margin for a given subaccount.
        """

        url = self._endpoints.margin_watch
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicMarginWatchResponseSchema)
        return response

    def get_vault_share(
        self,
        params: PublicGetVaultShareParamsSchema,
    ) -> PublicGetVaultShareResponseSchema:
        """
        Gets the value of a vault's token against the base currency, underlying
        currency, and USD for a timestamp range.

        The name of the vault from the Vault proxy contract is used to fetch the vault's
        value.
        """

        url = self._endpoints.get_vault_share
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetVaultShareResponseSchema)
        return response

    def get_vault_statistics(
        self,
        params: PublicGetVaultStatisticsParamsSchema,
    ) -> PublicGetVaultStatisticsResponseSchema:
        """
        Gets all the latest vault shareRate, totalSupply and TVL values for all vaults.

        For data on shares across chains, use public/get_vault_assets.
        """

        url = self._endpoints.get_vault_statistics
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetVaultStatisticsResponseSchema)
        return response

    def get_vault_balances(
        self,
        params: PublicGetVaultBalancesParamsSchema,
    ) -> PublicGetVaultBalancesResponseSchema:
        """
        Get all vault assets held by user. Can query by smart contract address or smart
        contract owner.

        Includes VaultERC20Pool balances
        """

        url = self._endpoints.get_vault_balances
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetVaultBalancesResponseSchema)
        return response

    def create_subaccount_debug(
        self,
        params: PublicCreateSubaccountDebugParamsSchema,
    ) -> PublicCreateSubaccountDebugResponseSchema:
        """
        Used for debugging only, do not use in production. Will return the incremental
        encoded and hashed data.

        See guides in Documentation for more.
        """

        url = self._endpoints.create_subaccount_debug
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicCreateSubaccountDebugResponseSchema)
        return response

    def deposit_debug(
        self,
        params: PublicDepositDebugParamsSchema,
    ) -> PublicDepositDebugResponseSchema:
        """
        Used for debugging only, do not use in production. Will return the incremental
        encoded and hashed data.

        See guides in Documentation for more.
        """

        url = self._endpoints.deposit_debug
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicDepositDebugResponseSchema)
        return response

    def withdraw_debug(
        self,
        params: PublicWithdrawDebugParamsSchema,
    ) -> PublicWithdrawDebugResponseSchema:
        """
        Used for debugging only, do not use in production. Will return the incremental
        encoded and hashed data.

        See guides in Documentation for more.
        """

        url = self._endpoints.withdraw_debug
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicWithdrawDebugResponseSchema)
        return response

    def send_quote_debug(
        self,
        params: PublicSendQuoteDebugParamsSchema,
    ) -> PublicSendQuoteDebugResponseSchema:
        """
        Sends a quote in response to an RFQ request.

        The legs supplied in the parameters must exactly match those in the RFQ.
        """

        url = self._endpoints.send_quote_debug
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicSendQuoteDebugResponseSchema)
        return response

    def execute_quote_debug(
        self,
        params: PublicExecuteQuoteDebugParamsSchema,
    ) -> PublicExecuteQuoteDebugResponseSchema:
        """
        Sends a quote in response to an RFQ request.

        The legs supplied in the parameters must exactly match those in the RFQ.
        """

        url = self._endpoints.execute_quote_debug
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicExecuteQuoteDebugResponseSchema)
        return response

    def get_time(
        self,
        params: PublicGetTimeParamsSchema,
    ) -> PublicGetTimeResponseSchema:
        url = self._endpoints.get_time
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetTimeResponseSchema)
        return response

    def get_live_incidents(
        self,
        params: PublicGetLiveIncidentsParamsSchema,
    ) -> PublicGetLiveIncidentsResponseSchema:
        url = self._endpoints.get_live_incidents
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetLiveIncidentsResponseSchema)
        return response

    def get_maker_programs(
        self,
        params: PublicGetMakerProgramsParamsSchema,
    ) -> PublicGetMakerProgramsResponseSchema:
        """
        Get all maker programs, including past / historical ones.
        """

        url = self._endpoints.get_maker_programs
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetMakerProgramsResponseSchema)
        return response

    def get_maker_program_scores(
        self,
        params: PublicGetMakerProgramScoresParamsSchema,
    ) -> PublicGetMakerProgramScoresResponseSchema:
        """
        Get scores breakdown by maker program.
        """

        url = self._endpoints.get_maker_program_scores
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetMakerProgramScoresResponseSchema)
        return response

    def get_referral_performance(
        self,
        params: PublicGetReferralPerformanceParamsSchema,
    ) -> PublicGetReferralPerformanceResponseSchema:
        """
        Get the broker program referral performance. Epochs are 28 days long.
        """

        url = self._endpoints.get_referral_performance
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PublicGetReferralPerformanceResponseSchema)
        return response


class PrivateAPI:
    """private API methods"""

    def __init__(self, session: HTTPSession, config: EnvConfig, auth: AuthContext):
        self._session = session
        self._config = config
        self._auth = auth
        self._endpoints = PrivateEndpoints(config.base_url)

    @property
    def headers(self) -> dict:
        return {**PUBLIC_HEADERS, **self._auth.signed_headers}

    def get_account(
        self,
        params: PrivateGetAccountParamsSchema,
    ) -> PrivateGetAccountResponseSchema:
        """
        Account details getter

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_account
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetAccountResponseSchema)
        return response

    def create_subaccount(
        self,
        params: PrivateCreateSubaccountParamsSchema,
    ) -> PrivateCreateSubaccountResponseSchema:
        """
        Create a new subaccount under a given wallet, and deposit an asset into that
        subaccount.

        See `public/create_subaccount_debug` for debugging invalid signature issues or
        go to guides in Documentation.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.create_subaccount
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateCreateSubaccountResponseSchema)
        return response

    def get_subaccount(
        self,
        params: PrivateGetSubaccountParamsSchema,
    ) -> PrivateGetSubaccountResponseSchema:
        """
        Get open orders, active positions, and collaterals of a subaccount

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_subaccount
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetSubaccountResponseSchema)
        return response

    def get_subaccounts(
        self,
        params: PrivateGetSubaccountsParamsSchema,
    ) -> PrivateGetSubaccountsResponseSchema:
        """
        Get all subaccounts of an account / wallet

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_subaccounts
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetSubaccountsResponseSchema)
        return response

    def get_all_portfolios(
        self,
        params: PrivateGetAllPortfoliosParamsSchema,
    ) -> PrivateGetAllPortfoliosResponseSchema:
        """
        Get all portfolios of a wallet

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_all_portfolios
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetAllPortfoliosResponseSchema)
        return response

    def change_subaccount_label(
        self,
        params: PrivateChangeSubaccountLabelParamsSchema,
    ) -> PrivateChangeSubaccountLabelResponseSchema:
        """
        Change a user defined label for given subaccount

        Required minimum session key permission level is `account`
        """

        url = self._endpoints.change_subaccount_label
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateChangeSubaccountLabelResponseSchema)
        return response

    def get_notifications(
        self,
        params: PrivateGetNotificationsParamsSchema,
    ) -> PrivateGetNotificationsResponseSchema:
        """
        Get the notifications related to a subaccount.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_notifications
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetNotificationsResponseSchema)
        return response

    def update_notifications(
        self,
        params: PrivateUpdateNotificationsParamsSchema,
    ) -> PrivateUpdateNotificationsResponseSchema:
        """
        RPC to mark specified notifications as seen for a given subaccount.

        Required minimum session key permission level is `account`
        """

        url = self._endpoints.update_notifications
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateUpdateNotificationsResponseSchema)
        return response

    def deposit(
        self,
        params: PrivateDepositParamsSchema,
    ) -> PrivateDepositResponseSchema:
        """
        Deposit an asset to a subaccount.

        See `public/deposit_debug' for debugging invalid signature issues or go to
        guides in Documentation.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.deposit
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateDepositResponseSchema)
        return response

    def withdraw(
        self,
        params: PrivateWithdrawParamsSchema,
    ) -> PrivateWithdrawResponseSchema:
        """
        Withdraw an asset to wallet.

        See `public/withdraw_debug` for debugging invalid signature issues or go to
        guides in Documentation.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.withdraw
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateWithdrawResponseSchema)
        return response

    def transfer_erc20(
        self,
        params: PrivateTransferErc20ParamsSchema,
    ) -> PrivateTransferErc20ResponseSchema:
        """
        Transfer ERC20 assets from one subaccount to another (e.g. USDC or ETH).

        For transfering positions (e.g. options or perps), use
        `private/transfer_position` instead.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.transfer_erc20
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateTransferErc20ResponseSchema)
        return response

    def transfer_position(
        self,
        params: PrivateTransferPositionParamsSchema,
    ) -> PrivateTransferPositionResponseSchema:
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
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateTransferPositionResponseSchema)
        return response

    def transfer_positions(
        self,
        params: PrivateTransferPositionsParamsSchema,
    ) -> PrivateTransferPositionsResponseSchema:
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
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateTransferPositionsResponseSchema)
        return response

    def order(
        self,
        params: PrivateOrderParamsSchema,
    ) -> PrivateOrderResponseSchema:
        """
        Create a new order.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.order
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateOrderResponseSchema)
        return response

    def replace(
        self,
        params: PrivateReplaceParamsSchema,
    ) -> PrivateReplaceResponseSchema:
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
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateReplaceResponseSchema)
        return response

    def order_debug(
        self,
        params: PrivateOrderDebugParamsSchema,
    ) -> PrivateOrderDebugResponseSchema:
        """
        Debug a new order

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.order_debug
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateOrderDebugResponseSchema)
        return response

    def get_order(
        self,
        params: PrivateGetOrderParamsSchema,
    ) -> PrivateGetOrderResponseSchema:
        """
        Get state of an order by order id.  If the order is an MMP order, it will not
        show up if cancelled/expired.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_order
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetOrderResponseSchema)
        return response

    def get_orders(
        self,
        params: PrivateGetOrdersParamsSchema,
    ) -> PrivateGetOrdersResponseSchema:
        """
        Get orders for a subaccount, with optional filtering.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_orders
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetOrdersResponseSchema)
        return response

    def get_open_orders(
        self,
        params: PrivateGetOpenOrdersParamsSchema,
    ) -> PrivateGetOpenOrdersResponseSchema:
        """
        Get all open orders of a subacccount

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_open_orders
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetOpenOrdersResponseSchema)
        return response

    def cancel(
        self,
        params: PrivateCancelParamsSchema,
    ) -> PrivateCancelResponseSchema:
        """
        Cancel a single order.

        Other `private/cancel_*` routes are available through both REST and WebSocket.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.cancel
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateCancelResponseSchema)
        return response

    def cancel_all(
        self,
        params: PrivateCancelAllParamsSchema,
    ) -> PrivateCancelAllResponseSchema:
        """
        Cancel all orders for this instrument.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.cancel_all
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateCancelAllResponseSchema)
        return response

    def cancel_by_label(
        self,
        params: PrivateCancelByLabelParamsSchema,
    ) -> PrivateCancelByLabelResponseSchema:
        """
        Cancel all open orders for a given subaccount and a given label.  If
        instrument_name is provided, only orders for that instrument will be cancelled.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.cancel_by_label
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateCancelByLabelResponseSchema)
        return response

    def cancel_by_nonce(
        self,
        params: PrivateCancelByNonceParamsSchema,
    ) -> PrivateCancelByNonceResponseSchema:
        """
        Cancel a single order by nonce. Uses up that nonce if the order does not exist,
        so any future orders with that nonce will fail

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.cancel_by_nonce
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateCancelByNonceResponseSchema)
        return response

    def cancel_by_instrument(
        self,
        params: PrivateCancelByInstrumentParamsSchema,
    ) -> PrivateCancelByInstrumentResponseSchema:
        """
        Cancel all orders for this instrument.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.cancel_by_instrument
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateCancelByInstrumentResponseSchema)
        return response

    def cancel_trigger_order(
        self,
        params: PrivateCancelTriggerOrderParamsSchema,
    ) -> PrivateCancelTriggerOrderResponseSchema:
        """
        Cancels a trigger order.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.cancel_trigger_order
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateCancelTriggerOrderResponseSchema)
        return response

    def cancel_all_trigger_orders(
        self,
        params: PrivateCancelAllTriggerOrdersParamsSchema,
    ) -> PrivateCancelAllTriggerOrdersResponseSchema:
        """
        Cancel all trigger orders for this subaccount.

        Also used by cancel_all in WS.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.cancel_all_trigger_orders
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateCancelAllTriggerOrdersResponseSchema)
        return response

    def get_order_history(
        self,
        params: PrivateGetOrderHistoryParamsSchema,
    ) -> PrivateGetOrderHistoryResponseSchema:
        """
        Get order history for a subaccount

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_order_history
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetOrderHistoryResponseSchema)
        return response

    def get_trade_history(
        self,
        params: PrivateGetTradeHistoryParamsSchema,
    ) -> PrivateGetTradeHistoryResponseSchema:
        """
        Get trade history for a subaccount, with filter parameters.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_trade_history
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetTradeHistoryResponseSchema)
        return response

    def get_deposit_history(
        self,
        params: PrivateGetDepositHistoryParamsSchema,
    ) -> PrivateGetDepositHistoryResponseSchema:
        """
        Get subaccount deposit history.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_deposit_history
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetDepositHistoryResponseSchema)
        return response

    def get_withdrawal_history(
        self,
        params: PrivateGetWithdrawalHistoryParamsSchema,
    ) -> PrivateGetWithdrawalHistoryResponseSchema:
        """
        Get subaccount withdrawal history.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_withdrawal_history
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetWithdrawalHistoryResponseSchema)
        return response

    def send_rfq(
        self,
        params: PrivateSendRfqParamsSchema,
    ) -> PrivateSendRfqResponseSchema:
        """
        Requests two-sided quotes from participating market makers.

        Required minimum session key permission level is `account`
        """

        url = self._endpoints.send_rfq
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateSendRfqResponseSchema)
        return response

    def cancel_rfq(
        self,
        params: PrivateCancelRfqParamsSchema,
    ) -> PrivateCancelRfqResponseSchema:
        """
        Cancels a single RFQ by id.

        Required minimum session key permission level is `account`
        """

        url = self._endpoints.cancel_rfq
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateCancelRfqResponseSchema)
        return response

    def cancel_batch_rfqs(
        self,
        params: PrivateCancelBatchRfqsParamsSchema,
    ) -> PrivateCancelBatchRfqsResponseSchema:
        """
        Cancels RFQs given optional filters.

        If no filters are provided, all RFQs for the subaccount are cancelled.

        All filters are combined using `AND` logic, so mutually exclusive filters will
        result in no RFQs being cancelled.

        Required minimum session key permission level is `account`
        """

        url = self._endpoints.cancel_batch_rfqs
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateCancelBatchRfqsResponseSchema)
        return response

    def get_rfqs(
        self,
        params: PrivateGetRfqsParamsSchema,
    ) -> PrivateGetRfqsResponseSchema:
        """
        Retrieves a list of RFQs matching filter criteria. Takers can use this to get
        their open RFQs, RFQ history, etc.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_rfqs
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetRfqsResponseSchema)
        return response

    def poll_rfqs(
        self,
        params: PrivatePollRfqsParamsSchema,
    ) -> PrivatePollRfqsResponseSchema:
        """
        Retrieves a list of RFQs matching filter criteria. Market makers can use this to
        poll RFQs directed to them.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.poll_rfqs
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivatePollRfqsResponseSchema)
        return response

    def send_quote(
        self,
        params: PrivateSendQuoteParamsSchema,
    ) -> PrivateSendQuoteResponseSchema:
        """
        Sends a quote in response to an RFQ request.

        The legs supplied in the parameters must exactly match those in the RFQ.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.send_quote
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateSendQuoteResponseSchema)
        return response

    def replace_quote(
        self,
        params: PrivateReplaceQuoteParamsSchema,
    ) -> PrivateReplaceQuoteResponseSchema:
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
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateReplaceQuoteResponseSchema)
        return response

    def cancel_quote(
        self,
        params: PrivateCancelQuoteParamsSchema,
    ) -> PrivateCancelQuoteResponseSchema:
        """
        Cancels an open quote.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.cancel_quote
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateCancelQuoteResponseSchema)
        return response

    def cancel_batch_quotes(
        self,
        params: PrivateCancelBatchQuotesParamsSchema,
    ) -> PrivateCancelBatchQuotesResponseSchema:
        """
        Cancels quotes given optional filters. If no filters are provided, all quotes by
        the subaccount are cancelled.

        All filters are combined using `AND` logic, so mutually exclusive filters will
        result in no quotes being cancelled.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.cancel_batch_quotes
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateCancelBatchQuotesResponseSchema)
        return response

    def get_quotes(
        self,
        params: PrivateGetQuotesParamsSchema,
    ) -> PrivateGetQuotesResponseSchema:
        """
        Retrieves a list of quotes matching filter criteria.

        Market makers can use this to get their open quotes, quote history, etc.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_quotes
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetQuotesResponseSchema)
        return response

    def poll_quotes(
        self,
        params: PrivatePollQuotesParamsSchema,
    ) -> PrivatePollQuotesResponseSchema:
        """
        Retrieves a list of quotes matching filter criteria.

        Takers can use this to poll open quotes that they can fill against their open
        RFQs.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.poll_quotes
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivatePollQuotesResponseSchema)
        return response

    def execute_quote(
        self,
        params: PrivateExecuteQuoteParamsSchema,
    ) -> PrivateExecuteQuoteResponseSchema:
        """
        Executes a quote.

        Required minimum session key permission level is `admin`
        """

        url = self._endpoints.execute_quote
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateExecuteQuoteResponseSchema)
        return response

    def rfq_get_best_quote(
        self,
        params: PrivateRfqGetBestQuoteParamsSchema,
    ) -> PrivateRfqGetBestQuoteResponseSchema:
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
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateRfqGetBestQuoteResponseSchema)
        return response

    def get_margin(
        self,
        params: PrivateGetMarginParamsSchema,
    ) -> PrivateGetMarginResponseSchema:
        """
        Calculates margin for a given subaccount and (optionally) a simulated state
        change. Does not take into account

        open orders margin requirements.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_margin
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetMarginResponseSchema)
        return response

    def get_collaterals(
        self,
        params: PrivateGetCollateralsParamsSchema,
    ) -> PrivateGetCollateralsResponseSchema:
        """
        Get collaterals of a subaccount

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_collaterals
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetCollateralsResponseSchema)
        return response

    def get_positions(
        self,
        params: PrivateGetPositionsParamsSchema,
    ) -> PrivateGetPositionsResponseSchema:
        """
        Get active positions of a subaccount

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_positions
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetPositionsResponseSchema)
        return response

    def get_option_settlement_history(
        self,
        params: PrivateGetOptionSettlementHistoryParamsSchema,
    ) -> PrivateGetOptionSettlementHistoryResponseSchema:
        """
        Get expired option settlement history for a subaccount

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_option_settlement_history
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetOptionSettlementHistoryResponseSchema)
        return response

    def get_subaccount_value_history(
        self,
        params: PrivateGetSubaccountValueHistoryParamsSchema,
    ) -> PrivateGetSubaccountValueHistoryResponseSchema:
        """
        Get the value history of a subaccount

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_subaccount_value_history
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetSubaccountValueHistoryResponseSchema)
        return response

    def expired_and_cancelled_history(
        self,
        params: PrivateExpiredAndCancelledHistoryParamsSchema,
    ) -> PrivateExpiredAndCancelledHistoryResponseSchema:
        """
        Generate a list of URLs to retrieve archived orders

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.expired_and_cancelled_history
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateExpiredAndCancelledHistoryResponseSchema)
        return response

    def get_funding_history(
        self,
        params: PrivateGetFundingHistoryParamsSchema,
    ) -> PrivateGetFundingHistoryResponseSchema:
        """
        Get subaccount funding history.

        DB: read replica

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_funding_history
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetFundingHistoryResponseSchema)
        return response

    def get_interest_history(
        self,
        params: PrivateGetInterestHistoryParamsSchema,
    ) -> PrivateGetInterestHistoryResponseSchema:
        """
        Get subaccount interest payment history.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_interest_history
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetInterestHistoryResponseSchema)
        return response

    def get_erc20_transfer_history(
        self,
        params: PrivateGetErc20TransferHistoryParamsSchema,
    ) -> PrivateGetErc20TransferHistoryResponseSchema:
        """
        Get subaccount erc20 transfer history.

        Position transfers (e.g. options or perps) are treated as trades. Use
        `private/get_trade_history` for position transfer history.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_erc20_transfer_history
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetErc20TransferHistoryResponseSchema)
        return response

    def get_liquidation_history(
        self,
        params: PrivateGetLiquidationHistoryParamsSchema,
    ) -> PrivateGetLiquidationHistoryResponseSchema:
        """
        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_liquidation_history
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetLiquidationHistoryResponseSchema)
        return response

    def liquidate(
        self,
        params: PrivateLiquidateParamsSchema,
    ) -> PrivateLiquidateResponseSchema:
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
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateLiquidateResponseSchema)
        return response

    def get_liquidator_history(
        self,
        params: PrivateGetLiquidatorHistoryParamsSchema,
    ) -> PrivateGetLiquidatorHistoryResponseSchema:
        """
        Returns a paginated history of auctions that the subaccount has participated in
        as a liquidator.

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_liquidator_history
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetLiquidatorHistoryResponseSchema)
        return response

    def session_keys(
        self,
        params: PrivateSessionKeysParamsSchema,
    ) -> PrivateSessionKeysResponseSchema:
        """
        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.session_keys
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateSessionKeysResponseSchema)
        return response

    def edit_session_key(
        self,
        params: PrivateEditSessionKeyParamsSchema,
    ) -> PrivateEditSessionKeyResponseSchema:
        """
        Edits session key parameters such as label and IP whitelist.

        For non-admin keys you can also toggle whether to disable a particular key.

        Disabling non-admin keys must be done through /deregister_session_key

        Required minimum session key permission level is `account`
        """

        url = self._endpoints.edit_session_key
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateEditSessionKeyResponseSchema)
        return response

    def register_scoped_session_key(
        self,
        params: PrivateRegisterScopedSessionKeyParamsSchema,
    ) -> PrivateRegisterScopedSessionKeyResponseSchema:
        """
        Registers a new session key bounded to a scope without a transaction attached.

        If you want to register an admin key, you must provide a signed raw transaction.

        Required minimum session key permission level is `account`
        """

        url = self._endpoints.register_scoped_session_key
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateRegisterScopedSessionKeyResponseSchema)
        return response

    def get_mmp_config(
        self,
        params: PrivateGetMmpConfigParamsSchema,
    ) -> PrivateGetMmpConfigResponseSchema:
        """
        Get the current mmp config for a subaccount (optionally filtered by currency)

        Required minimum session key permission level is `read_only`
        """

        url = self._endpoints.get_mmp_config
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateGetMmpConfigResponseSchema)
        return response

    def set_mmp_config(
        self,
        params: PrivateSetMmpConfigParamsSchema,
    ) -> PrivateSetMmpConfigResponseSchema:
        """
        Set the mmp config for the subaccount and currency

        Required minimum session key permission level is `account`
        """

        url = self._endpoints.set_mmp_config
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateSetMmpConfigResponseSchema)
        return response

    def reset_mmp(
        self,
        params: PrivateResetMmpParamsSchema,
    ) -> PrivateResetMmpResponseSchema:
        """
        Resets (unfreezes) the mmp state for a subaccount (optionally filtered by
        currency)

        Required minimum session key permission level is `account`
        """

        url = self._endpoints.reset_mmp
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateResetMmpResponseSchema)
        return response

    def set_cancel_on_disconnect(
        self,
        params: PrivateSetCancelOnDisconnectParamsSchema,
    ) -> PrivateSetCancelOnDisconnectResponseSchema:
        """
        Enables cancel on disconnect for the account

        Required minimum session key permission level is `account`
        """

        url = self._endpoints.set_cancel_on_disconnect
        data = encode_json_exclude_none(params)
        message = self._session._send_request(url, data, headers=self.headers)
        response = try_cast_response(message, PrivateSetCancelOnDisconnectResponseSchema)
        return response
