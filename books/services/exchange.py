"""USD exchange-rate client with a configurable fallback (S5, S7).

fetch_usd_rate returns (Decimal rate, "live" | "fallback"). Any transport
failure, non-200 status, malformed payload, missing currency or unusable rate is
logged and either replaced by FALLBACK_EXCHANGE_RATE or, when
EXCHANGE_FALLBACK_ENABLED is false, surfaced as ExchangeRateUnavailable so the
view can answer HTTP 503.
"""

import logging
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

RATE_SOURCE_LIVE = "live"
RATE_SOURCE_FALLBACK = "fallback"


class ExchangeRateError(Exception):
    """The FX provider answered, but not with a usable rate."""


class ExchangeRateUnavailable(Exception):
    """No rate is available and the configured fallback is disabled."""


def _fallback_or_raise(currency, reason, allow_fallback, fallback_rate):
    if allow_fallback and fallback_rate > 0:
        logger.warning(
            "Using the fallback USD->%s exchange rate %s (%s)",
            currency,
            fallback_rate,
            reason,
        )
        return fallback_rate, RATE_SOURCE_FALLBACK
    logger.error("No USD->%s exchange rate available (%s)", currency, reason)
    raise ExchangeRateUnavailable(
        f"The USD to {currency} exchange rate is currently unavailable. "
        "Please try again later."
    ) from reason


def fetch_usd_rate(
    target_currency,
    *,
    http_get=None,
    url=None,
    timeout=None,
    fallback_enabled=None,
    fallback_rate=None,
):
    """Resolve the current USD -> target_currency rate.

    Every collaborator is injectable so callers (and tests) never need to patch
    the network: pass http_get to replace requests.get.
    """
    currency = (target_currency or "").strip().upper()
    if not currency:
        raise ValueError("target_currency is required")

    getter = http_get or requests.get
    api_url = url or settings.EXCHANGE_RATE_API_URL
    request_timeout = settings.EXCHANGE_RATE_TIMEOUT if timeout is None else timeout
    allow_fallback = (
        settings.EXCHANGE_FALLBACK_ENABLED
        if fallback_enabled is None
        else fallback_enabled
    )
    fallback = Decimal(
        str(
            settings.FALLBACK_EXCHANGE_RATE
            if fallback_rate is None
            else fallback_rate
        )
    )

    try:
        response = getter(api_url, timeout=request_timeout)
        status_code = getattr(response, "status_code", None)
        if status_code != 200:
            raise ExchangeRateError(f"the exchange-rate API returned HTTP {status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise ExchangeRateError(
                "the exchange-rate API returned a non-object payload"
            )
        rates = payload.get("rates")
        if not isinstance(rates, dict):
            raise ExchangeRateError("the exchange-rate payload has no 'rates' object")
        if currency not in rates:
            raise ExchangeRateError(f"the exchange-rate payload has no {currency} rate")
        rate = Decimal(str(rates[currency]))
        if not rate.is_finite() or rate <= 0:
            raise ExchangeRateError(
                "the exchange-rate API returned an unusable "
                f"{currency} rate: {rates[currency]!r}"
            )
    except (
        requests.RequestException,
        ExchangeRateError,
        InvalidOperation,
        TypeError,
        ValueError,
    ) as exc:
        return _fallback_or_raise(currency, exc, allow_fallback, fallback)

    return rate, RATE_SOURCE_LIVE
