# ruff: noqa: E741,E501
from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from msgspec import Struct


class Period(Enum):
    field_900 = 900
    field_3600 = 3600
    field_14400 = 14400
    field_28800 = 28800
    field_86400 = 86400


class PublicGetFundingRateHistoryParamsSchema(Struct):
    instrument_name: str
    end_timestamp: int = 9223372036854776000
    period: Period = Period(3600)
    start_timestamp: int = 0


class FundingRateSchema(Struct):
    funding_rate: Decimal
    timestamp: int


class PrivateEditSessionKeyParamsSchema(Struct):
    public_session_key: str
    wallet: str
    disable: bool = False
    ip_whitelist: Optional[List[str]] = None
    label: Optional[str] = None


class PrivateEditSessionKeyResultSchema(Struct):
    expiry_sec: int
    ip_whitelist: List[str]
    label: str
    public_session_key: str
    registered_sec: int
    scope: str


class PublicGetLiquidationHistoryParamsSchema(Struct):
    end_timestamp: int = 9223372036854776000
    page: int = 1
    page_size: int = 100
    start_timestamp: int = 0
    subaccount_id: Optional[int] = None


class AuctionType(Enum):
    solvent = 'solvent'
    insolvent = 'insolvent'


class AuctionBidEventSchema(Struct):
    amounts_liquidated: Dict[str, Decimal]
    cash_received: Decimal
    discount_pnl: Decimal
    percent_liquidated: Decimal
    positions_realized_pnl: Dict[str, Decimal]
    positions_realized_pnl_excl_fees: Dict[str, Decimal]
    realized_pnl: Decimal
    realized_pnl_excl_fees: Decimal
    timestamp: int
    tx_hash: str


class PaginationInfoSchema(Struct):
    count: int
    num_pages: int


class PrivateGetOpenOrdersParamsSchema(Struct):
    subaccount_id: int


class CancelReason(Enum):
    field_ = ''
    user_request = 'user_request'
    mmp_trigger = 'mmp_trigger'
    insufficient_margin = 'insufficient_margin'
    signed_max_fee_too_low = 'signed_max_fee_too_low'
    cancel_on_disconnect = 'cancel_on_disconnect'
    ioc_or_market_partial_fill = 'ioc_or_market_partial_fill'
    session_key_deregistered = 'session_key_deregistered'
    subaccount_withdrawn = 'subaccount_withdrawn'
    compliance = 'compliance'
    trigger_failed = 'trigger_failed'
    validation_failed = 'validation_failed'


class Direction(Enum):
    buy = 'buy'
    sell = 'sell'


class OrderStatus(Enum):
    open = 'open'
    filled = 'filled'
    cancelled = 'cancelled'
    expired = 'expired'
    untriggered = 'untriggered'


class OrderType(Enum):
    limit = 'limit'
    market = 'market'


class TimeInForce(Enum):
    gtc = 'gtc'
    post_only = 'post_only'
    fok = 'fok'
    ioc = 'ioc'


class TriggerPriceType(Enum):
    mark = 'mark'
    index = 'index'


class TriggerType(Enum):
    stoploss = 'stoploss'
    takeprofit = 'takeprofit'


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
    trigger_price_type: Optional[TriggerPriceType] = None
    trigger_reject_message: Optional[str] = None
    trigger_type: Optional[TriggerType] = None


class Status(Enum):
    open = 'open'
    filled = 'filled'
    cancelled = 'cancelled'
    expired = 'expired'


class PrivatePollQuotesParamsSchema(Struct):
    subaccount_id: int
    from_timestamp: int = 0
    page: int = 1
    page_size: int = 100
    quote_id: Optional[str] = None
    rfq_id: Optional[str] = None
    status: Optional[Status] = None
    to_timestamp: int = 18446744073709552000


class CancelReason1(Enum):
    field_ = ''
    user_request = 'user_request'
    insufficient_margin = 'insufficient_margin'
    signed_max_fee_too_low = 'signed_max_fee_too_low'
    mmp_trigger = 'mmp_trigger'
    cancel_on_disconnect = 'cancel_on_disconnect'
    session_key_deregistered = 'session_key_deregistered'
    subaccount_withdrawn = 'subaccount_withdrawn'
    rfq_no_longer_open = 'rfq_no_longer_open'
    compliance = 'compliance'


class LiquidityRole(Enum):
    maker = 'maker'
    taker = 'taker'


class TxStatus(Enum):
    requested = 'requested'
    pending = 'pending'
    settled = 'settled'
    reverted = 'reverted'
    ignored = 'ignored'
    timed_out = 'timed_out'


class LegPricedSchema(Struct):
    amount: Decimal
    direction: Direction
    instrument_name: str
    price: Decimal


class PrivateGetTradeHistoryParamsSchema(Struct):
    from_timestamp: int = 0
    instrument_name: Optional[str] = None
    order_id: Optional[str] = None
    page: int = 1
    page_size: int = 100
    quote_id: Optional[str] = None
    subaccount_id: Optional[int] = None
    to_timestamp: int = 18446744073709552000
    wallet: Optional[str] = None


class TradeResponseSchema(Struct):
    direction: Direction
    expected_rebate: Decimal
    index_price: Decimal
    instrument_name: str
    is_transfer: bool
    label: str
    liquidity_role: LiquidityRole
    mark_price: Decimal
    order_id: str
    realized_pnl: Decimal
    realized_pnl_excl_fees: Decimal
    subaccount_id: int
    timestamp: int
    trade_amount: Decimal
    trade_fee: Decimal
    trade_id: str
    trade_price: Decimal
    transaction_id: str
    tx_status: TxStatus
    quote_id: Optional[str] = None
    tx_hash: Optional[str] = None


class InstrumentType(Enum):
    erc20 = 'erc20'
    option = 'option'
    perp = 'perp'


class TxStatus2(Enum):
    settled = 'settled'
    reverted = 'reverted'
    timed_out = 'timed_out'


class PublicGetTradeHistoryParamsSchema(Struct):
    currency: Optional[str] = None
    from_timestamp: int = 0
    instrument_name: Optional[str] = None
    instrument_type: Optional[InstrumentType] = None
    page: int = 1
    page_size: int = 100
    subaccount_id: Optional[int] = None
    to_timestamp: int = 18446744073709552000
    trade_id: Optional[str] = None
    tx_hash: Optional[str] = None
    tx_status: TxStatus2 = TxStatus2('settled')


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


class PublicStatisticsParamsSchema(Struct):
    instrument_name: str
    currency: Optional[str] = None
    end_time: Optional[int] = None


class PublicStatisticsResultSchema(Struct):
    daily_fees: Decimal
    daily_notional_volume: Decimal
    daily_premium_volume: Decimal
    daily_trades: int
    open_interest: Decimal
    total_fees: Decimal
    total_notional_volume: Decimal
    total_premium_volume: Decimal
    total_trades: int


class PublicGetInstrumentParamsSchema(Struct):
    instrument_name: str


class ERC20PublicDetailsSchema(Struct):
    decimals: int
    borrow_index: Decimal = Decimal('1')
    supply_index: Decimal = Decimal('1')
    underlying_erc20_address: str = ''


class OptionType(Enum):
    C = 'C'
    P = 'P'


class OptionPublicDetailsSchema(Struct):
    expiry: int
    index: str
    option_type: OptionType
    strike: Decimal
    settlement_price: Optional[Decimal] = None


class PerpPublicDetailsSchema(Struct):
    aggregate_funding: Decimal
    funding_rate: Decimal
    index: str
    max_rate_per_hour: Decimal
    min_rate_per_hour: Decimal
    static_interest_rate: Decimal


class LegUnpricedSchema(Struct):
    amount: Decimal
    direction: Direction
    instrument_name: str


class PrivateSendRfqResultSchema(Struct):
    cancel_reason: CancelReason1
    creation_timestamp: int
    filled_pct: Decimal
    label: str
    last_update_timestamp: int
    legs: List[LegUnpricedSchema]
    partial_fill_step: Decimal
    rfq_id: str
    status: Status
    subaccount_id: int
    valid_until: int
    wallet: str
    ask_total_cost: Optional[Decimal] = None
    bid_total_cost: Optional[Decimal] = None
    counterparties: Optional[List[str]] = None
    filled_direction: Optional[Direction] = None
    mark_total_cost: Optional[Decimal] = None
    max_total_cost: Optional[Decimal] = None
    min_total_cost: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None


