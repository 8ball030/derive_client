"""
Simple trading class for the websocket client.
"""

import asyncio
from decimal import Decimal
from typing import List

from dotenv import load_dotenv

from derive_client import WebSocketClient
from derive_client.data_types.channel_models import (
    Depth,
    Group,
    OrderbookInstrumentNameGroupDepthPublisherDataSchema,
    OrderResponseSchema,
    TradeResponseSchema,
)
from derive_client.data_types.generated_models import (
    AssetType,
    Direction,
    OrderStatus,
    OrderType,
    PositionResponseSchema,
)
from derive_client.data_types.utils import D

MARKET_1 = "ETH-PERP"
MAX_POSTION_SIZE = D(0.5)
QUOTE_SIZE = D(0.1)
BUY_OFFSET = D(0.99)
SELL_OFFSET = D(1.01)
MAX_ORDER_OFFSET = D(0.0125)
MIN_ORDER_OFFSET = D(0.0075)


def get_default_position(instrument_name: str) -> PositionResponseSchema:
    return PositionResponseSchema(
        instrument_name=instrument_name,
        amount=Decimal(0),
        average_price=Decimal(0),
        unrealized_pnl=Decimal(0),
        realized_pnl=Decimal(0),
        leverage=Decimal(0),
        maintenance_margin=Decimal(0),
        initial_margin=Decimal(0),
        liquidation_price=None,
        amount_step=Decimal(0),
        average_price_excl_fees=Decimal(0),
        creation_timestamp=0,
        cumulative_funding=Decimal(0),
        delta=Decimal(0),
        gamma=Decimal(0),
        vega=Decimal(0),
        theta=Decimal(0),
        unrealized_pnl_excl_fees=Decimal(0),
        index_price=Decimal(0),
        mark_price=Decimal(0),
        instrument_type=AssetType.perp,
        mark_value=Decimal(0),
        total_fees=Decimal(0),
        net_settlements=Decimal(0),
        open_orders_margin=Decimal(0),
        pending_funding=Decimal(0),
        realized_pnl_excl_fees=Decimal(0),
    )


class WebsocketQuoterStrategy:
    def __init__(self, ws_client: WebSocketClient):
        self.ws_client = ws_client
        self.current_position: PositionResponseSchema | None = None
        self.orders = {
            Direction.buy: {},
            Direction.sell: {},
        }
        self.pending_orders = {
            Direction.buy: False,
            Direction.sell: False,
        }
        self.logger = ws_client._logger

    async def on_orderbook_update(self, orderbook: OrderbookInstrumentNameGroupDepthPublisherDataSchema):
        if not orderbook.bids or not orderbook.asks:
            return

        if not self.current_position:
            return

        bid_price = orderbook.bids[0][0] * BUY_OFFSET
        ask_price = orderbook.asks[0][0] * SELL_OFFSET

        if all(
            [
                self.current_position.amount <= (MAX_POSTION_SIZE - QUOTE_SIZE),
                not self.orders[Direction.buy],
                not self.pending_orders[Direction.buy],
            ]
        ):
            price = bid_price * BUY_OFFSET
            await self.create_order(Direction.buy, price, QUOTE_SIZE)
            return
        if all(
            [
                self.current_position.amount >= -(MAX_POSTION_SIZE + QUOTE_SIZE),
                not self.orders[Direction.sell],
                not self.pending_orders[Direction.sell],
            ]
        ):
            price = ask_price * SELL_OFFSET
            await self.create_order(Direction.sell, price, QUOTE_SIZE)
            return
        # check if any existing orders need to be cancelled
        for order in list(self.orders[Direction.buy].values()):
            price_diff = abs((order.limit_price - bid_price) / bid_price)
            if price_diff > MAX_ORDER_OFFSET or price_diff < MIN_ORDER_OFFSET:
                del self.orders[Direction.buy][order.nonce]
                await self.ws_client.orders.cancel(order_id=order.order_id, instrument_name=MARKET_1)
        for order in list(self.orders[Direction.sell].values()):
            price_diff = abs((order.limit_price - ask_price) / ask_price)
            if price_diff > MAX_ORDER_OFFSET or price_diff < MIN_ORDER_OFFSET:
                del self.orders[Direction.sell][order.nonce]
                await self.ws_client.orders.cancel(order_id=order.order_id, instrument_name=MARKET_1)

    async def create_order(self, side: Direction, price: Decimal, amount: Decimal) -> OrderResponseSchema:
        self.pending_orders[side] = True
        order = await self.ws_client.orders.create(
            instrument_name=MARKET_1,
            direction=side,
            limit_price=price,
            amount=amount,
            order_type=OrderType.limit,
        )
        self.pending_orders[side] = False
        self.logger.info(f"{side.value} order placed: {order.nonce} at {price} for {amount}")
        self.orders[side][order.nonce] = order
        return order

    async def on_order(self, orders: List[OrderResponseSchema]):
        for order in orders:
            self.logger.info(
                f"Order update: {order.order_id} {order.order_status} "
                + f"{order.direction} {order.limit_price} {order.amount}"
            )
            match order.order_status:
                case OrderStatus.filled | OrderStatus.cancelled | OrderStatus.expired:
                    if order.filled_amount > 0:
                        self.logger.info(f"Order filled: {order.nonce} {order.filled_amount} @ {order.average_price}")
                    if order.nonce in self.orders[order.direction]:
                        del self.orders[order.direction][order.nonce]
                case OrderStatus.open:
                    self.orders[order.direction][order.nonce] = order
        await self.refresh_positions()

    async def on_trade(self, trades: List[TradeResponseSchema]):
        print(f"Trades update: {trades} trades")
        await self.refresh_positions()

    async def run_loop(self):
        """
        Run the message loop.
        """
        await self.setup_session()
        await asyncio.Event().wait()

    async def refresh_positions(self):
        self.current_position = None
        current_positions = await self.ws_client.positions.list()
        filtered_positions = [p for p in current_positions if p.instrument_name == MARKET_1]
        self.current_position = filtered_positions[0] if filtered_positions else get_default_position(MARKET_1)

    async def refresh_orders(self):
        current_orders = await self.ws_client.orders.list_open()
        self.orders = {
            Direction.buy: {
                o.nonce: o
                for o in current_orders
                if o.direction == Direction.buy and o.order_status == OrderStatus.open
            },
            Direction.sell: {
                o.nonce: o
                for o in current_orders
                if o.direction == Direction.sell and o.order_status == OrderStatus.open
            },
        }

    async def setup_session(self):
        await self.ws_client.connect()
        await self.refresh_positions()
        await self.refresh_orders()

        await self.ws_client.public_channels.orderbook_group_depth_by_instrument_name(
            instrument_name=MARKET_1,
            group=Group.field_1,
            depth=Depth.field_1,
            callback=self.on_orderbook_update,
        )
        await self.ws_client.private_channels.orders_by_subaccount_id(
            subaccount_id=str(self.ws_client.active_subaccount.id),
            callback=self.on_order,
        )

        await self.ws_client.private_channels.trades_by_subaccount_id(
            subaccount_id=str(self.ws_client.active_subaccount.id),
            callback=self.on_trade,
        )


async def main():
    load_dotenv()
    ws_client = WebSocketClient.from_env()
    quoter = WebsocketQuoterStrategy(ws_client)
    try:
        await quoter.run_loop()
    except KeyboardInterrupt:
        print("On keyboard interupt...")
    finally:
        await ws_client.orders.cancel_all()
        await ws_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
