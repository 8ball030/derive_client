from typing import Any


class Endpoint:
    """Descriptor that formats a full URL from the client's base_url, section, and path."""

    def __init__(self, section: str, path: str):
        self.section = section.strip("/")
        self.path = path.strip("/")

    def __get__(self, inst: Any, owner: Any) -> str:
        if inst is None:
            return self  # allow access on the class for introspection
        base = inst._base_url.rstrip("/")
        return f"{base}/{self.section}/{self.path}"


class PublicEndpoints:
    def __init__(self, base_url: str):
        self._base_url = base_url

    create_account = Endpoint("public", "create_account")
    get_instruments = Endpoint("public", "get_instruments")
    get_ticker = Endpoint("public", "get_ticker")
    get_all_currencies = Endpoint("public", "get_all_currencies")
    get_currency = Endpoint("public", "get_currency")
    get_transaction = Endpoint("public", "get_transaction")


class PrivateEndpoints:
    def __init__(self, base_url: str):
        self._base_url = base_url

    session_keys = Endpoint("private", "session_keys")
    get_subaccount = Endpoint("private", "get_subaccount")
    get_subaccounts = Endpoint("private", "get_subaccounts")
    get_order = Endpoint("private", "get_order")
    get_orders = Endpoint("private", "get_orders")
    get_positions = Endpoint("private", "get_positions")
    get_collaterals = Endpoint("private", "get_collaterals")
    create_subaccount = Endpoint("private", "create_subaccount")
    transfer_erc20 = Endpoint("private", "transfer_erc20")
    transfer_position = Endpoint("private", "transfer_position")
    transfer_positions = Endpoint("private", "transfer_positions")
    get_mmp_config = Endpoint("private", "get_mmp_config")
    set_mmp_config = Endpoint("private", "set_mmp_config")
    send_rfq = Endpoint("private", "send_rfq")
    poll_rfqs = Endpoint("private", "poll_rfqs")
    poll_quotes = Endpoint("private", "poll_quotes")
    cancel_rfq = Endpoint("private", "cancel_rfq")
    cancel_batch_rfqs = Endpoint("private", "cancel_batch_rfqs")
    execute_quote = Endpoint("private", "execute_quote")
    send_quote = Endpoint("private", "send_quote")
    poll_quotes = Endpoint("private", "poll_quotes")
    execute_quote = Endpoint("private", "execute_quote")
    deposit = Endpoint("private", "deposit")
    withdraw = Endpoint("private", "withdraw")
    order = Endpoint("private", "order")
    cancel = Endpoint("private", "cancel")
    cancel_all = Endpoint("private", "cancel_all")


class RestAPI:
    public: PublicEndpoints
    private: PrivateEndpoints

    def __init__(self, base_url: str):
        self._base_url = base_url
        self.public = PublicEndpoints(base_url)
        self.private = PrivateEndpoints(base_url)
