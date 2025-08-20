"""
Async client for Derive
"""

import asyncio
import functools
import json
import time
from datetime import datetime
from decimal import Decimal

import aiohttp
from derive_action_signing.utils import sign_ws_login, utc_now_ms

from derive_client._bridge import BridgeClient
from derive_client._bridge.standard_bridge import StandardBridge
from derive_client.constants import DEFAULT_REFERER, TEST_PRIVATE_KEY
from derive_client.data_types import (
    Address,
    BridgeTxResult,
    ChainID,
    Currency,
    Environment,
    InstrumentType,
    OrderSide,
    OrderType,
    PreparedBridgeTx,
    TimeInForce,
    UnderlyingCurrency,
)
from derive_client.utils import unwrap_or_raise

from .base_client import BaseClient, DeriveJSONRPCException


class AsyncClient(BaseClient):
    """
    We use the async client to make async requests to the derive API
    We us the ws client to make async requests to the derive ws API
    """

    current_subscriptions = {}
    listener = None
    subscribing = False

    def __init__(
        self,
        private_key: str = TEST_PRIVATE_KEY,
        env: Environment = Environment.TEST,
        logger=None,
        verbose=False,
        subaccount_id=None,
        wallet=None,
    ):
        super().__init__(
            wallet=wallet,
            private_key=private_key,
            env=env,
            logger=logger,
            verbose=verbose,
            subaccount_id=subaccount_id,
        )

        self.message_queues = {}
        self.connecting = False

    @functools.cached_property
    def _bridge(self) -> BridgeClient:
        return BridgeClient(env=self.env, account=self.signer, wallet=self.wallet, logger=self.logger)

    @functools.cached_property
    def _standard_bridge(self) -> StandardBridge:
        return StandardBridge(self.account, self.logger)

    async def prepare_standard_tx(
        self,
        human_amount: float,
        currency: Currency,
        to: Address,
        source_chain: ChainID,
        target_chain: ChainID,
    ) -> PreparedBridgeTx:
        """
        Prepare a transaction to bridge tokens to using Standard Bridge.

        This creates a signed transaction ready for submission but does not execute it.
        Review the returned PreparedBridgeTx before calling submit_bridge_tx().

        Args:
            human_amount: Amount in token units (e.g., 1.5 USDC, 0.1 ETH)
            currency: Currency enum value describing the token to bridge
            to: Destination address on the target chain
            source_chain: ChainID for the source chain
            target_chain: ChainID for the target chain

        Returns:
            PreparedBridgeTx: Contains transaction details including:
                - tx_hash: Pre-computed transaction hash
                - nonce: Transaction nonce for replacement/cancellation
                - tx_details: Contract address, method, gas estimates, signed transaction
                - currency, amount, source_chain, target_chain, bridge_type: Bridge context

        Use the returned object to:
            - Verify contract addresses and gas costs before submission
            - Submit with submit_bridge_tx() on approval
        """

        result = await self._standard_bridge.prepare_tx(
            human_amount=human_amount,
            currency=currency,
            to=to,
            source_chain=source_chain,
            target_chain=target_chain,
        )

        return unwrap_or_raise(result)

    async def prepare_deposit_to_derive(
        self,
        human_amount: float,
        currency: Currency,
        chain_id: ChainID,
    ) -> PreparedBridgeTx:
        """
        Prepare a deposit transaction to bridge tokens to Derive.

        This creates a signed transaction ready for submission but does not execute it.
        Review the returned PreparedBridgeTx before calling submit_bridge_tx().

        Args:
            human_amount: Amount in token units (e.g., 1.5 USDC, 0.1 ETH)
            currency: Token to bridge
            chain_id: Source chain to bridge from

        Returns:
            PreparedBridgeTx: Contains transaction details including:
                - tx_hash: Pre-computed transaction hash
                - nonce: Transaction nonce for replacement/cancellation
                - tx_details: Contract address, method, gas estimates, signed transaction
                - currency, amount, source_chain, target_chain, bridge_type: Bridge context

        Use the returned object to:
            - Verify contract addresses and gas costs before submission
            - Submit with submit_bridge_tx() on approval
        """

        if currency is Currency.ETH:
            raise NotImplementedError(
                "ETH deposits to the funding wallet (Light Account) are not implemented. "
                "For gas funding of the owner (EOA) use `prepare_standard_tx`."
            )

        result = await self._bridge.prepare_deposit(human_amount=human_amount, currency=currency, chain_id=chain_id)
        return unwrap_or_raise(result)

    async def prepare_withdrawal_from_derive(
        self,
        human_amount: float,
        currency: Currency,
        chain_id: ChainID,
    ) -> PreparedBridgeTx:
        """
        Prepare a withdrawal transaction to bridge tokens from Derive.

        This creates a signed transaction ready for submission but does not execute it.
        Review the returned PreparedBridgeTx before calling submit_bridge_tx().

        Args:
            human_amount: Amount in token units (e.g., 1.5 USDC, 0.1 ETH)
            currency: Token to bridge
            chain_id: Target chain to bridge to

        Returns:
            PreparedBridgeTx: Contains transaction details including:
                - tx_hash: Pre-computed transaction hash
                - nonce: Transaction nonce for replacement/cancellation
                - tx_details: Contract address, method, gas estimates, signed transaction
                - currency, amount, source_chain, target_chain, bridge_type: Bridge context

        Use the returned object to:
            - Verify contract addresses and gas costs before submission
            - Submit with submit_bridge_tx() when ready
        """

        result = await self._bridge.prepare_withdrawal(human_amount=human_amount, currency=currency, chain_id=chain_id)
        return unwrap_or_raise(result)

    async def submit_bridge_tx(self, prepared_tx: PreparedBridgeTx) -> BridgeTxResult:
        """
        Submit a prepared bridge transaction to the blockchain.

        This broadcasts the signed transaction and returns tracking information.
        The transaction is submitted but not yet confirmed - use poll_bridge_progress()
        to monitor completion.

        Args:
            prepared_tx: Transaction prepared by prepare_deposit_to_derive()
                         or prepare_withdrawal_from_derive()

        Returns:
            BridgeTxResult: Initial tracking object containing:
                - source_tx: Transaction hash on source chain (unconfirmed)
                - target_from_block: Block number to start polling target chain events
                - tx_details: Copy of original transaction details
                - currency, bridge, source_chain, target_chain: Bridge context

        Next steps:
            - Call poll_bridge_progress() to wait for cross-chain completion
        """

        if prepared_tx.currency == Currency.ETH:
            result = await self._standard_bridge.submit_bridge_tx(prepared_tx=prepared_tx)
        else:
            result = await self._bridge.submit_bridge_tx(prepared_tx=prepared_tx)

        return unwrap_or_raise(result)

    async def poll_bridge_progress(self, tx_result: BridgeTxResult) -> BridgeTxResult:
        """
        Poll for bridge transaction completion across both chains.

        This monitors the full cross-chain bridge pipeline:
        1. Source chain finality
        2. Target chain event detection
        3. Target chain finality

        Args:
            tx_result: Result from submit_bridge_tx() or previous poll attempt

        Returns:
            BridgeTxResult: Updated with completed bridge information:
                - source_tx.tx_receipt: Source chain transaction receipt (confirmed)
                - target_tx.tx_hash: Target chain transaction hash
                - target_tx.tx_receipt: Target chain transaction receipt (confirmed)

        Raises:
            PartialBridgeResult: Pipeline failed at some step. The exception contains
                the partially updated tx_result for inspection and retry. Common scenarios:
                - FinalityTimeout: Not enough confirmations, wait longer
                - TxPendingTimeout: Transaction stuck, consider resubmission
                - TransactionDropped: Transaction lost, likely needs resubmission

        Recovery strategies:
            - On PartialBridgeResult: inspect the tx_result in the exception
            - For FinalityTimeout: call poll_bridge_progress() again with the partial result
            - For TransactionDropped: prepare new tx with same nonce to replace
            - For TxPendingTimeout: prepare new tx with higher gas using same nonce.
            - In case of a nonce collision: verify whether previous transaction got included
                                            or whether the nonce was reused in another tx.
        """

        if tx_result.currency == Currency.ETH:
            result = await self._standard_bridge.poll_bridge_progress(tx_result=tx_result)
        else:
            result = await self._bridge.poll_bridge_progress(tx_result=tx_result)

        return unwrap_or_raise(result)

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
            await self.ws.send_json(msg)
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
                raise Exception(msg["error"])
            if "result" in msg:
                result = msg["result"]
                if "status" in result:
                    for channel, value in result['status'].items():
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
                    raise DeriveJSONRPCException(**message['error'])
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
                self.logger.error(f"Error fetching ticker {message}...")
                self._ws = await self.connect_ws()
                return await self.fetch_tickers(instrument_type, currency)
            message = json.loads(message.data)
            if message['id'] in ids_to_instrument_names:
                try:
                    results[message['result']['instrument_name']] = message['result']
                except KeyError:
                    self.logger.error(f"Error fetching ticker {message}")
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
            "referral_code": DEFAULT_REFERER,
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
                            raise DeriveJSONRPCException(**message['error'])
                        return message['result']['order']
                    except KeyError as error:
                        raise Exception(f"Unable to submit order {message}") from error
