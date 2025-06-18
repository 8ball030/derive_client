import logging
import sys

from rich.logging import RichHandler


def get_logger():
    """Get the logger."""
    logger = logging.getLogger(__name__)
    formatter = logging.Formatter("%(message)s")

    # we check if the logger already has a handler
    # to avoid adding multiple handlers
    if logger.hasHandlers():
        return logger
    if sys.stdout.isatty():
        handler = RichHandler(
            markup=False,
            rich_tracebacks=True,
            locals_max_string=None,
            locals_max_length=None,
        )
    else:
        handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
