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

MAX_POSITION_SIZE = D(10)
QUOTE_SIZE = D(1)

BUY_OFFSET = D(0.0003)
SELL_OFFSET = D(0.0003)

MAX_ORDER_OFFSET = D(0.01)
MIN_ORDER_OFFSET = D(0.000005)

ENTRY_LABEL = "simple_quoter"
TP_LABEL = "take_profit"


def buy_quote_price(bid: Decimal) -> Decimal:
    return bid * (D(1) - BUY_OFFSET)


def sell_quote_price(ask: Decimal) -> Decimal:
    return ask * (D(1) + SELL_OFFSET)


def buy_bounds(bid: Decimal) -> tuple[Decimal, Decimal]:
    # buy order should stay just below bid:
    low = bid * (D(1) - MAX_ORDER_OFFSET)
    high = bid * (D(1) - MIN_ORDER_OFFSET)
    return low, high


def sell_bounds(ask: Decimal) -> tuple[Decimal, Decimal]:
    # sell order should stay just above ask:
    low = ask * (D(1) + MIN_ORDER_OFFSET)
    high = ask * (D(1) + MAX_ORDER_OFFSET)
    return low, high


class WebsocketQuoterStrategy:
    current_position: PositionResponseSchema
    order: dict[Direction, OrderResponseSchema | None] = {
        Direction.buy: None,
        Direction.sell: None,
    }
    lock: dict[Direction, asyncio.Lock] = {
        Direction.buy: asyncio.Lock(),
        Direction.sell: asyncio.Lock(),
    }

    def __init__(self, ws_client: WebSocketClient):
        self.ws_client = ws_client
        self.logger = ws_client._logger

    async def run_loop(self):
        await self.setup_session()
        await asyncio.Event().wait()

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

    async def refresh_positions(self):
        positions = await self.ws_client.positions.list()
        p = next((p for p in positions if p.instrument_name == MARKET_1), None)
        self.current_position = p if p else get_default_position(MARKET_1)

    async def refresh_orders(self):
        open_orders = await self.ws_client.orders.list_open()
        buy = next(
            (
                o
                for o in open_orders
                if o.instrument_name == MARKET_1
                and o.order_status == OrderStatus.open
                and o.direction == Direction.buy
                and o.label == ENTRY_LABEL
            ),
            None,
        )
        sell = next(
            (
                o
                for o in open_orders
                if o.instrument_name == MARKET_1
                and o.order_status == OrderStatus.open
                and o.direction == Direction.sell
                and o.label == ENTRY_LABEL
            ),
            None,
        )
        self.order[Direction.buy] = buy
        self.order[Direction.sell] = sell

    async def on_orderbook_update(self, ob: OrderbookInstrumentNameGroupDepthPublisherDataSchema):
        if not ob.bids or not ob.asks:
            return
        if self.current_position is None:
            return

        bid = ob.bids[0][0]
        ask = ob.asks[0][0]

        await self.maybe_place_or_requote(Direction.buy, bid, ask)
        await self.maybe_place_or_requote(Direction.sell, bid, ask)

    async def maybe_place_or_requote(self, side: Direction, bid: Decimal, ask: Decimal):
        async with self.lock[side]:
            existing = self.order[side]

            # position gating
            pos = self.current_position.amount
            if side == Direction.buy:
                if pos > (MAX_POSITION_SIZE - QUOTE_SIZE):
                    return
                desired = buy_quote_price(bid)
                low, high = buy_bounds(bid)
            else:
                if pos < -(MAX_POSITION_SIZE - QUOTE_SIZE):
                    return
                desired = sell_quote_price(ask)
                low, high = sell_bounds(ask)

            # no working order: place one
            if existing is None:
                self.order[side] = await self.create_order(side, desired, QUOTE_SIZE)
                return

            # working order exists: replace if out of bounds
            if not (low <= existing.limit_price <= high):
                result = await self.ws_client.orders.replace(
                    order_id_to_cancel=existing.order_id,
                    instrument_name=MARKET_1,
                    direction=side,
                    limit_price=desired,
                    amount=QUOTE_SIZE,
                    order_type=OrderType.limit,
                    label=ENTRY_LABEL,
                )
                if result.create_order_error:
                    self.logger.error(
                        f"Failed to replace {side.value} order {existing.order_id}: {result.create_order_error}"
                    )
                elif result.order:
                    self.logger.debug(
                        f"{side.value} order replaced: {existing.order_id} -> "
                        + f"{result.order.order_id} at {desired} for {QUOTE_SIZE}"
                    )
                    self.order[side] = result.order

    async def create_order(self, side: Direction, price: Decimal, amount: Decimal) -> OrderResponseSchema:
        order = await self.ws_client.orders.create(
            instrument_name=MARKET_1,
            direction=side,
            limit_price=price,
            amount=amount,
            order_type=OrderType.limit,
            label=ENTRY_LABEL,
        )
        self.logger.debug(f"{side.value} order placed: {order.nonce} at {price} for {amount}")
        return order

    async def on_order(self, orders: List[OrderResponseSchema]):
        # Keep local state coherent with exchange events
        for o in orders:
            if o.instrument_name != MARKET_1:
                continue
            if o.label != ENTRY_LABEL:
                continue

            self.logger.debug(f"Order update: {o.order_id} {o.order_status} {o.direction} {o.limit_price} {o.amount}")

            if o.order_status in (OrderStatus.filled, OrderStatus.cancelled, OrderStatus.expired):
                # clear if it matches our currently tracked order
                cur = self.order[o.direction]
                if cur is not None and cur.order_id == o.order_id:
                    self.order[o.direction] = None

                if o.order_status == OrderStatus.filled and o.filled_amount > 0:
                    self.logger.debug(f"Order filled: {o.nonce} {o.filled_amount} @ {o.average_price}")
                    await self.refresh_positions()

            elif o.order_status == OrderStatus.open:
                # update tracked order (covers nonce/order_id changes in updates)
                self.order[o.direction] = o

    async def on_trade(self, trades: List[TradeResponseSchema]):
        # If you only care about take-profit orders on your ENTRY_LABEL fills,
        # you can skip refreshing positions here and do it in on_order(filled).
        for t in trades:
            self.logger.info(
                f"Trade executed: {t.trade_id} {t.direction} {t.trade_price} {t.trade_amount} on order {t.order_id}"
            )
            if t.label != ENTRY_LABEL:
                continue

            tp_side = Direction.sell if t.direction == Direction.buy else Direction.buy
            tp_price = (
                t.trade_price * (D(1) + SELL_OFFSET)
                if tp_side == Direction.sell
                else t.trade_price * (D(1) - BUY_OFFSET)
            )

            await self.ws_client.orders.create(
                instrument_name=MARKET_1,
                direction=tp_side,
                limit_price=tp_price,
                amount=t.trade_amount,
                order_type=OrderType.limit,
                label=TP_LABEL,
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
