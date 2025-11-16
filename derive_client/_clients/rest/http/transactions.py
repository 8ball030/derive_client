"""Transaction operations."""

from __future__ import annotations

from logging import Logger

from derive_client._clients.rest.http.api import PublicAPI
from derive_client.data_types.generated_models import (
    PublicGetTransactionParamsSchema,
    PublicGetTransactionResultSchema,
)


class TransactionOperations:
    """High-level transaction operations."""

    def __init__(self, *, public_api: PublicAPI, logger: Logger):
        """
        Initialize transactions operations.

        Args:
            public_api: PublicAPI instance providing access to public APIs
        """

        self._public_api = public_api
        self._logger = logger

    def get(self, *, transaction_id: str) -> PublicGetTransactionResultSchema:
        """Get a transaction by its transaction id."""

        params = PublicGetTransactionParamsSchema(transaction_id=transaction_id)
        response = self._public_api.get_transaction(params)
        return response.result
