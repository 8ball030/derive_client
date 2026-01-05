"""Auto-generated API classes for WebSocket"""

from enum import Enum
from typing import Any, Callable, List

import msgspec

from derive_client._clients.utils import decode_result
from derive_client._clients.websockets.session import WebSocketSession
from derive_client.data_types.channel_models import (
    AuctionResultSchema,
    BalanceUpdateSchema,
    BestQuoteChannelResultSchema,
    Depth,
    Group,
    InstrumentType,
    Interval,
    MarginWatchResultSchema,
    OrderbookInstrumentNameGroupDepthPublisherDataSchema,
    OrderResponseSchema,
    QuoteResultSchema,
    RFQResultPublicSchema,
    SpotFeedCurrencyPublisherDataSchema,
    TickerSlimInstrumentNameIntervalPublisherDataSchema,
    TradePublicResponseSchema,
    TradeResponseSchema,
    TradeSettledPublicResponseSchema,
    TxStatus2,
)
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


class SubscriptionResult(msgspec.Struct):
    status: dict[str, str]
    current_subscriptions: list[str]


# ============================================================================
# RPC API Classes
# ============================================================================


class PublicRPC:
    """public RPC methods"""

    def __init__(self, session: WebSocketSession):
        self._session = session

    def build_register_session_key_tx(
        self,
        params: PublicBuildRegisterSessionKeyTxParamsSchema,
    ) -> PublicBuildRegisterSessionKeyTxResultSchema:
        """
        Build a signable transaction params dictionary.
        """

        method = "public/build_register_session_key_tx"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicBuildRegisterSessionKeyTxResultSchema)

        return result

    def register_session_key(
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

        method = "public/register_session_key"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicRegisterSessionKeyResultSchema)

        return result

    def deregister_session_key(
        self,
        params: PublicDeregisterSessionKeyParamsSchema,
    ) -> PublicDeregisterSessionKeyResultSchema:
        """
        Used for de-registering admin scoped keys. For other scopes, use
        `/edit_session_key`.
        """

        method = "public/deregister_session_key"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicDeregisterSessionKeyResultSchema)

        return result

    def login(
        self,
        params: PublicLoginParamsSchema,
    ) -> List[int]:
        """
        Authenticate a websocket connection. Unavailable via HTTP.
        """

        method = "public/login"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, list[int])

        return result

    def statistics(
        self,
        params: PublicStatisticsParamsSchema,
    ) -> PublicStatisticsResultSchema:
        """
        Get statistics for a specific instrument or instrument type
        """

        method = "public/statistics"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicStatisticsResultSchema)

        return result

    def get_all_currencies(
        self,
        params: PublicGetAllCurrenciesParamsSchema,
    ) -> List[CurrencyDetailedResponseSchema]:
        """
        Get all active currencies with their spot price, spot price 24hrs ago.

        For real-time updates, recommend using channels -> ticker or orderbook.
        """

        method = "public/get_all_currencies"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, list[CurrencyDetailedResponseSchema])

        return result

    def get_currency(
        self,
        params: PublicGetCurrencyParamsSchema,
    ) -> PublicGetCurrencyResultSchema:
        """
        Get currency related risk params, spot price 24hrs ago and lending details for a
        specific currency.
        """

        method = "public/get_currency"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicGetCurrencyResultSchema)

        return result

    def get_instrument(
        self,
        params: PublicGetInstrumentParamsSchema,
    ) -> PublicGetInstrumentResultSchema:
        """
        Get single instrument by asset name
        """

        method = "public/get_instrument"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicGetInstrumentResultSchema)

        return result

    def get_all_instruments(
        self,
        params: PublicGetAllInstrumentsParamsSchema,
    ) -> PublicGetAllInstrumentsResultSchema:
        """
        Get a paginated history of all instruments
        """

        method = "public/get_all_instruments"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicGetAllInstrumentsResultSchema)

        return result

    def get_instruments(
        self,
        params: PublicGetInstrumentsParamsSchema,
    ) -> List[InstrumentPublicResponseSchema]:
        """
        Get all active instruments for a given `currency` and `type`.
        """

        method = "public/get_instruments"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, list[InstrumentPublicResponseSchema])

        return result

    def get_ticker(
        self,
        params: PublicGetTickerParamsSchema,
    ) -> PublicGetTickerResultSchema:
        """
        Get ticker information (best bid / ask, instrument contraints, fees info, etc.)
        for a single instrument

        DEPRECATION NOTICE: This RPC is deprecated in favor of `get_tickers` on Dec 1,
        2025.
        """

        method = "public/get_ticker"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicGetTickerResultSchema)

        return result

    def get_tickers(
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

        method = "public/get_tickers"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicGetTickersResultSchema)

        return result

    def get_latest_signed_feeds(
        self,
        params: PublicGetLatestSignedFeedsParamsSchema,
    ) -> PublicGetLatestSignedFeedsResultSchema:
        """
        Get latest signed data feeds
        """

        method = "public/get_latest_signed_feeds"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicGetLatestSignedFeedsResultSchema)

        return result

    def get_option_settlement_prices(
        self,
        params: PublicGetOptionSettlementPricesParamsSchema,
    ) -> PublicGetOptionSettlementPricesResultSchema:
        """
        Get settlement prices by expiry for each currency
        """

        method = "public/get_option_settlement_prices"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicGetOptionSettlementPricesResultSchema)

        return result

    def get_spot_feed_history(
        self,
        params: PublicGetSpotFeedHistoryParamsSchema,
    ) -> PublicGetSpotFeedHistoryResultSchema:
        """
        Get spot feed history by currency

        DB: read replica
        """

        method = "public/get_spot_feed_history"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicGetSpotFeedHistoryResultSchema)

        return result

    def get_spot_feed_history_candles(
        self,
        params: PublicGetSpotFeedHistoryCandlesParamsSchema,
    ) -> PublicGetSpotFeedHistoryCandlesResultSchema:
        """
        Get spot feed history candles by currency

        DB: read replica
        """

        method = "public/get_spot_feed_history_candles"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicGetSpotFeedHistoryCandlesResultSchema)

        return result

    def get_funding_rate_history(
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

        method = "public/get_funding_rate_history"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicGetFundingRateHistoryResultSchema)

        return result

    def get_trade_history(
        self,
        params: PublicGetTradeHistoryParamsSchema,
    ) -> PublicGetTradeHistoryResultSchema:
        """
        Get trade history for a subaccount, with filter parameters.
        """

        method = "public/get_trade_history"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicGetTradeHistoryResultSchema)

        return result

    def get_option_settlement_history(
        self,
        params: PublicGetOptionSettlementHistoryParamsSchema,
    ) -> PublicGetOptionSettlementHistoryResultSchema:
        """
        Get expired option settlement history for a subaccount
        """

        method = "public/get_option_settlement_history"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicGetOptionSettlementHistoryResultSchema)

        return result

    def get_liquidation_history(
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

        method = "public/get_liquidation_history"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicGetLiquidationHistoryResultSchema)

        return result

    def get_interest_rate_history(
        self,
        params: PublicGetInterestRateHistoryParamsSchema,
    ) -> PublicGetInterestRateHistoryResultSchema:
        """
        Get latest USDC interest rate history
        """

        method = "public/get_interest_rate_history"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicGetInterestRateHistoryResultSchema)

        return result

    def get_transaction(
        self,
        params: PublicGetTransactionParamsSchema,
    ) -> PublicGetTransactionResultSchema:
        """
        Used for getting a transaction by its transaction id
        """

        method = "public/get_transaction"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicGetTransactionResultSchema)

        return result

    def get_margin(
        self,
        params: PublicGetMarginParamsSchema,
    ) -> PublicGetMarginResultSchema:
        """
        Calculates margin for a given portfolio and (optionally) a simulated state
        change.

        Does not take into account open orders margin requirements.public/withdraw_debug
        """

        method = "public/get_margin"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicGetMarginResultSchema)

        return result

    def margin_watch(
        self,
        params: PublicMarginWatchParamsSchema,
    ) -> PublicMarginWatchResultSchema:
        """
        Calculates MtM and maintenance margin for a given subaccount.
        """

        method = "public/margin_watch"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicMarginWatchResultSchema)

        return result

    def get_vault_share(
        self,
        params: PublicGetVaultShareParamsSchema,
    ) -> PublicGetVaultShareResultSchema:
        """
        Gets the value of a vault's token against the base currency, underlying
        currency, and USD for a timestamp range.

        The name of the vault from the Vault proxy contract is used to fetch the vault's
        value.
        """

        method = "public/get_vault_share"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicGetVaultShareResultSchema)

        return result

    def get_vault_statistics(
        self,
        params: PublicGetVaultStatisticsParamsSchema,
    ) -> List[VaultStatisticsResponseSchema]:
        """
        Gets all the latest vault shareRate, totalSupply and TVL values for all vaults.

        For data on shares across chains, use public/get_vault_assets.
        """

        method = "public/get_vault_statistics"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, list[VaultStatisticsResponseSchema])

        return result

    def get_vault_balances(
        self,
        params: PublicGetVaultBalancesParamsSchema,
    ) -> List[VaultBalanceResponseSchema]:
        """
        Get all vault assets held by user. Can query by smart contract address or smart
        contract owner.

        Includes VaultERC20Pool balances
        """

        method = "public/get_vault_balances"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, list[VaultBalanceResponseSchema])

        return result

    def create_subaccount_debug(
        self,
        params: PublicCreateSubaccountDebugParamsSchema,
    ) -> PublicCreateSubaccountDebugResultSchema:
        """
        Used for debugging only, do not use in production. Will return the incremental
        encoded and hashed data.

        See guides in Documentation for more.
        """

        method = "public/create_subaccount_debug"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicCreateSubaccountDebugResultSchema)

        return result

    def deposit_debug(
        self,
        params: PublicDepositDebugParamsSchema,
    ) -> PublicDepositDebugResultSchema:
        """
        Used for debugging only, do not use in production. Will return the incremental
        encoded and hashed data.

        See guides in Documentation for more.
        """

        method = "public/deposit_debug"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicDepositDebugResultSchema)

        return result

    def withdraw_debug(
        self,
        params: PublicWithdrawDebugParamsSchema,
    ) -> PublicWithdrawDebugResultSchema:
        """
        Used for debugging only, do not use in production. Will return the incremental
        encoded and hashed data.

        See guides in Documentation for more.
        """

        method = "public/withdraw_debug"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicWithdrawDebugResultSchema)

        return result

    def send_quote_debug(
        self,
        params: PublicSendQuoteDebugParamsSchema,
    ) -> PublicSendQuoteDebugResultSchema:
        """
        Sends a quote in response to an RFQ request.

        The legs supplied in the parameters must exactly match those in the RFQ.
        """

        method = "public/send_quote_debug"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicSendQuoteDebugResultSchema)

        return result

    def execute_quote_debug(
        self,
        params: PublicExecuteQuoteDebugParamsSchema,
    ) -> PublicExecuteQuoteDebugResultSchema:
        """
        Sends a quote in response to an RFQ request.

        The legs supplied in the parameters must exactly match those in the RFQ.
        """

        method = "public/execute_quote_debug"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicExecuteQuoteDebugResultSchema)

        return result

    def get_time(
        self,
        params: PublicGetTimeParamsSchema,
    ) -> int:
        method = "public/get_time"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, int)

        return result

    def get_live_incidents(
        self,
        params: PublicGetLiveIncidentsParamsSchema,
    ) -> PublicGetLiveIncidentsResultSchema:
        method = "public/get_live_incidents"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicGetLiveIncidentsResultSchema)

        return result

    def get_maker_programs(
        self,
        params: PublicGetMakerProgramsParamsSchema,
    ) -> List[ProgramResponseSchema]:
        """
        Get all maker programs, including past / historical ones.
        """

        method = "public/get_maker_programs"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, list[ProgramResponseSchema])

        return result

    def get_maker_program_scores(
        self,
        params: PublicGetMakerProgramScoresParamsSchema,
    ) -> PublicGetMakerProgramScoresResultSchema:
        """
        Get scores breakdown by maker program.
        """

        method = "public/get_maker_program_scores"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicGetMakerProgramScoresResultSchema)

        return result

    def get_referral_performance(
        self,
        params: PublicGetReferralPerformanceParamsSchema,
    ) -> PublicGetReferralPerformanceResultSchema:
        """
        Get the broker program referral performance. Epochs are 28 days long.
        """

        method = "public/get_referral_performance"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PublicGetReferralPerformanceResultSchema)

        return result


