"""Order management operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from derive_client.config import INT64_MAX
from derive_client.data_types.generated_models import (
    InstrumentType,
    PrivateGetTradeHistoryParamsSchema,
    PublicGetTradeHistoryParamsSchema,
    TradeResponseSchema,
    TradeSettledPublicResponseSchema,
    TxStatus2,
)

if TYPE_CHECKING:
    from .subaccount import Subaccount


class TradeOperations:
    """High-level order management operations."""

    def __init__(self, subaccount: Subaccount):
        """
        Initialize order operations.

        Args:
            subaccount: Subaccount instance providing access to auth, config, and APIs
        """
        self._subaccount = subaccount

    async def list_public(
        self,
        currency: str | None = None,
        from_timestamp: int = 0,
        instrument_name: str | None = None,
        instrument_type: InstrumentType | None = None,
        page: int = 1,
        page_size: int = 100,
        subaccount_id: int | None = None,
        to_timestamp: int = INT64_MAX,
        trade_id: str | None = None,
        tx_hash: str | None = None,
        tx_status: TxStatus2 = TxStatus2('settled'),
    ) -> list[TradeSettledPublicResponseSchema]:
        """Get trade history for a subaccount, with filter parameters."""

        params = PublicGetTradeHistoryParamsSchema(
            currency=currency,
            from_timestamp=from_timestamp,
            instrument_name=instrument_name,
            instrument_type=instrument_type,
            page=page,
            page_size=page_size,
            subaccount_id=subaccount_id,
            to_timestamp=to_timestamp,
            trade_id=trade_id,
            tx_hash=tx_hash,
            tx_status=tx_status,
        )
        response = await self._subaccount._public_api.get_trade_history(params)
        return response.result.trades

    async def list_private(
        self,
        from_timestamp: int = 0,
        instrument_name: str | None = None,
        order_id: str | None = None,
        page: int = 1,
        page_size: int = 100,
        quote_id: str | None = None,
        to_timestamp: int = INT64_MAX,
    ) -> list[TradeResponseSchema]:
        """Get trade history for a subaccount, with filter parameters."""

        params = PrivateGetTradeHistoryParamsSchema(
            from_timestamp=from_timestamp,
            instrument_name=instrument_name,
            order_id=order_id,
            page=page,
            page_size=page_size,
            quote_id=quote_id,
            subaccount_id=self._subaccount.id,
            to_timestamp=to_timestamp,
            wallet=self._subaccount._auth.wallet,
        )
        response = await self._subaccount._private_api.get_trade_history(params)
        return response.result.trades
