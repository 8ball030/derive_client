"""
Class to handle base websocket client
"""

import json
import time
import uuid
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from derive_action_signing.utils import sign_ws_login, utc_now_ms
from websockets import State
from websockets.sync.client import ClientConnection, connect

from derive_client.constants import DEFAULT_REFERER
from derive_client.data_types import InstrumentType, UnderlyingCurrency
from derive_client.data_types.enums import OrderSide, OrderType, TimeInForce
from derive_client.exceptions import DeriveJSONRPCException

from .base_client import BaseClient


@dataclass
class Orderbook:
    channel: str
    timestamp: int
    instrument_name: str
    publish_id: int
    bids: list[list[float]]
    asks: list[list[float]]

    @classmethod
    def from_json(cls, data):
        return cls(
            channel=data["params"]["channel"],
            timestamp=data["params"]["data"]["timestamp"],
            instrument_name=data["params"]["data"]["instrument_name"],
            publish_id=data["params"]["data"]["publish_id"],
            bids=[[float(price), float(size)] for price, size in data["params"]["data"]["bids"]],
            asks=[[float(price), float(size)] for price, size in data["params"]["data"]["asks"]],
        )


@dataclass
class Position:
    """
    {'instrument_type': 'perp', 'instrument_name': 'ETH-PERP', 'amount': '0', 'average_price': '0', 'realized_pnl': '0',
      'unrealized_pnl': '0', 'total_fees': '0', 'average_price_excl_fees': '0', 'realized_pnl_excl_fees': '0', 'unrealized_pnl_excl_fees': '0',
      'net_settlements': '0', 'cumulative_funding': '0', 'pending_funding': '0', 'mark_price': '4153.1395224770267304847948253154754638671875',
        'index_price': '4156.522924638571', 'delta': '1', 'gamma': '0', 'vega': '0', 'theta': '0', 'mark_value': '0', 'maintenance_margin': '0',
          'initial_margin': '0', 'open_orders_margin': '-81.7268423838896751476568169891834259033203125', 'leverage': None, 'liquidation_price': None,
            'creation_timestamp': 0, 'amount_step': '0'}
    """

    instrument_type: str | None = None
    instrument_name: str | None = None
    amount: float | None = None
    average_price: float | None = None
    realized_pnl: float | None = None
    unrealized_pnl: float | None = None
    total_fees: float | None = None
    average_price_excl_fees: float | None = None
    realized_pnl_excl_fees: float | None = None
    unrealized_pnl_excl_fees: float | None = None
    net_settlements: float | None = None
    cumulative_funding: float | None = None
    pending_funding: float | None = None
    mark_price: float | None = None
    index_price: float | None = None
    delta: float | None = None
    gamma: float | None = None
    vega: float | None = None
    theta: float | None = None
    mark_value: float | None = None
    maintenance_margin: float | None = None
    initial_margin: float | None = None
    open_orders_margin: float | None = None
    leverage: float | None = None
    liquidation_price: float | None = None
    creation_timestamp: int | None = None
    amount_step: float | None = None

    @classmethod
    def from_json(cls, data):
        return cls(
            instrument_type=data.get("instrument_type"),
            instrument_name=data.get("instrument_name"),
            amount=float(data.get("amount", 0)) if data.get("amount") is not None else None,
            average_price=float(data.get("average_price", 0)) if data.get("average_price") is not None else None,
            realized_pnl=float(data.get("realized_pnl", 0)) if data.get("realized_pnl") is not None else None,
            unrealized_pnl=float(data.get("unrealized_pnl", 0)) if data.get("unrealized_pnl") is not None else None,
            total_fees=float(data.get("total_fees", 0)) if data.get("total_fees") is not None else None,
            average_price_excl_fees=float(data.get("average_price_excl_fees", 0))
            if data.get("average_price_excl_fees") is not None
            else None,
            realized_pnl_excl_fees=float(data.get("realized_pnl_excl_fees", 0))
            if data.get("realized_pnl_excl_fees") is not None
            else None,
            unrealized_pnl_excl_fees=float(data.get("unrealized_pnl_excl_fees", 0))
            if data.get("unrealized_pnl_excl_fees") is not None
            else None,
            net_settlements=float(data.get("net_settlements", 0)) if data.get("net_settlements") is not None else None,
            cumulative_funding=float(data.get("cumulative_funding", 0))
            if data.get("cumulative_funding") is not None
            else None,
            pending_funding=float(data.get("pending_funding", 0)) if data.get("pending_funding") is not None else None,
            mark_price=float(data.get("mark_price", 0)) if data.get("mark_price") is not None else None,
            index_price=float(data.get("index_price", 0)) if data.get("index_price") is not None else None,
            delta=float(data.get("delta", 0)) if data.get("delta") is not None else None,
            gamma=float(data.get("gamma", 0)) if data.get("gamma") is not None else None,
            vega=float(data.get("vega", 0)) if data.get("vega") is not None else None,
            theta=float(data.get("theta", 0)) if data.get("theta") is not None else None,
            mark_value=float(data.get("mark_value", 0)) if data.get("mark_value") is not None else None,
            maintenance_margin=float(data.get("maintenance_margin", 0))
            if data.get("maintenance_margin") is not None
            else None,
            initial_margin=float(data.get("initial_margin", 0)) if data.get("initial_margin") is not None else None,
            open_orders_margin=float(data.get("open_orders_margin", 0))
            if data.get("open_orders_margin") is not None
            else None,
            leverage=float(data.get("leverage")) if data.get("leverage") is not None else None,
            liquidation_price=float(data.get("liquidation_price"))
            if data.get("liquidation_price") is not None
            else None,
            creation_timestamp=int(data.get("creation_timestamp", 0))
            if data.get("creation_timestamp") is not None
            else None,
            amount_step=float(data.get("amount_step", 0)) if data.get("amount_step") is not None else None,
        )


