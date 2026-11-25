"""HTTP behaviour of the Book CRUD, search and low-stock endpoints (S2, S3, S4, S7).

Every assertion goes through the public API so the tests stay implementation
agnostic (no direct ORM access).
"""

from rest_framework.test import APITestCase

from books.tests.utils import BOOKS_URL, BOOK_FIELDS, book_payload, isbn_for


class BookCreateTests(APITestCase):
    def test_create_returns_201_with_every_documented_field(self):
        response = self.client.post(BOOKS_URL, book_payload(), format="json")

        self.assertEqual(response.status_code, 201, response.content)
        body = response.json()
        self.assertEqual(set(body), BOOK_FIELDS)
        self.assertIsInstance(body["id"], int)
        self.assertEqual(body["title"], "El Quijote")
        self.assertEqual(body["author"], "Miguel de Cervantes")
        # The caller's formatting is preserved (S2 example keeps the hyphens).
        self.assertEqual(body["isbn"], "978-84-376-0494-7")
        # Numbers must be JSON numbers, not strings.
        self.assertIsInstance(body["cost_usd"], float)
        self.assertEqual(body["cost_usd"], 15.99)
        self.assertIsNone(body["selling_price_local"])
        self.assertIsInstance(body["stock_quantity"], int)
        self.assertEqual(body["stock_quantity"], 25)
        self.assertEqual(body["category"], "Literatura Clásica")
        self.assertEqual(body["supplier_country"], "ES")
        for key in ("created_at", "updated_at"):
            self.assertRegex(
                body[key], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$"
            )
        self.assertEqual(body["created_at"], body["updated_at"])

    def test_supplier_country_is_stored_uppercase(self):
        response = self.client.post(
            BOOKS_URL, book_payload(supplier_country="es"), format="json"
        )

        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["supplier_country"], "ES")

    def test_create_accepts_a_plain_thirteen_digit_isbn(self):
        response = self.client.post(
            BOOKS_URL, book_payload(isbn="9788437604947"), format="json"
        )

        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["isbn"], "9788437604947")

    def test_create_accepts_a_ten_digit_isbn(self):
        response = self.client.post(
            BOOKS_URL, book_payload(isbn="0-306-40615-2"), format="json"
        )

        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["isbn"], "0-306-40615-2")


class BookValidationTests(APITestCase):
    def assert_rejected(self, payload, field, message_fragment=None):
        """POST must fail with a DRF field-error body and store nothing."""
        response = self.client.post(BOOKS_URL, payload, format="json")

        self.assertEqual(response.status_code, 400, response.content)
        body = response.json()
        self.assertIn(field, body, body)
        self.assertIsInstance(body[field], list)
        self.assertTrue(body[field], "expected at least one error message")
        self.assertTrue(all(isinstance(item, str) for item in body[field]))
        if message_fragment is not None:
            self.assertIn(message_fragment.lower(), body[field][0].lower())
        # Rejected input must not be persisted.
        self.assertEqual(self.client.get(BOOKS_URL).json()["count"], 0)
        return body

    def test_cost_usd_zero_is_rejected(self):
        self.assert_rejected(book_payload(cost_usd="0"), "cost_usd", "greater than")

    def test_cost_usd_negative_is_rejected(self):
        self.assert_rejected(
            book_payload(cost_usd="-15.99"), "cost_usd", "greater than"
        )

    def test_stock_quantity_negative_is_rejected(self):
        self.assert_rejected(book_payload(stock_quantity=-1), "stock_quantity")

    def test_stock_quantity_must_be_a_number(self):
        self.assert_rejected(book_payload(stock_quantity="many"), "stock_quantity")

    def test_isbn_with_wrong_digit_count_is_rejected(self):
        self.assert_rejected(book_payload(isbn="12345"), "isbn", "10 or 13 digits")

    def test_isbn_with_twelve_digits_is_rejected(self):
        self.assert_rejected(book_payload(isbn="978843760494"), "isbn")

    def test_isbn_with_letters_is_rejected(self):
        self.assert_rejected(
            book_payload(isbn="978-84-376-0494-X"), "isbn", "10 or 13 digits"
        )

    def test_supplier_country_must_be_two_letters(self):
        self.assert_rejected(book_payload(supplier_country="ESP"), "supplier_country")

    def test_missing_title_is_rejected(self):
        payload = book_payload()
        payload.pop("title")
        self.assert_rejected(payload, "title")