class PrivateGetSubaccountsParamsSchema(Struct):
    wallet: str


class PrivateGetSubaccountsResultSchema(Struct):
    subaccount_ids: List[int]
    wallet: str


class PrivateGetLiquidationHistoryParamsSchema(Struct):
    subaccount_id: int
    end_timestamp: int = 9223372036854776000
    start_timestamp: int = 0


class SignatureDetailsSchema(Struct):
    nonce: int
    signature: str
    signature_expiry_sec: int
    signer: str


class TransferDetailsSchema(Struct):
    address: str
    amount: Decimal
    sub_id: int


class PrivateTransferErc20ResultSchema(Struct):
    status: str
    transaction_id: str


class PrivateCancelAllTriggerOrdersParamsSchema(PrivateGetOpenOrdersParamsSchema):
    pass


class Result(Enum):
    ok = 'ok'


class PrivateCancelAllTriggerOrdersResponseSchema(Struct):
    id: Union[str, int]
    result: Result


class PrivateCancelByNonceParamsSchema(Struct):
    instrument_name: str
    nonce: int
    subaccount_id: int
    wallet: str


class PrivateCancelByNonceResultSchema(Struct):
    cancelled_orders: int


class PublicGetOptionSettlementHistoryParamsSchema(Struct):
    page: int = 1
    page_size: int = 100
    subaccount_id: Optional[int] = None


class OptionSettlementResponseSchema(Struct):
    amount: Decimal
    expiry: int
    instrument_name: str
    option_settlement_pnl: Decimal
    option_settlement_pnl_excl_fees: Decimal
    settlement_price: Decimal
    subaccount_id: int


class PrivateSetMmpConfigParamsSchema(Struct):
    currency: str
    mmp_frozen_time: int
    mmp_interval: int
    subaccount_id: int
    mmp_amount_limit: Decimal = Decimal('0')
    mmp_delta_limit: Decimal = Decimal('0')


class PrivateSetMmpConfigResultSchema(PrivateSetMmpConfigParamsSchema):
    pass


class PublicDepositDebugParamsSchema(Struct):
    amount: Decimal
    asset_name: str
    nonce: int
    signature_expiry_sec: int
    signer: str
    subaccount_id: int
    is_atomic_signing: bool = False


class PublicDepositDebugResultSchema(Struct):
    action_hash: str
    encoded_data: str
    encoded_data_hashed: str
    typed_data_hash: str


class PublicGetReferralPerformanceParamsSchema(Struct):
    end_ms: int
    start_ms: int
    referral_code: Optional[str] = None
    wallet: Optional[str] = None


class ReferralPerformanceByInstrumentTypeSchema(Struct):
    fee_reward: Decimal
    notional_volume: Decimal
    referred_fee: Decimal


class PrivateCancelByInstrumentParamsSchema(Struct):
    instrument_name: str
    subaccount_id: int


class PrivateCancelByInstrumentResultSchema(PrivateCancelByNonceResultSchema):
    pass


class PublicSendQuoteDebugParamsSchema(Struct):
    direction: Direction
    legs: List[LegPricedSchema]
    max_fee: Decimal
    nonce: int
    rfq_id: str
    signature: str
    signature_expiry_sec: int
    signer: str
    subaccount_id: int
    label: str = ''
    mmp: bool = False


class PublicSendQuoteDebugResultSchema(PublicDepositDebugResultSchema):
    pass


class MarginType(Enum):
    PM = 'PM'
    SM = 'SM'
    PM2 = 'PM2'


class PublicCreateSubaccountDebugParamsSchema(Struct):
    amount: Decimal
    asset_name: str
    margin_type: MarginType
    nonce: int
    signature_expiry_sec: int
    signer: str
    wallet: str
    currency: Optional[str] = None


class PublicCreateSubaccountDebugResultSchema(PublicDepositDebugResultSchema):
    pass


class PrivateGetErc20TransferHistoryParamsSchema(PrivateGetLiquidationHistoryParamsSchema):
    pass


class ERC20TransferSchema(Struct):
    amount: Decimal
    asset: str
    counterparty_subaccount_id: int
    is_outgoing: bool
    timestamp: int
    tx_hash: str


class PublicGetLatestSignedFeedsParamsSchema(Struct):
    currency: Optional[str] = None
    expiry: Optional[int] = None


class OracleSignatureDataSchema(Struct):
    signatures: Optional[List[str]] = None
    signers: Optional[List[str]] = None


class Type(Enum):
    P = 'P'
    A = 'A'
    B = 'B'


class PerpFeedDataSchema(Struct):
    confidence: Decimal
    currency: str
    deadline: int
    signatures: OracleSignatureDataSchema
    spot_diff_value: Decimal
    timestamp: int
    type: Type


class RateFeedDataSchema(Struct):
    confidence: Decimal
    currency: str
    deadline: int
    expiry: int
    rate: Decimal
    signatures: OracleSignatureDataSchema
    timestamp: int


class FeedSourceType(Enum):
    S = 'S'
    O = 'O'


class SpotFeedDataSchema(Struct):
    confidence: Decimal
    currency: str
    deadline: int
    price: Decimal
    signatures: OracleSignatureDataSchema
    timestamp: int
    feed_source_type: FeedSourceType = FeedSourceType('S')


class VolSVIParamDataSchema(Struct):
    SVI_a: Decimal
    SVI_b: Decimal
    SVI_fwd: Decimal
    SVI_m: Decimal
    SVI_refTau: Decimal
    SVI_rho: Decimal
    SVI_sigma: Decimal


class PrivateCancelTriggerOrderParamsSchema(Struct):
    order_id: str
    subaccount_id: int


class PrivateCancelTriggerOrderResultSchema(OrderResponseSchema):
    pass


class PublicLoginParamsSchema(Struct):
    signature: str
    timestamp: str
    wallet: str


class PublicLoginResponseSchema(Struct):
    id: Union[str, int]
    result: List[int]


class TradeModuleParamsSchema(Struct):
    amount: Decimal
    direction: Direction
    instrument_name: str
    limit_price: Decimal
    max_fee: Decimal
    nonce: int
    signature: str
    signature_expiry_sec: int
    signer: str
    subaccount_id: int


class PrivateTransferPositionResultSchema(Struct):
    maker_order: OrderResponseSchema
    maker_trade: TradeResponseSchema
    taker_order: OrderResponseSchema
    taker_trade: TradeResponseSchema


class PublicMarginWatchParamsSchema(Struct):
    subaccount_id: int
    force_onchain: bool = False


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


class PublicBuildRegisterSessionKeyTxParamsSchema(Struct):
    expiry_sec: int
    public_session_key: str
    wallet: str
    gas: Optional[int] = None
    nonce: Optional[int] = None


class PublicBuildRegisterSessionKeyTxResultSchema(Struct):
    tx_params: Dict[str, Any]


class PublicGetAllCurrenciesParamsSchema(Struct):
    pass


class MarketType(Enum):
    ALL = 'ALL'
    SRM_BASE_ONLY = 'SRM_BASE_ONLY'
    SRM_OPTION_ONLY = 'SRM_OPTION_ONLY'
    SRM_PERP_ONLY = 'SRM_PERP_ONLY'
    CASH = 'CASH'


class OpenInterestStatsSchema(Struct):
    current_open_interest: Decimal
    interest_cap: Decimal
    manager_currency: Optional[str] = None


class ManagerContractResponseSchema(Struct):
    address: str
    margin_type: MarginType
    currency: Optional[str] = None


class PM2CollateralDiscountsSchema(Struct):
    im_discount: Decimal
    manager_currency: str
    mm_discount: Decimal


class ProtocolAssetAddressesSchema(Struct):
    option: Optional[str] = None
    perp: Optional[str] = None
    spot: Optional[str] = None
    underlying_erc20: Optional[str] = None


class PrivateGetAccountParamsSchema(PrivateGetSubaccountsParamsSchema):
    pass


