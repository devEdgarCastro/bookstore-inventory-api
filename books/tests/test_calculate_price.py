"""POST /books/{id}/calculate-price: S5 business flow, S6 shape, S7 FX fallback.

No test in this module reaches the network: the FX HTTP client is always mocked.
"""

from unittest.mock import Mock, patch

import requests
from django.test import override_settings
from rest_framework.test import APITestCase

from books.tests.utils import BOOKS_URL, PRICE_CALCULATION_FIELDS, book_payload

EXCHANGE_CLIENT = "books.services.exchange.requests.get"


def rate_response(rates, status_code=200):
    """Build a stand-in for the exchangerate-api JSON response."""
    response = Mock()
    response.status_code = status_code
    response.json.return_value = {
        "result": "success",
        "base_code": "USD",
        "rates": rates,
    }
    return response


class CalculatePriceTests(APITestCase):
    def setUp(self):
        response = self.client.post(
            BOOKS_URL, book_payload(cost_usd="15.99"), format="json"
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.book = response.json()
        self.url = f"/books/{self.book['id']}/calculate-price"
        self.detail_url = f"/books/{self.book['id']}"

    def assert_s6_body(self, body, source):
        self.assertEqual(set(body), PRICE_CALCULATION_FIELDS)
        self.assertEqual(body["book_id"], self.book["id"])
        self.assertAlmostEqual(body["cost_usd"], 15.99)
        self.assertAlmostEqual(body["exchange_rate"], 0.85)
        self.assertAlmostEqual(body["cost_local"], 13.59)
        self.assertAlmostEqual(body["selling_price_local"], 19.03)
        self.assertEqual(body["margin_percentage"], 40)
        self.assertIsInstance(body["margin_percentage"], int)
        self.assertEqual(body["currency"], "EUR")
        self.assertEqual(body["exchange_rate_source"], source)
        self.assertRegex(
            body["calculation_timestamp"],
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$",
        )

    def persisted_selling_price(self):
        return self.client.get(self.detail_url).json()["selling_price_local"]

    @patch(EXCHANGE_CLIENT)
    def test_success_matches_the_s6_sample_and_persists_the_price(self, mock_get):
        mock_get.return_value = rate_response({"EUR": 0.85})

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200, response.content)
        self.assert_s6_body(response.json(), "live")
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn("exchangerate-api.com", args[0])
        self.assertEqual(kwargs.get("timeout"), 5)
        # Step 4 of S5: the calculated price is persisted.
        self.assertAlmostEqual(self.persisted_selling_price(), 19.03)

    @patch(EXCHANGE_CLIENT)
    def test_only_post_is_allowed(self, mock_get):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertEqual(self.client.put(self.url, {}, format="json").status_code, 405)
        self.assertEqual(self.client.patch(self.url, {}, format="json").status_code, 405)
        self.assertEqual(self.client.delete(self.url).status_code, 405)
        mock_get.assert_not_called()

    @patch(EXCHANGE_CLIENT)
    def test_request_timeout_falls_back_to_the_default_rate(self, mock_get):
        mock_get.side_effect = requests.Timeout("timed out")

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200, response.content)
        self.assert_s6_body(response.json(), "fallback")
        self.assertAlmostEqual(self.persisted_selling_price(), 19.03)

    @patch(EXCHANGE_CLIENT)
    def test_connection_error_falls_back_to_the_default_rate(self, mock_get):
        mock_get.side_effect = requests.ConnectionError("fx service unreachable")

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200, response.content)
        self.assert_s6_body(response.json(), "fallback")

    @patch(EXCHANGE_CLIENT)
    def test_non_200_response_falls_back_to_the_default_rate(self, mock_get):
        mock_get.return_value = rate_response({"EUR": 1.2}, status_code=500)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200, response.content)
        self.assert_s6_body(response.json(), "fallback")

    @patch(EXCHANGE_CLIENT)
    def test_malformed_json_falls_back_to_the_default_rate(self, mock_get):
        response = Mock()
        response.status_code = 200
        response.json.side_effect = ValueError("Expecting value: line 1 column 1")
        mock_get.return_value = response

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200, response.content)
        self.assert_s6_body(response.json(), "fallback")

    @patch(EXCHANGE_CLIENT)
    def test_missing_currency_key_falls_back_to_the_default_rate(self, mock_get):
        mock_get.return_value = rate_response({"GBP": 1.27})

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200, response.content)
        self.assert_s6_body(response.json(), "fallback")

    @patch(EXCHANGE_CLIENT)
    @override_settings(EXCHANGE_FALLBACK_ENABLED=False)
    def test_unavailable_rate_with_fallback_disabled_returns_503(self, mock_get):
        mock_get.side_effect = requests.ConnectionError("fx service unreachable")

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 503, response.content)
        # Nothing was persisted on failure.
        self.assertIsNone(self.persisted_selling_price())

    @patch(EXCHANGE_CLIENT)
    @override_settings(EXCHANGE_FALLBACK_ENABLED=False)
    def test_fallback_disabled_but_live_rate_available_returns_200(self, mock_get):
        mock_get.return_value = rate_response({"EUR": 0.85})

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200, response.content)
        self.assert_s6_body(response.json(), "live")

    @patch(EXCHANGE_CLIENT)
    @override_settings(
        LOCAL_CURRENCY="COP",
        FALLBACK_EXCHANGE_RATE="4000.00",
        EXCHANGE_FALLBACK_ENABLED=True,
    )
    def test_currency_and_fallback_rate_are_configurable(self, mock_get):
        mock_get.side_effect = requests.Timeout("timed out")

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertEqual(body["currency"], "COP")
        self.assertEqual(body["exchange_rate_source"], "fallback")
        self.assertAlmostEqual(body["exchange_rate"], 4000.0)
        self.assertAlmostEqual(body["cost_local"], 63960.00)
        self.assertAlmostEqual(body["selling_price_local"], 89544.00)

    @patch(EXCHANGE_CLIENT)
    def test_unknown_book_returns_404_without_calling_the_fx_service(self, mock_get):
        response = self.client.post("/books/999999/calculate-price")

        self.assertEqual(response.status_code, 404, response.content)
        mock_get.assert_not_called()