@dataclass
class Order:
    """
    {'id': 'b7252ea0-74f3-4c9e-8132-ea48e9e9676d', 'result': {'order': {'subaccount_id': 137626, 'order_id': '0c246553-c517-4f22-82c3-5950880aebe7',
      'instrument_name': 'ETH-PERP', 'direction': 'buy', 'label': '', 'quote_id': None, 'amount': '0.1', 'average_price': '0', 'cancel_reason': '',
        'creation_timestamp': 1759238104969, 'filled_amount': '0', 'is_transfer': False, 'last_update_timestamp': 1759238104969, 'limit_price': '4153.53',
        'max_fee': '1000', 'mmp': False, 'nonce': 17592381048800, 'order_fee': '0', 'order_status': 'open', 'order_type': 'limit', 'replaced_order_id': None,
        'signature': '041eb5946515e84130e1e7c94f539f865b85b7c7eb8516b44559b7811d25807121ef44b041cd6677f340863ff120e64bc6f3f24ff9f7194b232f03d451c1d3371c',
          'signature_expiry_sec': 2147483647, 'signer': '0x86042886b1063625D0B3DDCC9e4cBcf912B79e16', 'time_in_force': 'gtc', 'trigger_type': None,
            'trigger_price': None, 'trigger_price_type': None, 'trigger_reject_message': None}, 'trades': []}}
    """

    order_id: str | None = None
    subaccount_id: int | None = None
    instrument_name: str | None = None
    direction: OrderSide | None = None
    label: str | None = None
    quote_id: str | None = None
    amount: float | None = None
    average_price: float | None = None
    cancel_reason: str | None = None
    creation_timestamp: int | None = None
    filled_amount: float | None = None
    is_transfer: bool | None = None
    last_update_timestamp: int | None = None
    limit_price: float | None = None
    max_fee: float | None = None
    mmp: bool | None = None
    nonce: int | None = None
    order_fee: float | None = None
    order_status: str | None = None
    order_type: str | None = None
    replaced_order_id: str | None = None
    signature: str | None = None
    signature_expiry_sec: int | None = None
    signer: str | None = None
    time_in_force: str | None = None
    trigger_type: str | None = None
    trigger_price: float | None = None
    trigger_price_type: str | None = None
    trigger_reject_message: str | None = None
    referral_code: str | None = None

    @classmethod
    def from_json(cls, data):
        return cls(
            order_id=data.get("order_id"),
            subaccount_id=data.get("subaccount_id"),
            instrument_name=data.get("instrument_name"),
            direction=OrderSide(data.get("direction")),
            label=data.get("label"),
            quote_id=data.get("quote_id"),
            amount=float(data.get("amount", 0)) if data.get("amount") is not None else None,
            average_price=float(data.get("average_price", 0)) if data.get("average_price") is not None else None,
            cancel_reason=data.get("cancel_reason"),
            creation_timestamp=int(data.get("creation_timestamp", 0))
            if data.get("creation_timestamp") is not None
            else None,
            filled_amount=float(data.get("filled_amount", 0)) if data.get("filled_amount") is not None else None,
            is_transfer=data.get("is_transfer"),
            last_update_timestamp=int(data.get("last_update_timestamp", 0))
            if data.get("last_update_timestamp") is not None
            else None,
            limit_price=float(data.get("limit_price", 0)) if data.get("limit_price") is not None else None,
            max_fee=float(data.get("max_fee", 0)) if data.get("max_fee") is not None else None,
            mmp=data.get("mmp"),
            nonce=int(data.get("nonce", 0)) if data.get("nonce") is not None else None,
            order_fee=float(data.get("order_fee", 0)) if data.get("order_fee") is not None else None,
            order_status=data.get("order_status"),
            order_type=data.get("order_type"),
            replaced_order_id=data.get("replaced_order_id"),
            signature=data.get("signature"),
            signature_expiry_sec=int(data.get("signature_expiry_sec", 0))
            if data.get("signature_expiry_sec") is not None
            else None,
            signer=data.get("signer"),
            time_in_force=data.get("time_in_force"),
            trigger_type=data.get("trigger_type"),
            trigger_price=float(data.get("trigger_price", 0)) if data.get("trigger_price") is not None else None,
            trigger_price_type=data.get("trigger_price_type"),
            trigger_reject_message=data.get("trigger_reject_message"),
        )


