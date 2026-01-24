# ruff: noqa: E741,E501
from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from msgspec import Struct

from derive_client.data_types.generated_models import (
    AssetType,
    CancelReason,
    Direction,
    LegPricedSchema,
    LegUnpricedSchema,
    LiquidityRole,
    MarginType,
    OrderResponseSchema,
    PrivateGetAllPortfoliosParamsSchema,
    PrivateGetCollateralsParamsSchema,
    PrivateRfqGetBestQuoteResultSchema,
    PublicGetAllCurrenciesParamsSchema,
    PublicGetInstrumentParamsSchema,
    PublicGetOptionSettlementPricesParamsSchema,
    PublicMarginWatchResultSchema,
    QuoteResultSchema,
    RFQResultPublicSchema,
    RPCErrorFormatSchema,
    Status,
    TickerSlimSchema,
    TradeResponseSchema,
    TxStatus,
    TxStatus4,
)

DeriveWebsocketChannelSchemas = Any


class AuctionsWatchChannelSchema(PublicGetAllCurrenciesParamsSchema):
    pass


class State(Enum):
    ongoing = 'ongoing'
    ended = 'ended'


class AuctionDetailsSchema(Struct):
    estimated_bid_price: Decimal
    estimated_discount_pnl: Decimal
    estimated_mtm: Decimal
    estimated_percent_bid: Decimal
    last_seen_trade_id: int
    margin_type: MarginType
    min_cash_transfer: Decimal
    min_price_limit: Decimal
    subaccount_balances: Dict[str, Decimal]
    currency: Optional[str] = None


class MarginWatchChannelSchema(AuctionsWatchChannelSchema):
    pass


class Depth(Enum):
    field_1 = '1'
    field_10 = '10'
    field_20 = '20'
    field_100 = '100'


class Group(Enum):
    field_1 = '1'
    field_10 = '10'
    field_100 = '100'


class OrderbookInstrumentNameGroupDepthChannelSchema(Struct):
    depth: Depth
    group: Group
    instrument_name: str


class OrderbookInstrumentNameGroupDepthPublisherDataSchema(Struct):
    asks: List[List[Decimal]]
    bids: List[List[Decimal]]
    instrument_name: str
    publish_id: int
    timestamp: int


class SpotFeedCurrencyChannelSchema(PublicGetOptionSettlementPricesParamsSchema):
    pass


class SpotFeedSnapshotSchema(Struct):
    confidence: Decimal
    confidence_prev_daily: Decimal
    price: Decimal
    price_prev_daily: Decimal
    timestamp_prev_daily: int


class SubaccountIdBalancesChannelSchema(PrivateGetCollateralsParamsSchema):
    pass


class UpdateType(Enum):
    trade = 'trade'
    asset_deposit = 'asset_deposit'
    asset_withdrawal = 'asset_withdrawal'
    transfer = 'transfer'
    subaccount_deposit = 'subaccount_deposit'
    subaccount_withdrawal = 'subaccount_withdrawal'
    liquidation = 'liquidation'
    liquidator = 'liquidator'
    onchain_drift_fix = 'onchain_drift_fix'
    perp_settlement = 'perp_settlement'
    option_settlement = 'option_settlement'
    interest_accrual = 'interest_accrual'
    onchain_revert = 'onchain_revert'
    double_revert = 'double_revert'


class BalanceUpdateSchema(Struct):
    name: str
    new_balance: Decimal
    previous_balance: Decimal
    update_type: UpdateType


class SubaccountIdBestQuotesChannelSchema(SubaccountIdBalancesChannelSchema):
    pass


class SubaccountIdOrdersChannelSchema(SubaccountIdBalancesChannelSchema):
    pass


class SubaccountIdQuotesChannelSchema(SubaccountIdBalancesChannelSchema):
    pass


class SubaccountIdTradesChannelSchema(SubaccountIdBalancesChannelSchema):
    pass


class SubaccountIdTradesTxStatusChannelSchema(Struct):
    subaccount_id: int
    tx_status: TxStatus4


class Interval(Enum):
    field_100 = '100'
    field_1000 = '1000'


class TickerSlimInstrumentNameIntervalChannelSchema(Struct):
    instrument_name: str
    interval: Interval


class TradesInstrumentNameChannelSchema(PublicGetInstrumentParamsSchema):
    pass


class TradePublicResponseSchema(Struct):
    direction: Direction
    index_price: Decimal
    instrument_name: str
    mark_price: Decimal
    timestamp: int
    trade_amount: Decimal
    trade_id: str
    trade_price: Decimal
    quote_id: Optional[str] = None


class TradesInstrumentTypeCurrencyChannelSchema(Struct):
    currency: str
    instrument_type: AssetType


