"""
Conftest for derive tests
"""

from contextlib import contextmanager
from unittest.mock import patch

import pytest
from pytest_asyncio import is_async_test

OWNER_TEST_WALLET = "0xA419f70C696a4b449a4A24F92e955D91482d44e9"
ADMIN_TEST_WALLET = "0x8772185a1516f0d61fC1c2524926BfC69F95d698"
SESSION_KEY_PRIVATE_KEY = "0x2ae8be44db8a590d20bffbe3b6872df9b569147d3bf6801a35a28281a4816bbd"


def pytest_collection_modifyitems(items):
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)


@contextmanager
def assert_api_calls(client, expected: int):
    with patch.object(client._session, "_send_request", wraps=client._session._send_request) as api_requests:
        before = api_requests.call_count
        yield
        after = api_requests.call_count
    actual = after - before
    if actual != expected:
        raise AssertionError(f"Expected {expected} HTTP calls, got {actual}. (before={before}, after={after})")