class AccountFeeInfoSchema(Struct):
    base_fee_discount: Decimal
    rfq_maker_discount: Decimal
    rfq_taker_discount: Decimal
    option_maker_fee: Optional[Decimal] = None
    option_taker_fee: Optional[Decimal] = None
    perp_maker_fee: Optional[Decimal] = None
    perp_taker_fee: Optional[Decimal] = None
    spot_maker_fee: Optional[Decimal] = None
    spot_taker_fee: Optional[Decimal] = None


class PrivateSendQuoteParamsSchema(PublicSendQuoteDebugParamsSchema):
    pass


class PrivateSendQuoteResultSchema(Struct):
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
    tx_hash: Optional[str] = None
    tx_status: Optional[TxStatus] = None


class PrivateGetCollateralsParamsSchema(PrivateGetOpenOrdersParamsSchema):
    pass


class CollateralResponseSchema(Struct):
    amount: Decimal
    amount_step: Decimal
    asset_name: str
    asset_type: InstrumentType
    average_price: Decimal
    average_price_excl_fees: Decimal
    creation_timestamp: int
    cumulative_interest: Decimal
    currency: str
    delta: Decimal
    delta_currency: str
    initial_margin: Decimal
    maintenance_margin: Decimal
    mark_price: Decimal
    mark_value: Decimal
    open_orders_margin: Decimal
    pending_interest: Decimal
    realized_pnl: Decimal
    realized_pnl_excl_fees: Decimal
    total_fees: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_excl_fees: Decimal


class PublicGetTickerParamsSchema(PublicGetInstrumentParamsSchema):
    pass


class OptionPricingSchema(Struct):
    ask_iv: Decimal
    bid_iv: Decimal
    delta: Decimal
    discount_factor: Decimal
    forward_price: Decimal
    gamma: Decimal
    iv: Decimal
    mark_price: Decimal
    rho: Decimal
    theta: Decimal
    vega: Decimal


class AggregateTradingStatsSchema(Struct):
    contract_volume: Decimal
    high: Decimal
    low: Decimal
    num_trades: Decimal
    open_interest: Decimal
    percent_change: Decimal
    usd_change: Decimal


class PrivateReplaceQuoteParamsSchema(Struct):
    direction: Direction
    legs: List[LegPricedSchema]
    max_fee: Decimal
    nonce: int
    rfq_id: str
    signature: str
    signature_expiry_sec: int
    signer: str
    subaccount_id: int
    label: str = ''
    mmp: bool = False
    nonce_to_cancel: Optional[int] = None
    quote_id_to_cancel: Optional[str] = None


class QuoteResultSchema(PrivateSendQuoteResultSchema):
    pass


class RPCErrorFormatSchema(Struct):
    code: int
    message: str
    data: Optional[str] = None


class PrivateGetAllPortfoliosParamsSchema(PrivateGetSubaccountsParamsSchema):
    pass


class PositionResponseSchema(Struct):
    amount: Decimal
    amount_step: Decimal
    average_price: Decimal
    average_price_excl_fees: Decimal
    creation_timestamp: int
    cumulative_funding: Decimal
    delta: Decimal
    gamma: Decimal
    index_price: Decimal
    initial_margin: Decimal
    instrument_name: str
    instrument_type: InstrumentType
    maintenance_margin: Decimal
    mark_price: Decimal
    mark_value: Decimal
    net_settlements: Decimal
    open_orders_margin: Decimal
    pending_funding: Decimal
    realized_pnl: Decimal
    realized_pnl_excl_fees: Decimal
    theta: Decimal
    total_fees: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_excl_fees: Decimal
    vega: Decimal
    leverage: Optional[Decimal] = None
    liquidation_price: Optional[Decimal] = None


class PrivateSessionKeysParamsSchema(PrivateGetSubaccountsParamsSchema):
    pass


class SessionKeyResponseSchema(PrivateEditSessionKeyResultSchema):
    pass


class PrivateExpiredAndCancelledHistoryParamsSchema(Struct):
    end_timestamp: int
    expiry: int
    start_timestamp: int
    subaccount_id: int
    wallet: str


class PrivateExpiredAndCancelledHistoryResultSchema(Struct):
    presigned_urls: List[str]


class PrivateGetQuotesParamsSchema(PrivatePollQuotesParamsSchema):
    pass


class PrivateGetQuotesResultSchema(Struct):
    quotes: List[QuoteResultSchema]
    pagination: PaginationInfoSchema | None = None


class PublicGetVaultShareParamsSchema(Struct):
    from_timestamp_sec: int
    to_timestamp_sec: int
    vault_name: str
    page: int = 1
    page_size: int = 100


class VaultShareResponseSchema(Struct):
    base_value: Decimal
    block_number: int
    block_timestamp: int
    usd_value: Decimal
    underlying_value: Optional[Decimal] = None


class PublicRegisterSessionKeyParamsSchema(Struct):
    expiry_sec: int
    label: str
    public_session_key: str
    signed_raw_tx: str
    wallet: str


class PublicRegisterSessionKeyResultSchema(Struct):
    label: str
    public_session_key: str
    transaction_id: str


class Scope(Enum):
    admin = 'admin'
    account = 'account'
    read_only = 'read_only'


class PrivateRegisterScopedSessionKeyParamsSchema(Struct):
    expiry_sec: int
    public_session_key: str
    wallet: str
    ip_whitelist: Optional[List[str]] = None
    label: Optional[str] = None
    scope: Scope = Scope('read_only')
    signed_raw_tx: Optional[str] = None


class PrivateRegisterScopedSessionKeyResultSchema(Struct):
    expiry_sec: int
    public_session_key: str
    scope: Scope
    ip_whitelist: Optional[List[str]] = None
    label: Optional[str] = None
    transaction_id: Optional[str] = None


class PrivateGetMmpConfigParamsSchema(Struct):
    subaccount_id: int
    currency: Optional[str] = None


class MMPConfigResultSchema(Struct):
    currency: str
    is_frozen: bool
    mmp_frozen_time: int
    mmp_interval: int
    mmp_unfreeze_time: int
    subaccount_id: int
    mmp_amount_limit: Decimal = Decimal('0')
    mmp_delta_limit: Decimal = Decimal('0')


class PublicExecuteQuoteDebugParamsSchema(Struct):
    direction: Direction
    legs: List[LegPricedSchema]
    max_fee: Decimal
    nonce: int
    quote_id: str
    rfq_id: str
    signature: str
    signature_expiry_sec: int
    signer: str
    subaccount_id: int
    enable_taker_protection: bool = False
    label: str = ''


class PublicExecuteQuoteDebugResultSchema(Struct):
    action_hash: str
    encoded_data: str
    encoded_data_hashed: str
    encoded_legs: str
    legs_hash: str
    typed_data_hash: str


class Status6(Enum):
    unseen = 'unseen'
    seen = 'seen'
    hidden = 'hidden'


class PrivateUpdateNotificationsParamsSchema(Struct):
    notification_ids: List[int]
    subaccount_id: int
    status: Status6 = Status6('seen')


class PrivateUpdateNotificationsResultSchema(Struct):
    updated_count: int


class PrivateGetSubaccountValueHistoryParamsSchema(Struct):
    end_timestamp: int
    period: int
    start_timestamp: int
    subaccount_id: int


class SubAccountValueHistoryResponseSchema(Struct):
    subaccount_value: Decimal
    timestamp: int


class Period1(Enum):
    field_60 = 60
    field_300 = 300
    field_900 = 900
    field_1800 = 1800
    field_3600 = 3600
    field_14400 = 14400
    field_28800 = 28800
    field_86400 = 86400
    field_604800 = 604800


class PublicGetSpotFeedHistoryCandlesParamsSchema(Struct):
    currency: str
    end_timestamp: int
    period: Period1
    start_timestamp: int


class SpotFeedHistoryCandlesResponseSchema(Struct):
    close_price: Decimal
    high_price: Decimal
    low_price: Decimal
    open_price: Decimal
    price: Decimal
    timestamp: int
    timestamp_bucket: int


class PrivateRfqGetBestQuoteParamsSchema(Struct):
    legs: List[LegUnpricedSchema]
    subaccount_id: int
    counterparties: Optional[List[str]] = None
    direction: Direction = Direction('buy')
    label: str = ''
    max_total_cost: Optional[Decimal] = None
    min_total_cost: Optional[Decimal] = None
    partial_fill_step: Decimal = Decimal('1')
    rfq_id: Optional[str] = None


