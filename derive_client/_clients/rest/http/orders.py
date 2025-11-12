"""Order management operations."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from derive_action_signing import TradeModuleData

from derive_client.config import INT64_MAX
from derive_client.data_types.generated_models import (
    Direction,
    OrderResponseSchema,
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
    PrivateGetOrderParamsSchema,
    PrivateGetOrderResultSchema,
    PrivateGetOrdersParamsSchema,
    PrivateOrderParamsSchema,
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
        *,
        amount: Decimal,
        direction: Direction,
        instrument_name: str,
        limit_price: Decimal,
        max_fee: Decimal = Decimal("1000"),
        nonce: Optional[int] = None,
        signature_expiry_sec: Optional[int] = None,
        is_atomic_signing: Optional[bool] = False,
        label: str = "",
        mmp: bool = False,
        order_type: OrderType = OrderType.limit,
        reduce_only: bool = False,
        reject_timestamp: int = INT64_MAX,
        time_in_force: TimeInForce = TimeInForce.gtc,
        trigger_price: Optional[Decimal] = None,
        trigger_price_type: Optional[TriggerPriceType] = None,
        trigger_type: Optional[TriggerType] = None,
    ) -> OrderResponseSchema:
        """
        Create a new order.

        Amount and limit_price are automatically quantized to match instrument specifications.
        """

        subaccount_id = self._subaccount.id

        instrument = self._subaccount.markets._get_cached_instrument(instrument_name=instrument_name)
        asset_address = instrument.base_asset_address
        sub_id = int(instrument.base_asset_sub_id)

        amount = Decimal(amount).quantize(instrument.amount_step)
        limit_price = Decimal(limit_price).quantize(instrument.tick_size)

        is_bid = direction == Direction.buy
        module_data = TradeModuleData(
            asset_address=asset_address,
            sub_id=sub_id,
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

        params = PrivateOrderParamsSchema(
            amount=amount,
            direction=direction,
            instrument_name=instrument_name,
            limit_price=limit_price,
            max_fee=max_fee,
            nonce=signed_action.nonce,
            signature=signed_action.signature,
            signature_expiry_sec=signed_action.signature_expiry_sec,
            signer=signed_action.signer,
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
        return response.result.order

    def get(self, *, order_id: str) -> PrivateGetOrderResultSchema:
        """Get state of an order by order id."""

        subaccount_id = self._subaccount.id
        params = PrivateGetOrderParamsSchema(
            order_id=order_id,
            subaccount_id=subaccount_id,
        )
        response = self._subaccount._private_api.get_order(params)
        return response.result

    def list(
        self,
        *,
        instrument_name: Optional[str] = None,
        label: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
        status: Optional[OrderStatus] = None,
    ) -> List[OrderResponseSchema]:
        """Get orders for a subaccount, with optional filtering."""

        params = PrivateGetOrdersParamsSchema(
            subaccount_id=self._subaccount.id,
            instrument_name=instrument_name,
            label=label,
            page=page,
            page_size=page_size,
            status=status,
        )
        response = self._subaccount._private_api.get_orders(params)
        return response.result.orders

    def list_open(self) -> List[OrderResponseSchema]:
        """Get all open orders of a subacccount."""

        params = PrivateGetOpenOrdersParamsSchema(subaccount_id=self._subaccount.id)
        response = self._subaccount._private_api.get_open_orders(params)
        return response.result.orders

    def cancel(
        self,
        *,
        instrument_name: str,
        order_id: str,
    ) -> PrivateCancelResultSchema:
        """Cancel a single order."""

        params = PrivateCancelParamsSchema(
            instrument_name=instrument_name,
            order_id=order_id,
            subaccount_id=self._subaccount.id,
        )
        response = self._subaccount._private_api.cancel(params)
        return response.result

    def cancel_by_label(
        self,
        *,
        label: str,
        instrument_name: Optional[str] = None,
    ) -> PrivateCancelByLabelResultSchema:
        """
        Cancel all open orders for a given subaccount and a given label.

        If instrument_name is provided, only orders for that instrument will be cancelled.
        """

        params = PrivateCancelByLabelParamsSchema(
            label=label,
            instrument_name=instrument_name,
            subaccount_id=self._subaccount.id,
        )
        response = self._subaccount._private_api.cancel_by_label(params)
        return response.result

    def cancel_by_nonce(
        self,
        *,
        instrument_name: str,
        nonce: int,
    ) -> PrivateCancelByNonceResultSchema:
        """Cancel a single order by nonce. Uses up that nonce if the order does not exist,
        so any future orders with that nonce will fail."""

        params = PrivateCancelByNonceParamsSchema(
            nonce=nonce,
            instrument_name=instrument_name,
            subaccount_id=self._subaccount.id,
            wallet=self._subaccount._auth.wallet,
        )
        response = self._subaccount._private_api.cancel_by_nonce(params)
        return response.result

    def cancel_by_instrument(self, *, instrument_name: str) -> PrivateCancelByInstrumentResultSchema:
        """Cancel all orders for this instrument."""

        params = PrivateCancelByInstrumentParamsSchema(
            instrument_name=instrument_name,
            subaccount_id=self._subaccount.id,
        )
        response = self._subaccount._private_api.cancel_by_instrument(params)
        return response.result

    def cancel_all(self) -> Result:
        """Cancel all orders for this instrument."""

        params = PrivateCancelAllParamsSchema(subaccount_id=self._subaccount.id)
        response = self._subaccount._private_api.cancel_all(params)
        return response.result

    def replace(
        self,
        *,
        amount: Decimal,
        direction: Direction,
        instrument_name: str,
        limit_price: Decimal,
        max_fee: Decimal = Decimal("1000"),
        nonce: Optional[int] = None,
        signature_expiry_sec: Optional[int] = None,
        expected_filled_amount: Optional[Decimal] = None,
        is_atomic_signing: Optional[bool] = False,
        label: str = "",
        mmp: bool = False,
        nonce_to_cancel: Optional[int] = None,
        order_id_to_cancel: Optional[str] = None,
        order_type: OrderType = OrderType.limit,
        reduce_only: bool = False,
        reject_timestamp: int = INT64_MAX,
        time_in_force: TimeInForce = TimeInForce.gtc,
        trigger_price: Optional[Decimal] = None,
        trigger_price_type: Optional[TriggerPriceType] = None,
        trigger_type: Optional[TriggerType] = None,
    ) -> PrivateReplaceResultSchema:
        """
        Cancel an existing order with nonce or order_id and create new order with
        different order_id in a single RPC call.

        If the cancel fails, the new order will not be created.

        If the cancel succeeds but the new order fails, the old order will still be
        cancelled.

        Amount and limit_price are automatically quantized to match instrument specifications.
        """

        if (nonce_to_cancel is None) == (order_id_to_cancel is None):
            raise ValueError("Replace requires exactly one of nonce_to_cancel or order_id_to_cancel (but not both).")

        subaccount_id = self._subaccount.id

        instrument = self._subaccount.markets._get_cached_instrument(instrument_name=instrument_name)
        asset_address = instrument.base_asset_address
        sub_id = int(instrument.base_asset_sub_id)

        amount = Decimal(amount).quantize(instrument.amount_step)
        limit_price = Decimal(limit_price).quantize(instrument.tick_size)

        is_bid = direction == Direction.buy
        module_data = TradeModuleData(
            asset_address=asset_address,
            sub_id=sub_id,
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

        params = PrivateReplaceParamsSchema(
            amount=amount,
            direction=direction,
            instrument_name=instrument_name,
            limit_price=limit_price,
            max_fee=max_fee,
            nonce=signed_action.nonce,
            signature=signed_action.signature,
            signature_expiry_sec=signed_action.signature_expiry_sec,
            expected_filled_amount=expected_filled_amount,
            signer=signed_action.signer,
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
