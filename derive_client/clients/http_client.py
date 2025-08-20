"""
Base class for HTTP client.
"""

import functools
from logging import Logger, LoggerAdapter

from derive_client.data_types import Address, BridgeTxResult, ChainID, Currency, Environment, PreparedBridgeTx
from derive_client.utils.asyncio_sync import run_coroutine_sync

from .async_client import AsyncClient
from .base_client import BaseClient


class HttpClient(BaseClient):
    """HTTP client class."""

    def __init__(
        self,
        wallet: Address,
        private_key: str,
        env: Environment,
        logger: Logger | LoggerAdapter | None = None,
        verbose: bool = False,
        subaccount_id: int | None = None,
    ):
        super().__init__(
            wallet=wallet,
            private_key=private_key,
            env=env,
            logger=logger,
            verbose=verbose,
            subaccount_id=subaccount_id,
        )

    @functools.cached_property
    def _async_client(self) -> AsyncClient:
        return AsyncClient(
            wallet=self.wallet,
            private_key=self.private_key,
            env=self.env,
            logger=self.logger,
            verbose=self.verbose,
            subaccount_id=self.subaccount_id,
        )

    def prepare_standard_tx(
        self,
        human_amount: float,
        currency: Currency,
        to: Address,
        source_chain: ChainID,
        target_chain: ChainID,
    ) -> PreparedBridgeTx:
        """Thin sync wrapper around AsyncClient.prepare_standard_tx."""

        coroutine = self._async_client.prepare_standard_tx(
            human_amount=human_amount,
            currency=currency,
            to=to,
            source_chain=source_chain,
            target_chain=target_chain,
        )

        return run_coroutine_sync(coroutine)

    def prepare_deposit_to_derive(
        self,
        human_amount: float,
        currency: Currency,
        chain_id: ChainID,
    ) -> PreparedBridgeTx:
        """Thin sync wrapper around AsyncClient.prepare_deposit_to_derive."""

        coroutine = self._async_client.prepare_deposit_to_derive(
            human_amount=human_amount,
            currency=currency,
            chain_id=chain_id,
        )
        return run_coroutine_sync(coroutine)

    def prepare_withdrawal_from_derive(
        self,
        human_amount: float,
        currency: Currency,
        chain_id: ChainID,
    ) -> PreparedBridgeTx:
        """Thin sync wrapper around AsyncClient.prepare_withdrawal_from_derive."""

        coroutine = self._async_client.prepare_withdrawal_from_derive(
            human_amount=human_amount,
            currency=currency,
            chain_id=chain_id,
        )
        return run_coroutine_sync(coroutine)

    def submit_bridge_tx(self, prepared_tx: PreparedBridgeTx) -> BridgeTxResult:
        """Thin sync wrapper around AsyncClient.submit_bridge_tx."""

        coroutine = self._async_client.submit_bridge_tx(prepared_tx=prepared_tx)
        return run_coroutine_sync(coroutine)

    def poll_bridge_progress(self, tx_result: BridgeTxResult) -> BridgeTxResult:
        """Thin sync wrapper around AsyncClient.poll_bridge_progress."""

        coroutine = self._async_client.poll_bridge_progress(tx_result=tx_result)
        return run_coroutine_sync(coroutine)
