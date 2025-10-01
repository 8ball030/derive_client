"""
Get the volatility of a BTC.
"""

# curl -X GET "https://test.deribit.com/api/v2/public/get_volatility_index_data?currency=BTC&end_timestamp=1599376800000&resolution=60&start_timestamp=1599373800000" \
# -H "Content-Type: application/json"

import math
from datetime import datetime as date

import py_vollib.black_scholes.greeks.numerical
import py_vollib.black_scholes_merton
import requests
from pydantic import BaseModel

from derive_client.data_types.enums import OptionType

def black_scholes_call(S, K, T, r, sigma):
    """
    S: Current stock price
    K: Strike price
    T: Time to maturity (in years)
    r: Risk-free interest rate (annual)
    sigma: Volatility of the underlying stock (standard deviation)
    """
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    call_price = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    return call_price


def get_volatility(
    currency: str = "BTC", start_timestamp: int = None, end_timestamp: int = None, resolution: int = "1D"
):
    """Get the volatility of a currency."""

    start_timestamp = start_timestamp or date.now().timestamp() * 1000 - 3600 * 1000  # 1 hour ago
    end_timestamp = end_timestamp or date.now().timestamp() * 1000  # now
    result = requests.get(
        "https://test.deribit.com/api/v2/public/get_volatility_index_data",
        params={
            "currency": currency,
            "start_timestamp": int(start_timestamp),
            "end_timestamp": int(end_timestamp),
            "resolution": resolution,
        },
    )
    return result.json().get("result", {}).get("data", [])[-1][-1]


class BlackScholesData(BaseModel):
    cost: float
    delta: float
    gamma: float
    theta: float

class OptionDetails(BaseModel):
    index: str
    expiry: int
    strike: float
    option_type: OptionType
    settlement_price: float | None = None

def get_black_scholes_data(
    side: OptionType,
    current_stock_price: float,
    strike_price: float,
    expiration_time: float,
    sigma: float,
    risk_free_rate: float = 0.02,
):
    current_time = date.utcnow().timestamp()
    t = (expiration_time - current_time) / (3600 * 24 * 365.25)  # in years
    cost = py_vollib.black_scholes.black_scholes(
        side.lower(), current_stock_price, strike_price, t, risk_free_rate, sigma
    )
    delta = py_vollib.black_scholes.greeks.numerical.delta(
        side.lower(),
        current_stock_price,
        strike_price,
        t,
        risk_free_rate,
        sigma,
    )
    gamma = py_vollib.black_scholes.greeks.numerical.gamma(
        side.lower(),
        current_stock_price,
        strike_price,
        t,
        risk_free_rate,
        sigma,
    )
    theta = py_vollib.black_scholes.greeks.numerical.theta(
        side.lower(),
        current_stock_price,
        strike_price,
        t,
        risk_free_rate,
        sigma,
    )
    return BlackScholesData(cost=cost, delta=delta, gamma=gamma, theta=theta)


if __name__ == "__main__":
    vol_data = get_volatility(currency="ETH")
    print(f"Volatility data: {vol_data}")

    sigma = vol_data / 100  # Volatility of the underlying stock (standard deviation)

    option_details = {
        "index": "ETH-USD",
        "expiry": 1758700800,
        "strike": "4200",
        "option_type": "C",
        "settlement_price": None
      }
    
    current_price = 4196
    pos_size = -3
    option = OptionDetails(**option_details)
    option_greeks = get_black_scholes_data(
        side=option.option_type,
        current_stock_price=current_price,
        strike_price=option.strike,
        expiration_time=option.expiry,
        sigma=sigma,
    )

    # convert from time_to_expiry in seconds to years
    current_time = date.utcnow().timestamp()

    print(f"  Position Delta: {option_greeks.delta * pos_size}")
    print(f"  Position Gamma: {option_greeks.gamma * pos_size}")
    print(f"  Position Theta: {option_greeks.theta * pos_size}")
    print(f"  Position Cost: {option_greeks.cost * pos_size}")
