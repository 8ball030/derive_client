"""
Base Client for the derive dex.
"""

import json
import random
import time
from decimal import Decimal
from logging import Logger, LoggerAdapter
from time import sleep

import requests
from derive_action_signing.module_data import (
    DepositModuleData,
    MakerTransferPositionModuleData,
    MakerTransferPositionsModuleData,
    RecipientTransferERC20ModuleData,
    RFQQuoteDetails,
    RFQQuoteModuleData,
    SenderTransferERC20ModuleData,
    TakerTransferPositionModuleData,
    TakerTransferPositionsModuleData,
    TradeModuleData,
    TransferERC20Details,
    TransferPositionsDetails,
    WithdrawModuleData,
)
from derive_action_signing.signed_action import SignedAction
from derive_action_signing.utils import MAX_INT_32, get_action_nonce, sign_rest_auth_header, utc_now_ms
from hexbytes import HexBytes
from pydantic import validate_call
from web3 import Web3

from derive_client.constants import CONFIGS, DEFAULT_REFERER, PUBLIC_HEADERS, TOKEN_DECIMALS
from derive_client.data_types import (
    Address,
    CollateralAsset,
    CreateSubAccountData,
    CreateSubAccountDetails,
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
    PositionSpec,
    PositionsTransfer,
    PositionTransfer,
    RfqStatus,
    SessionKey,
    SubaccountType,
    TimeInForce,
    UnderlyingCurrency,
    WithdrawResult,
)
from derive_client.endpoints import RestAPI
from derive_client.exceptions import DeriveJSONRPCException
from derive_client.utils import get_logger, wait_until


def _is_final_tx(res: DeriveTxResult) -> bool:
    return res.status not in (DeriveTxStatus.REQUESTED, DeriveTxStatus.PENDING)


