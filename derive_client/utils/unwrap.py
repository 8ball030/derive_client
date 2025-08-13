from typing import TypeVar

from returns.result import Failure, Result, Success

T = TypeVar("T")


def unwrap_or_raise(result: Result[T, Exception]) -> T:
    """Convert a returns.Result into a normal Python value or raise the underlying exception."""

    match result:
        case Success():
            return result.unwrap()
        case Failure():
            raise result.failure()
        case _:
            raise RuntimeError("unwrap_or_raise received a non-Result value")
