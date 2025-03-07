"""
Tests for the main function.
"""
import random
import time
from datetime import datetime
from itertools import product

import pytest
import requests

from derive.analyser import PortfolioAnalyser
from derive.enums import (
    ActionType,
    CollateralAsset,
    InstrumentType,
    OrderSide,
    OrderType,
    SubaccountType,
    UnderlyingCurrency,
)
from tests.conftest import freeze_time


@pytest.mark.parametrize(
    "instrument_type, currency",
    product(
        [InstrumentType.PERP, InstrumentType.OPTION],
        [UnderlyingCurrency.BTC],
    ),
)
def test_derive_client_fetch_instruments(derive_client, instrument_type, currency):
    """
    Test the DeriveClient class.
    """
    assert derive_client.fetch_instruments(instrument_type=instrument_type, currency=currency)


def test_create_signature_headers(derive_client):
    """
    Test the DeriveClient class.
    """
    assert derive_client._create_signature_headers()


def test_fetch_subaccounts(derive_client):
    """
    Test the DeriveClient class.
    """
    accounts = derive_client.fetch_subaccounts()
    assert accounts['subaccount_ids']


def test_fetch_subaccount(derive_client):
    """
    Show we can fetch a subaccount.
    """
    subaccount_id = derive_client.fetch_subaccounts()['subaccount_ids'][0]
    subaccount = derive_client.fetch_subaccount(subaccount_id)
    assert subaccount['subaccount_id'] == subaccount_id


@pytest.mark.skip()
def test_create_pm_subaccount(derive_client):
    """
    Test the DeriveClient class.
    """
    # freeze_time(derive_client)
    collateral_asset = CollateralAsset.USDC
    underlying_currency = UnderlyingCurrency.ETH
    subaccount_id = derive_client.create_subaccount(
        subaccount_type=SubaccountType.PORTFOLIO,
        collateral_asset=collateral_asset,
        underlying_currency=underlying_currency,
    )
    assert subaccount_id


@pytest.mark.parametrize(
    "instrument_name, side, price",
    [
        ("ETH-PERP", OrderSide.BUY, 200),
        ("ETH-PERP", OrderSide.SELL, 10000),
        ("BTC-PERP", OrderSide.BUY, 2000),
        ("BTC-PERP", OrderSide.SELL, 100000),
    ],
)
def test_create_order(derive_client, instrument_name, side, price):
    """
    Test the DeriveClient class.
    """
    result = derive_client.create_order(
        price=price,
        amount=1,
        instrument_name=instrument_name,
        side=OrderSide(side),
        order_type=OrderType.LIMIT,
    )
    assert "error" not in result
    order_price = float(result['limit_price'])
    order_side = result['direction']
    assert order_price == price
    assert order_side == side.value


def test_fetch_ticker(derive_client):
    """
    Test the DeriveClient class.
    """
    instruments = derive_client.fetch_instruments(instrument_type=InstrumentType.PERP)
    instrument_name = instruments[0]['instrument_name']
    ticker = derive_client.fetch_ticker(instrument_name=instrument_name)
    assert ticker['instrument_name'] == instrument_name


def test_fetch_option_tickers(derive_client):
    """
    Test the DeriveClient class.
    """
    instruments = derive_client.fetch_instruments(instrument_type=InstrumentType.OPTION, expired=False)
    instrument_name = instruments[0]['instrument_name']
    ticker = derive_client.fetch_ticker(instrument_name=instrument_name)
    assert ticker['instrument_name'] == instrument_name


def test_fetch_first_subaccount(derive_client):
    """
    Test the DeriveClient class.
    """
    subaccount_id = derive_client.fetch_subaccounts()['subaccount_ids'][0]
    subaccount = derive_client.fetch_subaccount(subaccount_id)
    assert subaccount['subaccount_id'] == subaccount_id


def test_fetch_orders(derive_client):
    """
    Test the DeriveClient class.
    """
    orders = derive_client.fetch_orders()
    assert orders


def test_cancel_order(derive_client):
    """
    Test the DeriveClient class.
    """
    order = derive_client.create_order(
        price=200,
        amount=1,
        instrument_name="ETH-PERP",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
    )
    order_id = order['order_id']
    result = derive_client.cancel(instrument_name="ETH-PERP", order_id=order_id)
    assert result['order_id'] == order_id


def test_cancel_all_orders(derive_client):
    """Test all open orders are cancelled."""
    derive_client.create_order(
        price=200,
        amount=1,
        instrument_name="ETH-PERP",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
    )
    open_orders = derive_client.fetch_orders(status="open")
    assert open_orders
    derive_client.cancel_all()
    open_orders = derive_client.fetch_orders(status="open")
    assert not open_orders