class InvalidReason(Enum):
    Account_is_currently_under_maintenance_margin_requirements__trading_is_frozen_ = (
        'Account is currently under maintenance margin requirements, trading is frozen.'
    )
    This_order_would_cause_account_to_fall_under_maintenance_margin_requirements_ = (
        'This order would cause account to fall under maintenance margin requirements.'
    )
    Insufficient_buying_power__only_a_single_risk_reducing_open_order_is_allowed_ = (
        'Insufficient buying power, only a single risk-reducing open order is allowed.'
    )
    Insufficient_buying_power__consider_reducing_order_size_ = (
        'Insufficient buying power, consider reducing order size.'
    )
    Insufficient_buying_power__consider_reducing_order_size_or_canceling_other_orders_ = (
        'Insufficient buying power, consider reducing order size or canceling other orders.'
    )
    Consider_canceling_other_limit_orders_or_using_IOC__FOK__or_market_orders__This_order_is_risk_reducing__but_if_filled_with_other_open_orders__buying_power_might_be_insufficient_ = 'Consider canceling other limit orders or using IOC, FOK, or market orders. This order is risk-reducing, but if filled with other open orders, buying power might be insufficient.'
    Insufficient_buying_power_ = 'Insufficient buying power.'


class PublicGetSpotFeedHistoryParamsSchema(Struct):
    currency: str
    end_timestamp: int
    period: int
    start_timestamp: int


class SpotFeedHistoryResponseSchema(Struct):
    price: Decimal
    timestamp: int
    timestamp_bucket: int


class PrivateLiquidateParamsSchema(Struct):
    cash_transfer: Decimal
    last_seen_trade_id: int
    liquidated_subaccount_id: int
    nonce: int
    percent_bid: Decimal
    price_limit: Decimal
    signature: str
    signature_expiry_sec: int
    signer: str
    subaccount_id: int


class PrivateLiquidateResultSchema(Struct):
    estimated_bid_price: Decimal
    estimated_discount_pnl: Decimal
    estimated_percent_bid: Decimal
    transaction_id: str


class PrivateGetRfqsParamsSchema(Struct):
    subaccount_id: int
    from_timestamp: int = 0
    page: int = 1
    page_size: int = 100
    rfq_id: Optional[str] = None
    status: Optional[Status] = None
    to_timestamp: int = 18446744073709552000


class RFQResultSchema(PrivateSendRfqResultSchema):
    pass


class PrivateGetDepositHistoryParamsSchema(PrivateGetLiquidationHistoryParamsSchema):
    pass


class DepositSchema(Struct):
    amount: Decimal
    asset: str
    timestamp: int
    transaction_id: str
    tx_hash: str
    tx_status: TxStatus
    error_log: Optional[Dict[str, Any]] = None


class PrivateGetSubaccountParamsSchema(PrivateGetOpenOrdersParamsSchema):
    pass


class PrivateGetOrderHistoryParamsSchema(Struct):
    subaccount_id: int
    page: int = 1
    page_size: int = 100


class PrivateGetOrderHistoryResultSchema(Struct):
    orders: List[OrderResponseSchema]
    subaccount_id: int
    pagination: PaginationInfoSchema | None = None


class SimulatedCollateralSchema(Struct):
    amount: Decimal
    asset_name: str


class SimulatedPositionSchema(Struct):
    amount: Decimal
    instrument_name: str
    entry_price: Optional[Decimal] = None


class PublicGetMarginResultSchema(Struct):
    is_valid_trade: bool
    post_initial_margin: Decimal
    post_maintenance_margin: Decimal
    pre_initial_margin: Decimal
    pre_maintenance_margin: Decimal
    subaccount_id: int


class TypeEnum(Enum):
    deposit = 'deposit'
    withdraw = 'withdraw'
    transfer = 'transfer'
    trade = 'trade'
    settlement = 'settlement'
    liquidation = 'liquidation'
    custom = 'custom'


class PrivateGetNotificationsParamsSchema(Struct):
    page: Optional[int] = 1
    page_size: Optional[int] = 50
    status: Optional[Status6] = None
    subaccount_id: Optional[int] = None
    type: Optional[List[TypeEnum]] = None
    wallet: Optional[str] = None


class NotificationResponseSchema(Struct):
    event: str
    event_details: Dict[str, Any]
    id: int
    status: str
    subaccount_id: int
    timestamp: int
    transaction_id: Optional[int] = None
    tx_hash: Optional[str] = None


class PrivateGetFundingHistoryParamsSchema(Struct):
    subaccount_id: int
    end_timestamp: int = 9223372036854776000
    instrument_name: Optional[str] = None
    page: int = 1
    page_size: int = 100
    start_timestamp: int = 0


class FundingPaymentSchema(Struct):
    funding: Decimal
    instrument_name: str
    pnl: Decimal
    timestamp: int


class PrivateGetWithdrawalHistoryParamsSchema(PrivateGetLiquidationHistoryParamsSchema):
    pass


class WithdrawalSchema(Struct):
    amount: Decimal
    asset: str
    timestamp: int
    tx_hash: str
    tx_status: TxStatus
    error_log: Optional[Dict[str, Any]] = None


class PrivateOrderDebugParamsSchema(Struct):
    amount: Decimal
    direction: Direction
    instrument_name: str
    limit_price: Decimal
    max_fee: Decimal
    nonce: int
    signature: str
    signature_expiry_sec: int
    signer: str
    subaccount_id: int
    is_atomic_signing: Optional[bool] = False
    label: str = ''
    mmp: bool = False
    order_type: OrderType = OrderType('limit')
    reduce_only: bool = False
    referral_code: str = ''
    reject_timestamp: int = 9223372036854776000
    time_in_force: TimeInForce = TimeInForce('gtc')
    trigger_price: Optional[Decimal] = None
    trigger_price_type: Optional[TriggerPriceType] = None
    trigger_type: Optional[TriggerType] = None


class TradeModuleDataSchema(Struct):
    asset: str
    desired_amount: Decimal
    is_bid: bool
    limit_price: Decimal
    recipient_id: int
    sub_id: int
    trade_id: str
    worst_fee: Decimal


class PrivateReplaceParamsSchema(Struct):
    amount: Decimal
    direction: Direction
    instrument_name: str
    limit_price: Decimal
    max_fee: Decimal
    nonce: int
    signature: str
    signature_expiry_sec: int
    signer: str
    subaccount_id: int
    expected_filled_amount: Optional[Decimal] = None
    is_atomic_signing: Optional[bool] = False
    label: str = ''
    mmp: bool = False
    nonce_to_cancel: Optional[int] = None
    order_id_to_cancel: Optional[str] = None
    order_type: OrderType = OrderType('limit')
    reduce_only: bool = False
    referral_code: str = '0x9135BA0f495244dc0A5F029b25CDE95157Db89AD'
    reject_timestamp: int = 9223372036854776000
    time_in_force: TimeInForce = TimeInForce('gtc')
    trigger_price: Optional[Decimal] = None
    trigger_price_type: Optional[TriggerPriceType] = None
    trigger_type: Optional[TriggerType] = None


class PrivateReplaceResultSchema(Struct):
    cancelled_order: OrderResponseSchema
    create_order_error: Optional[RPCErrorFormatSchema] = None
    order: Optional[OrderResponseSchema] = None
    trades: Optional[List[TradeResponseSchema]] = None


class PublicGetTickersParamsSchema(Struct):
    currency: str
    instrument_type: InstrumentType
    expiry_date: Optional[str] = None


class OptionPricingSlimSchema(Struct):
    ai: Decimal
    bi: Decimal
    d: Decimal
    df: Decimal
    f: Decimal
    g: Decimal
    i: Decimal
    m: Decimal
    r: Decimal
    t: Decimal
    v: Decimal


class AggregateTradingStatsSlimSchema(Struct):
    c: Decimal
    h: Decimal
    l: Decimal
    n: int
    oi: Decimal
    p: Decimal
    pr: Decimal
    v: Decimal


