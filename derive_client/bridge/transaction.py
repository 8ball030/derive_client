from eth_account import Account
from web3 import Web3
from web3.contract import Contract

from derive_client.bridge.constants import DEPOSIT_GAS_LIMIT, MSG_GAS_LIMIT, PAYLOAD_SIZE
from derive_client.bridge.enums import TxStatus
from derive_client.bridge.models import Address
from derive_client.bridge.utils import sign_and_send_tx


def ensure_balance(token_contract: Contract, owner: Address, amount: int):
    balance = token_contract.functions.balanceOf(owner).call()
    if amount > balance:
        raise ValueError(f"Not enough funds: {balance}, tried to send: {amount}")


def ensure_allowance(
    w3: Web3,
    token_contract: Contract,
    owner: Address,
    spender: Address,
    amount: int,
    private_key: str,
):
    allowance = token_contract.functions.allowance(owner, spender).call()
    if amount > allowance:
        print(f"Increasing allowance from {allowance} to {amount}")
        increase_allowance(
            w3=w3,
            from_account=Account.from_key(private_key),
            erc20_contract=token_contract,
            spender=spender,
            amount=amount,
            private_key=private_key,
        )


def increase_allowance(
    w3: Web3,
    from_account: Account,
    erc20_contract: Contract,
    spender: Address,
    amount: int,
    private_key: str,
) -> None:
    func = erc20_contract.functions.approve(spender, amount)
    nonce = w3.eth.get_transaction_count(from_account.address)
    tx = func.build_transaction(
        {
            "from": from_account.address,
            "nonce": nonce,
            "gas": MSG_GAS_LIMIT,
            "gasPrice": w3.eth.gas_price,
        }
    )

    try:
        tx_receipt = sign_and_send_tx(w3, tx=tx, private_key=private_key)
        if tx_receipt.status == TxStatus.SUCCESS:
            print("Transaction succeeded!")
        else:
            raise Exception("Transaction reverted.")
    except Exception as error:
        raise error


def get_min_fees(w3: Web3, bridge_contract: Contract, connector: str) -> int:
    """Get min fees"""

    total_fees = bridge_contract.functions.getMinFees(
        connector_=Web3.to_checksum_address(connector),
        msgGasLimit_=MSG_GAS_LIMIT,
        payloadSize_=PAYLOAD_SIZE,
    ).call()
    return total_fees


def prepare_bridge_tx(
    w3: Web3,
    chain_id: int,
    account: Account,
    contract: Contract,
    receiver: str,
    amount: int,
    msg_gas_limit: int,
    connector: str,
) -> dict:
    """Build the function call for 'bridge'"""

    func = contract.functions.bridge(
        receiver_=w3.to_checksum_address(receiver),
        amount_=amount,
        msgGasLimit_=msg_gas_limit,
        connector_=w3.to_checksum_address(connector),
        extraData_=b"",
        options_=b"",
    )

    fees = get_min_fees(w3=w3, bridge_contract=contract, connector=connector)
    func.call({"from": account.address, "value": fees})

    nonce = w3.eth.get_transaction_count(account.address)
    tx = func.build_transaction(
        {
            "chainId": chain_id,
            "from": account.address,
            "nonce": nonce,
            "gas": DEPOSIT_GAS_LIMIT,
            "gasPrice": w3.eth.gas_price,
            "value": fees + 1,
        }
    )

    return tx