def test_get_positions(derive_client):
    """Test get positions."""
    positions = derive_client.get_positions()
    assert isinstance(positions, list)


def test_get_collaterals(derive_client):
    """Test get collaterals."""
    collaterals = derive_client.get_collaterals()
    assert isinstance(collaterals, dict)


def test_get_tickers(derive_client):
    """Test get tickers."""
    tickers = derive_client.fetch_tickers()
    assert isinstance(tickers, dict)


@pytest.mark.parametrize(
    "currency, side",
    [
        # (UnderlyingCurrency.ETH, OrderSide.BUY),
        # (UnderlyingCurrency.ETH, OrderSide.SELL),
        (UnderlyingCurrency.BTC, OrderSide.BUY),
        (UnderlyingCurrency.BTC, OrderSide.SELL),
    ],
)
def test_can_create_option_order(derive_client, currency, side):
    """Test can create option order."""
    tickers = derive_client.fetch_tickers(
        instrument_type=InstrumentType.OPTION,
        currency=currency,
    )
    symbol, ticker = [f for f in tickers.items() if f[1]['is_active']][0]
    if side == OrderSide.BUY:
        order_price = ticker['min_price']
    else:
        order_price = ticker['max_price']
    order = derive_client.create_order(
        price=order_price,
        amount=0.5,
        instrument_name=symbol,
        side=side,
        order_type=OrderType.LIMIT,
    )
    assert order


@pytest.mark.parametrize(
    "subaccount_type,underlying_currency,result",
    [
        (
            SubaccountType.STANDARD,
            None,
            (
                "247da26f2c790be0f0838efa1403703863af35a74c439665dca40a4491bd8c2f",
                "68031dbf2804c2c5c848de876db4cc334c69267ed7ff49646fbbd9d2aff16f71",
                "c164aa05f49611eb4aa67ab9736ab336c710d5ae9a71e05555e04f13f2bf32fc",
            ),
        ),
        (
            SubaccountType.PORTFOLIO,
            UnderlyingCurrency.ETH,
            (
                "af75590c7dde08338ed8f52c718140000bdee1476232b1321e694807d739aa74",
                "2c83609b60aec89e15520b340369a8d48257a83c95e18b751ac41b27fd3f7d7c",
                "d0bd37848578e76e7ea8afd96ecf821e194b2f8564729590fd8b6e264b5f0c7b",
            ),
        ),
    ],
)
def test_generate_necessary_data(derive_client, subaccount_type, underlying_currency, result):
    freeze_time(derive_client)
    collateral_asset = CollateralAsset.USDC
    subaccount_id = 0
    _, nonce, expiration = derive_client.get_nonce_and_signature_expiry()
    if subaccount_type is SubaccountType.STANDARD:
        contract_key = f"{subaccount_type.name}_RISK_MANAGER_ADDRESS"
    elif subaccount_type is SubaccountType.PORTFOLIO:
        if not collateral_asset:
            raise Exception("Underlying currency must be provided for portfolio subaccounts")
        contract_key = f"{underlying_currency.name}_{subaccount_type.name}_RISK_MANAGER_ADDRESS"
    deposit_data = derive_client._encode_deposit_data(
        amount=0.0,
        contract_key=contract_key,
    )
    assert deposit_data.hex() == result[0]

    action_hash = derive_client._generate_action_hash(
        subaccount_id=subaccount_id,
        encoded_deposit_data=deposit_data,
        expiration=expiration,
        nonce=nonce,
    )
    assert action_hash.hex() == result[1]

    typed_data_hash = derive_client._generate_typed_data_hash(
        action_hash=action_hash,
    )
    assert typed_data_hash.hex() == result[2]


def test_get_nonce_and_signature_expiration(derive_client):
    """Test get nonce and signature."""

    ts, nonce, expiration = derive_client.get_nonce_and_signature_expiry()
    assert ts
    assert nonce
    assert expiration


def test_transfer_collateral(derive_client):
    """Test transfer collateral."""
    # freeze_time(derive_client)
    amount = 1
    to = derive_client.fetch_subaccounts()['subaccount_ids'][1]
    asset = CollateralAsset.USDC
    result = derive_client.transfer_collateral(amount, to, asset)
    assert result