class PrivateRPC:
    """private RPC methods"""

    def __init__(self, session: WebSocketSession):
        self._session = session

    def get_account(
        self,
        params: PrivateGetAccountParamsSchema,
    ) -> PrivateGetAccountResultSchema:
        """
        Account details getter

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_account"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetAccountResultSchema)

        return result

    def create_subaccount(
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

        method = "private/create_subaccount"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateCreateSubaccountResultSchema)

        return result

    def get_subaccount(
        self,
        params: PrivateGetSubaccountParamsSchema,
    ) -> PrivateGetSubaccountResultSchema:
        """
        Get open orders, active positions, and collaterals of a subaccount

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_subaccount"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetSubaccountResultSchema)

        return result

    def get_subaccounts(
        self,
        params: PrivateGetSubaccountsParamsSchema,
    ) -> PrivateGetSubaccountsResultSchema:
        """
        Get all subaccounts of an account / wallet

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_subaccounts"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetSubaccountsResultSchema)

        return result

    def get_all_portfolios(
        self,
        params: PrivateGetAllPortfoliosParamsSchema,
    ) -> List[PrivateGetSubaccountResultSchema]:
        """
        Get all portfolios of a wallet

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_all_portfolios"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, list[PrivateGetSubaccountResultSchema])

        return result

    def change_subaccount_label(
        self,
        params: PrivateChangeSubaccountLabelParamsSchema,
    ) -> PrivateChangeSubaccountLabelResultSchema:
        """
        Change a user defined label for given subaccount

        Required minimum session key permission level is `account`
        """

        method = "private/change_subaccount_label"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateChangeSubaccountLabelResultSchema)

        return result

    def get_notifications(
        self,
        params: PrivateGetNotificationsParamsSchema,
    ) -> PrivateGetNotificationsResultSchema:
        """
        Get the notifications related to a subaccount.

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_notifications"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetNotificationsResultSchema)

        return result

    def update_notifications(
        self,
        params: PrivateUpdateNotificationsParamsSchema,
    ) -> PrivateUpdateNotificationsResultSchema:
        """
        RPC to mark specified notifications as seen for a given subaccount.

        Required minimum session key permission level is `account`
        """

        method = "private/update_notifications"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateUpdateNotificationsResultSchema)

        return result

    def deposit(
        self,
        params: PrivateDepositParamsSchema,
    ) -> PrivateDepositResultSchema:
        """
        Deposit an asset to a subaccount.

        See `public/deposit_debug' for debugging invalid signature issues or go to
        guides in Documentation.

        Required minimum session key permission level is `admin`
        """

        method = "private/deposit"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateDepositResultSchema)

        return result

    def withdraw(
        self,
        params: PrivateWithdrawParamsSchema,
    ) -> PrivateWithdrawResultSchema:
        """
        Withdraw an asset to wallet.

        See `public/withdraw_debug` for debugging invalid signature issues or go to
        guides in Documentation.

        Required minimum session key permission level is `admin`
        """

        method = "private/withdraw"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateWithdrawResultSchema)

        return result

    def transfer_erc20(
        self,
        params: PrivateTransferErc20ParamsSchema,
    ) -> PrivateTransferErc20ResultSchema:
        """
        Transfer ERC20 assets from one subaccount to another (e.g. USDC or ETH).

        For transfering positions (e.g. options or perps), use
        `private/transfer_position` instead.

        Required minimum session key permission level is `admin`
        """

        method = "private/transfer_erc20"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateTransferErc20ResultSchema)

        return result

    def transfer_position(
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

        method = "private/transfer_position"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateTransferPositionResultSchema)

        return result

    def transfer_positions(
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

        method = "private/transfer_positions"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateTransferPositionsResultSchema)

        return result

    def order(
        self,
        params: PrivateOrderParamsSchema,
    ) -> PrivateOrderResultSchema:
        """
        Create a new order.

        Required minimum session key permission level is `admin`
        """

        method = "private/order"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateOrderResultSchema)

        return result

    def replace(
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

        method = "private/replace"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateReplaceResultSchema)

        return result

    def order_debug(
        self,
        params: PrivateOrderDebugParamsSchema,
    ) -> PrivateOrderDebugResultSchema:
        """
        Debug a new order

        Required minimum session key permission level is `read_only`
        """

        method = "private/order_debug"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateOrderDebugResultSchema)

        return result

    def get_order(
        self,
        params: PrivateGetOrderParamsSchema,
    ) -> PrivateGetOrderResultSchema:
        """
        Get state of an order by order id.  If the order is an MMP order, it will not
        show up if cancelled/expired.

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_order"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetOrderResultSchema)

        return result

    def get_orders(
        self,
        params: PrivateGetOrdersParamsSchema,
    ) -> PrivateGetOrdersResultSchema:
        """
        Get orders for a subaccount, with optional filtering.

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_orders"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetOrdersResultSchema)

        return result

    def get_open_orders(
        self,
        params: PrivateGetOpenOrdersParamsSchema,
    ) -> PrivateGetOpenOrdersResultSchema:
        """
        Get all open orders of a subacccount

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_open_orders"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetOpenOrdersResultSchema)

        return result

    def cancel(
        self,
        params: PrivateCancelParamsSchema,
    ) -> PrivateCancelResultSchema:
        """
        Cancel a single order.

        Other `private/cancel_*` routes are available through both REST and WebSocket.

        Required minimum session key permission level is `admin`
        """

        method = "private/cancel"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateCancelResultSchema)

        return result

    def cancel_all(
        self,
        params: PrivateCancelAllParamsSchema,
    ) -> Result:
        """
        Cancel all orders for this instrument.

        Required minimum session key permission level is `admin`
        """

        method = "private/cancel_all"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, Result)

        return result

    def cancel_by_label(
        self,
        params: PrivateCancelByLabelParamsSchema,
    ) -> PrivateCancelByLabelResultSchema:
        """
        Cancel all open orders for a given subaccount and a given label.  If
        instrument_name is provided, only orders for that instrument will be cancelled.

        Required minimum session key permission level is `admin`
        """

        method = "private/cancel_by_label"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateCancelByLabelResultSchema)

        return result

    def cancel_by_nonce(
        self,
        params: PrivateCancelByNonceParamsSchema,
    ) -> PrivateCancelByNonceResultSchema:
        """
        Cancel a single order by nonce. Uses up that nonce if the order does not exist,
        so any future orders with that nonce will fail

        Required minimum session key permission level is `admin`
        """

        method = "private/cancel_by_nonce"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateCancelByNonceResultSchema)

        return result

    def cancel_by_instrument(
        self,
        params: PrivateCancelByInstrumentParamsSchema,
    ) -> PrivateCancelByInstrumentResultSchema:
        """
        Cancel all orders for this instrument.

        Required minimum session key permission level is `admin`
        """

        method = "private/cancel_by_instrument"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateCancelByInstrumentResultSchema)

        return result

    def cancel_trigger_order(
        self,
        params: PrivateCancelTriggerOrderParamsSchema,
    ) -> PrivateCancelTriggerOrderResultSchema:
        """
        Cancels a trigger order.

        Required minimum session key permission level is `admin`
        """

        method = "private/cancel_trigger_order"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateCancelTriggerOrderResultSchema)

        return result

    def cancel_all_trigger_orders(
        self,
        params: PrivateCancelAllTriggerOrdersParamsSchema,
    ) -> Result:
        """
        Cancel all trigger orders for this subaccount.

        Also used by cancel_all in WS.

        Required minimum session key permission level is `admin`
        """

        method = "private/cancel_all_trigger_orders"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, Result)

        return result

    def get_order_history(
        self,
        params: PrivateGetOrderHistoryParamsSchema,
    ) -> PrivateGetOrderHistoryResultSchema:
        """
        Get order history for a subaccount

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_order_history"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetOrderHistoryResultSchema)

        return result

    def get_trade_history(
        self,
        params: PrivateGetTradeHistoryParamsSchema,
    ) -> PrivateGetTradeHistoryResultSchema:
        """
        Get trade history for a subaccount, with filter parameters.

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_trade_history"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetTradeHistoryResultSchema)

        return result

    def get_deposit_history(
        self,
        params: PrivateGetDepositHistoryParamsSchema,
    ) -> PrivateGetDepositHistoryResultSchema:
        """
        Get subaccount deposit history.

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_deposit_history"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetDepositHistoryResultSchema)

        return result

    def get_withdrawal_history(
        self,
        params: PrivateGetWithdrawalHistoryParamsSchema,
    ) -> PrivateGetWithdrawalHistoryResultSchema:
        """
        Get subaccount withdrawal history.

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_withdrawal_history"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetWithdrawalHistoryResultSchema)

        return result

    def send_rfq(
        self,
        params: PrivateSendRfqParamsSchema,
    ) -> PrivateSendRfqResultSchema:
        """
        Requests two-sided quotes from participating market makers.

        Required minimum session key permission level is `account`
        """

        method = "private/send_rfq"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateSendRfqResultSchema)

        return result

    def cancel_rfq(
        self,
        params: PrivateCancelRfqParamsSchema,
    ) -> Result:
        """
        Cancels a single RFQ by id.

        Required minimum session key permission level is `account`
        """

        method = "private/cancel_rfq"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, Result)

        return result

    def cancel_batch_rfqs(
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

        method = "private/cancel_batch_rfqs"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateCancelBatchRfqsResultSchema)

        return result

    def get_rfqs(
        self,
        params: PrivateGetRfqsParamsSchema,
    ) -> PrivateGetRfqsResultSchema:
        """
        Retrieves a list of RFQs matching filter criteria. Takers can use this to get
        their open RFQs, RFQ history, etc.

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_rfqs"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetRfqsResultSchema)

        return result

    def poll_rfqs(
        self,
        params: PrivatePollRfqsParamsSchema,
    ) -> PrivatePollRfqsResultSchema:
        """
        Retrieves a list of RFQs matching filter criteria. Market makers can use this to
        poll RFQs directed to them.

        Required minimum session key permission level is `read_only`
        """

        method = "private/poll_rfqs"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivatePollRfqsResultSchema)

        return result

    def send_quote(
        self,
        params: PrivateSendQuoteParamsSchema,
    ) -> PrivateSendQuoteResultSchema:
        """
        Sends a quote in response to an RFQ request.

        The legs supplied in the parameters must exactly match those in the RFQ.

        Required minimum session key permission level is `admin`
        """

        method = "private/send_quote"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateSendQuoteResultSchema)

        return result

    def replace_quote(
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

        method = "private/replace_quote"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateReplaceQuoteResultSchema)

        return result

    def cancel_quote(
        self,
        params: PrivateCancelQuoteParamsSchema,
    ) -> PrivateCancelQuoteResultSchema:
        """
        Cancels an open quote.

        Required minimum session key permission level is `admin`
        """

        method = "private/cancel_quote"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateCancelQuoteResultSchema)

        return result

    def cancel_batch_quotes(
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

        method = "private/cancel_batch_quotes"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateCancelBatchQuotesResultSchema)

        return result

    def get_quotes(
        self,
        params: PrivateGetQuotesParamsSchema,
    ) -> PrivateGetQuotesResultSchema:
        """
        Retrieves a list of quotes matching filter criteria.

        Market makers can use this to get their open quotes, quote history, etc.

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_quotes"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetQuotesResultSchema)

        return result

    def poll_quotes(
        self,
        params: PrivatePollQuotesParamsSchema,
    ) -> PrivatePollQuotesResultSchema:
        """
        Retrieves a list of quotes matching filter criteria.

        Takers can use this to poll open quotes that they can fill against their open
        RFQs.

        Required minimum session key permission level is `read_only`
        """

        method = "private/poll_quotes"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivatePollQuotesResultSchema)

        return result

    def execute_quote(
        self,
        params: PrivateExecuteQuoteParamsSchema,
    ) -> PrivateExecuteQuoteResultSchema:
        """
        Executes a quote.

        Required minimum session key permission level is `admin`
        """

        method = "private/execute_quote"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateExecuteQuoteResultSchema)

        return result

    def rfq_get_best_quote(
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

        method = "private/rfq_get_best_quote"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateRfqGetBestQuoteResultSchema)

        return result

    def get_margin(
        self,
        params: PrivateGetMarginParamsSchema,
    ) -> PrivateGetMarginResultSchema:
        """
        Calculates margin for a given subaccount and (optionally) a simulated state
        change. Does not take into account

        open orders margin requirements.

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_margin"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetMarginResultSchema)

        return result

    def get_collaterals(
        self,
        params: PrivateGetCollateralsParamsSchema,
    ) -> PrivateGetCollateralsResultSchema:
        """
        Get collaterals of a subaccount

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_collaterals"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetCollateralsResultSchema)

        return result

    def get_positions(
        self,
        params: PrivateGetPositionsParamsSchema,
    ) -> PrivateGetPositionsResultSchema:
        """
        Get active positions of a subaccount

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_positions"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetPositionsResultSchema)

        return result

    def get_option_settlement_history(
        self,
        params: PrivateGetOptionSettlementHistoryParamsSchema,
    ) -> PrivateGetOptionSettlementHistoryResultSchema:
        """
        Get expired option settlement history for a subaccount

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_option_settlement_history"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetOptionSettlementHistoryResultSchema)

        return result

    def get_subaccount_value_history(
        self,
        params: PrivateGetSubaccountValueHistoryParamsSchema,
    ) -> PrivateGetSubaccountValueHistoryResultSchema:
        """
        Get the value history of a subaccount

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_subaccount_value_history"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetSubaccountValueHistoryResultSchema)

        return result

    def expired_and_cancelled_history(
        self,
        params: PrivateExpiredAndCancelledHistoryParamsSchema,
    ) -> PrivateExpiredAndCancelledHistoryResultSchema:
        """
        Generate a list of URLs to retrieve archived orders

        Required minimum session key permission level is `read_only`
        """

        method = "private/expired_and_cancelled_history"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateExpiredAndCancelledHistoryResultSchema)

        return result

    def get_funding_history(
        self,
        params: PrivateGetFundingHistoryParamsSchema,
    ) -> PrivateGetFundingHistoryResultSchema:
        """
        Get subaccount funding history.

        DB: read replica

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_funding_history"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetFundingHistoryResultSchema)

        return result

    def get_interest_history(
        self,
        params: PrivateGetInterestHistoryParamsSchema,
    ) -> PrivateGetInterestHistoryResultSchema:
        """
        Get subaccount interest payment history.

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_interest_history"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetInterestHistoryResultSchema)

        return result

    def get_erc20_transfer_history(
        self,
        params: PrivateGetErc20TransferHistoryParamsSchema,
    ) -> PrivateGetErc20TransferHistoryResultSchema:
        """
        Get subaccount erc20 transfer history.

        Position transfers (e.g. options or perps) are treated as trades. Use
        `private/get_trade_history` for position transfer history.

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_erc20_transfer_history"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetErc20TransferHistoryResultSchema)

        return result

    def get_liquidation_history(
        self,
        params: PrivateGetLiquidationHistoryParamsSchema,
    ) -> List[AuctionResultSchema]:
        """
        Required minimum session key permission level is `read_only`
        """

        method = "private/get_liquidation_history"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, list[AuctionResultSchema])

        return result

    def liquidate(
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

        method = "private/liquidate"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateLiquidateResultSchema)

        return result

    def get_liquidator_history(
        self,
        params: PrivateGetLiquidatorHistoryParamsSchema,
    ) -> PrivateGetLiquidatorHistoryResultSchema:
        """
        Returns a paginated history of auctions that the subaccount has participated in
        as a liquidator.

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_liquidator_history"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateGetLiquidatorHistoryResultSchema)

        return result

    def session_keys(
        self,
        params: PrivateSessionKeysParamsSchema,
    ) -> PrivateSessionKeysResultSchema:
        """
        Required minimum session key permission level is `read_only`
        """

        method = "private/session_keys"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateSessionKeysResultSchema)

        return result

    def edit_session_key(
        self,
        params: PrivateEditSessionKeyParamsSchema,
    ) -> PrivateEditSessionKeyResultSchema:
        """
        Edits session key parameters such as label and IP whitelist.

        For non-admin keys you can also toggle whether to disable a particular key.

        Disabling non-admin keys must be done through /deregister_session_key

        Required minimum session key permission level is `account`
        """

        method = "private/edit_session_key"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateEditSessionKeyResultSchema)

        return result

    def register_scoped_session_key(
        self,
        params: PrivateRegisterScopedSessionKeyParamsSchema,
    ) -> PrivateRegisterScopedSessionKeyResultSchema:
        """
        Registers a new session key bounded to a scope without a transaction attached.

        If you want to register an admin key, you must provide a signed raw transaction.

        Required minimum session key permission level is `account`
        """

        method = "private/register_scoped_session_key"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateRegisterScopedSessionKeyResultSchema)

        return result

    def get_mmp_config(
        self,
        params: PrivateGetMmpConfigParamsSchema,
    ) -> List[MMPConfigResultSchema]:
        """
        Get the current mmp config for a subaccount (optionally filtered by currency)

        Required minimum session key permission level is `read_only`
        """

        method = "private/get_mmp_config"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, list[MMPConfigResultSchema])

        return result

    def set_mmp_config(
        self,
        params: PrivateSetMmpConfigParamsSchema,
    ) -> PrivateSetMmpConfigResultSchema:
        """
        Set the mmp config for the subaccount and currency

        Required minimum session key permission level is `account`
        """

        method = "private/set_mmp_config"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, PrivateSetMmpConfigResultSchema)

        return result

    def reset_mmp(
        self,
        params: PrivateResetMmpParamsSchema,
    ) -> Result:
        """
        Resets (unfreezes) the mmp state for a subaccount (optionally filtered by
        currency)

        Required minimum session key permission level is `account`
        """

        method = "private/reset_mmp"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, Result)

        return result

    def set_cancel_on_disconnect(
        self,
        params: PrivateSetCancelOnDisconnectParamsSchema,
    ) -> Result:
        """
        Enables cancel on disconnect for the account

        Required minimum session key permission level is `account`
        """

        method = "private/set_cancel_on_disconnect"
        envelope = self._session._send_request(method, params=params)
        result = decode_result(envelope, Result)

        return result


# ============================================================================
# Channel Subscription Classes
# ============================================================================


class PublicChannels:
    """public channel subscriptions"""

    def __init__(self, session: WebSocketSession):
        self._session = session

    def auctions_watch(
        self,
        callback: Callable[[List[AuctionResultSchema]], None],
    ) -> SubscriptionResult:
        """
        Subscribe to state of ongoing auctions.

        Args:
            callback: Callback function to handle notifications

        Returns:
            Subscription result with status and current subscriptions
        """

        channel = "auctions.watch".format()
        envelope = self._session.subscribe(channel, callback, List[AuctionResultSchema])
        result = decode_result(envelope, SubscriptionResult)

        return result

    def margin_watch(
        self,
        callback: Callable[[List[MarginWatchResultSchema]], None],
    ) -> SubscriptionResult:
        """
        Subscribe to state of margin and MtM of all users.

        Args:
            callback: Callback function to handle notifications

        Returns:
            Subscription result with status and current subscriptions
        """

        channel = "margin.watch".format()
        envelope = self._session.subscribe(channel, callback, List[MarginWatchResultSchema])
        result = decode_result(envelope, SubscriptionResult)

        return result

    def orderbook_group_depth_by_instrument_name(
        self,
        instrument_name: str,
        group: Group,
        depth: Depth,
        callback: Callable[[OrderbookInstrumentNameGroupDepthPublisherDataSchema], None],
    ) -> SubscriptionResult:
        """
        Periodically publishes bids and asks for an instrument.

        The 100ms orderbook emits at 1s intervals if the orderbook is not changing,
        otherwise emits at 100ms intervals.

        Args:
            instrument_name: Instrument Name
            group: Group
            depth: Depth
            callback: Callback function to handle notifications

        Returns:
            Subscription result with status and current subscriptions
        """

        channel = "orderbook.{instrument_name}.{group}.{depth}".format(
            instrument_name=instrument_name.value if isinstance(instrument_name, Enum) else instrument_name,
            group=group.value if isinstance(group, Enum) else group,
            depth=depth.value if isinstance(depth, Enum) else depth,
        )
        envelope = self._session.subscribe(channel, callback, OrderbookInstrumentNameGroupDepthPublisherDataSchema)
        result = decode_result(envelope, SubscriptionResult)

        return result

    def spot_feed_by_currency(
        self,
        currency: str,
        callback: Callable[[SpotFeedCurrencyPublisherDataSchema], None],
    ) -> SubscriptionResult:
        """
        Periodically publishes spot index price by currency.

        Args:
            currency: Currency
            callback: Callback function to handle notifications

        Returns:
            Subscription result with status and current subscriptions
        """

        channel = "spot_feed.{currency}".format(
            currency=currency.value if isinstance(currency, Enum) else currency,
        )
        envelope = self._session.subscribe(channel, callback, SpotFeedCurrencyPublisherDataSchema)
        result = decode_result(envelope, SubscriptionResult)

        return result

    def ticker_slim_interval_by_instrument_name(
        self,
        instrument_name: str,
        interval: Interval,
        callback: Callable[[TickerSlimInstrumentNameIntervalPublisherDataSchema], None],
    ) -> SubscriptionResult:
        """
        Periodically publishes ticker info (best bid / ask, instrument contraints, fees,
        etc.) for a single instrument.

        The 100ms ticker emits at 1s intervals if best bid / ask are not changing,
        otherwise emits at 100ms interval.

        The 1s ticker always emits at 1s intervals.

        Args:
            instrument_name: Instrument Name
            interval: Interval
            callback: Callback function to handle notifications

        Returns:
            Subscription result with status and current subscriptions
        """

        channel = "ticker_slim.{instrument_name}.{interval}".format(
            instrument_name=instrument_name.value if isinstance(instrument_name, Enum) else instrument_name,
            interval=interval.value if isinstance(interval, Enum) else interval,
        )
        envelope = self._session.subscribe(channel, callback, TickerSlimInstrumentNameIntervalPublisherDataSchema)
        result = decode_result(envelope, SubscriptionResult)

        return result

    def trades_by_instrument_name(
        self,
        instrument_name: str,
        callback: Callable[[Any], None],
    ) -> SubscriptionResult:
        """
        Subscribe to trades (order executions) for a given instrument name.

        Args:
            instrument_name: Instrument Name
            callback: Callback function to handle notifications

        Returns:
            Subscription result with status and current subscriptions
        """

        channel = "trades.{instrument_name}".format(
            instrument_name=instrument_name.value if isinstance(instrument_name, Enum) else instrument_name,
        )
        envelope = self._session.subscribe(channel, callback, Any)
        result = decode_result(envelope, SubscriptionResult)

        return result

    def trades_by_instrument_type(
        self,
        instrument_type: InstrumentType,
        currency: str,
        callback: Callable[[List[TradePublicResponseSchema]], None],
    ) -> SubscriptionResult:
        """
        Subscribe to trades (order executions) for a given instrument type and currency.

        Args:
            instrument_type: Instrument Type
            currency: Currency
            callback: Callback function to handle notifications

        Returns:
            Subscription result with status and current subscriptions
        """

        channel = "trades.{instrument_type}.{currency}".format(
            instrument_type=instrument_type.value if isinstance(instrument_type, Enum) else instrument_type,
            currency=currency.value if isinstance(currency, Enum) else currency,
        )
        envelope = self._session.subscribe(channel, callback, List[TradePublicResponseSchema])
        result = decode_result(envelope, SubscriptionResult)

        return result

    def trades_tx_status_by_instrument_type(
        self,
        instrument_type: InstrumentType,
        currency: str,
        tx_status: TxStatus2,
        callback: Callable[[List[TradeSettledPublicResponseSchema]], None],
    ) -> SubscriptionResult:
        """
        Subscribe to the status on on-chain trade settlement events for a given
        instrument type and currency.

        Args:
            instrument_type: Instrument Type
            currency: Currency
            tx_status: Tx Status
            callback: Callback function to handle notifications

        Returns:
            Subscription result with status and current subscriptions
        """

        channel = "trades.{instrument_type}.{currency}.{tx_status}".format(
            instrument_type=instrument_type.value if isinstance(instrument_type, Enum) else instrument_type,
            currency=currency.value if isinstance(currency, Enum) else currency,
            tx_status=tx_status.value if isinstance(tx_status, Enum) else tx_status,
        )
        envelope = self._session.subscribe(channel, callback, List[TradeSettledPublicResponseSchema])
        result = decode_result(envelope, SubscriptionResult)

        return result


class PrivateChannels:
    """private channel subscriptions"""

    def __init__(self, session: WebSocketSession):
        self._session = session

    def balances_by_subaccount_id(
        self,
        subaccount_id: str,
        callback: Callable[[List[BalanceUpdateSchema]], None],
    ) -> SubscriptionResult:
        """
        Subscribe to changes in user's positions for a given subaccount ID.

        For perpetuals, additional balance updates are emitted under the name
        Q-{ccy}-PERP where Q stands for "quote".

        This balance is a proxy for an on-chain state of lastMarkPrice.

        Because of a synchronization lag with the on-chain state, the orderbook instead
        keeps track of a running total cost of perpetual trades,

        For example:

        Q-ETH-PERP balance of $6,600 and an ETH-PERP balance of 3 means the
        lastMarkPrice state is estimated to be $2,200.

        Args:
            subaccount_id: Subaccount Id
            callback: Callback function to handle notifications

        Returns:
            Subscription result with status and current subscriptions
        """

        channel = "{subaccount_id}.balances".format(
            subaccount_id=subaccount_id.value if isinstance(subaccount_id, Enum) else subaccount_id,
        )
        envelope = self._session.subscribe(channel, callback, List[BalanceUpdateSchema])
        result = decode_result(envelope, SubscriptionResult)

        return result

    def best_quotes_by_subaccount_id(
        self,
        subaccount_id: str,
        callback: Callable[[List[BestQuoteChannelResultSchema]], None],
    ) -> SubscriptionResult:
        """
        Subscribe to best quote state for a given subaccount ID.

        This will notify the user about the best quote available for the RFQ they have
        sent.

        Args:
            subaccount_id: Subaccount Id
            callback: Callback function to handle notifications

        Returns:
            Subscription result with status and current subscriptions
        """

        channel = "{subaccount_id}.best.quotes".format(
            subaccount_id=subaccount_id.value if isinstance(subaccount_id, Enum) else subaccount_id,
        )
        envelope = self._session.subscribe(channel, callback, List[BestQuoteChannelResultSchema])
        result = decode_result(envelope, SubscriptionResult)

        return result

    def orders_by_subaccount_id(
        self,
        subaccount_id: str,
        callback: Callable[[List[OrderResponseSchema]], None],
    ) -> SubscriptionResult:
        """
        Subscribe to changes in user's orders for a given subaccount ID.

        Args:
            subaccount_id: Subaccount Id
            callback: Callback function to handle notifications

        Returns:
            Subscription result with status and current subscriptions
        """

        channel = "{subaccount_id}.orders".format(
            subaccount_id=subaccount_id.value if isinstance(subaccount_id, Enum) else subaccount_id,
        )
        envelope = self._session.subscribe(channel, callback, List[OrderResponseSchema])
        result = decode_result(envelope, SubscriptionResult)

        return result

    def quotes_by_subaccount_id(
        self,
        subaccount_id: str,
        callback: Callable[[List[QuoteResultSchema]], None],
    ) -> SubscriptionResult:
        """
        Subscribe to quote state for a given subaccount ID.

        This will notify the usser about the state change of the quotes they have sent.

        Args:
            subaccount_id: Subaccount Id
            callback: Callback function to handle notifications

        Returns:
            Subscription result with status and current subscriptions
        """

        channel = "{subaccount_id}.quotes".format(
            subaccount_id=subaccount_id.value if isinstance(subaccount_id, Enum) else subaccount_id,
        )
        envelope = self._session.subscribe(channel, callback, List[QuoteResultSchema])
        result = decode_result(envelope, SubscriptionResult)

        return result

    def trades_by_subaccount_id(
        self,
        subaccount_id: str,
        callback: Callable[[Any], None],
    ) -> SubscriptionResult:
        """
        Subscribe to user's trades (order executions) for a given subaccount ID.

        Args:
            subaccount_id: Subaccount Id
            callback: Callback function to handle notifications

        Returns:
            Subscription result with status and current subscriptions
        """

        channel = "{subaccount_id}.trades".format(
            subaccount_id=subaccount_id.value if isinstance(subaccount_id, Enum) else subaccount_id,
        )
        envelope = self._session.subscribe(channel, callback, Any)
        result = decode_result(envelope, SubscriptionResult)

        return result

    def trades_tx_status_by_subaccount_id(
        self,
        subaccount_id: int,
        tx_status: TxStatus2,
        callback: Callable[[List[TradeResponseSchema]], None],
    ) -> SubscriptionResult:
        """
        Subscribe to user's trade settlement for a given subaccount ID.

        Args:
            subaccount_id: Subaccount Id
            tx_status: Tx Status
            callback: Callback function to handle notifications

        Returns:
            Subscription result with status and current subscriptions
        """

        channel = "{subaccount_id}.trades.{tx_status}".format(
            subaccount_id=subaccount_id.value if isinstance(subaccount_id, Enum) else subaccount_id,
            tx_status=tx_status.value if isinstance(tx_status, Enum) else tx_status,
        )
        envelope = self._session.subscribe(channel, callback, List[TradeResponseSchema])
        result = decode_result(envelope, SubscriptionResult)

        return result

    def rfqs_by_wallet(
        self,
        callback: Callable[[List[RFQResultPublicSchema]], None],
    ) -> SubscriptionResult:
        """
        Subscribe to RFQs directed to a given wallet.

        Args:
            callback: Callback function to handle notifications

        Returns:
            Subscription result with status and current subscriptions
        """

        channel = "wallet.rfqs".format()
        envelope = self._session.subscribe(channel, callback, List[RFQResultPublicSchema])
        result = decode_result(envelope, SubscriptionResult)

        return result


# ============================================================================
# Combined API Classes
# ============================================================================


class PublicAPI:
    """Combined  public API - RPC and channels"""

    def __init__(self, session: WebSocketSession):
        self.rpc = PublicRPC(session)

        self.channels = PublicChannels(session)


class PrivateAPI:
    """Combined  private API - RPC and channels"""

    def __init__(self, session: WebSocketSession):
        self.rpc = PrivateRPC(session)

        self.channels = PrivateChannels(session)
