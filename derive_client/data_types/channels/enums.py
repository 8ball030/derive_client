# ruff: noqa: E741,E501

from enum import Enum


class State(Enum):
    ongoing = 'ongoing'
    ended = 'ended'


class MarginType(Enum):
    PM = 'PM'
    SM = 'SM'
    PM2 = 'PM2'


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


class Interval(Enum):
    field_100 = '100'
    field_1000 = '1000'


class InstrumentType(Enum):
    erc20 = 'erc20'
    option = 'option'
    perp = 'perp'


class OptionType(Enum):
    C = 'C'
    P = 'P'


class Direction(Enum):
    buy = 'buy'
    sell = 'sell'


class LiquidityRole(Enum):
    maker = 'maker'
    taker = 'taker'


class Status(Enum):
    open = 'open'
    filled = 'filled'
    cancelled = 'cancelled'
    expired = 'expired'


class Depth(Enum):
    field_1 = '1'
    field_10 = '10'
    field_20 = '20'
    field_100 = '100'


class Group(Enum):
    field_1 = '1'
    field_10 = '10'
    field_100 = '100'


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


class TxStatus1(Enum):
    requested = 'requested'
    pending = 'pending'
    settled = 'settled'
    reverted = 'reverted'
    ignored = 'ignored'
    timed_out = 'timed_out'


class FilledDirection(Enum):
    buy = 'buy'
    sell = 'sell'


class AssetType(Enum):
    erc20 = 'erc20'
    option = 'option'
    perp = 'perp'


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
