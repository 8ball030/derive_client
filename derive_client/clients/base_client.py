"""
Base Client for the derive dex.
"""

import asyncio
import json
import random
from decimal import Decimal
from logging import Logger, LoggerAdapter
from time import sleep

import eth_abi
import requests
from derive_action_signing.module_data import (
    DepositModuleData,
    RecipientTransferERC20ModuleData,
    SenderTransferERC20ModuleData,
    TradeModuleData,
    TransferERC20Details,
    WithdrawModuleData,
)
from derive_action_signing.signed_action import SignedAction
from derive_action_signing.utils import MAX_INT_32, get_action_nonce, sign_rest_auth_header, utc_now_ms
from pydantic import validate_call
from returns.result import Result, safe
from web3 import Web3

from derive_client._bridge import BridgeClient
from derive_client.constants import CONFIGS, DEFAULT_REFERER, PUBLIC_HEADERS, TOKEN_DECIMALS
from derive_client.data_types import (
    Address,
    BridgeTxResult,
    ChainID,
    CollateralAsset,
    CreateSubAccountData,
    CreateSubAccountDetails,
    Currency,
    DepositResult,
    DeriveTxResult,
    DeriveTxStatus,
    Environment,
    InstrumentType,
    MainnetCurrency,
    ManagerAddress,
    MarginType,
    OrderSide,
    OrderStatus,
    OrderType,
    RfqStatus,
    SessionKey,
    SubaccountType,
    TimeInForce,
    UnderlyingCurrency,
    WithdrawResult,
)
from derive_client.endpoints import RestAPI
from derive_client.exceptions import DeriveJSONRPCException
from derive_client.utils import get_logger, unwrap_or_raise, wait_until


def _is_final_tx(res: DeriveTxResult) -> bool:
    return res.status not in (DeriveTxStatus.REQUESTED, DeriveTxStatus.PENDING)