def test_transfer_collateral_steps(
    derive_client,
):
    """Test transfer collateral."""
    # freeze_time(derive_client)
    # nonce = 1705782758455361
    # nonce_2 = 1705782758455653
    # expiration = 1705782764455

    ts = int(datetime.now().timestamp() * 1000)
    nonce = int(f"{int(ts)}{random.randint(100, 499)}")
    nonce_2 = int(f"{int(ts)}{random.randint(500, 999)}")
    expiration = int(datetime.now().timestamp() + 10000)

    asset = CollateralAsset.USDC
    to = 27060
    amount = 10
    transfer = {
        "address": derive_client.contracts["CASH_ASSET"],
        "amount": int(amount),
        "sub_id": 0,
    }
    print(f"Transfering to {to} amount {amount} asset {asset.name}")
    encoded_data = derive_client.encode_transfer(
        amount=amount,
        to=to,
    )

    send_action_hash = derive_client._generate_action_hash(
        subaccount_id=derive_client.subaccount_id,
        nonce=nonce,
        expiration=expiration,
        encoded_deposit_data=encoded_data,
        action_type=ActionType.TRANSFER,
    )

    from_signed_action_hash = derive_client._generate_signed_action(
        action_hash=send_action_hash,
        nonce=nonce,
        expiration=expiration,
    )

    print("signature:" + from_signed_action_hash['signature'])

    recipient_action_hash = derive_client._generate_action_hash(
        subaccount_id=to,
        nonce=nonce_2,
        expiration=expiration,
        encoded_deposit_data=derive_client.web3_client.keccak(bytes.fromhex("")),
        action_type=ActionType.TRANSFER,
    )

    print("recipient_action_hash:" + recipient_action_hash.hex())

    to_signed_action_hash = derive_client._generate_signed_action(
        action_hash=recipient_action_hash,
        nonce=nonce_2,
        expiration=expiration,
    )

    payload = {
        "subaccount_id": derive_client.subaccount_id,
        "recipient_subaccount_id": to,
        "sender_details": {
            "nonce": nonce,
            "signature": "string",
            "signature_expiry_sec": expiration,
            "signer": derive_client.signer.address,
        },
        "recipient_details": {
            "nonce": nonce_2,
            "signature": "string",
            "signature_expiry_sec": expiration,
            "signer": derive_client.signer.address,
        },
        "transfer": transfer,
    }
    payload['sender_details']['signature'] = from_signed_action_hash['signature']
    payload['recipient_details']['signature'] = to_signed_action_hash['signature']

    pre_account_balance = float(derive_client.fetch_subaccount(derive_client.subaccount_id)['collaterals_value'])

    headers = derive_client._create_signature_headers()
    url = f"{derive_client.contracts['BASE_URL']}/private/transfer_erc20"
    sub_accounts = derive_client.fetch_subaccounts()['subaccount_ids']
    response = requests.post(url, json=payload, headers=headers)

    print(response.json())
    assert "error" not in response.json()

    # we now wait for the transaction to be mined
    # we can do this by checking the balance of the account
    # we should see the balance decrease by the amount we sent
    # and the balance of the recipient should increase by the amount we sent
    # we can also check the nonce of the account

    while True:
        account_balance = float(derive_client.fetch_subaccount(derive_client.subaccount_id)['collaterals_value'])
        if account_balance != pre_account_balance:
            break
        else:
            print(f"waiting for transaction to be mined balance is {account_balance}")
            time.sleep(1)

    assert account_balance == pre_account_balance - amount

    # we now check if *any* of the subaccounts have a balance of the amount we sent
    # if they do then the transaction was successful
    for sub_account in sub_accounts:
        res = derive_client.fetch_subaccount(sub_account)
        sub_account_balance = float(res['collaterals_value'])
        if sub_account_balance != 0:
            break
    else:
        assert False, "No subaccount has a balance"


@pytest.mark.parametrize(
    "underlying_currency",
    [
        UnderlyingCurrency.BTC.value,
    ],
)
def test_analyser(underlying_currency, derive_client):
    """Test analyser."""
    raw_data = derive_client.fetch_subaccount(derive_client.subaccount_id)
    analyser = PortfolioAnalyser(raw_data)
    analyser.print_positions(underlying_currency)
    assert len(analyser.get_positions(underlying_currency))
    assert len(analyser.get_open_positions(underlying_currency))
    assert analyser.get_subaccount_value()
    assert len(analyser.get_total_greeks(underlying_currency))


def test_get_mmp_config(derive_client):
    """Test get mmp config."""
    config = derive_client.get_mmp_config(derive_client.subaccount_id)
    assert isinstance(config, list)


def test_set_mmp_config(derive_client):
    """Test set mmp config."""
    config = {
        "subaccount_id": derive_client.subaccount_id,
        "currency": UnderlyingCurrency.ETH,
        "mmp_frozen_time": 0,
        "mmp_interval": 10_000,
        "mmp_amount_limit": 10,
        "mmp_delta_limit": 0.1,
    }
    derive_client.set_mmp_config(**config)
    set_config = derive_client.get_mmp_config(derive_client.subaccount_id, UnderlyingCurrency.ETH)[0]
    for k, v in config.items():
        if k == "currency":
            assert set_config[k] == v.name
        else:
            assert float(set_config[k]) == v
