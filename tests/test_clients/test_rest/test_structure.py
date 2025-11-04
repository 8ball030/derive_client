"""
Sense checks for REST client structure.
"""

import libcst
import inspect
from derive_client._clients.rest.http.client import HTTPClient
from derive_client._clients.rest.async_http.client import AsyncHTTPClient


def test_clients_properties():
    """Test that both sync and async HTTP clients have the same top-level `property` names."""
    sync_client_props = {
        name
        for name, member in inspect.getmembers(HTTPClient, predicate=inspect.isdatadescriptor)
    }
    async_client_props = {
        name
        for name, member in inspect.getmembers(AsyncHTTPClient, predicate=inspect.isdatadescriptor)
    }

    assert sync_client_props == async_client_props, "Sync and Async HTTP clients have different properties"
