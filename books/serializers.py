"""Serializers for the Book resource and the price-calculation response (S2, S6)."""

import re
from decimal import Decimal

from django.db import IntegrityError
from rest_framework import serializers

from books.models import ISBN_FORMAT_ERROR, Book, is_valid_isbn, normalize_isbn

SUPPLIER_COUNTRY_PATTERN = re.compile(r"^[A-Z]{2}$")
DUPLICATE_ISBN_ERROR = "A book with this ISBN already exists."


class BookSerializer(serializers.ModelSerializer):
    """Exposes exactly the S2 field set and enforces the S7 business rules."""

    isbn = serializers.CharField(max_length=32)
    cost_usd = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
    selling_price_local = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    stock_quantity = serializers.IntegerField(min_value=0)
    supplier_country = serializers.CharField(max_length=2)

    class Meta:
        model = Book
        fields = [
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
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_isbn(self, value):
        isbn = (value or "").strip()
        if not is_valid_isbn(isbn):
            raise serializers.ValidationError(ISBN_FORMAT_ERROR)
        normalized = normalize_isbn(isbn)
        duplicates = Book.objects.filter(isbn_normalized=normalized)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError(DUPLICATE_ISBN_ERROR)
        return isbn

    def validate_supplier_country(self, value):
        country = (value or "").strip().upper()
        if not SUPPLIER_COUNTRY_PATTERN.match(country):
            raise serializers.ValidationError(
                "Supplier country must be a 2-letter ISO 3166-1 code, e.g. ES."
            )
        return country

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError:
            # A concurrent duplicate is still a 400, never a 500.
            raise serializers.ValidationError({"isbn": [DUPLICATE_ISBN_ERROR]})

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except IntegrityError:
            raise serializers.ValidationError({"isbn": [DUPLICATE_ISBN_ERROR]})


class PriceCalculationSerializer(serializers.Serializer):
    """Response shape of POST /books/{id}/calculate-price (S6)."""

    book_id = serializers.IntegerField()
    cost_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    exchange_rate = serializers.DecimalField(max_digits=16, decimal_places=6)
    cost_local = serializers.DecimalField(max_digits=14, decimal_places=2)
    margin_percentage = serializers.IntegerField()
    selling_price_local = serializers.DecimalField(max_digits=14, decimal_places=2)
    currency = serializers.CharField()
    calculation_timestamp = serializers.DateTimeField()
    exchange_rate_source = serializers.CharField()
