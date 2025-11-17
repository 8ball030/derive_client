"""derive_client CLI package."""

from __future__ import annotations

from pathlib import Path

import rich_click as click

from derive_client._clients.rest.http.client import HTTPClient

from ._account import account
from ._bridge import bridge
from ._collateral import collateral
from ._markets import market
from ._mmp import mmp
from ._orders import order
from ._positions import position
from ._transactions import transaction
from ._tree import print_tree

click.rich_click.USE_RICH_MARKUP = True


@click.group("Derive Client")
@click.option(
    "--session-key-path",
    "-k",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    default=None,
    help="Path to the file containing the session key to be used as signer.",
)
@click.option(
    "--env-file",
    "-e",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    default=None,
    help="Path to a .env file. Defaults to .env in the current working directory.",
)
@click.pass_context
def cli(ctx, session_key_path: Path | None, env_file: Path | None):
    """Derive client command line interface."""

    ctx.ensure_object(dict)
    client = HTTPClient.from_env(session_key_path=session_key_path, env_file=env_file)
    ctx.obj["client"] = client


cli.add_command(account)
cli.add_command(bridge)
cli.add_command(collateral)
cli.add_command(market)
cli.add_command(mmp)
cli.add_command(order)
cli.add_command(position)
cli.add_command(transaction)


@cli.command()
@click.option('--verbose', '-v', is_flag=True, help='Show command descriptions')
def tree(verbose: bool):
    '''Print the command tree structure.'''
    print_tree(cli, verbose=verbose)