class BookDuplicateIsbnTests(APITestCase):
    def test_duplicate_isbn_is_rejected(self):
        self.assertEqual(
            self.client.post(BOOKS_URL, book_payload(), format="json").status_code, 201
        )

        response = self.client.post(
            BOOKS_URL, book_payload(title="El Quijote (2nd ed.)"), format="json"
        )

        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("isbn", response.json())
        self.assertIn("exist", response.json()["isbn"][0].lower())
        self.assertEqual(self.client.get(BOOKS_URL).json()["count"], 1)

    def test_duplicate_isbn_collides_across_isbn_formatting(self):
        self.assertEqual(
            self.client.post(
                BOOKS_URL, book_payload(isbn="978-84-376-0494-7"), format="json"
            ).status_code,
            201,
        )

        for variant in ("9788437604947", "978 84 376 0494 7"):
            response = self.client.post(
                BOOKS_URL, book_payload(isbn=variant), format="json"
            )
            self.assertEqual(
                response.status_code, 400, f"{variant}: {response.content}"
            )
            self.assertIn("isbn", response.json())

        self.assertEqual(self.client.get(BOOKS_URL).json()["count"], 1)

    def test_update_to_an_existing_isbn_is_rejected(self):
        first = self.client.post(BOOKS_URL, book_payload(), format="json").json()
        second = self.client.post(
            BOOKS_URL, book_payload(isbn=isbn_for(1), title="Otro"), format="json"
        ).json()

        response = self.client.put(
            f"/books/{second['id']}",
            book_payload(isbn=first["isbn"], title="Otro"),
            format="json",
        )

        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("isbn", response.json())


class BookListTests(APITestCase):
    def create_books(self, count):
        ids = []
        for index in range(count):
            response = self.client.post(
                BOOKS_URL,
                book_payload(isbn=isbn_for(index), title=f"Book {index}"),
                format="json",
            )
            self.assertEqual(response.status_code, 201, response.content)
            ids.append(response.json()["id"])
        return ids

    def test_list_returns_the_paginated_envelope(self):
        self.create_books(3)

        response = self.client.get(BOOKS_URL)

        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertEqual(set(body), {"count", "next", "previous", "results"})
        self.assertEqual(body["count"], 3)
        self.assertEqual(len(body["results"]), 3)
        self.assertIsNone(body["next"])
        self.assertIsNone(body["previous"])
        self.assertEqual(set(body["results"][0]), BOOK_FIELDS)

    def test_list_is_paginated_with_the_default_page_size(self):
        self.create_books(12)

        body = self.client.get(BOOKS_URL).json()

        self.assertEqual(body["count"], 12)
        self.assertEqual(len(body["results"]), 10)
        self.assertIsNotNone(body["next"])

    def test_page_size_parameter_is_honoured(self):
        self.create_books(12)

        first_page = self.client.get(BOOKS_URL, {"page_size": 5}).json()
        second_page = self.client.get(BOOKS_URL, {"page_size": 5, "page": 2}).json()
        last_page = self.client.get(BOOKS_URL, {"page_size": 5, "page": 3}).json()

        self.assertEqual(first_page["count"], 12)
        self.assertEqual(len(first_page["results"]), 5)
        self.assertIsNotNone(first_page["next"])
        self.assertIsNone(first_page["previous"])
        self.assertEqual(len(second_page["results"]), 5)
        self.assertIsNotNone(second_page["previous"])
        self.assertEqual(len(last_page["results"]), 2)
        self.assertIsNone(last_page["next"])
        first_ids = {item["id"] for item in first_page["results"]}
        second_ids = {item["id"] for item in second_page["results"]}
        self.assertFalse(first_ids & second_ids)

    def test_documented_empty_page_parameter_returns_the_first_page(self):
        self.create_books(12)

        response = self.client.get(f"{BOOKS_URL}?page=&page_size=5")

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["count"], 12)
        self.assertEqual(len(response.json()["results"]), 5)

    def test_page_size_is_capped(self):
        self.create_books(12)

        body = self.client.get(BOOKS_URL, {"page_size": 1000}).json()

        self.assertEqual(body["count"], 12)
        self.assertEqual(len(body["results"]), 12)


