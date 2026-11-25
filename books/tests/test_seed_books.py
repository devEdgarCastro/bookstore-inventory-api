"""The seed_books management command (deliverable 8)."""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from books.tests.utils import BOOKS_URL


class SeedBooksTests(TestCase):
    def seed(self):
        stdout = StringIO()
        call_command("seed_books", stdout=stdout)
        return stdout.getvalue()

    def catalogue(self):
        response = self.client.get(BOOKS_URL, {"page_size": 100})
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def test_seed_creates_a_varied_catalogue(self):
        output = self.seed()

        body = self.catalogue()
        self.assertEqual(body["count"], 12)
        self.assertTrue(output.strip(), "the command should report what it did")
        self.assertGreaterEqual(len({item["category"] for item in body["results"]}), 4)
        self.assertGreaterEqual(
            len({item["supplier_country"] for item in body["results"]}), 3
        )
        self.assertGreaterEqual(
            len({item["selling_price_local"] for item in body["results"]}), 2
        )

    def test_seed_is_idempotent(self):
        self.seed()
        self.seed()

        self.assertEqual(self.catalogue()["count"], 12)