class TradesInstrumentTypeCurrencyNotificationParamsSchema(Struct):
    channel: str
    data: List[TradePublicResponseSchema]


class TradesInstrumentTypeCurrencyTxStatusChannelSchema(Struct):
    currency: str
    instrument_type: AssetType
    tx_status: TxStatus4


class TradeSettledPublicResponseSchema(Struct):
    direction: Direction
    expected_rebate: Decimal
    index_price: Decimal
    instrument_name: str
    liquidity_role: LiquidityRole
    mark_price: Decimal
    realized_pnl: Decimal
    realized_pnl_excl_fees: Decimal
    subaccount_id: int
    timestamp: int
    trade_amount: Decimal
    trade_fee: Decimal
    trade_id: str
    trade_price: Decimal
    tx_hash: str
    tx_status: TxStatus4
    wallet: str
    quote_id: Optional[str] = None


class WalletRfqsChannelSchema(PrivateGetAllPortfoliosParamsSchema):
    pass


class LegUnpricedSchema1(LegUnpricedSchema):
    pass


class AuctionResultSchema(Struct):
    state: State
    subaccount_id: int
    timestamp: int
    details: Optional[AuctionDetailsSchema] = None


class MarginWatchResultSchema(PublicMarginWatchResultSchema):
    pass


class OrderbookInstrumentNameGroupDepthNotificationParamsSchema(Struct):
    channel: str
    data: OrderbookInstrumentNameGroupDepthPublisherDataSchema


class SpotFeedCurrencyPublisherDataSchema(Struct):
    feeds: Dict[str, SpotFeedSnapshotSchema]
    timestamp: int


class SubaccountIdBalancesNotificationParamsSchema(Struct):
    channel: str
    data: List[BalanceUpdateSchema]


class SubaccountIdTradesTxStatusNotificationParamsSchema(Struct):
    channel: str
    data: List[TradeResponseSchema]


class TradesInstrumentNameNotificationParamsSchema(TradesInstrumentTypeCurrencyNotificationParamsSchema):
    pass


class TradesInstrumentTypeCurrencyNotificationSchema(Struct):
    method: str
    params: TradesInstrumentTypeCurrencyNotificationParamsSchema


class TradesInstrumentTypeCurrencyPubSubSchema(Struct):
    channel_params: TradesInstrumentTypeCurrencyChannelSchema
    notification: TradesInstrumentTypeCurrencyNotificationSchema


class TradesInstrumentTypeCurrencyTxStatusNotificationParamsSchema(Struct):
    channel: str
    data: List[TradeSettledPublicResponseSchema]


class AuctionsWatchNotificationParamsSchema(Struct):
    channel: str
    data: List[AuctionResultSchema]


class MarginWatchNotificationParamsSchema(Struct):
    channel: str
    data: List[MarginWatchResultSchema]


class OrderbookInstrumentNameGroupDepthNotificationSchema(Struct):
    method: str
    params: OrderbookInstrumentNameGroupDepthNotificationParamsSchema


class OrderbookInstrumentNameGroupDepthPubSubSchema(Struct):
    channel_params: OrderbookInstrumentNameGroupDepthChannelSchema
    notification: OrderbookInstrumentNameGroupDepthNotificationSchema


class SpotFeedCurrencyNotificationParamsSchema(Struct):
    channel: str
    data: SpotFeedCurrencyPublisherDataSchema


class SubaccountIdBalancesNotificationSchema(Struct):
    method: str
    params: SubaccountIdBalancesNotificationParamsSchema


class SubaccountIdBalancesPubSubSchema(Struct):
    channel_params: SubaccountIdBalancesChannelSchema
    notification: SubaccountIdBalancesNotificationSchema


class QuoteResultPublicSchema(Struct):
    cancel_reason: CancelReason
    creation_timestamp: int
    direction: Direction
    fill_pct: Decimal
    last_update_timestamp: int
    legs: List[LegPricedSchema]
    legs_hash: str
    liquidity_role: LiquidityRole
    quote_id: str
    rfq_id: str
    status: Status
    subaccount_id: int
    tx_status: TxStatus
    wallet: str
    tx_hash: Optional[str] = None


class SubaccountIdOrdersNotificationParamsSchema(Struct):
    channel: str
    data: List[OrderResponseSchema]


class SubaccountIdQuotesNotificationParamsSchema(Struct):
    channel: str
    data: List[QuoteResultSchema]


class SubaccountIdTradesNotificationParamsSchema(SubaccountIdTradesTxStatusNotificationParamsSchema):
    pass


class SubaccountIdTradesTxStatusNotificationSchema(Struct):
    method: str
    params: SubaccountIdTradesTxStatusNotificationParamsSchema


