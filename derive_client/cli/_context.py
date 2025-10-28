"""CLI context setup."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from derive_client._clients.rest.http.client import HTTPClient
from derive_client.data_types import Environment


def create_client(
    ctx,
    signer_key_path: Path | None,
) -> HTTPClient:
    """Set the client."""

    # we use dotenv to load the env vars from DIRECTORY where the cli tool is executed
    _path = os.getcwd()
    env_path = os.path.join(_path, ".env")
    load_dotenv(dotenv_path=env_path)

    session_key = signer_key_path.read_text().strip() if signer_key_path else os.environ.get("DERIVE_SESSION_KEY")
    wallet = os.environ.get("DERIVE_WALLET")
    subaccount_id = os.environ.get("DERIVE_SUBACCOUNT")
    env = Environment[os.environ.get("DERIVE_ENV", "PROD").upper()]

    if not session_key:
        raise ValueError("Session key not provided. Please provide a valid private key.")
    if not wallet:
        raise ValueError("Wallet not provided. Please provide a LightAccount address.")
    if not subaccount_id:
        raise ValueError("Subaccount ID not provided. Please provide a subaccount ID.")

    return HTTPClient(
        wallet=wallet,
        session_key=session_key,
        subaccount_id=subaccount_id,
        env=env,
    )
