"""Async bridge client - unified interface for all bridge operations."""

from decimal import Decimal
from logging import Logger

from eth_account import Account
from returns.io import IOResult

from derive_client._bridge._derive_bridge import DeriveBridge
from derive_client._bridge._standard_bridge import StandardBridge
from derive_client.data_types import (
    Address,
    BridgeTxResult,
    BridgeType,
    ChainID,
    Currency,
    Environment,
    PreparedBridgeTx,
)
from derive_client.exceptions import BridgePrimarySignerRequiredError, NotConnectedError
from derive_client.utils import unwrap_or_raise


class AsyncBridgeClient:
    """
    Async client for bridging tokens to/from Derive.

    Supports:
    - Deposits/withdrawals: USDC, USDT, WETH, DRV, OLAS, etc.
    - Gas funding: ETH to owner EOA
    - Multiple chains: BASE, ARBITRUM, OPTIMISM, ETH
    """

    def __init__(self, env: Environment, account: Account, wallet: Address, logger: Logger):
        self._env = env
        self._account = account
        self._wallet = wallet
        self._logger = logger

        self._derive_bridge: DeriveBridge | None = None
        self._standard_bridge: StandardBridge | None = None

    async def connect(self) -> None:
        if self._env != Environment.PROD:
            raise RuntimeError(f"Bridging is not supported in the {self._env.name} environment.")

        derive_bridge = DeriveBridge(account=self._account, wallet=self._wallet, logger=self._logger)
        owner = await derive_bridge.light_account.functions.owner().call()
        if owner != self._account.address:
            raise BridgePrimarySignerRequiredError(
                "Bridging disabled for secondary session-key signers: old-style assets "
                "(USDC, USDT) on Derive cannot specify a custom receiver. Using a "
                "secondary signer routes funds to the session key's contract instead of "
                "the primary owner's. Please run all bridge operations with the "
                "primary wallet owner."
            )

        self._derive_bridge = derive_bridge
        self._standard_bridge = StandardBridge(account=self._account, logger=self._logger)

    def _ensure_bridge_available(self) -> None:
        if self._derive_bridge and self._standard_bridge:
            return
        raise NotConnectedError("BridgeClient not connected. Call await .connect() first.")

    # === PUBLIC API (Simple - raises on error) ===
    async def prepare_deposit_tx(
        self,
        *,
        amount: Decimal,
        currency: Currency,
        chain_id: ChainID,
    ) -> PreparedBridgeTx:
        """Prepare deposit to your Derive LightAccount wallet."""

        result = await self.try_prepare_deposit_tx(
            amount=amount,
            currency=currency,
            chain_id=chain_id,
        )
        return unwrap_or_raise(result)

    async def prepare_withdrawal_tx(
        self,
        *,
        amount: Decimal,
        currency: Currency,
        chain_id: ChainID,
    ) -> PreparedBridgeTx:
        """Prepare withdrawal from your Derive trading account."""

        result = await self.try_prepare_withdrawal_tx(
            amount=amount,
            currency=currency,
            chain_id=chain_id,
        )
        return unwrap_or_raise(result)

    async def prepare_gas_deposit_tx(
        self,
        *,
        amount: Decimal,
        chain_id: ChainID = ChainID.ETH,
    ) -> PreparedBridgeTx:
        """
        Prepare ETH deposit to fund gas for your owner's account.

        Your owner's account needs ETH to sign transactions on Derive L2.
        This bridges ETH to your EOA (not your LightAccount wallet).

        Args:
            amount: ETH amount in decimal units (e.g., 0.001)
            chain_id: Currently only Ethereum mainnet supported

        Returns:
            PreparedBridgeTx ready for submission
        """

        result = await self.try_prepare_gas_deposit_tx(amount=amount, chain_id=chain_id)
        return unwrap_or_raise(result)

    async def submit_tx(self, *, prepared_tx: PreparedBridgeTx) -> BridgeTxResult:
        """Submit a prepared bridge transaction."""

        result = await self.try_submit_tx(prepared_tx=prepared_tx)
        return unwrap_or_raise(result)

    async def poll_tx_progress(self, *, tx_result: BridgeTxResult) -> BridgeTxResult:
        """
        Poll for bridge completion across both chains.

        Can take a variable amount of time depending on chains and chain congestion.
        """

        result = await self.try_poll_tx_progress(tx_result=tx_result)
        return unwrap_or_raise(result)

    # === ADVANCED API (IOResult - explicit error handling) ===
    async def try_prepare_gas_deposit_tx(
        self,
        *,
        amount: Decimal,
        chain_id: ChainID = ChainID.ETH,
    ) -> IOResult[PreparedBridgeTx, Exception]:
        """Prepare gas deposit with explicit error handling."""

        self._ensure_bridge_available()
        to = self._account.address
        target_chain = ChainID.DERIVE

        return await self._standard_bridge.prepare_eth_tx(
            amount=amount,
            to=to,
            source_chain=chain_id,
            target_chain=target_chain,
        )

    async def try_prepare_deposit_tx(
        self,
        *,
        amount: Decimal,
        currency: Currency,
        chain_id: ChainID,
    ) -> IOResult[PreparedBridgeTx, Exception]:
        """Prepare deposit with explicit error handling."""

        self._ensure_bridge_available()
        return await self._derive_bridge.prepare_deposit(
            amount=amount,
            currency=currency,
            chain_id=chain_id,
        )

    async def try_prepare_withdrawal_tx(
        self,
        *,
        amount: Decimal,
        currency: Currency,
        chain_id: ChainID,
    ) -> IOResult[PreparedBridgeTx, Exception]:
        """Prepare withdrawal with explicit error handling."""

        self._ensure_bridge_available()
        return await self._derive_bridge.prepare_withdrawal(
            amount=amount,
            currency=currency,
            chain_id=chain_id,
        )

    async def try_submit_tx(self, *, prepared_tx: PreparedBridgeTx) -> IOResult[BridgeTxResult, Exception]:
        """Submit transaction with explicit error handling."""

        self._ensure_bridge_available()
        if prepared_tx.bridge_type == BridgeType.STANDARD:
            return await self._standard_bridge.submit_bridge_tx(prepared_tx=prepared_tx)

        return await self._derive_bridge.submit_bridge_tx(prepared_tx=prepared_tx)

    async def try_poll_tx_progress(self, *, tx_result: BridgeTxResult) -> IOResult[BridgeTxResult, Exception]:
        """Poll progress with explicit error handling."""

        self._ensure_bridge_available()
        if tx_result.bridge_type == BridgeType.STANDARD:
            return await self._standard_bridge.poll_bridge_progress(tx_result=tx_result)

        return await self._derive_bridge.poll_bridge_progress(tx_result=tx_result)
