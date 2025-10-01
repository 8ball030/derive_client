"""
Simple trading class for the websocket client.
"""

import os

from dotenv import load_dotenv
from derive_client.clients.ws_client import Order, Orderbook, Orders, Position, Positions, Trades, WsClient
from derive_client.data_types import Environment
from derive_client.data_types.enums import OrderSide, OrderType

MARKET_1 = "ETH-PERP"
MAX_POSTION_SIZE = 0.5
QUOTE_SIZE = 0.1
BUY_OFFSET = 0.99
SELL_OFFSET = 1.01


class WebsocketQuoter:
    def __init__(self, ws_client: WsClient):
        self.ws_client = ws_client
        self.current_positions: Positions | None = None
        self.current_position: Position | None = None
        self.orders = {
            OrderSide.BUY: {},
            OrderSide.SELL: {},
        }

    def on_orderbook_update(self, orderbook: Orderbook):
        if not orderbook.bids or not orderbook.asks:
            return

        bid_price = orderbook.bids[0][0] * BUY_OFFSET
        ask_price = orderbook.asks[0][0] * SELL_OFFSET

        if self.current_position.amount <= (MAX_POSTION_SIZE - QUOTE_SIZE) and not self.orders[OrderSide.BUY]:
            self.create_order(OrderSide.BUY, bid_price, QUOTE_SIZE)
        if self.current_position.amount >= -(MAX_POSTION_SIZE + QUOTE_SIZE) and not self.orders[OrderSide.SELL]:
            self.create_order(OrderSide.SELL, ask_price, QUOTE_SIZE)

    def create_order(self, side: OrderSide, price: float, amount: float) -> Order:
        order = self.ws_client.create_order(
            instrument_name=MARKET_1,
            side=side,
            price=price,
            amount=amount,
            order_type=OrderType.LIMIT,
        )
        self.orders[side][order.nonce] = order
        print(f"{side.value} order placed: {order.nonce} at {price} for {amount}")
        return order

    def on_position_update(self, positions: Positions):
        self.current_positions = positions
        if not positions.positions:
            self.current_position = Position(instrument_name=MARKET_1, amount=0)
        else:
            _matches = [p for p in positions.positions if p.instrument_name == MARKET_1]
            self.current_position = _matches[0] if _matches else Position(instrument_name=MARKET_1, amount=0)

        pos = self.current_position
        print(f"Current position: {pos.instrument_name} {pos.amount} @ {pos.average_price}")

    def on_order(self, order: Order):
        print(f"Order update: {order.nonce} {order.order_status} {order.direction} {order.limit_price} {order.amount}")
        self.ws_client.get_positions()

    def on_orders_update(self, orders: Orders):
        print(f"Orders update: {len(orders.orders)} orders")

        for side in [OrderSide.BUY, OrderSide.SELL]:
            side_orders = [o for o in orders.orders if o.direction == side]
            self.orders[side].update({o.nonce: o for o in side_orders})
            current_orders = self.orders[side]
            for ix, (nonce, order) in enumerate(current_orders.copy().items()):
                if order.order_status != "open" or ix > 0:
                    print(f"Removing order {nonce} from tracking")
                    del self.orders[side][nonce]
                    self.ws_client.cancel(order.order_id, MARKET_1)

    def on_trade(self, trades: Trades):
        print(f"Trades update: {len(trades.trades)} trades")
        self.ws_client.get_positions()
        if self.current_position and abs(self.current_position.amount) >= MAX_POSTION_SIZE:
            self.ws_client.cancel_all()

    def run_loop(self):
        """
        Run the message loop.
        """
        self.ws_client.connect_ws()
        self.ws_client.login_client()
        # get state data
        self.ws_client.get_orders()
        self.ws_client.get_positions()
        # subscribe to updates
        self.ws_client.subscribe_tickers()
        self.ws_client.subscribe_orderbook(MARKET_1)
        self.ws_client.subscribe_trades()
        self.ws_client.subscribe_orders()

        while True:
            raw_message = self.ws_client.ws.recv()
            parsed_message = self.ws_client.parse_message(raw_message)
            if isinstance(parsed_message, Trades):
                self.on_trade(parsed_message)
            elif isinstance(parsed_message, Positions):
                self.on_position_update(parsed_message)
            elif isinstance(parsed_message, Orders):
                self.on_orders_update(parsed_message)
            elif isinstance(parsed_message, Order):
                self.on_order(parsed_message)
            elif isinstance(parsed_message, Orderbook):
                self.on_orderbook_update(parsed_message)
            else:
                print(f"Received unhandled message: {parsed_message}")

def create_client_from_env() -> WsClient:
    """
    Load in the client from environment variables.
    """
    load_dotenv()
    private_key = os.environ["ETH_PRIVATE_KEY"]
    wallet = os.environ["DERIVE_WALLET"]
    env = os.environ["DERIVE_ENV"]
    subaccount_id = os.environ.get("SUBACCOUNT_ID",)
    return WsClient(
        private_key=private_key,
        wallet=wallet,
        env=Environment(env),
        subaccount_id=subaccount_id,

    )

if __name__ == "__main__":
    ws_client = create_client_from_env()
    quoter = WebsocketQuoter(ws_client)
    try:
        quoter.run_loop()
    except KeyboardInterrupt:
        print("On keyboard interupt...")
    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        ws_client.ws.close()
