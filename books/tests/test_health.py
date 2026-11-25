"""Health endpoint and CORS wiring (S1)."""

from rest_framework.test import APITestCase


class HealthzTests(APITestCase):
    def test_healthz_returns_ok(self):
        response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_cors_allows_the_angular_dev_server_origin(self):
        response = self.client.get("/healthz", HTTP_ORIGIN="http://localhost:4200")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Access-Control-Allow-Origin"], "http://localhost:4200"
        )

    def test_cors_does_not_allow_unknown_origins(self):
        response = self.client.get("/healthz", HTTP_ORIGIN="http://evil.example")

        self.assertNotIn("Access-Control-Allow-Origin", response)