class BaseClient:
    """Client for the Derive dex."""

    referral_code: str = None

    def _create_signature_headers(self):
        """
        Create the signature headers.
        """
        return sign_rest_auth_header(
            web3_client=self.web3_client,
            smart_contract_wallet=self.wallet,
            session_key_or_wallet_private_key=self.signer._private_key,
        )

    @validate_call(config=dict(arbitrary_types_allowed=True))
    def __init__(
        self,
        wallet: Address,
        private_key: str,
        env: Environment,
        logger: Logger | LoggerAdapter | None = None,
        verbose: bool = False,
        subaccount_id: int | None = None,
        referral_code: Address | None = None,
    ):
        self.verbose = verbose
        self.env = env
        self.config = CONFIGS[env]
        self.logger = logger or get_logger()
        self.web3_client = Web3(Web3.HTTPProvider(self.config.rpc_endpoint))
        self.signer = self.web3_client.eth.account.from_key(private_key)
        self.wallet = wallet
        self._verify_wallet(wallet)
        self.subaccount_id = self._determine_subaccount_id(subaccount_id)
        self.referral_code = referral_code

    @property
    def endpoints(self) -> RestAPI:
        """Return the chain ID."""
        return RestAPI(self.config.base_url)

    def _verify_wallet(self, wallet: Address):
        if not self.web3_client.is_connected():
            raise ConnectionError(f"Failed to connect to RPC at {self.config.rpc_endpoint}")
        if not self.web3_client.eth.get_code(wallet):
            msg = f"{wallet} appears to be an EOA (no bytecode). Expected a smart-contract wallet on Derive."
            raise ValueError(msg)
        session_keys = self._get_session_keys(wallet)
        if not any(self.signer.address == s.public_session_key for s in session_keys):
            msg = f"{self.signer.address} is not among registered session keys for wallet {wallet}."
            raise ValueError(msg)

    def _determine_subaccount_id(self, subaccount_id: int | None) -> int:
        subaccounts = self.fetch_subaccounts()
        if not (subaccount_ids := subaccounts.get("subaccount_ids", [])):
            raise ValueError(f"No subaccounts found for {self.wallet}. Please create one on Derive first.")
        if subaccount_id is not None and subaccount_id not in subaccount_ids:
            raise ValueError(f"Provided subaccount {subaccount_id} not among retrieved aubaccounts: {subaccounts!r}")
        subaccount_id = subaccount_id or subaccount_ids[0]
        self.logger.info(f"Selected subaccount_id: {subaccount_id}")
        return subaccount_id

    def create_account(self, wallet):
        """Call the create account endpoint."""
        payload = {"wallet": wallet}
        url = self.endpoints.public.create_account
        result = requests.post(
            headers=PUBLIC_HEADERS,
            url=url,
            json=payload,
        )
        result_code = json.loads(result.content)

        if "error" in result_code:
            raise Exception(result_code["error"])
        return True

    @safe
    @validate_call
    def deposit_to_derive_result(
        self,
        chain_id: ChainID,
        currency: Currency,
        amount: float,
    ) -> Result[BridgeTxResult, Exception]:
        """
        Submit a deposit into the Derive chain funding contract and return its initial BridgeTxResult
        without waiting for completion.

        Parameters:
            chain_id (ChainID): The chain you are bridging FROM.
            currency (Currency): The asset being bridged.
            amount (float): amount to deposit, in human units (will be scaled to Wei).
        Returns:
            Result[BridgeTxResult, Exception]: A Result object containing either the BridgeTxResult on success,
            or an Exception on failure.
        """

        client = BridgeClient(self.env, account=self.signer, wallet=self.wallet, logger=self.logger)

        async def _run():
            future = (
                client.prepare_deposit(token_amount=amount, currency=currency, chain_id=chain_id)
                .bind(client.submit_bridge_tx)
                .bind(client.poll_bridge_progress)
            )
            return await future.awaitable()

        return unwrap_or_raise(asyncio.run(_run()))

    def deposit_to_derive(
        self,
        chain_id: ChainID,
        currency: Currency,
        amount: float,
    ) -> BridgeTxResult:
        """
        Submit a deposit into the Derive chain funding contract and return its initial BridgeTxResult
        without waiting for completion.

        Parameters:
            chain_id (ChainID): The chain you are bridging FROM.
            currency (Currency): The asset being bridged.
            amount (float): amount to deposit, in human units (will be scaled to Wei).
        Raises:
            Exception: If the deposit fails.
        Returns:
            BridgeTxResult: The result of the deposit operation.
        """

        result = self.deposit_to_derive_result(chain_id=chain_id, currency=currency, amount=amount)
        return unwrap_or_raise(result)

    @safe
    @validate_call
    def withdraw_from_derive_result(
        self,
        chain_id: ChainID,
        currency: Currency,
        amount: float,
    ) -> Result[BridgeTxResult, Exception]:
        """
        Submit a withdrawal from the Derive chain funding contract and return its initial BridgeTxResult
        without waiting for completion.

        Parameters:
            chain_id (ChainID): The chain you are bridging TO.
            currency (Currency): The asset being bridged.
            amount (float): amount to withdraw, in human units (will be scaled to Wei).
        Returns:
            Result[BridgeTxResult, Exception]: A Result object containing either the BridgeTxResult on success,
            or an Exception on failure.
        """

        client = BridgeClient(self.env, account=self.signer, wallet=self.wallet, logger=self.logger)

        async def _run():
            future = (
                client.prepare_withdrawal(token_amount=amount, currency=currency, chain_id=chain_id)
                .bind(client.submit_bridge_tx)
                .bind(client.poll_bridge_progress)
            )
            return await future.awaitable()

        return unwrap_or_raise(asyncio.run(_run()))

    def withdraw_from_derive(
        self,
        chain_id: ChainID,
        currency: Currency,
        amount: float,
    ) -> BridgeTxResult:
        """
        Submit a withdrawal from the Derive chain funding contract and return its initial BridgeTxResult
        without waiting for completion.

        Parameters:
            chain_id (ChainID): The chain you are bridging TO.
            currency (Currency): The asset being bridged.
            amount (float): amount to withdraw, in human units (will be scaled to Wei).
        Raises:
            Exception: If the withdrawal fails.
        Returns:
            BridgeTxResult: The result of the withdrawal operation.
        """

        result = self.withdraw_from_derive_result(chain_id=chain_id, currency=currency, amount=amount)
        return unwrap_or_raise(result)

    @safe
    @validate_call
    def poll_bridge_progress_result(self, tx_result: BridgeTxResult) -> Result[BridgeTxResult, Exception]:
        """
        Given a pending BridgeTxResult, return a new BridgeTxResult with updated status.
        Raises AlreadyFinalizedError if tx_result is not in PENDING status.

        Parameters:
            tx_result (BridgeTxResult): the result to refresh.
        Returns:
            Result[BridgeTxResult, Exception]: A Result object containing either the BridgeTxResult on success,
            or an Exception on failure.
        """

        client = BridgeClient(account=self.signer, wallet=self.wallet, logger=self.logger)

        async def _run():
            return await client.poll_bridge_progress(tx_result=tx_result)

        return asyncio.run(_run())

    def poll_bridge_progress(self, tx_result: BridgeTxResult) -> BridgeTxResult:
        """
        Given a pending BridgeTxResult, return a new BridgeTxResult with updated status.
        Raises AlreadyFinalizedError if tx_result is not in PENDING status.

        Parameters:
            tx_result (BridgeTxResult): the result to refresh.
        Raises:
            Exception: If the polling fails.
        Returns:
            BridgeTxResult: The result of the polling operation.
        """

        result = self.poll_bridge_progress_result(tx_result=tx_result)
        return unwrap_or_raise(result)

    def fetch_instruments(
        self,
        expired=False,
        instrument_type: InstrumentType = InstrumentType.PERP,
        currency: UnderlyingCurrency = UnderlyingCurrency.BTC,
    ):
        """
        Return the tickers.
        First fetch all instrucments
        Then get the ticket for all instruments.
        """
        url = self.endpoints.public.get_instruments
        payload = {
            "expired": expired,
            "instrument_type": instrument_type.value,
            "currency": currency.name,
        }
        return self._send_request(url, json=payload, headers=PUBLIC_HEADERS)

    def _get_session_keys(self, wallet: Address) -> list[SessionKey]:
        url = self.endpoints.private.session_keys
        payload = {"wallet": wallet}
        session_keys = self._send_request(url, json=payload)
        if not (public_session_keys := session_keys.get("public_session_keys")):
            msg = f"No session keys registered for this wallet: {wallet}"
            raise ValueError(msg)
        return list(map(lambda kwargs: SessionKey(**kwargs), public_session_keys))

    def fetch_subaccounts(self):
        """
        Returns the subaccounts for a given wallet
        """
        url = self.endpoints.private.get_subaccounts
        payload = {"wallet": self.wallet}
        return self._send_request(url, json=payload)

    def fetch_subaccount(self, subaccount_id: int):
        """
        Returns information for a given subaccount
        """
        url = self.endpoints.private.get_subaccount
        payload = {"subaccount_id": subaccount_id}
        return self._send_request(url, json=payload)

    def _internal_map_instrument(self, instrument_type, currency):
        """
        Map the instrument.
        """
        instruments = self.fetch_instruments(instrument_type=instrument_type, currency=currency)
        return {i["instrument_name"]: i for i in instruments}

    def create_order(
        self,
        price,
        amount: int,
        instrument_name: str,
        reduce_only=False,
        instrument_type: InstrumentType = InstrumentType.PERP,
        side: OrderSide = OrderSide.BUY,
        order_type: OrderType = OrderType.LIMIT,
        time_in_force: TimeInForce = TimeInForce.GTC,
        instruments=None,  # temporary hack to allow async fetching of instruments
    ):
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

        price_step = instrument["tick_size"]
        rounded_price = Decimal(str(price)).quantize(Decimal(str(price_step)))

        module_data = {
            "asset_address": instrument["base_asset_address"],
            "sub_id": int(instrument["base_asset_sub_id"]),
            "limit_price": Decimal(str(rounded_price)),
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
            "referral_code": DEFAULT_REFERER if not self.referral_code else self.referral_code,
            **signed_action.to_json(),
        }

        response = self.submit_order(order)
        return response

    def _generate_signed_action(
        self,
        module_address: str,
        module_data: dict,
        module_data_class=TradeModuleData,
        subaccount_id=None,
    ):
        """
        Generate the signed action
        """
        action = SignedAction(
            subaccount_id=self.subaccount_id if subaccount_id is None else subaccount_id,
            owner=self.wallet,
            signer=self.signer.address,
            signature_expiry_sec=MAX_INT_32,
            nonce=get_action_nonce(),
            module_address=module_address,
            module_data=module_data_class(**module_data),
            DOMAIN_SEPARATOR=self.config.DOMAIN_SEPARATOR,
            ACTION_TYPEHASH=self.config.ACTION_TYPEHASH,
        )
        action.sign(self.signer._private_key)
        return action

    def submit_order(self, order):
        url = self.endpoints.private.order
        return self._send_request(url, json=order)["order"]

    def _sign_quote(self, quote):
        """
        Sign the quote
        """
        rfq_module_data = self._encode_quote_data(quote)
        return self._sign_quote_data(quote, rfq_module_data)

    def _encode_quote_data(self, quote, underlying_currency: UnderlyingCurrency = UnderlyingCurrency.ETH):
        """
        Convert the quote to encoded data.
        """
        instruments = self.fetch_instruments(instrument_type=InstrumentType.OPTION, currency=underlying_currency)
        ledgs_to_subids = {i["instrument_name"]: i["base_asset_sub_id"] for i in instruments}
        dir_sign = 1 if quote["direction"] == "buy" else -1
        quote["price"] = "10"

        def encode_leg(leg):
            sub_id = ledgs_to_subids[leg["instrument_name"]]
            leg_sign = 1 if leg["direction"] == "buy" else -1
            signed_amount = self.web3_client.to_wei(leg["amount"], "ether") * leg_sign * dir_sign
            return [
                self.config.contracts[f"{underlying_currency.name}_OPTION"],
                sub_id,
                self.web3_client.to_wei(quote["price"], "ether"),
                signed_amount,
            ]

        self.logger.info(f"Quote: {quote}")
        encoded_legs = [encode_leg(leg) for leg in quote["legs"]]
        rfq_data = [self.web3_client.to_wei(quote["max_fee"], "ether"), encoded_legs]

        encoded_data = eth_abi.encode(
            # ['uint256(address,uint256,uint256,int256)[]'],
            [
                "uint256",
                "address",
                "uint256",
                "int256",
            ],
            [rfq_data],
        )
        return self.web3_client.keccak(encoded_data)

    def fetch_ticker(self, instrument_name):
        """
        Fetch the ticker for a given instrument name.
        """
        url = self.endpoints.public.get_ticker
        payload = {"instrument_name": instrument_name}
        response = requests.post(url, json=payload, headers=PUBLIC_HEADERS)
        results = json.loads(response.content)["result"]
        return results

    def fetch_tickers(
        self,
        instrument_type: InstrumentType = InstrumentType.OPTION,
        currency: UnderlyingCurrency = UnderlyingCurrency.BTC,
    ):
        instruments = self.fetch_instruments(instrument_type=instrument_type, currency=currency)
        return {inst["instrument_name"]: self.fetch_ticker(inst["instrument_name"]) for inst in instruments}

    def fetch_orders(
        self,
        instrument_name: str = None,
        label: str = None,
        page: int = 1,
        page_size: int = 100,
        status: OrderStatus = None,
    ):
        """
        Fetch the orders for a given instrument name.
        """
        url = self.endpoints.private.get_orders
        payload = {
            "instrument_name": instrument_name,
            "subaccount_id": self.subaccount_id,
        }
        for key, value in {
            "label": label,
            "page": page,
            "page_size": page_size,
            "status": status,
        }.items():
            if value:
                payload[key] = value
        headers = self._create_signature_headers()
        response = requests.post(url, json=payload, headers=headers)
        results = response.json()["result"]["orders"]
        return results

    def cancel(self, order_id, instrument_name):
        """
        Cancel an order
        """
        url = self.endpoints.private.cancel
        payload = {
            "order_id": order_id,
            "subaccount_id": self.subaccount_id,
            "instrument_name": instrument_name,
        }
        return self._send_request(url, json=payload)

    def cancel_all(self):
        """
        Cancel all orders
        """
        url = self.endpoints.private.cancel_all
        payload = {"subaccount_id": self.subaccount_id}
        return self._send_request(url, json=payload)

    def _check_output_for_rate_limit(self, message):
        if error := message.get("error"):
            if "Rate limit exceeded" in error["message"]:
                sleep((int(error["data"].split(" ")[-2]) / 1000))
                self.logger.info("Rate limit exceeded, sleeping and retrying request")
                return True
        return False

    def get_positions(self):
        """
        Get positions
        """
        url = self.endpoints.private.get_positions
        payload = {"subaccount_id": self.subaccount_id}
        headers = sign_rest_auth_header(
            web3_client=self.web3_client,
            smart_contract_wallet=self.wallet,
            session_key_or_wallet_private_key=self.signer._private_key,
        )
        response = requests.post(url, json=payload, headers=headers)
        results = response.json()["result"]["positions"]
        return results

    def get_collaterals(self):
        """
        Get collaterals
        """
        url = self.endpoints.private.get_collaterals
        payload = {"subaccount_id": self.subaccount_id}
        result = self._send_request(url, json=payload)
        return result["collaterals"]

    def create_subaccount(
        self,
        amount: int = 0,
        subaccount_type: SubaccountType = SubaccountType.STANDARD,
        collateral_asset: CollateralAsset = CollateralAsset.USDC,
        underlying_currency: UnderlyingCurrency = UnderlyingCurrency.ETH,
    ):
        """
        Create a subaccount.
        """
        url = self.endpoints.private.create_subaccount
        if subaccount_type is SubaccountType.STANDARD:
            contract_key = f"{subaccount_type.name}_RISK_MANAGEr"
        elif subaccount_type is SubaccountType.PORTFOLIO:
            if not collateral_asset:
                raise Exception("Underlying currency must be provided for portfolio subaccounts")
            contract_key = f"{underlying_currency.name}_{subaccount_type.name}_RISK_MANAGER"

        signed_action = self._generate_signed_action(
            module_address=self.config.contracts[contract_key],
            module_data={
                "amount": amount,
                "asset_name": collateral_asset.name,
                "margin_type": "SM" if subaccount_type is SubaccountType.STANDARD else "PM",
                "create_account_details": CreateSubAccountDetails(
                    amount=amount,
                    base_asset_address=self.config.contracts.CASH_ASSET,
                    sub_asset_address=self.config.contracts[contract_key],
                ),
            },
            module_data_class=CreateSubAccountData,
            subaccount_id=0,
        )

        payload = {
            "amount": str(amount),
            "asset_name": collateral_asset.name,
            "margin_type": "SM" if subaccount_type is SubaccountType.STANDARD else "PM",
            "wallet": self.wallet,
            **signed_action.to_json(),
        }
        if subaccount_type is SubaccountType.PORTFOLIO:
            payload["currency"] = underlying_currency.name
        del payload["subaccount_id"]
        response = self._send_request(url, json=payload)
        return response

    def get_nonce_and_signature_expiry(self):
        """
        Returns the nonce and signature expiry
        """
        ts = utc_now_ms()
        nonce = int(f"{int(ts)}{random.randint(100, 999)}")
        expiration = int(ts) + 6000
        return ts, nonce, expiration

    def transfer_collateral(self, amount: int, to: str, asset: CollateralAsset):
        """
        Transfer collateral
        """
        url = self.endpoints.private.transfer_erc20
        transfer_details = TransferERC20Details(
            base_address=self.config.contracts.CASH_ASSET,
            sub_id=0,
            amount=Decimal(amount),
        )
        sender_action = SignedAction(
            subaccount_id=self.subaccount_id,
            owner=self.wallet,
            signer=self.signer.address,
            signature_expiry_sec=MAX_INT_32,
            nonce=get_action_nonce(),
            module_address=self.config.contracts.TRANSFER_MODULE,
            module_data=SenderTransferERC20ModuleData(
                to_subaccount_id=to,
                transfers=[transfer_details],
            ),
            DOMAIN_SEPARATOR=self.config.DOMAIN_SEPARATOR,
            ACTION_TYPEHASH=self.config.ACTION_TYPEHASH,
        )
        sender_action.sign(self.signer.key)

        recipient_action = SignedAction(
            subaccount_id=to,
            owner=self.wallet,
            signer=self.signer.address,
            signature_expiry_sec=MAX_INT_32,
            nonce=get_action_nonce(),
            module_address=self.config.contracts.TRANSFER_MODULE,
            module_data=RecipientTransferERC20ModuleData(),
            DOMAIN_SEPARATOR=self.config.DOMAIN_SEPARATOR,
            ACTION_TYPEHASH=self.config.ACTION_TYPEHASH,
        )
        recipient_action.sign(self.signer.key)
        payload = {
            "subaccount_id": self.subaccount_id,
            "recipient_subaccount_id": to,
            "sender_details": {
                "nonce": sender_action.nonce,
                "signature": sender_action.signature,
                "signature_expiry_sec": sender_action.signature_expiry_sec,
                "signer": sender_action.signer,
            },
            "recipient_details": {
                "nonce": recipient_action.nonce,
                "signature": recipient_action.signature,
                "signature_expiry_sec": recipient_action.signature_expiry_sec,
                "signer": recipient_action.signer,
            },
            "transfer": {
                "address": self.config.contracts.CASH_ASSET,
                "amount": str(transfer_details.amount),
                "sub_id": str(transfer_details.sub_id),
            },
        }
        return self._send_request(url, json=payload)

    def get_mmp_config(self, subaccount_id: int, currency: UnderlyingCurrency = None):
        """Get the mmp config."""
        url = self.endpoints.private.get_mmp_config
        payload = {"subaccount_id": self.subaccount_id}
        if currency:
            payload["currency"] = currency.name
        return self._send_request(url, json=payload)

    def set_mmp_config(
        self,
        subaccount_id: int,
        currency: UnderlyingCurrency,
        mmp_frozen_time: int,
        mmp_interval: int,
        mmp_amount_limit: str,
        mmp_delta_limit: str,
    ):
        """Set the mmp config."""
        url = self.endpoints.private.set_mmp_config
        payload = {
            "subaccount_id": subaccount_id,
            "currency": currency.name,
            "mmp_frozen_time": mmp_frozen_time,
            "mmp_interval": mmp_interval,
            "mmp_amount_limit": mmp_amount_limit,
            "mmp_delta_limit": mmp_delta_limit,
        }
        return self._send_request(url, json=payload)

    def send_rfq(self, rfq):
        """Send an RFQ."""
        url = self.endpoints.private.send_rfq
        return self._send_request(url, rfq)

    def poll_rfqs(self):
        """
        Poll RFQs.
            type RfqResponse = {
              subaccount_id: number,
              creation_timestamp: number,
              last_update_timestamp: number,
              status: string,
              cancel_reason: string,
              rfq_id: string,
              valid_until: number,
              legs: Array<RfqLeg>
            }
        """
        url = self.endpoints.private.poll_rfqs
        params = {
            "subaccount_id": self.subaccount_id,
            "status": RfqStatus.OPEN.value,
        }
        return self._send_request(
            url,
            json=params,
        )

    def send_quote(self, quote):
        """Send a quote."""
        url = self.endpoints.private.send_quote
        return self._send_request(url, quote)

    def create_quote_object(
        self,
        rfq_id,
        legs,
        direction,
    ):
        """Create a quote object."""
        _, nonce, expiration = self.get_nonce_and_signature_expiry()
        return {
            "subaccount_id": self.subaccount_id,
            "rfq_id": rfq_id,
            "legs": legs,
            "direction": direction,
            "max_fee": "10.0",
            "nonce": nonce,
            "signer": self.signer.address,
            "signature_expiry_sec": expiration,
            "signature": "filled_in_below",
        }

    def _send_request(self, url, json=None, params=None, headers=None):
        headers = self._create_signature_headers() if not headers else headers
        response = requests.post(url, json=json, headers=headers, params=params)
        response.raise_for_status()
        json_data = response.json()
        if error := json_data.get("error"):
            raise DeriveJSONRPCException(**error)
        else:
            return json_data["result"]

    def fetch_all_currencies(self):
        """
        Fetch the currency list
        """
        url = self.endpoints.public.get_all_currencies
        return self._send_request(url, json={})

    def fetch_currency(self, asset_name):
        """
        Fetch the currency list
        """
        url = self.endpoints.public.get_currency
        payload = {"currency": asset_name}
        return self._send_request(url, json=payload)

    def get_transaction(self, transaction_id: str) -> DeriveTxResult:
        """Get a transaction by its transaction id."""
        url = self.endpoints.public.get_transaction
        payload = {"transaction_id": transaction_id}
        return DeriveTxResult(**self._send_request(url, json=payload), transaction_id=transaction_id)

    def transfer_from_funding_to_subaccount(self, amount: int, asset_name: str, subaccount_id: int) -> DeriveTxResult:
        """
        Transfer from funding to subaccount
        """
        manager_address, underlying_address, decimals = self.get_manager_for_subaccount(subaccount_id, asset_name)
        if not manager_address or not underlying_address:
            raise Exception(f"Unable to find manager address or underlying address for {asset_name}")

        currency = UnderlyingCurrency[asset_name.upper()]
        deposit_module_data = DepositModuleData(
            amount=str(amount),
            asset=underlying_address,
            manager=manager_address,
            decimals=decimals,
            asset_name=currency.name,
        )

        sender_action = SignedAction(
            subaccount_id=self.subaccount_id,
            owner=self.wallet,
            signer=self.signer.address,
            signature_expiry_sec=MAX_INT_32,
            nonce=get_action_nonce(),
            module_address=self.config.contracts.DEPOSIT_MODULE,
            module_data=deposit_module_data,
            DOMAIN_SEPARATOR=self.config.DOMAIN_SEPARATOR,
            ACTION_TYPEHASH=self.config.ACTION_TYPEHASH,
        )
        sender_action.sign(self.signer.key)
        payload = {
            "amount": str(amount),
            "asset_name": currency.name,
            "is_atomic_signing": False,
            "nonce": sender_action.nonce,
            "signature": sender_action.signature,
            "signature_expiry_sec": sender_action.signature_expiry_sec,
            "signer": sender_action.signer,
            "subaccount_id": subaccount_id,
        }
        url = self.endpoints.private.deposit

        deposit_result = DepositResult(**self._send_request(url, json=payload))
        return wait_until(
            self.get_transaction,
            condition=_is_final_tx,
            transaction_id=deposit_result.transaction_id,
        )

    def get_manager_for_subaccount(self, subaccount_id: int, asset_name):
        """
        Look up the manager for a subaccount

        Check if target account is PM or SM
        If SM, use the standard manager address
        If PM, use the appropriate manager address based on the currency of the subaccount
        """
        deposit_currency = UnderlyingCurrency[asset_name.upper()]
        currency = self.fetch_currency(asset_name.upper())
        underlying_address = currency["protocol_asset_addresses"]["spot"]
        managers = list(map(lambda kwargs: ManagerAddress(**kwargs), currency["managers"]))
        manager_by_type = {}
        for manager in managers:
            manager_by_type.setdefault((manager.margin_type, manager.currency), []).append(manager)

        to_account = self.fetch_subaccount(subaccount_id)
        account_currency = None
        if to_account.get("currency") != "all":
            account_currency = MainnetCurrency[to_account.get("currency")]

        margin_type = MarginType[to_account.get("margin_type")]

        def get_unique_manager(margin_type, currency):
            matches = manager_by_type.get((margin_type, currency), [])
            if len(matches) != 1:
                raise ValueError(f"Expected exactly one ManagerAddress for {(margin_type, currency)}, found {matches}")
            return matches[0]

        manager = get_unique_manager(margin_type, account_currency)
        if not manager.address or not underlying_address:
            raise Exception(f"Unable to find manager address or underlying address for {asset_name}")
        return manager.address, underlying_address, TOKEN_DECIMALS[deposit_currency]

    def transfer_from_subaccount_to_funding(self, amount: int, asset_name: str, subaccount_id: int) -> DeriveTxResult:
        """
        Transfer from subaccount to funding
        """
        manager_address, underlying_address, decimals = self.get_manager_for_subaccount(subaccount_id, asset_name)
        if not manager_address or not underlying_address:
            raise Exception(f"Unable to find manager address or underlying address for {asset_name}")

        currency = UnderlyingCurrency[asset_name.upper()]
        module_data = WithdrawModuleData(
            amount=str(amount),
            asset=underlying_address,
            decimals=decimals,
            asset_name=currency.name,
        )
        sender_action = SignedAction(
            subaccount_id=subaccount_id,
            owner=self.wallet,
            signer=self.signer.address,
            signature_expiry_sec=MAX_INT_32,
            nonce=get_action_nonce(),
            module_address=self.config.contracts.WITHDRAWAL_MODULE,
            module_data=module_data,
            DOMAIN_SEPARATOR=self.config.DOMAIN_SEPARATOR,
            ACTION_TYPEHASH=self.config.ACTION_TYPEHASH,
        )
        sender_action.sign(self.signer.key)
        payload = {
            "is_atomic_signing": False,
            "amount": str(amount),
            "asset_name": currency.name,
            "nonce": sender_action.nonce,
            "signature": sender_action.signature,
            "signature_expiry_sec": sender_action.signature_expiry_sec,
            "signer": sender_action.signer,
            "subaccount_id": subaccount_id,
        }
        url = self.endpoints.private.withdraw

        withdraw_result = WithdrawResult(**self._send_request(url, json=payload))
        return wait_until(
            self.get_transaction,
            condition=_is_final_tx,
            transaction_id=withdraw_result.transaction_id,
        )
