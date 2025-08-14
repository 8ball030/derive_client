from logging import Logger

from eth_account import Account
from web3 import Web3
from web3.contract import Contract

from derive_client.data_types import Address, TxStatus
from derive_client.exceptions import InsufficientTokenBalance
from derive_client.utils import build_standard_transaction, send_tx, sign_tx, wait_for_tx_finality


async def ensure_token_balance(token_contract: Contract, owner: Address, amount: int):
    balance = await token_contract.functions.balanceOf(owner).call()
    if amount > balance:
        raise InsufficientTokenBalance(
            f"Not enough tokens to withdraw: {amount} < {balance} ({(balance / amount * 100):.2f}%)"
        )


async def ensure_token_allowance(
    w3: Web3,
    token_contract: Contract,
    owner: Address,
    spender: Address,
    amount: int,
    private_key: str,
    logger: Logger,
):
    allowance = await token_contract.functions.allowance(owner, spender).call()
    if amount > allowance:
        logger.info(f"Increasing allowance from {allowance} to {amount}")
        await _increase_token_allowance(
            w3=w3,
            from_account=Account.from_key(private_key),
            erc20_contract=token_contract,
            spender=spender,
            amount=amount,
            private_key=private_key,
            logger=logger,
        )


async def _increase_token_allowance(
    w3: Web3,
    from_account: Account,
    erc20_contract: Contract,
    spender: Address,
    amount: int,
    private_key: str,
    logger: Logger,
) -> None:
    func = erc20_contract.functions.approve(spender, amount)
    tx = await build_standard_transaction(func=func, account=from_account, w3=w3)
    signed_tx = sign_tx(w3=w3, tx=tx, private_key=private_key)
    tx_hash = await send_tx(w3=w3, signed_tx=signed_tx)
    tx_receipt = await wait_for_tx_finality(w3=w3, tx_hash=tx_hash, logger=logger)
    if tx_receipt.status != TxStatus.SUCCESS:
        raise RuntimeError("approve() failed")
