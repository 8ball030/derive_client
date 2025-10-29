"""Market maker protection configuration operations."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from derive_client.data.generated.models import (
    MMPConfigResultSchema,
    PrivateGetMmpConfigParamsSchema,
    PrivateResetMmpParamsSchema,
    PrivateSetMmpConfigParamsSchema,
    PrivateSetMmpConfigResultSchema,
    Result,
)

if TYPE_CHECKING:
    from .subaccount import Subaccount


class MMPOperations:
    """Market maker protection operations."""

    def __init__(self, subaccount: Subaccount):
        """
        Initialize market maker protection operations.

        Args:
            subaccount: Subaccount instance providing access to auth, config, and APIs
        """
        self._subaccount = subaccount

    def get_config(self, *, currency: Optional[str] = None) -> list[MMPConfigResultSchema]:
        subaccount_id = self._subaccount.id
        params = PrivateGetMmpConfigParamsSchema(
            subaccount_id=subaccount_id,
            currency=currency,
        )
        response = self._subaccount._private_api.get_mmp_config(params=params)
        return response.result

    def set_config(
        self,
        *,
        currency: str,
        mmp_frozen_time: int,
        mmp_interval: int,
        mmp_amount_limit: Decimal = Decimal("0"),
        mmp_delta_limit: Decimal = Decimal("0"),
    ) -> PrivateSetMmpConfigResultSchema:
        subaccount_id = self._subaccount.id
        params = PrivateSetMmpConfigParamsSchema(
            subaccount_id=subaccount_id,
            currency=currency,
            mmp_frozen_time=mmp_frozen_time,
            mmp_interval=mmp_interval,
            mmp_amount_limit=mmp_amount_limit,
            mmp_delta_limit=mmp_delta_limit,
        )
        response = self._subaccount._private_api.set_mmp_config(params=params)
        return response.result

    def reset(self, *, currency: Optional[str] = None) -> Result:
        subaccount_id = self._subaccount.id
        params = PrivateResetMmpParamsSchema(
            subaccount_id=subaccount_id,
            currency=currency,
        )
        response = self._subaccount._private_api.reset_mmp(params=params)
        return response.result
