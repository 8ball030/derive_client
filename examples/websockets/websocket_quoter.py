"""
Simple trading class for the websocket client.
"""

import asyncio
from decimal import Decimal
from typing import List

from dotenv import load_dotenv
from utils import get_default_position

from derive_client import WebSocketClient
from derive_client.data_types.channel_models import (
    Depth,
    Group,
    OrderbookInstrumentNameGroupDepthPublisherDataSchema,
    OrderResponseSchema,
    TradeResponseSchema,
)
from derive_client.data_types.generated_models import (
    Direction,
    OrderStatus,
    OrderType,
    PositionResponseSchema,
)
from derive_client.data_types.utils import D

MARKET_1 = "HYPE-PERP"
MAX_POSTION_SIZE = D(10)
QUOTE_SIZE = D(1)
BUY_OFFSET = D(0.0003)
SELL_OFFSET = D(0.0003)
# for adjusting orders
MAX_ORDER_OFFSET = D(0.01)
MIN_ORDER_OFFSET = D(0.000005)

ENTRY_LABEL = "simple_quoter"


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

        bid_price = orderbook.bids[0][0]
        ask_price = orderbook.asks[0][0]

        if all(
            [
                self.current_position.amount <= (MAX_POSTION_SIZE - QUOTE_SIZE),
                not self.orders[Direction.buy],
                not self.pending_orders[Direction.buy],
            ]
        ):
            order_price = bid_price * (D(1) - BUY_OFFSET)
            await self.create_order(Direction.buy, order_price, QUOTE_SIZE)
            return
        if all(
            [
                self.current_position.amount >= -(MAX_POSTION_SIZE + QUOTE_SIZE),
                not self.orders[Direction.sell],
                not self.pending_orders[Direction.sell],
            ]
        ):
            order_price = ask_price * (D(1) + SELL_OFFSET)
            await self.create_order(Direction.sell, order_price, QUOTE_SIZE)
            return
        # check if any existing orders need to be adjusted based on the price.
        for order in list(self.orders[Direction.buy].values()):
            if self.pending_orders[Direction.buy]:
                continue
            # we check the price bounds here
            lower_bound = bid_price * (D(1) - MAX_ORDER_OFFSET)
            upper_bound = bid_price * (D(1) - MIN_ORDER_OFFSET)
            if not (lower_bound <= order.limit_price <= upper_bound):
                self.pending_orders[Direction.buy] = True
                await self.ws_client.orders.cancel(order_id=order.order_id, instrument_name=MARKET_1)
                del self.orders[Direction.buy][order.nonce]
                self.pending_orders[Direction.buy] = False
        for order in list(self.orders[Direction.sell].values()):
            if self.pending_orders[Direction.sell]:
                continue
            # we check the price bounds here
            lower_bound = ask_price * (D(1) + MIN_ORDER_OFFSET)
            upper_bound = ask_price * (D(1) + MAX_ORDER_OFFSET)
            if not (lower_bound <= order.limit_price <= upper_bound):
                self.pending_orders[Direction.sell] = True
                await self.ws_client.orders.cancel(order_id=order.order_id, instrument_name=MARKET_1)
                del self.orders[Direction.sell][order.nonce]
                self.pending_orders[Direction.sell] = False

    async def create_order(self, side: Direction, price: Decimal, amount: Decimal) -> OrderResponseSchema:
        self.pending_orders[side] = True
        order = await self.ws_client.orders.create(
            instrument_name=MARKET_1,
            direction=side,
            limit_price=price,
            amount=amount,
            order_type=OrderType.limit,
            label=ENTRY_LABEL,
        )
        self.pending_orders[side] = False
        self.logger.info(f"{side.value} order placed: {order.nonce} at {price} for {amount}")
        self.orders[side][order.nonce] = order
        return order

    async def on_order(self, orders: List[OrderResponseSchema]):
        for order in orders:
            if order.instrument_name != MARKET_1 or order.label != ENTRY_LABEL:
                continue
            self.logger.info(
                f"Order update: {order.order_id} {order.order_status} "
                + f"{order.direction} {order.limit_price} {order.amount}"
            )
            match order.order_status:
                case OrderStatus.filled | OrderStatus.cancelled:
                    if order.filled_amount > 0:
                        self.logger.info(f"Order filled: {order.nonce} {order.filled_amount} @ {order.average_price}")
                        await self.refresh_positions()
                    if order.nonce in self.orders[order.direction]:
                        del self.orders[order.direction][order.nonce]
                case OrderStatus.open:
                    self.orders[order.direction][order.nonce] = order
                case OrderStatus.expired:
                    if order.nonce in self.orders[order.direction]:
                        del self.orders[order.direction][order.nonce]

    async def on_trade(self, trades: List[TradeResponseSchema]):
        await self.refresh_positions()
        for trade in trades:
            self.logger.info(
                f"Trade executed: {trade.trade_id} {trade.direction} "
                + f"{trade.trade_price} {trade.trade_amount} "
                + f"on order {trade.order_id}"
            )
            if trade.label != ENTRY_LABEL or trade.instrument_name != MARKET_1:
                continue
            # we make a take profit or stop loss adjustment here if needed
            tp_direction = Direction.sell if trade.direction == Direction.buy else Direction.buy
            tp_price = trade.trade_price * (D(1) + SELL_OFFSET if tp_direction == Direction.sell else D(1) - BUY_OFFSET)
            await self.ws_client.orders.create(
                instrument_name=MARKET_1,
                direction=tp_direction,
                limit_price=tp_price,
                amount=trade.trade_amount,
                order_type=OrderType.limit,
                label="take_profit",
            )

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
                if o.direction == Direction.buy
                and o.order_status == OrderStatus.open
                and o.instrument_name == MARKET_1
                and o.label == ENTRY_LABEL
            },
            Direction.sell: {
                o.nonce: o
                for o in current_orders
                if o.direction == Direction.sell
                and o.order_status == OrderStatus.open
                and o.instrument_name == MARKET_1
                and o.label == ENTRY_LABEL
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
    assert (
        BUY_OFFSET < MAX_ORDER_OFFSET
        and SELL_OFFSET < MAX_ORDER_OFFSET
        and BUY_OFFSET > MIN_ORDER_OFFSET
        and SELL_OFFSET > MIN_ORDER_OFFSET
    ), "Offsets are not correctly set."
    ws_client = WebSocketClient.from_env()
    quoter = WebsocketQuoterStrategy(ws_client)
    try:
        await quoter.run_loop()
    except KeyboardInterrupt:
        quoter.logger.info("Shutting down quoter strategy...")
    finally:
        await ws_client.orders.cancel_by_label(instrument_name=MARKET_1, label=ENTRY_LABEL)
        await ws_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