class PrivateDepositParamsSchema(Struct):
    amount: Decimal
    asset_name: str
    nonce: int
    signature: str
    signature_expiry_sec: int
    signer: str
    subaccount_id: int
    is_atomic_signing: bool = False


class PrivateDepositResultSchema(PrivateTransferErc20ResultSchema):
    pass


class PrivateCancelParamsSchema(Struct):
    instrument_name: str
    order_id: str
    subaccount_id: int


class PrivateCancelResultSchema(OrderResponseSchema):
    pass


class PrivateWithdrawParamsSchema(PrivateDepositParamsSchema):
    pass


class PrivateWithdrawResultSchema(PrivateTransferErc20ResultSchema):
    pass


class PrivateCancelBatchRfqsParamsSchema(Struct):
    subaccount_id: int
    label: Optional[str] = None
    nonce: Optional[int] = None
    rfq_id: Optional[str] = None


class PrivateCancelBatchRfqsResultSchema(Struct):
    cancelled_ids: List[str]


class PublicWithdrawDebugParamsSchema(PublicDepositDebugParamsSchema):
    pass


class PublicWithdrawDebugResultSchema(PublicDepositDebugResultSchema):
    pass


class PrivateCancelByLabelParamsSchema(Struct):
    label: str
    subaccount_id: int
    instrument_name: Optional[str] = None


class PrivateCancelByLabelResultSchema(PrivateCancelByNonceResultSchema):
    pass


class PublicGetCurrencyParamsSchema(Struct):
    currency: str


class PublicGetCurrencyResultSchema(Struct):
    asset_cap_and_supply_per_manager: Dict[str, Dict[str, List[OpenInterestStatsSchema]]]
    borrow_apy: Decimal
    currency: str
    instrument_types: List[InstrumentType]
    managers: List[ManagerContractResponseSchema]
    market_type: MarketType
    pm2_collateral_discounts: List[PM2CollateralDiscountsSchema]
    protocol_asset_addresses: ProtocolAssetAddressesSchema
    spot_price: Decimal
    srm_im_discount: Decimal
    srm_mm_discount: Decimal
    supply_apy: Decimal
    total_borrow: Decimal
    total_supply: Decimal
    erc20_details: Optional[Dict[str, Union[Optional[str], Optional[int]]]] = None
    spot_price_24h: Optional[Decimal] = None


class PrivateResetMmpParamsSchema(PrivateGetMmpConfigParamsSchema):
    pass


class PrivateResetMmpResponseSchema(PrivateCancelAllTriggerOrdersResponseSchema):
    pass


class PublicGetInterestRateHistoryParamsSchema(Struct):
    from_timestamp_sec: int
    to_timestamp_sec: int
    page: int = 1
    page_size: int = 100


class InterestRateHistoryResponseSchema(Struct):
    block: int
    borrow_apy: Decimal
    supply_apy: Decimal
    timestamp_sec: int
    total_borrow: Decimal
    total_supply: Decimal


class PrivatePollRfqsParamsSchema(Struct):
    subaccount_id: int
    from_timestamp: int = 0
    page: int = 1
    page_size: int = 100
    rfq_id: Optional[str] = None
    rfq_subaccount_id: Optional[int] = None
    status: Optional[Status] = None
    to_timestamp: int = 18446744073709552000


class RFQResultPublicSchema(Struct):
    cancel_reason: CancelReason1
    creation_timestamp: int
    filled_pct: Decimal
    last_update_timestamp: int
    legs: List[LegUnpricedSchema]
    partial_fill_step: Decimal
    rfq_id: str
    status: Status
    subaccount_id: int
    valid_until: int
    wallet: str
    fill_rate: Optional[Decimal] = None
    filled_direction: Optional[Direction] = None
    recent_fill_rate: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None


class PrivateCancelQuoteParamsSchema(Struct):
    quote_id: str
    subaccount_id: int


class PrivateCancelQuoteResultSchema(PrivateSendQuoteResultSchema):
    pass


class SignedQuoteParamsSchema(Struct):
    direction: Direction
    legs: List[LegPricedSchema]
    max_fee: Decimal
    nonce: int
    signature: str
    signature_expiry_sec: int
    signer: str
    subaccount_id: int


class PrivateTransferPositionsResultSchema(Struct):
    maker_quote: QuoteResultSchema
    taker_quote: QuoteResultSchema


class PublicGetTransactionParamsSchema(Struct):
    transaction_id: str


class PublicGetTransactionResultSchema(Struct):
    data: dict
    status: TxStatus
    error_log: Optional[dict] = None
    transaction_hash: Optional[str] = None


class PrivateGetPositionsParamsSchema(PrivateGetOpenOrdersParamsSchema):
    pass


class PrivateGetPositionsResultSchema(Struct):
    positions: List[PositionResponseSchema]
    subaccount_id: int


class PublicGetTimeParamsSchema(PublicGetAllCurrenciesParamsSchema):
    pass


class PublicGetTimeResponseSchema(Struct):
    id: Union[str, int]
    result: int


class PrivateGetInterestHistoryParamsSchema(PrivateGetLiquidationHistoryParamsSchema):
    pass


class InterestPaymentSchema(Struct):
    interest: Decimal
    timestamp: int


class PublicDeregisterSessionKeyParamsSchema(Struct):
    public_session_key: str
    signed_raw_tx: str
    wallet: str


class PublicDeregisterSessionKeyResultSchema(Struct):
    public_session_key: str
    transaction_id: str


class PublicGetOptionSettlementPricesParamsSchema(PublicGetCurrencyParamsSchema):
    pass


class ExpiryResponseSchema(Struct):
    expiry_date: str
    utc_expiry_sec: int
    price: Optional[Decimal] = None


class PrivateCancelAllParamsSchema(Struct):
    subaccount_id: int
    cancel_trigger_orders: bool = False


class PrivateCancelAllResponseSchema(PrivateCancelAllTriggerOrdersResponseSchema):
    pass


class PublicGetVaultStatisticsParamsSchema(PublicGetAllCurrenciesParamsSchema):
    pass


class VaultStatisticsResponseSchema(Struct):
    base_value: Decimal
    block_number: int
    block_timestamp: int
    total_supply: Decimal
    usd_tvl: Decimal
    usd_value: Decimal
    vault_name: str
    subaccount_value_at_last_trade: Optional[Decimal] = None
    underlying_value: Optional[Decimal] = None


class PublicGetLiveIncidentsParamsSchema(PublicGetAllCurrenciesParamsSchema):
    pass


class MonitorType(Enum):
    manual = 'manual'
    auto = 'auto'


