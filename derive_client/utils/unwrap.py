from typing import TypeVar

from returns.io import IOFailure, IOResult, IOSuccess
from returns.result import Failure, Result, Success
from returns.unsafe import unsafe_perform_io

T = TypeVar("T")


def unwrap_or_raise(result: Result[T, Exception] | IOResult[T, Exception]) -> T:
    """Convert a returns.Result into a normal Python value or raise the underlying exception."""

    match result:
        case Success():
            return result.unwrap()
        case Failure():
            raise result.failure()
        case IOSuccess():
            return unsafe_perform_io(result.unwrap())
        case IOFailure():
            raise unsafe_perform_io(result.failure())
        case _:
            raise RuntimeError(f"unwrap_or_raise received a non-Result value: {result}")