@dataclass
class Trade(Order):
    pass


@dataclass
class Trades:
    trades: list[dict]

    @classmethod
    def from_json(cls, data):
        return cls(
            trades=[Trade.from_json(trade) for trade in data],
        )


@dataclass
class Positions:
    positions: list[Position]
    subaccount_id: str

    @classmethod
    def from_json(cls, data):
        return cls(
            positions=[Position.from_json(pos) for pos in data],
            subaccount_id=data["subaccount_id"],
        )


@dataclass
class Orders:
    orders: list[Order]

    @classmethod
    def from_json(cls, data):
        return cls(
            orders=[Order.from_json(order) for order in data],
        )


class Depth(StrEnum):
    DEPTH_1 = "1"
    DEPTH_10 = "10"
    DEPTH_20 = "20"
    DEPTH_100 = "100"


class Group(StrEnum):
    GROUP_1 = "1"
    GROUP_10 = "10"
    GROUP_100 = "100"


class WsClient(BaseClient):
    """Websocket client class."""

    _ws: ClientConnection | None = None
    subsriptions: dict = {}
    requests_in_flight: dict = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.login_client()

    def connect_ws(self):
        return connect(
            self.config.ws_address,
        )

    @property
    def ws(self):
        if self._ws is None:
            self._ws = self.connect_ws()
        if self._ws.state is not State.OPEN:
            self._ws = self.connect_ws()
        return self._ws

    def login_client(
        self,
        retries=3,
    ):
        login_request = {
            "method": "public/login",
            "params": sign_ws_login(
                web3_client=self.web3_client,
                smart_contract_wallet=self.wallet,
                session_key_or_wallet_private_key=self.signer._private_key,
            ),
            "id": str(utc_now_ms()),
        }
        try:
            self.ws.send(json.dumps(login_request))
            # we need to wait for the response
            while True:
                message = json.loads(self.ws.recv())
                if message["id"] == login_request["id"]:
                    if "result" not in message:
                        if self._check_output_for_rate_limit(message):
                            return self.login_client()
                        raise DeriveJSONRPCException(**message["error"])
                    break
        except Exception as error:
            if retries:
                time.sleep(1)
                self.login_client(retries=retries - 1)
            raise error

    def create_order(
        self,
        amount: int,
        instrument_name: str,
        price: float = None,
        reduce_only=False,
        instrument_type: InstrumentType = InstrumentType.PERP,
        side: OrderSide = OrderSide.BUY,
        order_type: OrderType = OrderType.LIMIT,
        time_in_force: TimeInForce = TimeInForce.GTC,
        instruments=None,  # temporary hack to allow async fetching of instruments
    ) -> Order:
        """
        Create the order.
        """
        if side.name.upper() not in OrderSide.__members__:
            raise Exception(f"Invalid side {side}")

        if not instruments:
            _currency = UnderlyingCurrency[instrument_name.split("-")[0]]
            if instrument_type in [
                InstrumentType.PERP,
                InstrumentType.ERC20,
                InstrumentType.OPTION,
            ]:
                instruments = self._internal_map_instrument(instrument_type, _currency)
            else:
                raise Exception(f"Invalid instrument type {instrument_type}")

        instrument = instruments[instrument_name]
        amount_step = instrument["amount_step"]
        rounded_amount = Decimal(str(amount)).quantize(Decimal(str(amount_step)))

        if price is not None:
            price_step = instrument["tick_size"]
            rounded_price = Decimal(str(price)).quantize(Decimal(str(price_step)))

        module_data = {
            "asset_address": instrument["base_asset_address"],
            "sub_id": int(instrument["base_asset_sub_id"]),
            "limit_price": Decimal(str(rounded_price)) if price is not None else Decimal(0),
            "amount": Decimal(str(rounded_amount)),
            "max_fee": Decimal(1000),
            "recipient_id": int(self.subaccount_id),
            "is_bid": side == OrderSide.BUY,
        }

        signed_action = self._generate_signed_action(
            module_address=self.config.contracts.TRADE_MODULE, module_data=module_data
        )

        order = {
            "instrument_name": instrument_name,
            "direction": side.name.lower(),
            "order_type": order_type.name.lower(),
            "mmp": False,
            "time_in_force": time_in_force.value,
            "referral_code": DEFAULT_REFERER,
            **signed_action.to_json(),
        }
        _id = str(uuid.uuid4())
        self.ws.send(json.dumps({"method": "private/order", "params": order, "id": _id}))
        self.requests_in_flight[_id] = self._parse_order_message
        return Order(**order)

    def subscribe_orderbook(self, instrument_name, group: Group = Group.GROUP_1, depth: Depth = Depth.DEPTH_1):
        """
        Subscribe to an orderbook feed.
        """
        msg = f"orderbook.{instrument_name}.{group}.{depth}"
        self.ws.send(json.dumps({"method": "subscribe", "params": {"channels": [msg]}, "id": str(utc_now_ms())}))
        self.subsriptions[msg] = self._parse_orderbook_message

    def subscribe_trades(self):
        """
        Subscribe to trades feed.
        """
        msg = f"{self.subaccount_id}.trades"
        self.ws.send(json.dumps({"method": "subscribe", "params": {"channels": [msg]}, "id": str(utc_now_ms())}))
        self.subsriptions[msg] = self._parse_trades_message

    def subscribe_orders(self):
        """
        Subscribe to orders feed.
        """
        msg = f"{self.subaccount_id}.orders"
        self.ws.send(json.dumps({"method": "subscribe", "params": {"channels": [msg]}, "id": str(utc_now_ms())}))
        self.subsriptions[msg] = self._parse_orders_stream

    def _parse_orderbook_message(self, json_message):
        """
        Parse an orderbook message.
        """
        return Orderbook.from_json(json_message)

    def _parse_trades_message(self, json_message):
        """
        Parse a trades message.
        """
        return Trades.from_json(json_message["params"]["data"])

    def _parse_order_message(self, json_message):
        """
        Parse an orders message.
        """
        result = json_message.get("result", None)
        if result is None:
            raise Exception(f"Invalid order message {json_message}")
        if "order" not in result:
            return Order.from_json(json_message["result"])
        return Order.from_json(json_message["result"]["order"])

    def _parse_orders_stream(self, json_message):
        """
        Parse an orders message.
        """
        return Orders.from_json(json_message["params"]["data"])

    def _parse_orders_message(self, json_message):
        """
        Parse an orders message.
        """
        return Orders.from_json(json_message["result"]["orders"])

    def get_positions(self):
        """
        Get positions
        """
        id = str(uuid.uuid4())
        payload = {"subaccount_id": self.subaccount_id}
        self.ws.send(json.dumps({"method": "private/get_positions", "params": payload, "id": id}))
        self.requests_in_flight[id] = self._parse_positions_response

    def get_orders(self):
        """
        Get orders
        """
        id = str(uuid.uuid4())
        payload = {"subaccount_id": self.subaccount_id}
        self.ws.send(json.dumps({"method": "private/get_open_orders", "params": payload, "id": id}))
        self.requests_in_flight[id] = self._parse_orders_message

    def _parse_positions_response(self, json_message):
        """
        Parse a positions response message.
        """
        return Positions(
            [Position.from_json(pos) for pos in json_message["result"]["positions"]],
            subaccount_id=json_message["result"]["subaccount_id"],
        )

    def parse_message(self, raw_message):
        """
        find the parser based on the message type.
        """
        json_message = json.loads(raw_message)
        if "method" in json_message and json_message["method"] == "subscription":
            channel = json_message["params"]["channel"]
            if channel in self.subsriptions:
                return self.subsriptions[channel](json_message)
            raise Exception(f"Unknown channel {channel}")
        if "id" in json_message and json_message["id"] in self.requests_in_flight:
            parser = self.requests_in_flight.pop(json_message["id"])
            return parser(json_message)
        return json_message

    def cancel(self, order_id, instrument_name):
        """
        Cancel an order
        """

        id = str(uuid.uuid4())
        payload = {
            "order_id": order_id,
            "subaccount_id": self.subaccount_id,
            "instrument_name": instrument_name,
        }
        self.ws.send(json.dumps({"method": "private/cancel", "params": payload, "id": id}))
        self.requests_in_flight[id] = self._parse_order_cancel_message

    def _parse_order_cancel_message(self, json_message):
        """
        Parse an order cancel message.
        """
        error = json_message.get("error", None)
        if error and error.get("code") in [11006, -32603]:
            return
        result = json_message.get("result", None)
        return Order.from_json(result)

    def cancel_all(self):
        """
        Cancel all orders
        """
        id = str(uuid.uuid4())
        payload = {"subaccount_id": self.subaccount_id}
        self.ws.send(json.dumps({"method": "private/cancel_all", "params": payload, "id": id}))