class Severity(Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'


class IncidentResponseSchema(Struct):
    creation_timestamp_sec: int
    label: str
    message: str
    monitor_type: MonitorType
    severity: Severity


class PublicGetAllInstrumentsParamsSchema(Struct):
    expired: bool
    instrument_type: InstrumentType
    currency: Optional[str] = None
    page: int = 1
    page_size: int = 100


class InstrumentPublicResponseSchema(Struct):
    amount_step: Decimal
    base_asset_address: str
    base_asset_sub_id: str
    base_currency: str
    base_fee: Decimal
    fifo_min_allocation: Decimal
    instrument_name: str
    instrument_type: InstrumentType
    is_active: bool
    maker_fee_rate: Decimal
    maximum_amount: Decimal
    minimum_amount: Decimal
    pro_rata_amount_step: Decimal
    pro_rata_fraction: Decimal
    quote_currency: str
    scheduled_activation: int
    scheduled_deactivation: int
    taker_fee_rate: Decimal
    tick_size: Decimal
    erc20_details: Optional[ERC20PublicDetailsSchema] = None
    option_details: Optional[OptionPublicDetailsSchema] = None
    perp_details: Optional[PerpPublicDetailsSchema] = None
    mark_price_fee_rate_cap: Optional[Decimal] = None


class PublicGetMakerProgramScoresParamsSchema(Struct):
    epoch_start_timestamp: int
    program_name: str


class ProgramResponseSchema(Struct):
    asset_types: List[str]
    currencies: List[str]
    end_timestamp: int
    min_notional: Decimal
    name: str
    rewards: Dict[str, Decimal]
    start_timestamp: int


class ScoreBreakdownSchema(Struct):
    coverage_score: Decimal
    holder_boost: Decimal
    quality_score: Decimal
    total_score: Decimal
    volume: Decimal
    volume_multiplier: Decimal
    wallet: str


class PublicGetInstrumentsParamsSchema(Struct):
    currency: str
    expired: bool
    instrument_type: InstrumentType


class PublicGetInstrumentsResponseSchema(Struct):
    id: Union[str, int]
    result: List[InstrumentPublicResponseSchema]


class PrivateGetOptionSettlementHistoryParamsSchema(PrivateGetOpenOrdersParamsSchema):
    pass


class PrivateGetOptionSettlementHistoryResultSchema(Struct):
    settlements: List[OptionSettlementResponseSchema]
    subaccount_id: int


class PrivateGetMarginParamsSchema(Struct):
    subaccount_id: int
    simulated_collateral_changes: Optional[List[SimulatedCollateralSchema]] = None
    simulated_position_changes: Optional[List[SimulatedPositionSchema]] = None


class PrivateGetMarginResultSchema(PublicGetMarginResultSchema):
    pass


class PrivateChangeSubaccountLabelParamsSchema(Struct):
    label: str
    subaccount_id: int


class PrivateChangeSubaccountLabelResultSchema(PrivateChangeSubaccountLabelParamsSchema):
    pass


class PublicGetVaultBalancesParamsSchema(Struct):
    smart_contract_owner: Optional[str] = None
    wallet: Optional[str] = None


class VaultBalanceResponseSchema(Struct):
    address: str
    amount: Decimal
    chain_id: int
    name: str
    vault_asset_type: str


class PublicGetMakerProgramsParamsSchema(PublicGetAllCurrenciesParamsSchema):
    pass


class PublicGetMakerProgramsResponseSchema(Struct):
    id: Union[str, int]
    result: List[ProgramResponseSchema]


class PrivateExecuteQuoteParamsSchema(PublicExecuteQuoteDebugParamsSchema):
    pass


class PrivateExecuteQuoteResultSchema(Struct):
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
    rfq_filled_pct: Decimal
    rfq_id: str
    signature: str
    signature_expiry_sec: int
    signer: str
    status: Status
    subaccount_id: int
    tx_hash: Optional[str] = None
    tx_status: Optional[TxStatus] = None


class PrivateGetOrdersParamsSchema(Struct):
    subaccount_id: int
    instrument_name: Optional[str] = None
    label: Optional[str] = None
    page: int = 1
    page_size: int = 100
    status: Optional[OrderStatus] = None


class PrivateGetOrdersResultSchema(PrivateGetOrderHistoryResultSchema):
    pass


class PrivateOrderParamsSchema(PrivateOrderDebugParamsSchema):
    referral_code: str = '0x9135BA0f495244dc0A5F029b25CDE95157Db89AD'
    pass


class PrivateOrderResultSchema(Struct):
    order: OrderResponseSchema
    trades: List[TradeResponseSchema]


class PrivateCancelBatchQuotesParamsSchema(Struct):
    subaccount_id: int
    label: Optional[str] = None
    nonce: Optional[int] = None
    quote_id: Optional[str] = None
    rfq_id: Optional[str] = None


class PrivateCancelBatchQuotesResultSchema(PrivateCancelBatchRfqsResultSchema):
    pass


class PrivateSetCancelOnDisconnectParamsSchema(Struct):
    enabled: bool
    wallet: str


class PrivateSetCancelOnDisconnectResponseSchema(PrivateCancelAllTriggerOrdersResponseSchema):
    pass


class PrivateCancelRfqParamsSchema(Struct):
    rfq_id: str
    subaccount_id: int


class PrivateCancelRfqResponseSchema(PrivateCancelAllTriggerOrdersResponseSchema):
    pass


class PrivateGetOrderParamsSchema(PrivateCancelTriggerOrderParamsSchema):
    pass


class PrivateGetOrderResultSchema(OrderResponseSchema):
    pass


class PrivateCreateSubaccountParamsSchema(Struct):
    amount: Decimal
    asset_name: str
    margin_type: MarginType
    nonce: int
    signature: str
    signature_expiry_sec: int
    signer: str
    wallet: str
    currency: Optional[str] = None


class PrivateCreateSubaccountResultSchema(PrivateTransferErc20ResultSchema):
    pass


class PrivateGetLiquidatorHistoryParamsSchema(Struct):
    subaccount_id: int
    end_timestamp: int = 9223372036854776000
    page: int = 1
    page_size: int = 100
    start_timestamp: int = 0


class PrivateGetLiquidatorHistoryResultSchema(Struct):
    bids: List[AuctionBidEventSchema]
    pagination: PaginationInfoSchema | None = None


class PublicGetFundingRateHistoryResultSchema(Struct):
    funding_rate_history: List[FundingRateSchema]


class PrivateEditSessionKeyResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateEditSessionKeyResultSchema


class AuctionResultSchema(Struct):
    auction_id: str
    auction_type: AuctionType
    bids: List[AuctionBidEventSchema]
    fee: Decimal
    start_timestamp: int
    subaccount_id: int
    tx_hash: str
    end_timestamp: Optional[int] = None


class PrivateGetOpenOrdersResultSchema(Struct):
    orders: List[OrderResponseSchema]
    subaccount_id: int


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
    wallet: str
    tx_hash: Optional[str] = None
    tx_status: Optional[TxStatus] = None


class PrivateGetTradeHistoryResultSchema(Struct):
    subaccount_id: int
    trades: List[TradeResponseSchema]
    pagination: PaginationInfoSchema | None = None


class PublicGetTradeHistoryResultSchema(Struct):
    trades: List[TradeSettledPublicResponseSchema]
    pagination: PaginationInfoSchema | None = None


class PublicStatisticsResponseSchema(Struct):
    id: Union[str, int]
    result: PublicStatisticsResultSchema


class PublicGetInstrumentResultSchema(InstrumentPublicResponseSchema):
    pass


class PrivateSendRfqParamsSchema(Struct):
    legs: List[LegUnpricedSchema]
    subaccount_id: int
    counterparties: Optional[List[str]] = None
    label: str = ''
    max_total_cost: Optional[Decimal] = None
    min_total_cost: Optional[Decimal] = None
    partial_fill_step: Decimal = Decimal('1')


class PrivateSendRfqResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateSendRfqResultSchema


class PrivateGetSubaccountsResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetSubaccountsResultSchema


class PrivateGetLiquidationHistoryResponseSchema(Struct):
    id: Union[str, int]
    result: List[AuctionResultSchema]


class PrivateTransferErc20ParamsSchema(Struct):
    recipient_details: SignatureDetailsSchema
    recipient_subaccount_id: int
    sender_details: SignatureDetailsSchema
    subaccount_id: int
    transfer: TransferDetailsSchema


class PrivateTransferErc20ResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateTransferErc20ResultSchema


class PrivateCancelByNonceResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateCancelByNonceResultSchema


class PublicGetOptionSettlementHistoryResultSchema(Struct):
    settlements: List[OptionSettlementResponseSchema]
    pagination: PaginationInfoSchema | None = None


class PrivateSetMmpConfigResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateSetMmpConfigResultSchema


class PublicDepositDebugResponseSchema(Struct):
    id: Union[str, int]
    result: PublicDepositDebugResultSchema


class PublicGetReferralPerformanceResultSchema(Struct):
    fee_share_percentage: Decimal
    referral_code: str
    rewards: Dict[str, Dict[str, Dict[str, ReferralPerformanceByInstrumentTypeSchema]]]
    stdrv_balance: Decimal
    total_fee_rewards: Decimal
    total_notional_volume: Decimal
    total_referred_fees: Decimal


class PrivateCancelByInstrumentResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateCancelByInstrumentResultSchema


class PublicSendQuoteDebugResponseSchema(Struct):
    id: Union[str, int]
    result: PublicSendQuoteDebugResultSchema


class PublicCreateSubaccountDebugResponseSchema(Struct):
    id: Union[str, int]
    result: PublicCreateSubaccountDebugResultSchema


class PrivateGetErc20TransferHistoryResultSchema(Struct):
    events: List[ERC20TransferSchema]


class ForwardFeedDataSchema(Struct):
    confidence: Decimal
    currency: str
    deadline: int
    expiry: int
    fwd_diff: Decimal
    signatures: OracleSignatureDataSchema
    spot_aggregate_latest: Decimal
    spot_aggregate_start: Decimal
    timestamp: int


class VolFeedDataSchema(Struct):
    confidence: Decimal
    currency: str
    deadline: int
    expiry: int
    signatures: OracleSignatureDataSchema
    timestamp: int
    vol_data: VolSVIParamDataSchema


class PrivateCancelTriggerOrderResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateCancelTriggerOrderResultSchema


class PrivateTransferPositionParamsSchema(Struct):
    maker_params: TradeModuleParamsSchema
    taker_params: TradeModuleParamsSchema
    wallet: str


class PrivateTransferPositionResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateTransferPositionResultSchema


class PublicMarginWatchResultSchema(Struct):
    collaterals: List[CollateralPublicResponseSchema]
    currency: str
    initial_margin: Decimal
    maintenance_margin: Decimal
    margin_type: MarginType
    positions: List[PositionPublicResponseSchema]
    subaccount_id: int
    subaccount_value: Decimal
    valuation_timestamp: int


class PublicBuildRegisterSessionKeyTxResponseSchema(Struct):
    id: Union[str, int]
    result: PublicBuildRegisterSessionKeyTxResultSchema


class CurrencyDetailedResponseSchema(PublicGetCurrencyResultSchema):
    pass


class PrivateGetAccountResultSchema(Struct):
    cancel_on_disconnect: bool
    fee_info: AccountFeeInfoSchema
    is_rfq_maker: bool
    per_endpoint_tps: Dict[str, Any]
    subaccount_ids: List[int]
    wallet: str
    websocket_matching_tps: int
    websocket_non_matching_tps: int
    websocket_option_tps: int
    websocket_perp_tps: int
    referral_code: Optional[str] = None


class PrivateSendQuoteResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateSendQuoteResultSchema


class PrivateGetCollateralsResultSchema(Struct):
    collaterals: List[CollateralResponseSchema]
    subaccount_id: int


class PublicGetTickerResultSchema(Struct):
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


class PrivateReplaceQuoteResultSchema(Struct):
    cancelled_quote: QuoteResultSchema
    create_quote_error: Optional[RPCErrorFormatSchema] = None
    quote: Optional[QuoteResultSchema] = None


class PrivateGetSubaccountResultSchema(Struct):
    collaterals: List[CollateralResponseSchema]
    collaterals_initial_margin: Decimal
    collaterals_maintenance_margin: Decimal
    collaterals_value: Decimal
    currency: str
    initial_margin: Decimal
    is_under_liquidation: bool
    label: str
    maintenance_margin: Decimal
    margin_type: MarginType
    open_orders: List[OrderResponseSchema]
    open_orders_margin: Decimal
    positions: List[PositionResponseSchema]
    positions_initial_margin: Decimal
    positions_maintenance_margin: Decimal
    positions_value: Decimal
    projected_margin_change: Decimal
    subaccount_id: int
    subaccount_value: Decimal


class PrivateSessionKeysResultSchema(Struct):
    public_session_keys: List[SessionKeyResponseSchema]


class PrivateExpiredAndCancelledHistoryResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateExpiredAndCancelledHistoryResultSchema


class PrivateGetQuotesResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetQuotesResultSchema


class PublicGetVaultShareResultSchema(Struct):
    vault_shares: List[VaultShareResponseSchema]
    pagination: PaginationInfoSchema | None = None


class PublicRegisterSessionKeyResponseSchema(Struct):
    id: Union[str, int]
    result: PublicRegisterSessionKeyResultSchema


class PrivateRegisterScopedSessionKeyResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateRegisterScopedSessionKeyResultSchema


class PrivateGetMmpConfigResponseSchema(Struct):
    id: Union[str, int]
    result: List[MMPConfigResultSchema]


class PublicExecuteQuoteDebugResponseSchema(Struct):
    id: Union[str, int]
    result: PublicExecuteQuoteDebugResultSchema


class PrivateUpdateNotificationsResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateUpdateNotificationsResultSchema


class PrivateGetSubaccountValueHistoryResultSchema(Struct):
    subaccount_id: int
    subaccount_value_history: List[SubAccountValueHistoryResponseSchema]


class PublicGetSpotFeedHistoryCandlesResultSchema(Struct):
    currency: str
    spot_feed_history: List[SpotFeedHistoryCandlesResponseSchema]


class PrivateRfqGetBestQuoteResultSchema(Struct):
    direction: Direction
    estimated_fee: Decimal
    estimated_realized_pnl: Decimal
    estimated_realized_pnl_excl_fees: Decimal
    estimated_total_cost: Decimal
    filled_pct: Decimal
    is_valid: bool
    post_initial_margin: Decimal
    pre_initial_margin: Decimal
    suggested_max_fee: Decimal
    best_quote: Optional[QuoteResultPublicSchema] = None
    down_liquidation_price: Optional[Decimal] = None
    invalid_reason: Optional[InvalidReason] = None
    orderbook_total_cost: Optional[Decimal] = None
    post_liquidation_price: Optional[Decimal] = None
    up_liquidation_price: Optional[Decimal] = None


class PublicGetSpotFeedHistoryResultSchema(Struct):
    currency: str
    spot_feed_history: List[SpotFeedHistoryResponseSchema]


class PrivateLiquidateResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateLiquidateResultSchema


class PrivateGetRfqsResultSchema(Struct):
    rfqs: List[RFQResultSchema]
    pagination: PaginationInfoSchema | None = None


class PrivateGetDepositHistoryResultSchema(Struct):
    events: List[DepositSchema]


class PrivateGetSubaccountResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetSubaccountResultSchema


class PrivateGetOrderHistoryResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetOrderHistoryResultSchema


class PublicGetMarginParamsSchema(Struct):
    margin_type: MarginType
    simulated_collaterals: List[SimulatedCollateralSchema]
    simulated_positions: List[SimulatedPositionSchema]
    market: Optional[str] = None
    simulated_collateral_changes: Optional[List[SimulatedCollateralSchema]] = None
    simulated_position_changes: Optional[List[SimulatedPositionSchema]] = None


class PublicGetMarginResponseSchema(Struct):
    id: Union[str, int]
    result: PublicGetMarginResultSchema


class PrivateGetNotificationsResultSchema(Struct):
    notifications: List[NotificationResponseSchema]
    pagination: PaginationInfoSchema | None = None


class PrivateGetFundingHistoryResultSchema(Struct):
    events: List[FundingPaymentSchema]
    pagination: PaginationInfoSchema | None = None


class PrivateGetWithdrawalHistoryResultSchema(Struct):
    events: List[WithdrawalSchema]


class SignedTradeOrderSchema(Struct):
    data: TradeModuleDataSchema
    expiry: int
    is_atomic_signing: bool
    module: str
    nonce: int
    owner: str
    signature: str
    signer: str
    subaccount_id: int


class PrivateReplaceResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateReplaceResultSchema


class TickerSlimSchema(Struct):
    A: Decimal
    B: Decimal
    I: Decimal
    M: Decimal
    a: Decimal
    b: Decimal
    maxp: Decimal
    minp: Decimal
    stats: AggregateTradingStatsSlimSchema
    t: int
    f: Optional[Decimal] = None
    option_pricing: Optional[OptionPricingSlimSchema] = None


class PrivateDepositResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateDepositResultSchema


class PrivateCancelResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateCancelResultSchema


class PrivateWithdrawResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateWithdrawResultSchema


class PrivateCancelBatchRfqsResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateCancelBatchRfqsResultSchema


class PublicWithdrawDebugResponseSchema(Struct):
    id: Union[str, int]
    result: PublicWithdrawDebugResultSchema


class PrivateCancelByLabelResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateCancelByLabelResultSchema


class PublicGetCurrencyResponseSchema(Struct):
    id: Union[str, int]
    result: PublicGetCurrencyResultSchema


class PublicGetInterestRateHistoryResultSchema(Struct):
    interest_rates: List[InterestRateHistoryResponseSchema]
    pagination: PaginationInfoSchema | None = None


class PrivatePollRfqsResultSchema(Struct):
    rfqs: List[RFQResultPublicSchema]
    pagination: PaginationInfoSchema | None = None


class PrivateCancelQuoteResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateCancelQuoteResultSchema


class PrivateTransferPositionsParamsSchema(Struct):
    maker_params: SignedQuoteParamsSchema
    taker_params: SignedQuoteParamsSchema
    wallet: str


class PrivateTransferPositionsResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateTransferPositionsResultSchema


class PublicGetTransactionResponseSchema(Struct):
    id: Union[str, int]
    result: PublicGetTransactionResultSchema


class PrivateGetPositionsResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetPositionsResultSchema


class PrivateGetInterestHistoryResultSchema(Struct):
    events: List[InterestPaymentSchema]


class PublicDeregisterSessionKeyResponseSchema(Struct):
    id: Union[str, int]
    result: PublicDeregisterSessionKeyResultSchema


class PublicGetOptionSettlementPricesResultSchema(Struct):
    expiries: List[ExpiryResponseSchema]


class PublicGetVaultStatisticsResponseSchema(Struct):
    id: Union[str, int]
    result: List[VaultStatisticsResponseSchema]


class PublicGetLiveIncidentsResultSchema(Struct):
    incidents: List[IncidentResponseSchema]


class PublicGetAllInstrumentsResultSchema(Struct):
    instruments: List[InstrumentPublicResponseSchema]
    pagination: PaginationInfoSchema | None = None


class PublicGetMakerProgramScoresResultSchema(Struct):
    program: ProgramResponseSchema
    scores: List[ScoreBreakdownSchema]
    total_score: Decimal
    total_volume: Decimal


class PrivateGetOptionSettlementHistoryResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetOptionSettlementHistoryResultSchema


class PrivateGetMarginResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetMarginResultSchema


class PrivateChangeSubaccountLabelResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateChangeSubaccountLabelResultSchema


class PublicGetVaultBalancesResponseSchema(Struct):
    id: Union[str, int]
    result: List[VaultBalanceResponseSchema]


class PrivateExecuteQuoteResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateExecuteQuoteResultSchema


class PrivateGetOrdersResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetOrdersResultSchema


class PrivateOrderResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateOrderResultSchema


class PrivateCancelBatchQuotesResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateCancelBatchQuotesResultSchema


class PrivateGetOrderResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetOrderResultSchema


class PrivateCreateSubaccountResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateCreateSubaccountResultSchema


class PrivateGetLiquidatorHistoryResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetLiquidatorHistoryResultSchema


class PublicGetFundingRateHistoryResponseSchema(Struct):
    id: Union[str, int]
    result: PublicGetFundingRateHistoryResultSchema


class PublicGetLiquidationHistoryResultSchema(Struct):
    auctions: List[AuctionResultSchema]
    pagination: PaginationInfoSchema | None = None


class PrivateGetOpenOrdersResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetOpenOrdersResultSchema


class PrivatePollQuotesResultSchema(Struct):
    quotes: List[QuoteResultPublicSchema]
    pagination: PaginationInfoSchema | None = None


class PrivateGetTradeHistoryResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetTradeHistoryResultSchema


class PublicGetTradeHistoryResponseSchema(Struct):
    id: Union[str, int]
    result: PublicGetTradeHistoryResultSchema


class PublicGetInstrumentResponseSchema(Struct):
    id: Union[str, int]
    result: PublicGetInstrumentResultSchema


class PublicGetOptionSettlementHistoryResponseSchema(Struct):
    id: Union[str, int]
    result: PublicGetOptionSettlementHistoryResultSchema


class PublicGetReferralPerformanceResponseSchema(Struct):
    id: Union[str, int]
    result: PublicGetReferralPerformanceResultSchema


class PrivateGetErc20TransferHistoryResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetErc20TransferHistoryResultSchema


class PublicGetLatestSignedFeedsResultSchema(Struct):
    fwd_data: Dict[str, Dict[str, ForwardFeedDataSchema]]
    perp_data: Dict[str, Dict[str, PerpFeedDataSchema]]
    rate_data: Dict[str, Dict[str, RateFeedDataSchema]]
    spot_data: Dict[str, SpotFeedDataSchema]
    vol_data: Dict[str, Dict[str, VolFeedDataSchema]]


class PublicMarginWatchResponseSchema(Struct):
    id: Union[str, int]
    result: PublicMarginWatchResultSchema


class PublicGetAllCurrenciesResponseSchema(Struct):
    id: Union[str, int]
    result: List[CurrencyDetailedResponseSchema]


class PrivateGetAccountResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetAccountResultSchema


class PrivateGetCollateralsResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetCollateralsResultSchema


class PublicGetTickerResponseSchema(Struct):
    id: Union[str, int]
    result: PublicGetTickerResultSchema


class PrivateReplaceQuoteResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateReplaceQuoteResultSchema


class PrivateGetAllPortfoliosResponseSchema(Struct):
    id: Union[str, int]
    result: List[PrivateGetSubaccountResultSchema]


class PrivateSessionKeysResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateSessionKeysResultSchema


class PublicGetVaultShareResponseSchema(Struct):
    id: Union[str, int]
    result: PublicGetVaultShareResultSchema


class PrivateGetSubaccountValueHistoryResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetSubaccountValueHistoryResultSchema


class PublicGetSpotFeedHistoryCandlesResponseSchema(Struct):
    id: Union[str, int]
    result: PublicGetSpotFeedHistoryCandlesResultSchema


class PrivateRfqGetBestQuoteResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateRfqGetBestQuoteResultSchema


class PublicGetSpotFeedHistoryResponseSchema(Struct):
    id: Union[str, int]
    result: PublicGetSpotFeedHistoryResultSchema


class PrivateGetRfqsResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetRfqsResultSchema


class PrivateGetDepositHistoryResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetDepositHistoryResultSchema


class PrivateGetNotificationsResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetNotificationsResultSchema


class PrivateGetFundingHistoryResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetFundingHistoryResultSchema


class PrivateGetWithdrawalHistoryResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetWithdrawalHistoryResultSchema


class PrivateOrderDebugResultSchema(Struct):
    action_hash: str
    encoded_data: str
    encoded_data_hashed: str
    raw_data: SignedTradeOrderSchema
    typed_data_hash: str


class PublicGetTickersResultSchema(Struct):
    tickers: Dict[str, TickerSlimSchema]


class PublicGetInterestRateHistoryResponseSchema(Struct):
    id: Union[str, int]
    result: PublicGetInterestRateHistoryResultSchema


class PrivatePollRfqsResponseSchema(Struct):
    id: Union[str, int]
    result: PrivatePollRfqsResultSchema


class PrivateGetInterestHistoryResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateGetInterestHistoryResultSchema


class PublicGetOptionSettlementPricesResponseSchema(Struct):
    id: Union[str, int]
    result: PublicGetOptionSettlementPricesResultSchema


class PublicGetLiveIncidentsResponseSchema(Struct):
    id: Union[str, int]
    result: PublicGetLiveIncidentsResultSchema


class PublicGetAllInstrumentsResponseSchema(Struct):
    id: Union[str, int]
    result: PublicGetAllInstrumentsResultSchema


class PublicGetMakerProgramScoresResponseSchema(Struct):
    id: Union[str, int]
    result: PublicGetMakerProgramScoresResultSchema


class PublicGetLiquidationHistoryResponseSchema(Struct):
    id: Union[str, int]
    result: PublicGetLiquidationHistoryResultSchema


class PrivatePollQuotesResponseSchema(Struct):
    id: Union[str, int]
    result: PrivatePollQuotesResultSchema


class PublicGetLatestSignedFeedsResponseSchema(Struct):
    id: Union[str, int]
    result: PublicGetLatestSignedFeedsResultSchema


class PrivateOrderDebugResponseSchema(Struct):
    id: Union[str, int]
    result: PrivateOrderDebugResultSchema


class PublicGetTickersResponseSchema(Struct):
    id: Union[str, int]
    result: PublicGetTickersResultSchema
