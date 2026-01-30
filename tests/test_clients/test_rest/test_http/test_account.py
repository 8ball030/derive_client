"""Tests for (Light)Account module."""

import pytest
from eth_account import Account

from derive_client.config import INT64_MAX
from derive_client.data_types.generated_models import (
    PrivateCreateSubaccountResultSchema,
    PrivateEditSessionKeyResultSchema,
    PrivateGetAccountResultSchema,
    PrivateGetSubaccountResultSchema,
    PrivateGetSubaccountsResultSchema,
    PrivateRegisterScopedSessionKeyResultSchema,
    PrivateSessionKeysResultSchema,
    Result,
    Scope,
)


@pytest.mark.skip(reason="Disabled to prevent test account clutter.")
def test_account_register_scoped_session_key(client_admin_wallet):
    expiry_sec = INT64_MAX
    account = Account.create()
    public_session_key = account.address
    scoped_session_key = client_admin_wallet.account.register_scoped_session_key(
        expiry_sec=expiry_sec,
        public_session_key=public_session_key,
        scope=Scope.account,
    )
    assert isinstance(scoped_session_key, PrivateRegisterScopedSessionKeyResultSchema)


def test_account_edit_session_key(client_admin_wallet):
    session_keys = client_admin_wallet.account.session_keys()
    public_session_key = session_keys.public_session_keys[0].public_session_key
    session_key = client_admin_wallet.account.edit_session_key(public_session_key=public_session_key)
    assert isinstance(session_key, PrivateEditSessionKeyResultSchema)


def test_account_session_keys(client_admin_wallet):
    session_keys = client_admin_wallet.account.session_keys()
    assert isinstance(session_keys, PrivateSessionKeysResultSchema)


def test_account_get_all_portfolios(client_admin_wallet):
    all_portfolios = client_admin_wallet.account.get_all_portfolios()
    assert isinstance(all_portfolios, list)
    assert all(isinstance(item, PrivateGetSubaccountResultSchema) for item in all_portfolios)


def test_account_get_subaccounts(client_admin_wallet):
    subaccounts = client_admin_wallet.account.get_subaccounts()
    assert isinstance(subaccounts, PrivateGetSubaccountsResultSchema)


def test_account_get(client_admin_wallet):
    account = client_admin_wallet.account.get()
    assert isinstance(account, PrivateGetAccountResultSchema)


@pytest.mark.skip(reason="Disabled to prevent test account clutter.")
def test_account_create_subaccount(client_admin_wallet):
    create_subaccount_result = client_admin_wallet.account.create_subaccount()
    assert isinstance(create_subaccount_result, PrivateCreateSubaccountResultSchema)


def test_account_set_cancel_on_disconnect(client_admin_wallet):
    result = client_admin_wallet.account.set_cancel_on_disconnect()
    assert isinstance(result, Result)
