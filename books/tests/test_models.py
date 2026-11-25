"""Book model rules: ISBN normalization, uniqueness, field validation (S2, S7)."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase

from books.models import Book, is_valid_isbn, normalize_isbn
from books.tests.utils import book_payload


class NormalizeIsbnTests(SimpleTestCase):
    def test_removes_hyphens_and_spaces(self):
        for raw in ("978-84-376-0494-7", "978 84 376 0494 7", " 9788437604947 "):
            self.assertEqual(normalize_isbn(raw), "9788437604947")

    def test_keeps_the_digits_of_a_ten_digit_isbn(self):
        self.assertEqual(normalize_isbn("0-306-40615-2"), "0306406152")

    def test_accepts_ten_and_thirteen_digit_forms(self):
        for raw in ("978-84-376-0494-7", "9788437604947", "0-306-40615-2"):
            self.assertTrue(is_valid_isbn(raw), raw)

    def test_rejects_wrong_length_or_letters(self):
        for raw in ("12345", "978843760494", "978-84-376-0494-X", "", "12345678901234"):
            self.assertFalse(is_valid_isbn(raw), raw)


class BookModelTests(TestCase):
    def make_book(self, **overrides):
        return Book.objects.create(**book_payload(**overrides))

    def test_isbn_normalized_is_derived_from_the_isbn(self):
        book = self.make_book()

        self.assertEqual(book.isbn, "978-84-376-0494-7")
        self.assertEqual(book.isbn_normalized, "9788437604947")

    def test_isbn_normalized_follows_isbn_changes(self):
        book = self.make_book()

        book.isbn = "0-306-40615-2"
        book.save()
        book.refresh_from_db()

        self.assertEqual(book.isbn_normalized, "0306406152")

    def test_database_rejects_a_duplicate_normalized_isbn(self):
        self.make_book()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.make_book(isbn="978 84 376 0494 7")

    def test_selling_price_local_defaults_to_null(self):
        self.assertIsNone(self.make_book().selling_price_local)

    def test_full_clean_rejects_a_non_positive_cost(self):
        for cost in ("0", "-1.00"):
            with self.assertRaises(ValidationError):
                Book(**book_payload(cost_usd=cost)).full_clean()

    def test_full_clean_rejects_negative_stock(self):
        with self.assertRaises(ValidationError):
            Book(**book_payload(stock_quantity=-1)).full_clean()

    def test_full_clean_rejects_an_invalid_isbn(self):
        with self.assertRaises(ValidationError):
            Book(**book_payload(isbn="12345")).full_clean()

    def test_newest_book_is_listed_first(self):
        first = self.make_book()
        second = self.make_book(isbn="0306406152")

        self.assertEqual(list(Book.objects.all()), [second, first])
