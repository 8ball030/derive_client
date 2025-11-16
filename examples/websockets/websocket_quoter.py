"""
Simple trading class for the websocket client.
"""

import os
import traceback

from dotenv import load_dotenv
from websockets import ConnectionClosedError

from derive_client.clients.ws_client import (
    Orderbook,
    OrderResponseSchema,
    PrivateGetOrdersResultSchema,
    TradeResponseSchema,
    WsClient,
)
from derive_client.data.generated.models import (
    Direction,
    OrderStatus,
    PositionResponseSchema,
    PrivateGetPositionsResponseSchema,
    PrivateGetPositionsResultSchema,
)
from derive_client.data_types import Environment
from derive_client.data_types.enums import InstrumentType, OrderSide, OrderType

MARKET_1 = "ETH-PERP"
MAX_POSTION_SIZE = 0.5
QUOTE_SIZE = 0.1
BUY_OFFSET = 0.99
SELL_OFFSET = 1.01


class WebsocketQuoterStrategy:
    def __init__(self, ws_client: WsClient):
        self.ws_client = ws_client
        self.current_positions: PrivateGetPositionsResponseSchema | None = None
        self.current_position: PositionResponseSchema | None | bool = False
        self.orders = {
            Direction.buy: {},
            Direction.sell: {},
        }
        self.pending_orders = {
            Direction.buy: {},
            Direction.sell: {},
        }

    def on_orderbook_update(self, orderbook: Orderbook):
        if not orderbook.bids or not orderbook.asks:
            return

        if self.current_position is None:
            return

        print(orderbook)

        bid_price = orderbook.bids[0][0] * BUY_OFFSET
        ask_price = orderbook.asks[0][0] * SELL_OFFSET

        if all(
            [
                self.current_position.amount <= (MAX_POSTION_SIZE - QUOTE_SIZE),
                not self.orders[Direction.buy],
                self.pending_orders[Direction.buy] == {},
            ]
        ):
            self.create_order(Direction.buy, bid_price, QUOTE_SIZE)
        if all(
            [
                self.current_position.amount >= -(MAX_POSTION_SIZE + QUOTE_SIZE),
                not self.orders[Direction.sell],
                self.pending_orders[Direction.sell] == {},
            ]
        ):
            self.create_order(Direction.sell, ask_price, QUOTE_SIZE)

    def update_order_price(self, old_order_nonce: str, new_price: float):
        pass

    def create_order(self, side: OrderSide, price: float, amount: float) -> OrderResponseSchema:
        order = self.ws_client.create_order(
            instrument_name=MARKET_1,
            side=side,
            price=price,
            amount=amount,
            order_type=OrderType.LIMIT,
        )
        self.pending_orders[side][order.nonce] = order
        print(f"{side.value} order placed: {order.nonce} at {price} for {amount}")
        return order

    def on_position_update(self, positions: PrivateGetPositionsResultSchema):
        self.current_positions = positions
        if not positions.positions:
            self.current_position = self.get_empty_position()
            print("No current position")

        else:
            _matches = [p for p in positions.positions if p.instrument_name == MARKET_1]
            if _matches:
                self.current_position = _matches[0]
                pos = self.current_position
                print(f"Current position: {pos.instrument_name} {pos.amount} @ {pos.average_price}")
            else:
                self.current_position = self.get_empty_position()
                print("No current position")

    def get_empty_position(self) -> PositionResponseSchema:
        return PositionResponseSchema(
            amount=0,
            amount_step=0,
            average_price=0,
            average_price_excl_fees=0,
            creation_timestamp=0,
            cumulative_funding=0,
            delta=0,
            gamma=0,
            index_price=0,
            initial_margin=0,
            instrument_name=MARKET_1,
            instrument_type=InstrumentType.PERP,
            maintenance_margin=0,
            mark_price=0,
            mark_value=0,
            net_settlements=0,
            open_orders_margin=0,
            pending_funding=0,
            realized_pnl=0,
            realized_pnl_excl_fees=0,
            theta=0,
            total_fees=0,
            unrealized_pnl=0,
            unrealized_pnl_excl_fees=0,
            vega=0,
        )

    def on_order(self, order: OrderResponseSchema):
        print(f"Order update: {order.nonce} {order.order_status} {order.direction} {order.limit_price} {order.amount}")
        self.ws_client.get_positions()
        if order.order_status is OrderStatus.open:
            if order.nonce in self.pending_orders[order.direction]:
                print(f"Moving order {order.nonce} from pending to active")
                del self.pending_orders[order.direction][order.nonce]
            self.orders[order.direction][order.nonce] = order

    def on_orders_update(self, orders: PrivateGetOrdersResultSchema):
        print(f"Orders update: {len(orders.orders)} orders")

        for side in [Direction.buy, Direction.sell]:
            side_orders = [o for o in orders.orders if o.direction == side]
            self.orders[side].update({o.nonce: o for o in side_orders})
            current_orders = self.orders[side]
            for ix, (nonce, order) in enumerate(current_orders.copy().items()):
                if order.order_status != OrderStatus.open or ix > 0:
                    print(f"Removing order {nonce} from tracking")
                    del self.orders[side][nonce]
                    self.ws_client.cancel(order.order_id, MARKET_1)

    def on_trade(self, trades: TradeResponseSchema):
        print(f"Trades update: {len(trades.trades)} trades")
        self.ws_client.get_positions()
        if self.current_position and abs(self.current_position.amount) >= MAX_POSTION_SIZE:
            self.ws_client.cancel_all()

    def run_loop(self):
        """
        Run the message loop.
        """
        self.setup_session()

        while True:
            try:
                raw_message = self.ws_client.ws.recv()
            except ConnectionClosedError:
                print("Connection closed, exiting...")
                self.setup_session()
            parsed_message = self.ws_client.parse_message(raw_message)
            try:
                if isinstance(parsed_message, TradeResponseSchema):
                    self.on_trade(parsed_message)
                elif isinstance(parsed_message, PrivateGetPositionsResultSchema):
                    print("Position update received")
                    self.on_position_update(parsed_message)
                elif isinstance(parsed_message, PrivateGetOrdersResultSchema):
                    self.on_orders_update(parsed_message)
                elif isinstance(parsed_message, OrderResponseSchema):
                    self.on_order(parsed_message)
                elif isinstance(parsed_message, Orderbook):
                    self.on_orderbook_update(parsed_message)
                else:
                    print(f"Received unhandled message: {parsed_message}")
            except Exception:
                print(f"Error processing message {parsed_message}: {traceback.format_exc()}")

    def setup_session(self):
        self.ws_client.connect_ws()
        self.ws_client.login_client()
        # get state data
        print("Fetching initial state...")
        self.ws_client.get_orders()
        self.ws_client.get_positions()
        # subscribe to updates
        self.ws_client.subscribe_orderbook(MARKET_1)
        self.ws_client.subscribe_trades()
        self.ws_client.subscribe_orders()


def create_client_from_env() -> WsClient:
    """
    Load in the client from environment variables.
    """
    load_dotenv()
    private_key = os.environ["ETH_PRIVATE_KEY"]
    wallet = os.environ["DERIVE_WALLET"]
    env = os.environ["DERIVE_ENV"]
    subaccount_id = os.environ.get(
        "SUBACCOUNT_ID",
    )
    return WsClient(
        private_key=private_key,
        wallet=wallet,
        env=Environment(env),
        subaccount_id=subaccount_id,
    )


if __name__ == "__main__":
    ws_client = create_client_from_env()
    print(ws_client.signer.address)
    quoter = WebsocketQuoterStrategy(ws_client)
    try:
        quoter.run_loop()
    except KeyboardInterrupt:
        print("On keyboard interupt...")
    finally:
        ws_client.ws.close()
