"""Sale-price arithmetic for the price-calculation endpoint (S5, S6).

Kept free of Django view/HTTP concerns so it can be unit tested directly:
cost_local = round_half_up(cost_usd * rate) and
selling_price_local = round_half_up(cost_usd * rate * (1 + margin / 100)).
"""

from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings

MONEY_QUANTUM = Decimal("0.01")
ONE_HUNDRED = Decimal("100")


def round_money(value) -> Decimal:
    """Round a monetary value to 2 decimals using ROUND_HALF_UP."""
    return Decimal(str(value)).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def resolve_margin_percentage(margin_percentage=None) -> int:
    """Return the profit margin as an int, defaulting to the configured 40%."""
    if margin_percentage is None:
        margin_percentage = settings.PROFIT_MARGIN_PERCENTAGE
    return int(Decimal(str(margin_percentage)))


def calculate_price_breakdown(cost_usd, exchange_rate, margin_percentage=None) -> dict:
    """Return the rounded breakdown used by POST /books/{id}/calculate-price."""
    cost = Decimal(str(cost_usd))
    rate = Decimal(str(exchange_rate))
    margin = resolve_margin_percentage(margin_percentage)
    cost_local_exact = cost * rate
    multiplier = Decimal(1) + (Decimal(margin) / ONE_HUNDRED)
    return {
        "cost_usd": cost,
        "exchange_rate": rate,
        "cost_local": round_money(cost_local_exact),
        "margin_percentage": margin,
        "selling_price_local": round_money(cost_local_exact * multiplier),
    }