class SubaccountIdTradesTxStatusPubSubSchema(Struct):
    channel_params: SubaccountIdTradesTxStatusChannelSchema
    notification: SubaccountIdTradesTxStatusNotificationSchema


class TickerSlimInstrumentNameIntervalPublisherDataSchema(Struct):
    instrument_ticker: TickerSlimSchema
    timestamp: int


class TradesInstrumentNameNotificationSchema(Struct):
    method: str
    params: TradesInstrumentNameNotificationParamsSchema


class TradesInstrumentNamePubSubSchema(Struct):
    channel_params: TradesInstrumentNameChannelSchema
    notification: TradesInstrumentNameNotificationSchema


class TradesInstrumentTypeCurrencyTxStatusNotificationSchema(Struct):
    method: str
    params: TradesInstrumentTypeCurrencyTxStatusNotificationParamsSchema


class TradesInstrumentTypeCurrencyTxStatusPubSubSchema(Struct):
    channel_params: TradesInstrumentTypeCurrencyTxStatusChannelSchema
    notification: TradesInstrumentTypeCurrencyTxStatusNotificationSchema


class AuctionsWatchNotificationSchema(Struct):
    method: str
    params: AuctionsWatchNotificationParamsSchema


class AuctionsWatchPubSubSchema(Struct):
    channel_params: AuctionsWatchChannelSchema
    notification: AuctionsWatchNotificationSchema


class MarginWatchNotificationSchema(Struct):
    method: str
    params: MarginWatchNotificationParamsSchema


class MarginWatchPubSubSchema(Struct):
    channel_params: MarginWatchChannelSchema
    notification: MarginWatchNotificationSchema


class SpotFeedCurrencyNotificationSchema(Struct):
    method: str
    params: SpotFeedCurrencyNotificationParamsSchema


class SpotFeedCurrencyPubSubSchema(Struct):
    channel_params: SpotFeedCurrencyChannelSchema
    notification: SpotFeedCurrencyNotificationSchema


class RFQGetBestQuoteResultSchema(PrivateRfqGetBestQuoteResultSchema):
    pass


class SubaccountIdOrdersNotificationSchema(Struct):
    method: str
    params: SubaccountIdOrdersNotificationParamsSchema


class SubaccountIdOrdersPubSubSchema(Struct):
    channel_params: SubaccountIdOrdersChannelSchema
    notification: SubaccountIdOrdersNotificationSchema


class SubaccountIdQuotesNotificationSchema(Struct):
    method: str
    params: SubaccountIdQuotesNotificationParamsSchema


class SubaccountIdQuotesPubSubSchema(Struct):
    channel_params: SubaccountIdQuotesChannelSchema
    notification: SubaccountIdQuotesNotificationSchema


class SubaccountIdTradesNotificationSchema(Struct):
    method: str
    params: SubaccountIdTradesNotificationParamsSchema


class SubaccountIdTradesPubSubSchema(Struct):
    channel_params: SubaccountIdTradesChannelSchema
    notification: SubaccountIdTradesNotificationSchema


class TickerSlimInstrumentNameIntervalNotificationParamsSchema(Struct):
    channel: str
    data: TickerSlimInstrumentNameIntervalPublisherDataSchema


class WalletRfqsNotificationParamsSchema(Struct):
    channel: str
    data: List[RFQResultPublicSchema]


class BestQuoteChannelResultSchema(Struct):
    rfq_id: str
    error: Optional[RPCErrorFormatSchema] = None
    result: Optional[RFQGetBestQuoteResultSchema] = None


class TickerSlimInstrumentNameIntervalNotificationSchema(Struct):
    method: str
    params: TickerSlimInstrumentNameIntervalNotificationParamsSchema


class TickerSlimInstrumentNameIntervalPubSubSchema(Struct):
    channel_params: TickerSlimInstrumentNameIntervalChannelSchema
    notification: TickerSlimInstrumentNameIntervalNotificationSchema


class WalletRfqsNotificationSchema(Struct):
    method: str
    params: WalletRfqsNotificationParamsSchema


class WalletRfqsPubSubSchema(Struct):
    channel_params: WalletRfqsChannelSchema
    notification: WalletRfqsNotificationSchema


class SubaccountIdBestQuotesNotificationParamsSchema(Struct):
    channel: str
    data: List[BestQuoteChannelResultSchema]


class SubaccountIdBestQuotesNotificationSchema(Struct):
    method: str
    params: SubaccountIdBestQuotesNotificationParamsSchema


class SubaccountIdBestQuotesPubSubSchema(Struct):
    channel_params: SubaccountIdBestQuotesChannelSchema
    notification: SubaccountIdBestQuotesNotificationSchema
