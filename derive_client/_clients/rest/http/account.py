"""Account management operations."""

from derive_client.data.generated.models import (
    PrivateGetAccountParamsSchema,
    PrivateGetAccountResultSchema,
    PrivateGetAllPortfoliosParamsSchema,
    PrivateGetSubaccountResultSchema,
    PrivateGetSubaccountsParamsSchema,
    PrivateGetSubaccountsResultSchema,
    PrivateSessionKeysParamsSchema,
    PrivateSessionKeysResultSchema,
    PrivateGetSubaccountParamsSchema,
)


class AccountOperations:
    """High-level account management operations."""

    def __init__(self, client):
        """
        Initialize account operations.

        Args:
            client: HTTPClient instance providing access to public/private APIs
        """
        self._client = client

    def session_keys(self) -> PrivateSessionKeysResultSchema:
        params = PrivateSessionKeysParamsSchema(wallet=self._client.wallet)
        response = self._client.private.session_keys(params)
        return response.result

    def get_all_portfolios(self) -> list[PrivateGetSubaccountResultSchema]:
        params = PrivateGetAllPortfoliosParamsSchema(wallet=self._client.wallet)
        response = self._client.private.get_all_portfolios(params)
        return response.result

    def get_subaccount(self) -> PrivateGetSubaccountResultSchema:
        params = PrivateGetSubaccountParamsSchema(subaccount_id=self._client.subaccount_id)
        response = self._client.private.get_subaccount(params)
        return response.result

    def get_subaccounts(self) -> PrivateGetSubaccountsResultSchema:
        params = PrivateGetSubaccountsParamsSchema(wallet=self._client.wallet)
        response = self._client.private.get_subaccounts(params)
        return response.result

    def get(self) -> PrivateGetAccountResultSchema:
        params = PrivateGetAccountParamsSchema(wallet=self._client.wallet)
        response = self._client.private.get_account(params)
        return response.result
