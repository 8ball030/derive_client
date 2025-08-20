"""
Derive is a Python library for trading on Derive.
"""

import pandas as pd
from web3 import Web3

from derive_client.clients import HttpClient

# we set to show 4 decimal places
pd.options.display.float_format = '{:,.4f}'.format


def to_32byte_hex(val):
    return Web3.to_hex(Web3.to_bytes(val).rjust(32, b"\0"))


class DeriveClient(HttpClient):
    """Client for the derive dex."""

    def _create_signature_headers(self):
        """Generate the signature headers."""
        return HttpClient._create_signature_headers(self)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
