from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Optional

from msgspec import Struct

from derive_client.data_types.channels.enums import InstrumentType, Interval, OptionType


class TickerInstrumentNameIntervalChannelSchema(Struct):
    instrument_name: str
    interval: Interval


class ERC20PublicDetailsSchema(Struct):
    decimals: int
    borrow_index: Decimal = Decimal('1')
    supply_index: Decimal = Decimal('1')
    underlying_erc20_address: str = ''


class OpenInterestStatsSchema(Struct):
    current_open_interest: Decimal
    interest_cap: Decimal
    manager_currency: Optional[str] = None


class OptionPublicDetailsSchema(Struct):
    expiry: int
    index: str
    option_type: OptionType
    strike: Decimal
    settlement_price: Optional[Decimal] = None


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


class PerpPublicDetailsSchema(Struct):
    aggregate_funding: Decimal
    funding_rate: Decimal
    index: str
    max_rate_per_hour: Decimal
    min_rate_per_hour: Decimal
    static_interest_rate: Decimal


class AggregateTradingStatsSchema(Struct):
    contract_volume: Decimal
    high: Decimal
    low: Decimal
    num_trades: Decimal
    open_interest: Decimal
    percent_change: Decimal
    usd_change: Decimal


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


class TickerInstrumentNameIntervalPublisherDataSchema(Struct):
    instrument_ticker: InstrumentTickerSchema
    timestamp: int


class TickerInstrumentNameIntervalNotificationParamsSchema(Struct):
    channel: str
    data: TickerInstrumentNameIntervalPublisherDataSchema


class TickerInstrumentNameIntervalNotificationSchema(Struct):
    method: str
    params: TickerInstrumentNameIntervalNotificationParamsSchema


class TickerInstrumentNameIntervalPubSubSchema(Struct):
    channel_params: TickerInstrumentNameIntervalChannelSchema
    notification: TickerInstrumentNameIntervalNotificationSchema


class TickerInstrumentNameInterval(TickerInstrumentNameIntervalPubSubSchema):
    pass
