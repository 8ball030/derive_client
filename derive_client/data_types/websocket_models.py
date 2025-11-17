# ruff: noqa: E741,E501
from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from msgspec import Struct

from derive_client.data_types.generated_models import (
    AggregateTradingStatsSchema,
    CancelReason,
    CancelReason1,
    Direction,
    InstrumentType,
    InvalidReason,
    LegPricedSchema,
    LegUnpricedSchema,
    LiquidityRole,
    MarginType,
    OpenInterestStatsSchema,
    OptionPricingSchema,
    OptionPublicDetailsSchema,
    OrderStatus,
    OrderType,
    PerpPublicDetailsSchema,
    PrivateGetOpenOrdersParamsSchema,
    PrivateGetSubaccountsParamsSchema,
    PublicGetAllCurrenciesParamsSchema,
    PublicGetCurrencyParamsSchema,
    PublicGetInstrumentParamsSchema,
    PublicMarginWatchResultSchema,
    RPCErrorFormatSchema,
    Status,
    TimeInForce,
    TradeResponseSchema,
    TriggerPriceType,
    TriggerType,
    TxStatus,
    TxStatus2,
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


class InstrumentType(Enum):
    erc20 = 'erc20'
    option = 'option'
    perp = 'perp'


class CollateralPublicResponseSchema(Struct):
    amount: Decimal
    asset_name: str
    asset_type: InstrumentType
    initial_margin: Decimal
    maintenance_margin: Decimal
    mark_price: Decimal
    mark_value: Decimal


class PositionPublicResponseSchema(Struct):
    amount: Decimal
    delta: Decimal
    gamma: Decimal
    index_price: Decimal
    initial_margin: Decimal
    instrument_name: str
    instrument_type: InstrumentType
    maintenance_margin: Decimal
    mark_price: Decimal
    mark_value: Decimal
    theta: Decimal
    vega: Decimal
    liquidation_price: Optional[Decimal] = None


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


class SpotFeedCurrencyChannelSchema(PublicGetCurrencyParamsSchema):
    pass


class SpotFeedSnapshotSchema(Struct):
    confidence: Decimal
    confidence_prev_daily: Decimal
    price: Decimal
    price_prev_daily: Decimal
    timestamp_prev_daily: int


class SubaccountIdBalancesChannelSchema(PrivateGetOpenOrdersParamsSchema):
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


class OrderResponseSchema(Struct):
    amount: Decimal
    average_price: Decimal
    cancel_reason: CancelReason
    creation_timestamp: int
    direction: Direction
    filled_amount: Decimal
    instrument_name: str
    is_transfer: bool
    label: str
    last_update_timestamp: int
    limit_price: Decimal
    max_fee: Decimal
    mmp: bool
    nonce: int
    order_fee: Decimal
    order_id: str
    order_status: OrderStatus
    order_type: OrderType
    signature: str
    signature_expiry_sec: int
    signer: str
    subaccount_id: int
    time_in_force: TimeInForce
    quote_id: Optional[str] = None
    replaced_order_id: Optional[str] = None
    trigger_price: Optional[Decimal] = None
    trigger_price_type: TriggerPriceType = None
    trigger_reject_message: Optional[str] = None
    trigger_type: TriggerType = None


class SubaccountIdQuotesChannelSchema(SubaccountIdBalancesChannelSchema):
    pass


class QuoteResultSchema(Struct):
    cancel_reason: CancelReason1
    creation_timestamp: int
    direction: Direction
    fee: Decimal
    fill_pct: Decimal
    is_transfer: bool
    label: str
    last_update_timestamp: int
    legs: List[LegPricedSchema]
    legs_hash: str
    liquidity_role: LiquidityRole
    max_fee: Decimal
    mmp: bool
    nonce: int
    quote_id: str
    rfq_id: str
    signature: str
    signature_expiry_sec: int
    signer: str
    status: Status
    subaccount_id: int
    tx_status: TxStatus
    tx_hash: Optional[str] = None


class SubaccountIdTradesChannelSchema(SubaccountIdBalancesChannelSchema):
    pass


class TxStatus2(Enum):
    settled = 'settled'
    reverted = 'reverted'
    timed_out = 'timed_out'


class SubaccountIdTradesTxStatusChannelSchema(Struct):
    subaccount_id: int
    tx_status: TxStatus2


class SubaccountIdTradesTxStatusNotificationParamsSchema(Struct):
    channel: str
    data: List[TradeResponseSchema]


class Interval(Enum):
    field_100 = '100'
    field_1000 = '1000'


class TickerInstrumentNameIntervalChannelSchema(Struct):
    instrument_name: str
    interval: Interval


class ERC20PublicDetailsSchema(Struct):
    decimals: int
    borrow_index: Decimal = Decimal('1')
    supply_index: Decimal = Decimal('1')
    underlying_erc20_address: str = ''


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
    instrument_type: InstrumentType


class TradesInstrumentTypeCurrencyNotificationParamsSchema(Struct):
    channel: str
    data: List[TradePublicResponseSchema]


class TradesInstrumentTypeCurrencyTxStatusChannelSchema(Struct):
    currency: str
    instrument_type: InstrumentType
    tx_status: TxStatus2


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
    tx_status: TxStatus2
    wallet: str
    quote_id: Optional[str] = None


class WalletRfqsChannelSchema(PrivateGetSubaccountsParamsSchema):
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


class QuoteResultPublicSchema(Struct):
    cancel_reason: CancelReason1
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


class InstrumentTickerSchema(Struct):
    amount_step: Decimal
    base_asset_address: str
    base_asset_sub_id: str
    base_currency: str
    base_fee: Decimal
    best_ask_amount: Decimal
    best_ask_price: Decimal
    best_bid_amount: Decimal
    best_bid_price: Decimal
    fifo_min_allocation: Decimal
    five_percent_ask_depth: Decimal
    five_percent_bid_depth: Decimal
    index_price: Decimal
    instrument_name: str
    instrument_type: InstrumentType
    is_active: bool
    maker_fee_rate: Decimal
    mark_price: Decimal
    max_price: Decimal
    maximum_amount: Decimal
    min_price: Decimal
    minimum_amount: Decimal
    open_interest: Dict[str, List[OpenInterestStatsSchema]]
    pro_rata_amount_step: Decimal
    pro_rata_fraction: Decimal
    quote_currency: str
    scheduled_activation: int
    scheduled_deactivation: int
    stats: AggregateTradingStatsSchema
    taker_fee_rate: Decimal
    tick_size: Decimal
    timestamp: int
    erc20_details: Optional[ERC20PublicDetailsSchema] = None
    option_details: Optional[OptionPublicDetailsSchema] = None
    option_pricing: Optional[OptionPricingSchema] = None
    perp_details: Optional[PerpPublicDetailsSchema] = None
    mark_price_fee_rate_cap: Optional[Decimal] = None


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


class RFQResultPublicSchema(Struct):
    cancel_reason: CancelReason1
    creation_timestamp: int
    filled_direction: Direction
    filled_pct: Decimal
    last_update_timestamp: int
    legs: List[LegUnpricedSchema]
    partial_fill_step: Decimal
    rfq_id: str
    status: Status
    subaccount_id: int
    valid_until: int
    total_cost: Optional[Decimal] = None


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


class RFQGetBestQuoteResultSchema(Struct):
    direction: Direction
    estimated_fee: Decimal
    estimated_realized_pnl: Decimal
    estimated_realized_pnl_excl_fees: Decimal
    estimated_total_cost: Decimal
    filled_pct: Decimal
    invalid_reason: InvalidReason
    is_valid: bool
    post_initial_margin: Decimal
    pre_initial_margin: Decimal
    suggested_max_fee: Decimal
    best_quote: Optional[QuoteResultPublicSchema] = None
    down_liquidation_price: Optional[Decimal] = None
    orderbook_total_cost: Optional[Decimal] = None
    post_liquidation_price: Optional[Decimal] = None
    up_liquidation_price: Optional[Decimal] = None


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


class TickerInstrumentNameIntervalPublisherDataSchema(Struct):
    instrument_ticker: InstrumentTickerSchema
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


class WalletRfqsNotificationParamsSchema(Struct):
    channel: str
    data: List[RFQResultPublicSchema]


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


class BestQuoteChannelResultSchema(Struct):
    rfq_id: str
    error: Optional[RPCErrorFormatSchema] = None
    result: Optional[RFQGetBestQuoteResultSchema] = None


class TickerInstrumentNameIntervalNotificationParamsSchema(Struct):
    channel: str
    data: TickerInstrumentNameIntervalPublisherDataSchema


class WalletRfqsNotificationSchema(Struct):
    method: str
    params: WalletRfqsNotificationParamsSchema


class WalletRfqsPubSubSchema(Struct):
    channel_params: WalletRfqsChannelSchema
    notification: WalletRfqsNotificationSchema


class SubaccountIdBestQuotesNotificationParamsSchema(Struct):
    channel: str
    data: List[BestQuoteChannelResultSchema]


class TickerInstrumentNameIntervalNotificationSchema(Struct):
    method: str
    params: TickerInstrumentNameIntervalNotificationParamsSchema


class TickerInstrumentNameIntervalPubSubSchema(Struct):
    channel_params: TickerInstrumentNameIntervalChannelSchema
    notification: TickerInstrumentNameIntervalNotificationSchema


class SubaccountIdBestQuotesNotificationSchema(Struct):
    method: str
    params: SubaccountIdBestQuotesNotificationParamsSchema


class SubaccountIdBestQuotesPubSubSchema(Struct):
    channel_params: SubaccountIdBestQuotesChannelSchema
    notification: SubaccountIdBestQuotesNotificationSchema
