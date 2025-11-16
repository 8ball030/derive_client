"""Generate a tree visualization of Click CLI commands."""

from typing import Generator, Union

import click
from more_itertools import mark_ends

ClickCommand = Union[click.Command, click.Group]


def longest_command_length(group: click.Group, prefix: str = "") -> int:
    """Calculate the longest command path length in the CLI tree."""
    max_length = 0

    for name, cmd in group.commands.items():
        current_length = len(prefix + name)
        max_length = max(max_length, current_length)

        if isinstance(cmd, click.Group):
            sub_length = longest_command_length(cmd, prefix=prefix + name + " ")
            max_length = max(max_length, sub_length)

    return max_length


def get_name_and_help(name: str, cmd: click.Command) -> tuple[str, str]:
    """Extract name and help text from a Click command."""
    help_text = cmd.help or cmd.callback.__doc__ if cmd.callback else ""
    # Clean up help text - take first line only
    if help_text:
        help_text = help_text.split('\n')[0].strip()
    return name, help_text or ""


def command_tree(group: click.Group, verbose: bool = False, use_rich: bool = True) -> Generator[str, None, None]:
    """Generate a tree visualization of Click CLI structure.

    Args:
        group: The root Click Group to traverse
        verbose: If True, include help text for each command
        use_rich: If True, use Rich markup for colors

    Yields:
        Formatted strings representing the CLI tree structure
    """
    space = "    "
    branch = "│   "
    tee = "├── "
    last = "└── "

    offset = 3
    max_length = longest_command_length(group) + offset

    def format_command(name: str, cmd: click.Command, is_last: bool, prefix: str) -> str:
        """Format a single command line in the tree."""
        cmd_name, help_text = get_name_and_help(name, cmd)
        pointer = last if is_last else tee
        node = f"{prefix}{pointer}{cmd_name}"

        if verbose and help_text:
            if use_rich:
                dots = "[dim]" + "." * (max_length - len(prefix) - len(cmd_name) - len(pointer)) + "[/dim]"
                node += f"{dots} [cyan]{help_text}[/cyan]"
            else:
                dots = "." * (max_length - len(prefix) - len(cmd_name) - len(pointer))
                node += f"{dots} {help_text}"

        return node

    def walk_group(grp: click.Group, prefix: str = "") -> Generator[str, None, None]:
        """Recursively walk through command groups."""
        if not grp.commands:
            return

        items = sorted(grp.commands.items())

        for _, is_last, (name, cmd) in mark_ends(items):
            yield format_command(name, cmd, is_last, prefix)

            if isinstance(cmd, click.Group):
                extension = space if is_last else branch
                yield from walk_group(cmd, prefix=prefix + extension)

    # Yield root group name
    root_name = group.name or "CLI"
    if use_rich:
        yield f"[bold]{root_name}[/bold]"
    else:
        yield root_name

    # Yield the tree structure
    yield from walk_group(group)


def print_tree(group: click.Group, verbose: bool = False):
    """Print the CLI tree to console.

    Args:
        group: The root Click Group
        verbose: Include help text
    """
    try:
        from rich.console import Console

        console = Console()
        use_rich = True
    except ImportError:
        console = None
        use_rich = False

    for line in command_tree(group, verbose=verbose, use_rich=use_rich):
        if console:
            console.print(line)
        else:
            print(line)
