# ruff: noqa: E741,E501

from enum import Enum


class State(Enum):
    ongoing = 'ongoing'
    ended = 'ended'


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


class Depth(Enum):
    field_1 = '1'
    field_10 = '10'
    field_20 = '20'
    field_100 = '100'


class Group(Enum):
    field_1 = '1'
    field_10 = '10'
    field_100 = '100'
