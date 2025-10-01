"""
Tests for the main function.
"""

import time
from itertools import product

import pytest

from derive_client.analyser import PortfolioAnalyser
from derive_client.constants import DEFAULT_SPOT_QUOTE_TOKEN
from derive_client.data_types import (
    CollateralAsset,
    InstrumentType,
    OrderSide,
    OrderType,
    SubaccountType,
    UnderlyingCurrency,
)
from derive_client.utils import wait_until


@pytest.mark.parametrize(
    "instrument_tuple",
    [
        (InstrumentType.PERP, UnderlyingCurrency.BTC),
        (InstrumentType.OPTION, UnderlyingCurrency.BTC),
        (InstrumentType.ERC20, UnderlyingCurrency.LBTC),
    ],
)
def test_derive_client_fetch_instruments(derive_client, instrument_tuple):
    """
    Test the DeriveClient class.
    """
    instrument_type, currency = instrument_tuple
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


@pytest.mark.skip("This test is not working")
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


@pytest.mark.skip("This test is not working")
def test_create_sm_subaccount(derive_client):
    """
    Test the DeriveClient class.
    """
    # freeze_time(derive_client)
    collateral_asset = CollateralAsset.USDC
    subaccount_id = derive_client.create_subaccount(
        subaccount_type=SubaccountType.STANDARD,
        collateral_asset=collateral_asset,
    )
    assert subaccount_id


@pytest.mark.parametrize(
    "instrument_name, side, price, instrument_type",
    [
        ("ETH-PERP", OrderSide.BUY, 200, InstrumentType.PERP),
        ("ETH-PERP", OrderSide.SELL, 10000, InstrumentType.PERP),
    ],
)
def test_create_order(derive_client, instrument_name, side, price, instrument_type):
    """
    Test the DeriveClient class.
    """
    result = derive_client.create_order(
        price=price,
        amount=0.1,
        instrument_name=instrument_name,
        side=side,
        order_type=OrderType.LIMIT,
        instrument_type=instrument_type,
    )
    assert "error" not in result
    order_price = float(result['limit_price'])
    order_side = result['direction']
    assert order_price == price
    assert order_side == side.value


@pytest.mark.parametrize(
    "instrument_type, currency",
    product(
        [
            InstrumentType.PERP,
            InstrumentType.OPTION,
        ],
        [UnderlyingCurrency.BTC],
    ),
)
def test_fetch_instrument_ticker(derive_client, instrument_type, currency):
    """
    Test the DeriveClient class.
    """
    instruments = derive_client.fetch_instruments(
        instrument_type=instrument_type,
        currency=currency,
    )
    instrument_name = instruments[0]['instrument_name']
    ticker = derive_client.fetch_ticker(instrument_name=instrument_name)
    assert ticker['instrument_name'] == instrument_name


@pytest.mark.parametrize(
    "instrument_type, currency",
    product(
        [InstrumentType.ERC20],
        ["ETH"],
    ),
)
def test_fetch_spot_ticker(derive_client, instrument_type, currency):
    """
    Test the DeriveClient class.
    """
    instrument_name = f"{currency}-{DEFAULT_SPOT_QUOTE_TOKEN}"
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
    open_orders = wait_until(
        func=derive_client.fetch_orders,
        condition=lambda orders: orders,
        status="open",
        timeout_message="Orders not openened",
    )
    assert open_orders

    derive_client.cancel_all()
    open_orders = wait_until(
        func=derive_client.fetch_orders,
        condition=lambda orders: not orders,
        status="open",
        timeout_message="Outstanding orders not cancelled",
    )
    assert not open_orders


def test_get_positions(derive_client):
    """Test get positions."""
    positions = derive_client.get_positions()
    assert isinstance(positions, list)


def test_get_collaterals(derive_client):
    """Test get collaterals."""
    collaterals = derive_client.get_collaterals()
    assert isinstance(collaterals, list)


def test_get_tickers(derive_client):
    """Test get tickers."""
    tickers = derive_client.fetch_tickers()
    assert isinstance(tickers, dict)


@pytest.mark.parametrize(
    "currency, side",
    [
        (UnderlyingCurrency.ETH, OrderSide.BUY),
        (UnderlyingCurrency.ETH, OrderSide.SELL),
    ],
)
def test_can_create_option_order(derive_client, currency, side):
    """Test can create option order."""
    tickers = derive_client.fetch_tickers(
        instrument_type=InstrumentType.OPTION,
        currency=currency,
    )
    symbol, ticker = [f for f in tickers.items() if f[1]['is_active']][-1]
    order_price = ticker['min_price'] if side == OrderSide.BUY else ticker['max_price']
    order = derive_client.create_order(
        amount=0.5,
        side=side,
        price=order_price,
        instrument_name=symbol,
        instrument_type=InstrumentType.OPTION,
        order_type=OrderType.LIMIT,
    )
    assert order


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
    subaccounts = derive_client.fetch_subaccounts()
    to = subaccounts['subaccount_ids'][1]
    asset = CollateralAsset.USDC
    result = derive_client.transfer_collateral(amount, to, asset)
    assert result


def test_transfer_collateral_steps(derive_client):
    """Test transfer collateral."""

    subaccounts = derive_client.fetch_subaccounts()
    receiver = subaccounts['subaccount_ids'][1]
    sender = subaccounts['subaccount_ids'][0]

    pre_account_balance = float(derive_client.fetch_subaccount(sender)['collaterals_value'])
    asset = CollateralAsset.USDC
    amount = 1
    derive_client.transfer_collateral(amount, receiver, asset)
    while True:
        account_balance = float(derive_client.fetch_subaccount(sender)['collaterals_value'])
        if account_balance != pre_account_balance:
            break
        else:
            print(f"waiting for transaction to be mined balance is {account_balance}")
            time.sleep(1)

    assert account_balance == pre_account_balance - amount

    # we now check if *any* of the subaccounts have a balance of the amount we sent
    # if they do then the transaction was successful
    sub_accounts = derive_client.fetch_subaccounts()['subaccount_ids']
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
@pytest.mark.skip("Currently the subaccounts have no open positions")
def test_analyser(underlying_currency, derive_client):
    """Test analyser."""
    raw_data = derive_client.fetch_subaccount(derive_client.subaccount_id)
    analyser = PortfolioAnalyser(raw_data)
    analyser.print_positions(underlying_currency)
    analyser.get_open_positions(underlying_currency)
    analyser.get_subaccount_value()
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


def test_fetch_all_currencies(derive_client):
    """Test fetch all currencies."""
    currencies = derive_client.fetch_all_currencies()
    assert isinstance(currencies, list)
    assert len(currencies) > 0


def test_fetch_currency(derive_client):
    """Test fetch currency."""
    currency = derive_client.fetch_currency(UnderlyingCurrency.BTC.name)
    assert isinstance(currency, dict)
    assert currency['currency'] == UnderlyingCurrency.BTC.name
    assert currency['managers'].pop().get('address') is not None