class BookDetailTests(APITestCase):
    def setUp(self):
        response = self.client.post(BOOKS_URL, book_payload(), format="json")
        self.assertEqual(response.status_code, 201, response.content)
        self.book = response.json()
        self.detail_url = f"/books/{self.book['id']}"

    def test_retrieve_returns_the_book(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["isbn"], self.book["isbn"])

    def test_retrieve_unknown_id_returns_404(self):
        response = self.client.get("/books/999999")

        self.assertEqual(response.status_code, 404, response.content)

    def test_put_updates_the_book(self):
        payload = book_payload(
            title="El Quijote (2nd ed.)",
            cost_usd="20.00",
            stock_quantity=8,
            category="Clásicos",
        )

        response = self.client.put(self.detail_url, payload, format="json")

        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertEqual(body["id"], self.book["id"])
        self.assertEqual(body["title"], "El Quijote (2nd ed.)")
        self.assertEqual(body["cost_usd"], 20.00)
        self.assertEqual(body["stock_quantity"], 8)
        self.assertEqual(body["category"], "Clásicos")
        self.assertEqual(body["isbn"], self.book["isbn"])
        self.assertGreaterEqual(body["updated_at"], body["created_at"])
        # The update is persisted, not just echoed back.
        persisted = self.client.get(self.detail_url).json()
        self.assertEqual(persisted["title"], "El Quijote (2nd ed.)")
        self.assertEqual(persisted["cost_usd"], 20.00)

    def test_put_with_invalid_payload_returns_400_and_keeps_the_book(self):
        response = self.client.put(
            self.detail_url, book_payload(cost_usd="0"), format="json"
        )

        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("cost_usd", response.json())
        self.assertEqual(self.client.get(self.detail_url).json()["cost_usd"], 15.99)

    def test_put_unknown_id_returns_404(self):
        response = self.client.put("/books/999999", book_payload(), format="json")

        self.assertEqual(response.status_code, 404, response.content)

    def test_delete_returns_204_and_removes_the_book(self):
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, 204, response.content)
        self.assertEqual(self.client.get(self.detail_url).status_code, 404)
        self.assertEqual(self.client.get(BOOKS_URL).json()["count"], 0)

    def test_delete_unknown_id_returns_404(self):
        response = self.client.delete("/books/999999")

        self.assertEqual(response.status_code, 404, response.content)


class BookSearchTests(APITestCase):
    def setUp(self):
        fixtures = [
            ("El Quijote", "Literatura Clásica", 25, isbn_for(1)),
            ("La Celestina", "Literatura Clásica", 4, isbn_for(2)),
            ("Clean Code", "Tecnología", 12, isbn_for(3)),
        ]
        for title, category, stock, isbn in fixtures:
            response = self.client.post(
                BOOKS_URL,
                book_payload(
                    title=title, category=category, stock_quantity=stock, isbn=isbn
                ),
                format="json",
            )
            self.assertEqual(response.status_code, 201, response.content)

    def test_search_filters_by_category(self):
        response = self.client.get("/books/search", {"category": "Literatura Clásica"})

        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertEqual(set(body), {"count", "next", "previous", "results"})
        self.assertEqual(body["count"], 2)
        self.assertEqual(
            {item["category"] for item in body["results"]}, {"Literatura Clásica"}
        )

    def test_search_matches_category_ignoring_case(self):
        body = self.client.get(
            "/books/search", {"category": "literatura clásica"}
        ).json()

        self.assertEqual(body["count"], 2)

    def test_search_without_category_returns_every_book(self):
        body = self.client.get("/books/search").json()

        self.assertEqual(body["count"], 3)

    def test_search_with_unknown_category_returns_an_empty_page(self):
        body = self.client.get("/books/search", {"category": "Poesía"}).json()

        self.assertEqual(body["count"], 0)
        self.assertEqual(body["results"], [])


class BookLowStockTests(APITestCase):
    def setUp(self):
        for index, stock in enumerate((3, 10, 11)):
            response = self.client.post(
                BOOKS_URL,
                book_payload(stock_quantity=stock, isbn=isbn_for(index)),
                format="json",
            )
            self.assertEqual(response.status_code, 201, response.content)

    def test_threshold_is_inclusive(self):
        body = self.client.get("/books/low-stock", {"threshold": 10}).json()

        self.assertEqual(set(body), {"count", "next", "previous", "results"})
        self.assertEqual(body["count"], 2)
        self.assertEqual(
            sorted(item["stock_quantity"] for item in body["results"]), [3, 10]
        )

    def test_default_threshold_is_ten(self):
        body = self.client.get("/books/low-stock").json()

        self.assertEqual(body["count"], 2)

    def test_custom_threshold_selects_a_single_book(self):
        body = self.client.get("/books/low-stock", {"threshold": 5}).json()

        self.assertEqual(body["count"], 1)
        self.assertEqual(body["results"][0]["stock_quantity"], 3)

    def test_threshold_above_every_stock_returns_all_books(self):
        body = self.client.get("/books/low-stock", {"threshold": 50}).json()

        self.assertEqual(body["count"], 3)

    def test_non_numeric_threshold_is_rejected(self):
        response = self.client.get("/books/low-stock", {"threshold": "abc"})

        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("threshold", response.json())

    def test_negative_threshold_is_rejected(self):
        response = self.client.get("/books/low-stock", {"threshold": -1})

        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("threshold", response.json())
