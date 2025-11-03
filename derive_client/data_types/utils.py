from decimal import Decimal


def D(value: int | float | str | Decimal) -> Decimal:
    """
    Helper function to cast int, float, and str to Decimal.

    Args:
        value: The value to convert to Decimal

    Returns:
        Decimal representation of the value

    Examples:
        >>> D(0.1)
        Decimal('0.1')
        >>> D("123.456")
        Decimal('123.456')
        >>> D(42)
        Decimal('42')
    """
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
