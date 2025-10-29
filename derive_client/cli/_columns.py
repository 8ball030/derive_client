"""Column presets and ordering for CLI table display."""

CURRENCY_COLUMNS = [
    "currency",
    "instrument_types",
    "market_type",
    "spot_price",
    "spot_price_24h",
    "borrow_apy",
    "total_supply",
    "total_borrow",
    "srm_im_discount",
    "srm_mm_discount",
]

INSTRUMENT_COLUMNS = [
    "instrument_name",
    "base_currency",
    "instrument_type",
    "is_active",
    "taker_fee_rate",
    "maker_fee_rate",
    "tick_size",
    "amount_step",
    "minimum_amount",
    "maximum_amount",
]

ORDER_COLUMNS = [
    "order_id",
    "subaccount_id",
    "instrument_name",
    "direction",
    "order_type",
    "order_status",
    "time_in_force",
    "amount",
    "filled_amount",
    "limit_price",
    "trigger_price",
    "trigger_price_type",
    "order_fee",
    "max_fee",
]


POSITION_COLUMNS = [
    "subaccount_id",
    "instrument_name",
    "amount",
    "mark_price",
    "mark_value",
    "unrealized_pnl_excl_fees",
    "realized_pnl_excl_fees",
    "total_fees",
    "initial_margin",
    "maintenance_margin",
    "open_orders_margin",
    "net_settlements",
    "leverage",
    "liquidation_price",
    "cumulative_funding",
]


OPEN_POSITION_COLUMNS = [
    "instrument_name",
    "instrument_type",
    "amount",
    "mark_price",
    "index_price",
    "mark_value",
    "unrealized_pnl",
    "realized_pnl",
    "leverage",
    "initial_margin",
    "maintenance_margin",
    "open_orders_margin",
    "liquidation_price",
    "total_fees",
]


TRADE_COLUMNS = [
    "subaccount_id",
    "liquidity_role",
    "instrument_name",
    "direction",
    "trade_amount",
    "mark_price",
    "trade_price",
    "trade_fee",
    "timestamp",
    "transaction_id",
]

SUBACCOUNT_COLUMNS = [
    "subaccount_id",
    "label",
    "margin_type",
    "currency",
    "is_under_liquidation",
    "subaccount_value",
    "initial_margin",
    "maintenance_margin",
    "open_orders_margin",
    "projected_margin_change",
    "positions_value",
    "positions_initial_margin",
    "positions_maintenance_margin",
]

COLLATERAL_COLUMNS = [
    "subaccount_id",
    "asset_name",
    "amount",
    "initial_margin",
    "maintenance_margin",
    "open_orders_margin",
    "mark_price",
    "mark_value",
    "unrealized_pnl_excl_fees",
    "realized_pnl_excl_fees",
    "total_fees",
]
