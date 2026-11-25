"""Seed a small, varied bookstore catalogue so the SPA has data to display.

The command is idempotent: books are keyed by their normalized ISBN, so running
it again refreshes the sample rows instead of duplicating them.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from books.models import Book, normalize_isbn

SEED_BOOKS = [
    {
        "title": "El Quijote",
        "author": "Miguel de Cervantes",
        "isbn": "978-84-376-0494-7",
        "cost_usd": Decimal("15.99"),
        "selling_price_local": None,
        "stock_quantity": 25,
        "category": "Literatura Clásica",
        "supplier_country": "ES",
    },
    {
        "title": "Cien Años de Soledad",
        "author": "Gabriel García Márquez",
        "isbn": "978-84-397-3396-1",
        "cost_usd": Decimal("21.50"),
        "selling_price_local": None,
        "stock_quantity": 12,
        "category": "Literatura Clásica",
        "supplier_country": "CO",
    },
    {
        "title": "Rayuela",
        "author": "Julio Cortázar",
        "isbn": "978-84-376-0441-1",
        "cost_usd": Decimal("17.90"),
        "selling_price_local": None,
        "stock_quantity": 21,
        "category": "Literatura Clásica",
        "supplier_country": "AR",
    },
    {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "isbn": "978-0-13-235088-4",
        "cost_usd": Decimal("32.99"),
        "selling_price_local": Decimal("39.26"),
        "stock_quantity": 8,
        "category": "Tecnología",
        "supplier_country": "US",
    },
    {
        "title": "The Pragmatic Programmer",
        "author": "Andrew Hunt & David Thomas",
        "isbn": "978-0-20-161622-4",
        "cost_usd": Decimal("39.95"),
        "selling_price_local": None,
        "stock_quantity": 5,
        "category": "Tecnología",
        "supplier_country": "US",
    },
    {
        "title": "Introducción a los Algoritmos",
        "author": "Thomas H. Cormen",
        "isbn": "978-84-7829-144-2",
        "cost_usd": Decimal("55.00"),
        "selling_price_local": None,
        "stock_quantity": 4,
        "category": "Tecnología",
        "supplier_country": "ES",
    },
    {
        "title": "Sapiens: De animales a dioses",
        "author": "Yuval Noah Harari",
        "isbn": "978-0-06-231609-7",
        "cost_usd": Decimal("18.75"),
        "selling_price_local": None,
        "stock_quantity": 18,
        "category": "Historia",
        "supplier_country": "IL",
    },
    {
        "title": "Thinking, Fast and Slow",
        "author": "Daniel Kahneman",
        "isbn": "978-0-37-453355-7",
        "cost_usd": Decimal("24.00"),
        "selling_price_local": None,
        "stock_quantity": 9,
        "category": "Psicología",
        "supplier_country": "US",
    },
    {
        "title": "Dune",
        "author": "Frank Herbert",
        "isbn": "978-0-44-101359-3",
        "cost_usd": Decimal("12.99"),
        "selling_price_local": Decimal("15.46"),
        "stock_quantity": 30,
        "category": "Ciencia Ficción",
        "supplier_country": "US",
    },
    {
        "title": "1984",
        "author": "George Orwell",
        "isbn": "978-84-9759-076-8",
        "cost_usd": Decimal("11.20"),
        "selling_price_local": None,
        "stock_quantity": 42,
        "category": "Ciencia Ficción",
        "supplier_country": "GB",
    },
    {
        "title": "El Principito",
        "author": "Antoine de Saint-Exupéry",
        "isbn": "978-84-206-7337-3",
        "cost_usd": Decimal("9.95"),
        "selling_price_local": Decimal("11.84"),
        "stock_quantity": 60,
        "category": "Infantil",
        "supplier_country": "FR",
    },
    {
        "title": "Breve Historia del Tiempo",
        "author": "Stephen Hawking",
        "isbn": "978-84-8432-176-1",
        "cost_usd": Decimal("14.60"),
        "selling_price_local": None,
        "stock_quantity": 7,
        "category": "Ciencia",
        "supplier_country": "GB",
    },
]


class Command(BaseCommand):
    help = "Create or refresh the sample bookstore catalogue (safe to run repeatedly)."

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        updated = 0
        for entry in SEED_BOOKS:
            _, was_created = Book.objects.update_or_create(
                isbn_normalized=normalize_isbn(entry["isbn"]),
                defaults=dict(entry),
            )
            created += int(was_created)
            updated += int(not was_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(SEED_BOOKS)} books ({created} created, {updated} updated)."
            )
        )
