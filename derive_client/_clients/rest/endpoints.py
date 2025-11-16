"""Auto-generated endpoint definitions from OpenAPI spec."""

from __future__ import annotations

from typing import Any, overload


class Endpoint:
    """Descriptor that provides both REST URLs and WebSocket method names."""

    def __init__(self, section: str, path: str):
        self.section = section
        self.path = path
        self.method = f"{section}/{path}"

    def url(self, base_url: str) -> str:
        """Returns full URL for REST"""
        return f"{base_url.rstrip('/')}/{self.method}"

    @overload
    def __get__(self, inst: None, owner: type) -> Endpoint: ...

    @overload
    def __get__(self, inst: object, owner: type) -> str: ...

    def __get__(self, inst: Any, owner: Any) -> Endpoint | str:
        if inst is None:
            return self  # Allow class-level access to .method
        return self.url(inst._base_url)


class PublicEndpoints:
    def __init__(self, base_url: str):
        self._base_url = base_url

    build_register_session_key_tx = Endpoint("public", "build_register_session_key_tx")
    register_session_key = Endpoint("public", "register_session_key")
    deregister_session_key = Endpoint("public", "deregister_session_key")
    login = Endpoint("public", "login")
    statistics = Endpoint("public", "statistics")
    get_all_currencies = Endpoint("public", "get_all_currencies")
    get_currency = Endpoint("public", "get_currency")
    get_instrument = Endpoint("public", "get_instrument")
    get_all_instruments = Endpoint("public", "get_all_instruments")
    get_instruments = Endpoint("public", "get_instruments")
    get_ticker = Endpoint("public", "get_ticker")
    get_tickers = Endpoint("public", "get_tickers")
    get_latest_signed_feeds = Endpoint("public", "get_latest_signed_feeds")
    get_option_settlement_prices = Endpoint("public", "get_option_settlement_prices")
    get_spot_feed_history = Endpoint("public", "get_spot_feed_history")
    get_spot_feed_history_candles = Endpoint("public", "get_spot_feed_history_candles")
    get_funding_rate_history = Endpoint("public", "get_funding_rate_history")
    get_trade_history = Endpoint("public", "get_trade_history")
    get_option_settlement_history = Endpoint("public", "get_option_settlement_history")
    get_liquidation_history = Endpoint("public", "get_liquidation_history")
    get_interest_rate_history = Endpoint("public", "get_interest_rate_history")
    get_transaction = Endpoint("public", "get_transaction")
    get_margin = Endpoint("public", "get_margin")
    margin_watch = Endpoint("public", "margin_watch")
    get_vault_share = Endpoint("public", "get_vault_share")
    get_vault_statistics = Endpoint("public", "get_vault_statistics")
    get_vault_balances = Endpoint("public", "get_vault_balances")
    create_subaccount_debug = Endpoint("public", "create_subaccount_debug")
    deposit_debug = Endpoint("public", "deposit_debug")
    withdraw_debug = Endpoint("public", "withdraw_debug")
    send_quote_debug = Endpoint("public", "send_quote_debug")
    execute_quote_debug = Endpoint("public", "execute_quote_debug")
    get_time = Endpoint("public", "get_time")
    get_live_incidents = Endpoint("public", "get_live_incidents")
    get_maker_programs = Endpoint("public", "get_maker_programs")
    get_maker_program_scores = Endpoint("public", "get_maker_program_scores")
    get_referral_performance = Endpoint("public", "get_referral_performance")


class PrivateEndpoints:
    def __init__(self, base_url: str):
        self._base_url = base_url

    get_account = Endpoint("private", "get_account")
    create_subaccount = Endpoint("private", "create_subaccount")
    get_subaccount = Endpoint("private", "get_subaccount")
    get_subaccounts = Endpoint("private", "get_subaccounts")
    get_all_portfolios = Endpoint("private", "get_all_portfolios")
    change_subaccount_label = Endpoint("private", "change_subaccount_label")
    get_notifications = Endpoint("private", "get_notifications")
    update_notifications = Endpoint("private", "update_notifications")
    deposit = Endpoint("private", "deposit")
    withdraw = Endpoint("private", "withdraw")
    transfer_erc20 = Endpoint("private", "transfer_erc20")
    transfer_position = Endpoint("private", "transfer_position")
    transfer_positions = Endpoint("private", "transfer_positions")
    order = Endpoint("private", "order")
    replace = Endpoint("private", "replace")
    order_debug = Endpoint("private", "order_debug")
    get_order = Endpoint("private", "get_order")
    get_orders = Endpoint("private", "get_orders")
    get_open_orders = Endpoint("private", "get_open_orders")
    cancel = Endpoint("private", "cancel")
    cancel_all = Endpoint("private", "cancel_all")
    cancel_by_label = Endpoint("private", "cancel_by_label")
    cancel_by_nonce = Endpoint("private", "cancel_by_nonce")
    cancel_by_instrument = Endpoint("private", "cancel_by_instrument")
    cancel_trigger_order = Endpoint("private", "cancel_trigger_order")
    cancel_all_trigger_orders = Endpoint("private", "cancel_all_trigger_orders")
    get_order_history = Endpoint("private", "get_order_history")
    get_trade_history = Endpoint("private", "get_trade_history")
    get_deposit_history = Endpoint("private", "get_deposit_history")
    get_withdrawal_history = Endpoint("private", "get_withdrawal_history")
    send_rfq = Endpoint("private", "send_rfq")
    cancel_rfq = Endpoint("private", "cancel_rfq")
    cancel_batch_rfqs = Endpoint("private", "cancel_batch_rfqs")
    get_rfqs = Endpoint("private", "get_rfqs")
    poll_rfqs = Endpoint("private", "poll_rfqs")
    send_quote = Endpoint("private", "send_quote")
    replace_quote = Endpoint("private", "replace_quote")
    cancel_quote = Endpoint("private", "cancel_quote")
    cancel_batch_quotes = Endpoint("private", "cancel_batch_quotes")
    get_quotes = Endpoint("private", "get_quotes")
    poll_quotes = Endpoint("private", "poll_quotes")
    execute_quote = Endpoint("private", "execute_quote")
    rfq_get_best_quote = Endpoint("private", "rfq_get_best_quote")
    get_margin = Endpoint("private", "get_margin")
    get_collaterals = Endpoint("private", "get_collaterals")
    get_positions = Endpoint("private", "get_positions")
    get_option_settlement_history = Endpoint("private", "get_option_settlement_history")
    get_subaccount_value_history = Endpoint("private", "get_subaccount_value_history")
    expired_and_cancelled_history = Endpoint("private", "expired_and_cancelled_history")
    get_funding_history = Endpoint("private", "get_funding_history")
    get_interest_history = Endpoint("private", "get_interest_history")
    get_erc20_transfer_history = Endpoint("private", "get_erc20_transfer_history")
    get_liquidation_history = Endpoint("private", "get_liquidation_history")
    liquidate = Endpoint("private", "liquidate")
    get_liquidator_history = Endpoint("private", "get_liquidator_history")
    session_keys = Endpoint("private", "session_keys")
    edit_session_key = Endpoint("private", "edit_session_key")
    register_scoped_session_key = Endpoint("private", "register_scoped_session_key")
    get_mmp_config = Endpoint("private", "get_mmp_config")
    set_mmp_config = Endpoint("private", "set_mmp_config")
    reset_mmp = Endpoint("private", "reset_mmp")
    set_cancel_on_disconnect = Endpoint("private", "set_cancel_on_disconnect")
