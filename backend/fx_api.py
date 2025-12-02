import json
from decimal import Decimal, getcontext
from datetime import date, timedelta
from typing import List, Dict, Optional, Tuple
import requests
from requests import Response, Session
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

getcontext().prec = 28  # high precision for FX calculations


# HTTP Session with retries
def _build_session() -> Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


_SESSION = _build_session()
_TIMEOUT: Tuple[float, float] = (5.0, 10.0)

FRANKFURTER_API = "https://api.frankfurter.dev/v1"
RESTCOUNTRIES_API = "https://restcountries.com/v3.1"


# Helper functions
def _raise_for_status_verbose(resp: Response) -> None:
    if 400 <= resp.status_code:
        raise requests.HTTPError(
            f"HTTP {resp.status_code} Error for {resp.url}: {resp.text[:300]}",
            response=resp,
        )


def _get_json(url: str, params: Optional[dict] = None) -> dict:
    resp = _SESSION.get(url, params=params, timeout=_TIMEOUT)
    _raise_for_status_verbose(resp)
    try:
        return resp.json()
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON returned from {url}")


def _to_decimal(x) -> Decimal:
    if isinstance(x, Decimal):
        return x
    if isinstance(x, (int, str)):
        return Decimal(str(x))
    if isinstance(x, float):
        return Decimal(repr(x))
    raise TypeError(f"Cannot convert {type(x)} to Decimal")


# 1. get_country_currency
def get_country_currency(country_name: str) -> str:
    """Return 3-letter currency code for a given 2- or 3-letter country code."""
    code = country_name.strip().upper()
    url = f"{RESTCOUNTRIES_API}/alpha/{code}"
    data = _get_json(url)

    if isinstance(data, list):
        data = data[0]
    currencies = data.get("currencies", {})
    if not currencies:
        raise KeyError(f"No currency info found for {country_name}")

    return next(iter(currencies.keys())).upper()


# 2. get_supported_currencies
def get_supported_currencies() -> List[str]:
    """Return list of supported 3-letter currency codes from Frankfurter API."""
    data = _get_json(f"{FRANKFURTER_API}/currencies")
    if not isinstance(data, dict):
        raise ValueError("Invalid response format from /currencies")
    return sorted([k.upper() for k in data.keys()])


# 3. get_current_rate
def get_current_rate(base_currency: str, target_currency: str) -> Decimal:
    """Fetch latest exchange rate between base and target (Frankfurter v1)."""
    base = base_currency.upper()
    target = target_currency.upper()
    if base == target:
        return Decimal("1")

    params = {"base": base, "symbols": target}
    data = _get_json(f"{FRANKFURTER_API}/latest", params=params)
    rate = data.get("rates", {}).get(target)
    if rate is None:
        raise KeyError(f"No rate found for {base}->{target}")
    return _to_decimal(rate)


# 4. get_currency_conversion_result
def get_currency_conversion_result(
    base_currency: str, target_currency: str, amount: Decimal
) -> Decimal:
    """Convert amount from base to target currency using latest FX rate."""
    if not isinstance(amount, Decimal):
        amount = _to_decimal(amount)
    rate = get_current_rate(base_currency, target_currency)
    return (amount * rate).quantize(Decimal("0.0001"))


# 5. get_monthly_rates
def get_monthly_rates(base_currency: str, target_currency: str) -> List[Decimal]:
    base = base_currency.upper()
    target = target_currency.upper()
    if base == target:
        return [Decimal("1")] * 30

    today = date.today()
    start = today - timedelta(days=29)
    url = f"{FRANKFURTER_API}/{start.isoformat()}..{today.isoformat()}"
    data = _get_json(url, params={"base": base, "symbols": target})
    rates = data.get("rates", {})

    rate_map: Dict[str, Decimal] = {
        d: _to_decimal(obj[target]) for d, obj in rates.items() if target in obj
    }

    result: List[Decimal] = []
    last_val: Optional[Decimal] = None
    for i in range(30):
        d = (start + timedelta(days=i)).isoformat()
        if d in rate_map:
            last_val = rate_map[d]
        elif last_val is None:
            last_val = get_current_rate(base, target)
        result.append(last_val)
    return result


# 6. analyze_rate_trend
def analyze_rate_trend(rates: List[Decimal]) -> int:
    """
    Analyze trend in a 30-day FX rate list.
    Returns:
        0 -> up, 1 -> down, 2 -> flat
    """
    if not rates or len(rates) < 2:
        return 2

    first, last = _to_decimal(rates[0]), _to_decimal(rates[-1])
    if first == 0:
        return 2
    change = (last - first) / first * Decimal("100")

    if abs(change) < Decimal("0.1"):
        return 2
    return 0 if change > 0 else 1


# CLI testing
if __name__ == "__main__":
    from decimal import Decimal as D

    print("Supported currencies:", get_supported_currencies())
    print("GBP of GB:", get_country_currency("GB"))
    print("EUR->USD rate:", get_current_rate("EUR", "USD"))
    print(
        "Convert 100 EUR->USD:", get_currency_conversion_result("EUR", "USD", D("100"))
    )
    rates = get_monthly_rates("USD", "CNY")
    print("Trend:", analyze_rate_trend(rates))
