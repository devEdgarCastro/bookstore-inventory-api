"""Pure rounding/margin arithmetic behind calculate-price (S5, S6)."""

from decimal import Decimal

from django.test import SimpleTestCase, override_settings

from books.services.pricing import calculate_price_breakdown


class PriceBreakdownTests(SimpleTestCase):
    def test_reproduces_the_s6_sample_exactly(self):
        result = calculate_price_breakdown(Decimal("15.99"), Decimal("0.85"))

        self.assertEqual(result["cost_local"], Decimal("13.59"))
        self.assertEqual(result["selling_price_local"], Decimal("19.03"))
        self.assertEqual(result["margin_percentage"], 40)
        self.assertIsInstance(result["margin_percentage"], int)

    def test_rounds_half_up_instead_of_half_even(self):
        # 2.49 * 0.50 = 1.245: ROUND_HALF_UP -> 1.25, ROUND_HALF_EVEN -> 1.24
        result = calculate_price_breakdown(Decimal("2.49"), Decimal("0.50"))

        self.assertEqual(result["cost_local"], Decimal("1.25"))
        self.assertEqual(result["selling_price_local"], Decimal("1.74"))

    def test_margin_is_applied_on_the_local_cost(self):
        result = calculate_price_breakdown(Decimal("100.00"), Decimal("1.00"))

        self.assertEqual(result["cost_local"], Decimal("100.00"))
        self.assertEqual(result["selling_price_local"], Decimal("140.00"))

    def test_values_are_quantized_to_two_decimals(self):
        result = calculate_price_breakdown(Decimal("7.77"), Decimal("0.3333"))

        self.assertEqual(result["cost_local"], Decimal("2.59"))
        self.assertEqual(result["selling_price_local"], Decimal("3.63"))
        self.assertEqual(result["cost_local"].as_tuple().exponent, -2)
        self.assertEqual(result["selling_price_local"].as_tuple().exponent, -2)

    @override_settings(PROFIT_MARGIN_PERCENTAGE=Decimal("25"))
    def test_margin_percentage_is_configurable(self):
        result = calculate_price_breakdown(Decimal("100.00"), Decimal("1.00"))

        self.assertEqual(result["margin_percentage"], 25)
        self.assertEqual(result["selling_price_local"], Decimal("125.00"))

    def test_explicit_margin_argument_wins_over_settings(self):
        result = calculate_price_breakdown(
            Decimal("100.00"), Decimal("1.00"), margin_percentage=10
        )

        self.assertEqual(result["margin_percentage"], 10)
        self.assertEqual(result["selling_price_local"], Decimal("110.00"))
