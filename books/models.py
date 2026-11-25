"""The Book inventory model and its ISBN rules (S2, S7)."""

import re
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

ISBN_DIGITS_PATTERN = re.compile(r"^(?:\d{10}|\d{13})$")
SUPPLIER_COUNTRY_PATTERN = re.compile(r"^[A-Z]{2}$")

ISBN_FORMAT_ERROR = (
    "ISBN must contain 10 or 13 digits (hyphens and spaces are allowed)."
)


def normalize_isbn(value: str) -> str:
    """Return the ISBN digits only, dropping hyphens and whitespace."""
    if value is None:
        return ""
    return re.sub(r"[\s\-]", "", str(value))


def is_valid_isbn(value: str) -> bool:
    """True when the ISBN has 10 or 13 digits once hyphens/spaces are removed."""
    return bool(ISBN_DIGITS_PATTERN.match(normalize_isbn(value)))


def _as_decimal(value):
    """Best-effort Decimal conversion used by model validation."""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _as_int(value):
    """Best-effort int conversion used by model validation."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class Book(models.Model):
    """A title in the bookstore inventory.

    isbn keeps whatever punctuation the caller sent (the S2 example keeps its
    hyphens) while isbn_normalized stores the digits only and carries the
    uniqueness rule, so 978-84-376-0494-7 and 9788437604947 are the same book.
    """

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=32)
    isbn_normalized = models.CharField(max_length=13, unique=True, editable=False)
    cost_usd = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    selling_price_local = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    stock_quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    category = models.CharField(max_length=120)
    supplier_country = models.CharField(
        max_length=2,
        validators=[
            RegexValidator(
                SUPPLIER_COUNTRY_PATTERN,
                "Supplier country must be a 2-letter ISO 3166-1 code, e.g. ES.",
            )
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["category"], name="books_category_idx"),
            models.Index(fields=["stock_quantity"], name="books_stock_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.isbn})"

    def clean(self):
        super().clean()
        errors = {}
        if not is_valid_isbn(self.isbn):
            errors["isbn"] = ISBN_FORMAT_ERROR
        cost_usd = _as_decimal(self.cost_usd)
        if cost_usd is not None and cost_usd <= 0:
            errors["cost_usd"] = "Cost in USD must be greater than 0."
        stock_quantity = _as_int(self.stock_quantity)
        if stock_quantity is not None and stock_quantity < 0:
            errors["stock_quantity"] = "Stock quantity cannot be negative."
        if self.supplier_country and not SUPPLIER_COUNTRY_PATTERN.match(
            self.supplier_country
        ):
            errors["supplier_country"] = (
                "Supplier country must be a 2-letter ISO 3166-1 code, e.g. ES."
            )
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.isbn_normalized = normalize_isbn(self.isbn)
        if self.supplier_country:
            self.supplier_country = self.supplier_country.strip().upper()
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            update_fields = set(update_fields)
            if "isbn" in update_fields:
                update_fields.add("isbn_normalized")
            kwargs["update_fields"] = update_fields
        super().save(*args, **kwargs)
