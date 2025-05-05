"""
Async client for Derive
"""

import asyncio
import json
import time
from datetime import datetime
from decimal import Decimal

import aiohttp
from derive_action_signing.utils import sign_ws_login, utc_now_ms
from web3 import Web3

from derive_client.constants import CONFIGS, DEFAULT_REFERER, TEST_PRIVATE_KEY
from derive_client.data_types import Environment, InstrumentType, OrderSide, OrderType, TimeInForce, UnderlyingCurrency
from derive_client.utils import get_logger

from .base_client import ApiException
from .ws_client import WsClient as BaseClient


class AsyncClient(BaseClient):
    """
    We use the async client to make async requests to the derive API
    We us the ws client to make async requests to the derive ws API
    """

    current_subscriptions = {}

    listener = None
    subscribing = False
    _ws = None

    def __init__(
        self,
        private_key: str = TEST_PRIVATE_KEY,
        env: Environment = Environment.TEST,
        logger=None,
        verbose=False,
        subaccount_id=None,
        wallet=None,
    ):
        self.verbose = verbose
        self.env = env
        self.config = CONFIGS[env]
        self.logger = logger or get_logger()
        self.web3_client = Web3()
        self.signer = self.web3_client.eth.account.from_key(private_key)
        self.wallet = self.signer.address if not wallet else wallet
        print(f"Signing address: {self.signer.address}")
        if wallet:
            print(f"Using wallet: {wallet}")
        self.subaccount_id = subaccount_id
        print(f"Using subaccount id: {self.subaccount_id}")
        self.message_queues = {}
        self.connecting = False
        # we make sure to get the event loop

    @property
    async def ws(self):
        if self._ws is None:
            self._ws = await self.connect_ws()
        if not self._ws.connected:
            self._ws = await self.connect_ws()
        return self._ws

    def get_subscription_id(self, instrument_name: str, group: str = "1", depth: str = "100"):
        return f"orderbook.{instrument_name}.{group}.{depth}"

    async def subscribe(self, instrument_name: str, group: str = "1", depth: str = "100"):
        """
        Subscribe to the order book for a symbol
        """
        # if self.listener is None or self.listener.done():
        asyncio.create_task(self.listen_for_messages())
        channel = self.get_subscription_id(instrument_name, group, depth)
        if channel not in self.message_queues:
            self.message_queues[channel] = asyncio.Queue()
            msg = {"method": "subscribe", "params": {"channels": [channel]}}
            await self._ws.send_json(msg)
            return

        while instrument_name not in self.current_subscriptions:
            await asyncio.sleep(0.01)
        return self.current_subscriptions[instrument_name]

    async def connect_ws(self):
        self.connecting = True
        self.session = aiohttp.ClientSession()
        ws = await self.session.ws_connect(self.config.ws_address)
        self._ws = ws
        self.connecting = False
        return ws

    async def listen_for_messages(
        self,
    ):
        while True:
            try:
                msg = await self.ws.receive_json()
            except TypeError:
                continue
            if "error" in msg:
                print(msg)
                raise Exception(msg["error"])
            if "result" in msg:
                result = msg["result"]
                if "status" in result:
                    # print(f"Succesfully subscribed to {result['status']}")
                    for channel, value in result['status'].items():
                        # print(f"Channel {channel} has value {value}")
                        if "error" in value:
                            raise Exception(f"Subscription error for channel: {channel} error: {value['error']}")
                    continue
            #  default to putting the message in the queue
            subscription = msg['params']['channel']
            data = msg['params']['data']
            self.handle_message(subscription, data)

    async def login_client(
        self,
        retries=3,
    ):
        login_request = {
            'method': 'public/login',
            'params': sign_ws_login(
                web3_client=self.web3_client,
                smart_contract_wallet=self.wallet,
                session_key_or_wallet_private_key=self.signer._private_key,
            ),
            'id': str(utc_now_ms()),
        }
        await self._ws.send_json(login_request)
        # we need to wait for the response
        async for msg in self._ws:
            message = json.loads(msg.data)
            if message['id'] == login_request['id']:
                if "result" not in message:
                    if self._check_output_for_rate_limit(message):
                        return await self.login_client()
                    raise ApiException(message['error'])
                break

    def handle_message(self, subscription, data):
        bids = data['bids']
        asks = data['asks']

        bids = list(map(lambda x: (float(x[0]), float(x[1])), bids))
        asks = list(map(lambda x: (float(x[0]), float(x[1])), asks))

        instrument_name = subscription.split(".")[1]

        if subscription in self.current_subscriptions:
            old_params = self.current_subscriptions[subscription]
            _asks, _bids = old_params["asks"], old_params["bids"]
            if not asks:
                asks = _asks
            if not bids:
                bids = _bids
        timestamp = data['timestamp']
        datetime_str = datetime.fromtimestamp(timestamp / 1000)
        nonce = data['publish_id']
        self.current_subscriptions[instrument_name] = {
            "asks": asks,
            "bids": bids,
            "timestamp": timestamp,
            "datetime": datetime_str.isoformat(),
            "nonce": nonce,
            "symbol": instrument_name,
        }
        return self.current_subscriptions[instrument_name]

    async def watch_order_book(self, instrument_name: str, group: str = "1", depth: str = "100"):
        """
        Watch the order book for a symbol
        orderbook.{instrument_name}.{group}.{depth}
        """

        if not self.ws and not self.connecting:
            await self.connect_ws()
            await self.login_client()

        subscription = self.get_subscription_id(instrument_name, group, depth)

        if subscription not in self.message_queues:
            while any([self.subscribing, self.ws is None, self.connecting]):
                await asyncio.sleep(1)
            await self.subscribe(instrument_name, group, depth)

        while instrument_name not in self.current_subscriptions and not self.connecting:
            await asyncio.sleep(0.01)

        return self.current_subscriptions[instrument_name]

    async def fetch_instruments(
        self,
        expired=False,
        instrument_type: InstrumentType = InstrumentType.PERP,
        currency: UnderlyingCurrency = UnderlyingCurrency.BTC,
    ):
        return super().fetch_instruments(expired, instrument_type, currency)

    async def close(self):
        """
        Close the connection
        """
        self.ws.close()

    async def fetch_tickers(
        self,
        instrument_type: InstrumentType = InstrumentType.OPTION,
        currency: UnderlyingCurrency = UnderlyingCurrency.BTC,
    ):
        if not self._ws:
            await self.connect_ws()
        instruments = await self.fetch_instruments(instrument_type=instrument_type, currency=currency)
        instrument_names = [i['instrument_name'] for i in instruments]
        id_base = str(int(time.time()))
        ids_to_instrument_names = {
            f'{id_base}_{enumerate}': instrument_name for enumerate, instrument_name in enumerate(instrument_names)
        }
        for id, instrument_name in ids_to_instrument_names.items():
            payload = {"instrument_name": instrument_name}
            await self._ws.send_json({'method': 'public/get_ticker', 'params': payload, 'id': id})
            await asyncio.sleep(0.1)  # otherwise we get rate limited...
        results = {}
        while ids_to_instrument_names:
            message = await self._ws.receive()
            if message is None:
                continue
            if 'error' in message:
                raise Exception(f"Error fetching ticker {message}")
            if message.type == aiohttp.WSMsgType.CLOSED:
                # we try to reconnect
                print(f"Erorr fetching ticker {message}...")
                self._ws = await self.connect_ws()
                return await self.fetch_tickers(instrument_type, currency)
            message = json.loads(message.data)
            if message['id'] in ids_to_instrument_names:
                try:
                    results[message['result']['instrument_name']] = message['result']
                except KeyError:
                    print(f"Error fetching ticker {message}")
                del ids_to_instrument_names[message['id']]
        return results

    async def get_collaterals(self):
        return super().get_collaterals()

    async def get_positions(self, currency: UnderlyingCurrency = UnderlyingCurrency.BTC):
        return super().get_positions()

    async def get_open_orders(self, status, currency: UnderlyingCurrency = UnderlyingCurrency.BTC):
        return super().fetch_orders(
            status=status,
        )

    async def fetch_ticker(self, instrument_name: str):
        """
        Fetch the ticker for a symbol
        """
        return super().fetch_ticker(instrument_name)

    async def create_order(
        self,
        price,
        amount,
        instrument_name: str,
        reduce_only=False,
        side: OrderSide = OrderSide.BUY,
        order_type: OrderType = OrderType.LIMIT,
        time_in_force: TimeInForce = TimeInForce.GTC,
        instrument_type: InstrumentType = InstrumentType.PERP,
        underlying_currency: UnderlyingCurrency = UnderlyingCurrency.USDC,
    ):
        """
        Create the order.
        """
        if not self._ws:
            await self.connect_ws()
            await self.login_client()
        if side.name.upper() not in OrderSide.__members__:
            raise Exception(f"Invalid side {side}")
        instruments = await self._internal_map_instrument(instrument_type, underlying_currency)
        instrument = instruments[instrument_name]

        rounded_price = Decimal(price).quantize(
            Decimal(instrument['tick_size']),
        )
        rounded_amount = Decimal(amount).quantize(
            Decimal(instrument['amount_step']),
        )

        module_data = {
            "asset_address": instrument['base_asset_address'],
            "sub_id": int(instrument['base_asset_sub_id']),
            "limit_price": rounded_price,
            "amount": rounded_amount,
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
            "referral_code": DEFAULT_REFERER if not self.referral_code else self.referral_code,
            **signed_action.to_json(),
        }
        try:
            response = await self.submit_order(order)
        except aiohttp.ClientConnectionResetError:
            await self.connect_ws()
            await self.login_client()
            response = await self.submit_order(order)
        return response

    async def _internal_map_instrument(self, instrument_type, currency):
        """
        Map the instrument.
        """
        instruments = await self.fetch_instruments(instrument_type=instrument_type, currency=currency)
        return {i['instrument_name']: i for i in instruments}

    async def submit_order(self, order):
        id = str(utc_now_ms())
        await self._ws.send_json({'method': 'private/order', 'params': order, 'id': id})
        while True:
            async for msg in self._ws:
                message = json.loads(msg.data)
                if message['id'] == id:
                    try:
                        if "result" not in message:
                            if self._check_output_for_rate_limit(message):
                                return await self.submit_order(order)
                            raise ApiException(message['error'])
                        return message['result']['order']
                    except KeyError as error:
                        print(message)
                        raise Exception(f"Unable to submit order {message}") from error
