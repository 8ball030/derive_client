"""Order management operations."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from derive_action_signing.module_data import TradeModuleData

from derive_client.constants import INT64_MAX
from derive_client.data.generated.models import (
    Direction,
    OrderStatus,
    OrderType,
    PrivateCancelAllParamsSchema,
    PrivateCancelByInstrumentParamsSchema,
    PrivateCancelByInstrumentResultSchema,
    PrivateCancelByLabelParamsSchema,
    PrivateCancelByLabelResultSchema,
    PrivateCancelByNonceParamsSchema,
    PrivateCancelByNonceResultSchema,
    PrivateCancelParamsSchema,
    PrivateCancelResultSchema,
    PrivateGetOpenOrdersParamsSchema,
    PrivateGetOpenOrdersResultSchema,
    PrivateGetOrderParamsSchema,
    PrivateGetOrderResultSchema,
    PrivateGetOrdersParamsSchema,
    PrivateGetOrdersResultSchema,
    PrivateOrderParamsSchema,
    PrivateOrderResultSchema,
    PrivateReplaceParamsSchema,
    PrivateReplaceResultSchema,
    Result,
    TimeInForce,
    TriggerPriceType,
    TriggerType,
)

if TYPE_CHECKING:
    from .subaccount import Subaccount


class OrderOperations:
    """High-level order management operations."""

    def __init__(self, subaccount: Subaccount):
        """
        Initialize order operations.

        Args:
            subaccount: Subaccount instance providing access to auth, config, and APIs
        """
        self._subaccount = subaccount

    def create(
        self,
        amount: Decimal,
        direction: Direction,
        instrument_name: str,
        limit_price: Decimal,
        max_fee: Decimal,
        nonce: Optional[int] = None,
        signature_expiry_sec: int = INT64_MAX,
        is_atomic_signing: Optional[bool] = False,
        label: str = '',
        mmp: bool = False,
        order_type: OrderType = 'limit',
        reduce_only: bool = False,
        reject_timestamp: int = INT64_MAX,
        time_in_force: TimeInForce = 'gtc',
        trigger_price: Optional[Decimal] = None,
        trigger_price_type: Optional[TriggerPriceType] = None,
        trigger_type: Optional[TriggerType] = None,
    ) -> PrivateOrderResultSchema:
        subaccount_id = self._subaccount.id
        instrument = self._subaccount.markets.get_instrument(instrument_name=instrument_name)

        amount = amount.quantize(instrument.amount_step)
        limit_price = limit_price.quantize(instrument.tick_size)

        is_bid = direction == Direction.buy
        module_data = TradeModuleData(
            asset_address=instrument.base_asset_address,
            sub_id=int(instrument.base_asset_sub_id),
            limit_price=limit_price,
            amount=amount,
            max_fee=max_fee,
            recipient_id=subaccount_id,
            is_bid=is_bid,
        )

        module_address = self._subaccount._config.contracts.TRADE_MODULE
        signed_action = self._subaccount.sign_action(
            nonce=nonce,
            module_address=module_address,
            module_data=module_data,
            signature_expiry_sec=signature_expiry_sec,
        )

        signer = signed_action.signer
        signature = signed_action.signature
        nonce = signed_action.nonce

        params = PrivateOrderParamsSchema(
            amount=amount,
            direction=direction,
            instrument_name=instrument_name,
            limit_price=limit_price,
            max_fee=max_fee,
            nonce=nonce,
            signature=signature,
            signature_expiry_sec=signature_expiry_sec,
            signer=signer,
            subaccount_id=subaccount_id,
            is_atomic_signing=is_atomic_signing,
            label=label,
            mmp=mmp,
            order_type=order_type,
            reduce_only=reduce_only,
            reject_timestamp=reject_timestamp,
            time_in_force=time_in_force,
            trigger_price=trigger_price,
            trigger_price_type=trigger_price_type,
            trigger_type=trigger_type,
        )
        response = self._subaccount._private_api.order(params)
        return response.result

    def get(self, order_id: str) -> PrivateGetOrderResultSchema:
        subaccount_id = self._subaccount.id
        params = PrivateGetOrderParamsSchema(
            order_id=order_id,
            subaccount_id=subaccount_id,
        )
        response = self._subaccount._private_api.get_order(params)
        return response.result

    def list(
        self,
        instrument_name: Optional[str] = None,
        label: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
        status: Optional[OrderStatus] = None,
    ) -> PrivateGetOrdersResultSchema:
        params = PrivateGetOrdersParamsSchema(
            subaccount_id=self._subaccount.id,
            instrument_name=instrument_name,
            label=label,
            page=page,
            page_size=page_size,
            status=status,
        )
        response = self._subaccount._private_api.get_orders(params)
        return response.result

    def list_open(self) -> PrivateGetOpenOrdersResultSchema:
        params = PrivateGetOpenOrdersParamsSchema(subaccount_id=self._subaccount.id)
        response = self._subaccount._private_api.get_open_orders(params)
        return response.result

    def cancel(self, instrument_name: str, order_id: str) -> PrivateCancelResultSchema:
        params = PrivateCancelParamsSchema(
            instrument_name=instrument_name,
            order_id=order_id,
            subaccount_id=self._subaccount.id,
        )
        response = self._subaccount._private_api.cancel(params)
        return response.result

    def cancel_by_label(self, label: str, instrument_name: Optional[str] = None) -> PrivateCancelByLabelResultSchema:
        params = PrivateCancelByLabelParamsSchema(
            label=label,
            instrument_name=instrument_name,
            subaccount_id=self._subaccount.id,
        )
        response = self._subaccount._private_api.cancel_by_label(params)
        return response.result

    def cancel_by_nonce(self, instrument_name: str, nonce: int) -> PrivateCancelByNonceResultSchema:
        params = PrivateCancelByNonceParamsSchema(
            nonce=nonce,
            instrument_name=instrument_name,
            subaccount_id=self._subaccount.id,
            wallet=self._subaccount._auth.wallet,
        )
        response = self._subaccount._private_api.cancel_by_nonce(params)
        return response.result

    def cancel_by_instrument(self, instrument_name: str) -> PrivateCancelByInstrumentResultSchema:
        params = PrivateCancelByInstrumentParamsSchema(
            instrument_name=instrument_name,
            subaccount_id=self._subaccount.id,
        )
        response = self._subaccount._private_api.cancel_by_instrument(params)
        return response.result

    def cancel_all(self) -> Result:
        params = PrivateCancelAllParamsSchema(subaccount_id=self._subaccount.id)
        response = self._subaccount._private_api.cancel_all(params)
        return response.result

    def replace(
        self,
        amount: Decimal,
        direction: Direction,
        instrument_name: str,
        limit_price: Decimal,
        max_fee: Decimal,
        nonce: Optional[int] = None,
        signature_expiry_sec: int = INT64_MAX,
        expected_filled_amount: Optional[Decimal] = None,
        is_atomic_signing: Optional[bool] = False,
        label: str = '',
        mmp: bool = False,
        nonce_to_cancel: Optional[int] = None,
        order_id_to_cancel: Optional[str] = None,
        order_type: OrderType = 'limit',
        reduce_only: bool = False,
        reject_timestamp: int = INT64_MAX,
        time_in_force: TimeInForce = 'gtc',
        trigger_price: Optional[Decimal] = None,
        trigger_price_type: Optional[TriggerPriceType] = None,
        trigger_type: Optional[TriggerType] = None,
    ) -> PrivateReplaceResultSchema:
        if (nonce_to_cancel is None) == (order_id_to_cancel is None):
            raise ValueError("Replace requires exactly one of nonce_to_cancel or order_id_to_cancel (but not both).")

        subaccount_id = self._subaccount.id
        instrument = self._subaccount.markets.get_instrument(instrument_name=instrument_name)

        is_bid = direction == Direction.buy
        module_data = TradeModuleData(
            asset_address=instrument.base_asset_address,
            sub_id=int(instrument.base_asset_sub_id),
            limit_price=limit_price,
            amount=amount,
            max_fee=max_fee,
            recipient_id=subaccount_id,
            is_bid=is_bid,
        )

        module_address = self._subaccount._config.contracts.TRADE_MODULE
        signed_action = self._subaccount.sign_action(
            nonce=nonce,
            module_address=module_address,
            module_data=module_data,
            signature_expiry_sec=signature_expiry_sec,
        )

        signer = signed_action.signer
        signature = signed_action.signature
        nonce = signed_action.nonce

        params = PrivateReplaceParamsSchema(
            amount=amount,
            direction=direction,
            instrument_name=instrument_name,
            limit_price=limit_price,
            max_fee=max_fee,
            nonce=nonce,
            signature=signature,
            signature_expiry_sec=signature_expiry_sec,
            expected_filled_amount=expected_filled_amount,
            signer=signer,
            subaccount_id=subaccount_id,
            is_atomic_signing=is_atomic_signing,
            label=label,
            mmp=mmp,
            nonce_to_cancel=nonce_to_cancel,
            order_id_to_cancel=order_id_to_cancel,
            order_type=order_type,
            reduce_only=reduce_only,
            reject_timestamp=reject_timestamp,
            time_in_force=time_in_force,
            trigger_price=trigger_price,
            trigger_price_type=trigger_price_type,
            trigger_type=trigger_type,
        )
        response = self._subaccount._private_api.replace(params)
        return response.result
