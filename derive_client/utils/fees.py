"""Module for calculating the fees on Derive."""

# https://docs.derive.xyz/reference/fees-1

from enum import Enum
from decimal import Decimal

from derive_client.data_types import Leg, InstrumentType, OrderSide


SECONDS_PER_YEAR = 60 * 60 * 24 * 365


class LegGroup(Enum):
    LONG_CALLS = "long_calls"
    SHORT_CALLS = "short_calls" 
    LONG_PUTS = "long_puts"
    SHORT_PUTS = "short_puts"
    PERPS = "perps"


def _is_box_spread(legs: list[Leg], tickers: dict) -> bool:
    """
    1. must have 4 legs
    2. all options
    3. same expiry
    4. one long call and short put at one strike price, 
       and one short call and a long put at another strike price
    """

    if not len(legs) == 4:
        return False

    options_details = [tickers[leg.instrument_name].get("options_details") for leg in legs]
    if not all(options_details):
        return False

    expiries = set()
    strikes = dict()
    for leg, details in zip(legs, options_details):
        expiries.add(details["expiry"])
        strike = details["strike"]
        option_type = details["option_type"]
        strikes.setdefault(strike, dict()).setdefault(option_type, set()).add(leg.direction)

    if not len(set(expiries)) == 1:
        return False

    if not len(strikes) == 2:
        return False

    # check we have both calls and puts at each price
    if not (set(positions) == {"C", "P"} for positions in strikes.values()):
        return False

    # calls must be opposite, puts must be opposite
    strike1_positions, strike2_positions = strikes.values()
    call1, put1 = strike1_positions["C"], strike1_positions["P"]
    call2, put2 = strike2_positions["C"], strike2_positions["P"]
    return call1 != call2 and put1 != put2


def _classify_leg(leg: Leg, ticker: dict):
    instrument_type = InstrumentType(ticker["instrument_type"])
    option_type = ticker.get("option_details", {}).get("option_type", {})

    match instrument_type, leg.direction, option_type:
        case InstrumentType.PERP, _, _:
            return LegGroup.PERPS
        case InstrumentType.OPTION, OrderSide.BUY, "C":
            return LegGroup.LONG_CALLS
        case InstrumentType.OPTION, OrderSide.SELL, "C":
            return LegGroup.SHORT_CALLS
        case InstrumentType.OPTION, OrderSide.BUY, "P":
            return LegGroup.LONG_PUTS
        case InstrumentType.OPTION, OrderSide.SELL, "P":
            return LegGroup.SHORT_PUTS
        case _:
            raise NotImplementedError()


def rfq_max_fee(client, legs: list[Leg], is_taker: bool = True) -> float:
    """
    Max fee ($ for the full trade).
    Request will be rejected if the supplied max fee is below the estimated fee for this trade.
    DeriveJSONRPCException: Derive RPC 11023: Max fee order param is too low
    """

    tickers = {}
    for leg in legs:
        instrument_name = leg.instrument_name
        ticker = client.fetch_ticker(instrument_name=instrument_name)
        tickers[instrument_name] = ticker

    if _is_box_spread(legs, tickers):
        
        first_ticker = tickers[legs[0]["instrument_name"]]
        timestamp = int(first_ticker["timestamp"])
        expiry = int(first_ticker["option_details"]["expiry"])

        strike1, strike2 = {Decimal(t["option_details"]["strike"]) for t in tickers.values()}
        notional = abs(strike1 - strike2)
        years_to_expiry = (expiry - timestamp / 1000) / SECONDS_PER_YEAR  # why not use Fraction?
        yield_spread_fee = (notional * Decimal("0.01") * Decimal(str(years_to_expiry)))

        total_fee = yield_spread_fee
        if is_taker:
            total_fee += max(t["base_fee"] for t in tickers.values())

        amounts = [Decimal(leg["amount"]) for leg in legs]
        return total_fee

    # Normal multi-leg handling
    for leg in legs:
        ticker = tickers[leg.instrument_name]
        group = _classify_leg(leg, ticker)

        base_fee = float(ticker["base_fee"])
        maker_fee_rate = float(ticker["maker_fee_rate"])
        taker_fee_rate = float(ticker["taker_fee_rate"])
        index_price = float(ticker["index_price"])
        mark_price = float(ticker["mark_price"])
        max_fee = str(base_fee + index_price * taker_fee_rate)

    return