class BaseClient:
    """Client for the Derive dex."""

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
        private_key: str | HexBytes,
        env: Environment,
        logger: Logger | LoggerAdapter | None = None,
        verbose: bool = False,
        subaccount_id: int | None = None,
    ):
        self.verbose = verbose
        self.env = env
        self.config = CONFIGS[env]
        self.logger = logger or get_logger()
        self.web3_client = Web3(Web3.HTTPProvider(self.config.rpc_endpoint))
        self.signer = self.web3_client.eth.account.from_key(private_key)
        print(self.signer.address)
        self.wallet = wallet
        self._verify_wallet(wallet)
        self.subaccount_ids = self.fetch_subaccounts().get("subaccount_ids", [])
        if subaccount_id is not None and subaccount_id not in self.subaccount_ids:
            msg = f"Provided subaccount {subaccount_id} not among retrieved aubaccounts: {self.subaccounts!r}"
            raise ValueError(msg)
        self.subaccount_id = subaccount_id or self.subaccount_ids[0]

    @property
    def account(self):
        return self.signer

    @property
    def private_key(self) -> HexBytes:
        return self.account._private_key

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

    def fetch_instruments(
        self,
        expired=False,
        instrument_type: InstrumentType = InstrumentType.PERP,
        currency: UnderlyingCurrency = UnderlyingCurrency.BTC,
    ):
        """
        Return the tickers.
        First fetch all instruments
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
        amount: int,
        instrument_name: str,
        price: float = None,
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
            module_address=self.config.contracts.TRADE_MODULE,
            module_data=module_data,
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

        url = self.endpoints.private.order
        return self._send_request(url, json=order)["order"]

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

    def get_order(self, order_id: str) -> dict:
        url = self.endpoints.private.get_order
        headers = self._create_signature_headers()
        payload = {
            "order_id": order_id,
            "subaccount_id": self.subaccount_id,
        }
        response = requests.post(url, json=payload, headers=headers)
        return response.json()["result"]

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
        if (error := message.get("error")) and "Rate limit exceeded" in error["message"]:
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
        payload = {
            **rfq,
            "subaccount_id": self.subaccount_id,
        }
        return self._send_request(url, payload)

    def poll_rfqs(self, rfq_status: RfqStatus | None = None):
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
        }
        if rfq_status:
            params["status"] = rfq_status.value
        return self._send_request(
            url,
            json=params,
        )

    def send_quote(self, quote):
        """Send a quote."""
        url = self.endpoints.private.send_quote
        return self._send_request(url, quote)

    def create_quote(
        self,
        rfq_id,
        legs,
        direction,
    ):
        """Create a quote object."""
        _, nonce, expiration = self.get_nonce_and_signature_expiry()

        rfq_legs: list[RFQQuoteDetails] = []
        for leg in legs:
            ticker = self.fetch_ticker(instrument_name=leg["instrument_name"])
            rfq_quote_details = RFQQuoteDetails(
                instrument_name=ticker["instrument_name"],
                direction=leg["direction"],
                asset_address=ticker["base_asset_address"],
                sub_id=int(ticker["base_asset_sub_id"]),
                price=Decimal(leg["price"]),
                amount=Decimal(leg["amount"]),
            )
            rfq_legs.append(rfq_quote_details)

        action = SignedAction(
            subaccount_id=self.subaccount_id,
            owner=self.wallet,
            signer=self.signer.address,
            signature_expiry_sec=MAX_INT_32,
            nonce=nonce,
            module_address=self.config.contracts.RFQ_MODULE,
            module_data=RFQQuoteModuleData(
                global_direction=direction,
                max_fee=Decimal(100),
                legs=rfq_legs,
            ),
            DOMAIN_SEPARATOR=self.config.DOMAIN_SEPARATOR,
            ACTION_TYPEHASH=self.config.ACTION_TYPEHASH,
        )

        action.sign(self.signer.key)

        payload = {
            **action.to_json(),
            "label": "",
            "mmp": False,
            "rfq_id": rfq_id,
        }

        return self.send_quote(quote=payload)

    def execute_quote(
        self,
        quote: RFQQuoteDetails,
        rfq_id: str = None,
        quote_id: str = None,
    ):
        """Execute a quote."""
        _, nonce, expiration = self.get_nonce_and_signature_expiry()

        action = SignedAction(
            subaccount_id=self.subaccount_id,
            owner=self.wallet,
            signer=self.signer.address,
            signature_expiry_sec=MAX_INT_32,
            nonce=nonce,
            module_address=self.config.contracts.RFQ_MODULE,
            module_data=quote,
            DOMAIN_SEPARATOR=self.config.DOMAIN_SEPARATOR,
            ACTION_TYPEHASH=self.config.ACTION_TYPEHASH,
        )
        action.sign(self.signer.key)
        payload = {
            **action.to_json(),
            "label": "",
            "rfq_id": rfq_id,
            "quote_id": quote_id,
        }
        url = self.endpoints.private.execute_quote
        return self._send_request(url, json=payload)

    def cancel_rfq(self, rfq_id: str):
        """Cancel an RFQ."""
        url = self.endpoints.private.cancel_rfq
        payload = {
            "subaccount_id": self.subaccount_id,
            "rfq_id": rfq_id,
        }
        return self._send_request(url, json=payload)

    def cancel_batch_rfqs(self, rfq_id: str = None, label: str = None, nonce: int = None):
        """Cancel RFQs in batch."""
        url = self.endpoints.private.cancel_batch_rfqs
        payload = {
            "subaccount_id": self.subaccount_id,
        }
        if rfq_id:
            payload["rfq_id"] = rfq_id
        if label:
            payload["label"] = label
        if nonce:
            payload["nonce"] = nonce
        return self._send_request(url, json=payload)

    def poll_quotes(self, rfq_id: str = None, quote_id: str = None, status: RfqStatus = None):
        url = self.endpoints.private.poll_quotes
        payload = {
            "subaccount_id": self.subaccount_id,
        }
        if rfq_id:
            payload["rfq_id"] = rfq_id
        if quote_id:
            payload["quote_id"] = quote_id
        if status:
            payload["status"] = status.value

        return self._send_request(url, json=payload)

    def _send_request(self, url, json=None, params=None, headers=None):
        headers = headers if headers else self._create_signature_headers()
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

    def transfer_position(
        self,
        instrument_name: str,
        amount: float,
        to_subaccount_id: int,
    ) -> PositionTransfer:
        """
        Transfer a position from the current subaccount to another subaccount.

        Parameters:
            instrument_name (str): Instrument to transfer (e.g. 'ETH-PERP').
            amount (float): Amount to transfer. Positive for a long, negative for a short.
            to_subaccount_id (int): Destination subaccount id (must be different and present in self.subaccount_ids).

        Returns:
            PositionTransfer: Result containing maker/taker order and trade details.
        """
        if to_subaccount_id == self.subaccount_id:
            raise ValueError("Target subaccount is self")
        if to_subaccount_id not in self.subaccount_ids:
            raise ValueError(f"Subaccount id {to_subaccount_id} not in {self.subaccount_ids}")

        url = self.endpoints.private.transfer_position
        positions = [p for p in self.get_positions() if p["instrument_name"] == instrument_name]
        if not len(positions) == 1:
            raise ValueError(f"Expected to find a position for {instrument_name}, found: {positions}")

        position = positions[0]
        position_amount = float(position["amount"])
        if abs(position_amount) < abs(amount):
            raise ValueError(f"Position {position_amount} not sufficient for transfer {amount}")

        ticker = self.fetch_ticker(instrument_name=instrument_name)
        mark_price = Decimal(ticker["mark_price"]).quantize(Decimal(ticker["tick_size"]))
        base_asset_address = ticker["base_asset_address"]
        base_asset_sub_id = int(ticker["base_asset_sub_id"])

        transfer_amount = Decimal(str(abs(amount)))
        original_position_amount = Decimal(str(position_amount))

        maker_action = SignedAction(
            subaccount_id=self.subaccount_id,
            owner=self.wallet,
            signer=self.signer.address,
            signature_expiry_sec=MAX_INT_32,
            nonce=get_action_nonce(),
            module_address=self.config.contracts.TRADE_MODULE,
            module_data=MakerTransferPositionModuleData(
                asset_address=base_asset_address,
                sub_id=base_asset_sub_id,
                limit_price=mark_price,
                amount=transfer_amount,
                recipient_id=self.subaccount_id,
                position_amount=original_position_amount,
            ),
            DOMAIN_SEPARATOR=self.config.DOMAIN_SEPARATOR,
            ACTION_TYPEHASH=self.config.ACTION_TYPEHASH,
        )

        # Small delay to ensure different nonces
        time.sleep(0.001)

        taker_action = SignedAction(
            subaccount_id=to_subaccount_id,
            owner=self.wallet,
            signer=self.signer.address,
            signature_expiry_sec=MAX_INT_32,
            nonce=get_action_nonce(),
            module_address=self.config.contracts.TRADE_MODULE,
            module_data=TakerTransferPositionModuleData(
                asset_address=base_asset_address,
                sub_id=base_asset_sub_id,
                limit_price=mark_price,
                amount=transfer_amount,
                recipient_id=to_subaccount_id,
                position_amount=original_position_amount,
            ),
            DOMAIN_SEPARATOR=self.config.DOMAIN_SEPARATOR,
            ACTION_TYPEHASH=self.config.ACTION_TYPEHASH,
        )

        maker_action.sign(self.signer.key)
        taker_action.sign(self.signer.key)

        maker_params = {
            "direction": maker_action.module_data.get_direction(),
            "instrument_name": instrument_name,
            **maker_action.to_json(),
        }
        taker_params = {
            "direction": taker_action.module_data.get_direction(),
            "instrument_name": instrument_name,
            **taker_action.to_json(),
        }

        payload = {
            "wallet": self.wallet,
            "maker_params": maker_params,
            "taker_params": taker_params,
        }

        response_data = self._send_request(url, json=payload)
        position_transfer = PositionTransfer(**response_data)

        return position_transfer

    def get_position_amount(self, instrument_name: str, subaccount_id: int) -> float:
        """
        Get the current position amount for a specific instrument in a subaccount.

        This is a helper method for getting position amounts to use with transfer_position().

        Parameters:
            instrument_name (str): The name of the instrument.
            subaccount_id (int): The subaccount ID to check.

        Returns:
            float: The current position amount.

        Raises:
            ValueError: If no position found for the instrument in the subaccount.
        """
        positions = self.get_positions()
        # get_positions() returns a list directly
        position_list = positions if isinstance(positions, list) else positions.get("positions", [])
        for pos in position_list:
            if pos["instrument_name"] == instrument_name:
                return float(pos["amount"])

        raise ValueError(f"No position found for {instrument_name} in subaccount {subaccount_id}")

    def transfer_positions(
        self,
        positions: list[PositionSpec],  # amount, instrument_name
        to_subaccount_id: int,
        direction: OrderSide,  # TransferDirection
    ) -> PositionsTransfer:
        """
        Transfer multiple positions between subaccounts using RFQ system.
        Parameters:
            positions (list[TransferPosition]): list of TransferPosition objects containing:
                - instrument_name (str): Name of the instrument
                - amount (float): Amount to transfer (must be positive)
                - limit_price (float): Limit price for the transfer (must be positive)
            from_subaccount_id (int): The subaccount ID to transfer from.
            to_subaccount_id (int): The subaccount ID to transfer to.
            global_direction (str): Global direction for the transfer ("buy" or "sell").
        Returns:
            DeriveTxResult: The result of the transfer transaction.
        Raises:
            ValueError: If positions list is empty, invalid global_direction, or if any instrument not found.
        """

        if to_subaccount_id == self.subaccount_id:
            raise ValueError("Target subaccount is self")
        if to_subaccount_id not in self.subaccount_ids:
            raise ValueError(f"Subaccount id {to_subaccount_id} not in {self.subaccount_ids}")

        url = self.endpoints.private.transfer_positions
        current_positions = {p["instrument_name"]: p for p in self.get_positions()}

        transfer_details = []
        for position in positions:
            amount = Decimal(str(position.amount))
            instrument_name = position.instrument_name

            if (current_position := current_positions.get(instrument_name)) is None:
                available = ", ".join(sorted(current_positions.keys())) or "none"
                msg = f"No position for {instrument_name} (available: {available})"
                raise ValueError(msg)

            current_amount = Decimal(current_position["amount"]).quantize(Decimal(current_position["amount_step"]))
            if abs(current_amount) < abs(amount):
                msg = f"Insufficient position for {instrument_name}: have {current_amount}, need {amount}"
                raise ValueError(msg)

            ticker = self.fetch_ticker(instrument_name=instrument_name)
            mark_price = Decimal(ticker["mark_price"]).quantize(Decimal(ticker["tick_size"]))
            base_asset_address = ticker["base_asset_address"]
            base_asset_sub_id = int(ticker["base_asset_sub_id"])

            transfer_amount = Decimal(str(abs(amount)))

            leg_direction = "sell" if amount > 0 else "buy"
            transfer_details.append(
                TransferPositionsDetails(
                    instrument_name=instrument_name,
                    direction=leg_direction,
                    asset_address=base_asset_address,
                    sub_id=base_asset_sub_id,
                    price=mark_price,
                    amount=transfer_amount,
                )
            )

        # Derive RPC -32602: Invalid params  [data=['Legs must be sorted by instrument name']]
        transfer_details.sort(key=lambda x: x.instrument_name)

        # Create maker action (sender) - USING RFQ_MODULE, not TRADE_MODULE
        maker_action = SignedAction(
            subaccount_id=self.subaccount_id,
            owner=self.wallet,
            signer=self.signer.address,
            signature_expiry_sec=MAX_INT_32,
            nonce=get_action_nonce(),  # maker_nonce
            module_address=self.config.contracts.RFQ_MODULE,
            module_data=MakerTransferPositionsModuleData(
                global_direction=direction.value,
                positions=transfer_details,
            ),
            DOMAIN_SEPARATOR=self.config.DOMAIN_SEPARATOR,
            ACTION_TYPEHASH=self.config.ACTION_TYPEHASH,
        )

        # Small delay to ensure different nonces
        time.sleep(0.001)

        # Create taker action (recipient) - USING RFQ_MODULE, not TRADE_MODULE
        opposite_direction = "sell" if direction.value == "buy" else "buy"
        taker_action = SignedAction(
            subaccount_id=to_subaccount_id,
            owner=self.wallet,
            signer=self.signer.address,
            signature_expiry_sec=MAX_INT_32,
            nonce=get_action_nonce(),
            module_address=self.config.contracts.RFQ_MODULE,
            module_data=TakerTransferPositionsModuleData(
                global_direction=opposite_direction,
                positions=transfer_details,
            ),
            DOMAIN_SEPARATOR=self.config.DOMAIN_SEPARATOR,
            ACTION_TYPEHASH=self.config.ACTION_TYPEHASH,
        )

        maker_action.sign(self.signer.key)
        taker_action.sign(self.signer.key)

        payload = {
            "wallet": self.wallet,
            "maker_params": maker_action.to_json(),
            "taker_params": taker_action.to_json(),
        }

        response_data = self._send_request(url, json=payload)
        positions_transfer = PositionsTransfer(**response_data)

        return positions_transfer
