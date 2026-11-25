"""Shared helpers for the API test suite (not collected: name does not match test*.py)."""

BOOKS_URL = "/books"

#: Exactly the serialized fields required by S2.
BOOK_FIELDS = {
    "id",
    "title",
    "author",
    "isbn",
    "cost_usd",
    "selling_price_local",
    "stock_quantity",
    "category",
    "supplier_country",
    "created_at",
    "updated_at",
}

#: Exactly the fields of the S6 price-calculation response.
PRICE_CALCULATION_FIELDS = {
    "book_id",
    "cost_usd",
    "exchange_rate",
    "cost_local",
    "margin_percentage",
    "selling_price_local",
    "currency",
    "calculation_timestamp",
    "exchange_rate_source",
}

DEFAULT_BOOK = {
    "title": "El Quijote",
    "author": "Miguel de Cervantes",
    "isbn": "978-84-376-0494-7",
    "cost_usd": "15.99",
    "stock_quantity": 25,
    "category": "Literatura Clásica",
    "supplier_country": "ES",
}


def book_payload(**overrides):
    """Return a valid create payload, optionally overriding single fields."""
    payload = dict(DEFAULT_BOOK)
    payload.update(overrides)
    return payload


def isbn_for(index: int) -> str:
    """Return a unique, valid 13-digit ISBN for generated fixtures."""
    return f"97800000000{index:02d}"
