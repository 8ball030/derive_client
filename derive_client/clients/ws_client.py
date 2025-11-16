"""
Class to handle base websocket client
"""

import json
import time
import uuid
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

import msgspec
from derive_action_signing.utils import sign_ws_login, utc_now_ms
from websockets import State
from websockets.sync.client import ClientConnection, connect

from derive_client.constants import DEFAULT_REFERER
from derive_client.data.generated.models import (
    Direction,
    OrderResponseSchema,
    PrivateGetOrdersResultSchema,
    PrivateGetPositionsResultSchema,
    PrivateOrderParamsSchema,
    PublicGetTickerResultSchema,
    TradeResponseSchema,
)
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


class Depth(StrEnum):
    DEPTH_1 = "1"
    DEPTH_10 = "10"
    DEPTH_20 = "20"
    DEPTH_100 = "100"


class Group(StrEnum):
    GROUP_1 = "1"
    GROUP_10 = "10"
    GROUP_100 = "100"


class Interval(StrEnum):
    ONE_HUNDRED_MS = "100"
    ONE_SECOND = "1000"


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
    ) -> OrderResponseSchema:
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
            "is_bid": side == Direction.buy,
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
        return PrivateOrderParamsSchema(**order)

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

    def subscribe_ticker(self, instrument_name, interval: Interval = Interval.ONE_HUNDRED_MS):
        """
        Subscribe to a ticker feed.
        """
        msg = f"ticker.{instrument_name}.{interval}"
        self.ws.send(json.dumps({"method": "subscribe", "params": {"channels": [msg]}, "id": str(utc_now_ms())}))
        self.subsriptions[msg] = self._parse_ticker

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

    def _parse_ticker(self, json_message):
        """
        Parse a ticker message.
        """
        return msgspec.convert(json_message["params"]["data"]['instrument_ticker'], PublicGetTickerResultSchema)

    def _parse_orderbook_message(self, json_message):
        """
        Parse an orderbook message.
        """
        return Orderbook.from_json(json_message)

    def _parse_trades_message(self, json_message):
        """
        Parse a trades message.
        """
        return msgspec.convert(json_message["params"]["data"], TradeResponseSchema)

    def _parse_order_message(self, json_message):
        """
        Parse an orders message.
        """
        result = json_message.get("result", None)
        if result is None:
            raise Exception(f"Invalid order message {json_message}")
        if "order" not in result:
            return msgspec.convert(json_message["result"], OrderResponseSchema)
        return msgspec.convert(json_message["result"]["order"], OrderResponseSchema)

    def _parse_orders_stream(self, json_message):
        """
        Parse an orders message.
        """
        return msgspec.convert(
            {"subaccount_id": self.subaccount_id, "orders": json_message['params']['data']},
            PrivateGetOrdersResultSchema,
        )

    def _parse_orders_message(self, json_message):
        """
        Parse an orders message.
        """
        return msgspec.convert(json_message['result'], PrivateGetOrdersResultSchema)

    def _parse_positions_response(self, json_message):
        """
        Parse a positions response message.
        """
        return msgspec.convert(json_message['result'], PrivateGetPositionsResultSchema)

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
        return OrderResponseSchema(**result)

    def cancel_all(self):
        """
        Cancel all orders
        """
        id = str(uuid.uuid4())
        payload = {"subaccount_id": self.subaccount_id}
        self.ws.send(json.dumps({"method": "private/cancel_all", "params": payload, "id": id}))
