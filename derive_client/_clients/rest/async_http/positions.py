"""Position management operations."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from derive_action_signing.module_data import (
    MakerTransferPositionModuleData,
    MakerTransferPositionsModuleData,
    TakerTransferPositionModuleData,
    TakerTransferPositionsModuleData,
    TransferPositionsDetails,
)

from derive_client._clients.utils import PositionTransfer, sort_by_instrument_name
from derive_client.data.generated.models import (
    Direction,
    LegPricedSchema,
    PrivateGetPositionsParamsSchema,
    PrivateGetPositionsResultSchema,
    PrivateTransferPositionParamsSchema,
    PrivateTransferPositionResultSchema,
    PrivateTransferPositionsParamsSchema,
    PrivateTransferPositionsResultSchema,
    SignedQuoteParamsSchema,
    TradeModuleParamsSchema,
)

if TYPE_CHECKING:
    from .subaccount import Subaccount


class PositionOperations:
    """High-level position management operations."""

    def __init__(self, subaccount: Subaccount):
        """
        Initialize order operations.

        Args:
            subaccount: Subaccount instance providing access to auth, config, and APIs
        """
        self._subaccount = subaccount

    async def list(self) -> PrivateGetPositionsResultSchema:
        """Get all positions"""

        params = PrivateGetPositionsParamsSchema(subaccount_id=self._subaccount.id)
        response = await self._subaccount._private_api.get_positions(params)
        return response.result

    async def transfer(
        self,
        *,
        amount: Decimal,
        instrument_name: str,
        to_subaccount: int,
        signature_expiry_sec: Optional[int] = None,
        maker_nonce: Optional[int] = None,
        taker_nonce: Optional[int] = None,
    ) -> PrivateTransferPositionResultSchema:
        """Transfer position to another subaccount"""

        from_subaccount = self._subaccount.id
        max_fee = Decimal("0")

        instrument = self._subaccount.markets.get_cached_instrument(instrument_name=instrument_name)
        limit_price = instrument.tick_size
        asset_address = instrument.base_asset_address
        sub_id = int(instrument.base_asset_sub_id)

        module_address = self._subaccount._config.contracts.TRADE_MODULE

        maker_module_data = MakerTransferPositionModuleData(
            asset_address=asset_address,
            sub_id=sub_id,
            limit_price=limit_price,
            amount=abs(amount),
            recipient_id=from_subaccount,
            position_amount=amount,
        )
        taker_module_data = TakerTransferPositionModuleData(
            asset_address=asset_address,
            sub_id=sub_id,
            limit_price=limit_price,
            amount=abs(amount),
            recipient_id=to_subaccount,
            position_amount=amount,
        )

        maker_action = self._subaccount.sign_action(
            nonce=maker_nonce,
            module_address=module_address,
            module_data=maker_module_data,
            signature_expiry_sec=signature_expiry_sec,
        )
        taker_action = self._subaccount._auth.sign_action(
            nonce=taker_nonce,
            module_address=module_address,
            module_data=taker_module_data,
            signature_expiry_sec=signature_expiry_sec,
            subaccount_id=to_subaccount,
        )

        maker_params = TradeModuleParamsSchema(
            amount=abs(amount),
            direction=maker_module_data.get_direction(),
            instrument_name=instrument_name,
            limit_price=limit_price,
            max_fee=max_fee,
            nonce=maker_action.nonce,
            signature=maker_action.signature,
            signature_expiry_sec=maker_action.signature_expiry_sec,
            signer=maker_action.signer,
            subaccount_id=from_subaccount,
        )
        taker_params = TradeModuleParamsSchema(
            amount=abs(amount),
            direction=taker_module_data.get_direction(),
            instrument_name=instrument_name,
            limit_price=limit_price,
            max_fee=max_fee,
            nonce=taker_action.nonce,
            signature=taker_action.signature,
            signature_expiry_sec=taker_action.signature_expiry_sec,
            signer=taker_action.signer,
            subaccount_id=to_subaccount,
        )

        params = PrivateTransferPositionParamsSchema(
            maker_params=maker_params,
            taker_params=taker_params,
            wallet=self._subaccount._auth.wallet,
        )
        response = await self._subaccount._private_api.transfer_position(params)
        return response.result

    async def transfer_batch(
        self,
        *,
        positions: list[PositionTransfer],
        direction: Direction,
        to_subaccount: int,
        signature_expiry_sec: Optional[int] = None,
        maker_nonce: Optional[int] = None,
        taker_nonce: Optional[int] = None,
    ) -> PrivateTransferPositionsResultSchema:
        """Transfer multiple positions"""

        from_subaccount = self._subaccount.id
        positions = sort_by_instrument_name(positions)
        max_fee = Decimal("0")

        legs = []
        transfer_details = []
        for position in positions:
            amount = abs(position.amount)
            leg_direction = Direction.buy if position.amount < 0 else Direction.sell

            instrument_name = position.instrument_name
            instrument = self._subaccount.markets.get_cached_instrument(instrument_name=instrument_name)
            price = instrument.tick_size
            asset_address = instrument.base_asset_address
            sub_id = int(instrument.base_asset_sub_id)

            priced_leg = LegPricedSchema(
                amount=amount,
                direction=leg_direction,
                instrument_name=instrument_name,
                price=price,
            )
            legs.append(priced_leg)

            details = TransferPositionsDetails(
                instrument_name=instrument_name,
                direction=leg_direction,
                asset_address=asset_address,
                sub_id=sub_id,
                price=price,
                amount=amount,
            )
            transfer_details.append(details)

        maker_direction = direction
        taker_direction = Direction.buy if maker_direction == Direction.sell else Direction.sell

        module_address = self._subaccount._config.contracts.RFQ_MODULE

        maker_module_data = MakerTransferPositionsModuleData(
            global_direction=maker_direction,
            positions=transfer_details,
        )
        taker_module_data = TakerTransferPositionsModuleData(
            global_direction=taker_direction,
            positions=transfer_details,
        )

        maker_action = self._subaccount.sign_action(
            nonce=maker_nonce,
            module_address=module_address,
            module_data=maker_module_data,
            signature_expiry_sec=signature_expiry_sec,
        )
        taker_action = self._subaccount._auth.sign_action(
            nonce=taker_nonce,
            module_address=module_address,
            module_data=taker_module_data,
            signature_expiry_sec=signature_expiry_sec,
            subaccount_id=to_subaccount,
        )

        maker_params = SignedQuoteParamsSchema(
            direction=maker_direction,
            legs=legs,
            max_fee=max_fee,
            nonce=maker_action.nonce,
            signature=maker_action.signature,
            signature_expiry_sec=maker_action.signature_expiry_sec,
            signer=maker_action.signer,
            subaccount_id=from_subaccount,
        )
        taker_params = SignedQuoteParamsSchema(
            direction=taker_direction,
            legs=legs,
            max_fee=max_fee,
            nonce=taker_action.nonce,
            signature=taker_action.signature,
            signature_expiry_sec=taker_action.signature_expiry_sec,
            signer=taker_action.signer,
            subaccount_id=to_subaccount,
        )

        params = PrivateTransferPositionsParamsSchema(
            maker_params=maker_params,
            taker_params=taker_params,
            wallet=self._subaccount._auth.wallet,
        )
        response = await self._subaccount._private_api.transfer_positions(params)
        return response.result
