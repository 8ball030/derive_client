"""CLI context setup."""

from __future__ import annotations

import os
from pathlib import Path

import rich_click as click
from dotenv import load_dotenv

from derive_client._clients.rest.http.client import HTTPClient
from derive_client.data_types import Environment


def create_client(
    ctx,
    session_key_path: Path | None,
    env_file: Path | None,
) -> HTTPClient:
    """Create the HTTPClient instance."""

    dotenv_path = env_file or Path.cwd() / ".env"
    load_dotenv(dotenv_path=dotenv_path)

    session_key = session_key_path.read_text().strip() if session_key_path else os.environ.get("DERIVE_SESSION_KEY")
    wallet = os.environ.get("DERIVE_WALLET")
    subaccount_id = os.environ.get("DERIVE_SUBACCOUNT")
    env = Environment[os.environ.get("DERIVE_ENV", "PROD").upper()]

    missing = []
    if not session_key:
        missing.append("DERIVE_SESSION_KEY: Not found in environment variables or via --session-key-path flag")
    if not wallet:
        missing.append("DERIVE_WALLET: Not found in environment variables.")
    if not subaccount_id:
        missing.append("DERIVE_SUBACCOUNT: Not found in environment variables.")

    if missing:
        error_msg = "Missing required configuration:\n\n" + "\n".join(f"  • {m}" for m in missing)
        error_msg += f"\n\nSearched for .env file at: {dotenv_path.absolute()}"

        if not dotenv_path.exists():
            error_msg += " (file not found)"

        error_msg += "\n\nProvide via environment variables or create a .env file with:"
        error_msg += "\n  DERIVE_SESSION_KEY=<your-session-key>"
        error_msg += "\n  DERIVE_WALLET=<your-wallet-address>"
        error_msg += "\n  DERIVE_SUBACCOUNT=<your-subaccount-id>"
        error_msg += "\n  DERIVE_ENV=PROD  # optional, defaults to PROD"

        raise click.ClickException(error_msg)

    return HTTPClient(
        wallet=wallet,
        session_key=session_key,
        subaccount_id=subaccount_id,
        env=env,
    )
