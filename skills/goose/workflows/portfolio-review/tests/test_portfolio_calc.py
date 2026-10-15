"""Synthetic fixtures only; no live security, account or personal data."""
import copy
from decimal import Decimal
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "portfolio_calc.py"
SPEC = importlib.util.spec_from_file_location("portfolio_calc", SCRIPT)
calc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(calc)


def fixture():
    return {"base_currency": "KRW", "as_of": "2026-10-16T09:00:00+09:00", "coverage": "partial",
            "max_price_age_days": 3,
            "holdings": [{"id": "synthetic-a", "ticker": "SYNTH-A", "market": "FICTIONAL",
                          "quantity": "10", "average_cost": "100", "cost_currency": "KRW",
                          "current_price": "120", "price_currency": "KRW",
                          "price_as_of": "2026-10-15T09:00:00+09:00", "price_source": "synthetic test fixture",
                          "issuer_id": "fictional-issuer", "sector": "fictional-sector"}],
            "cash": [{"id": "cash-krw", "currency": "KRW", "amount": "300"}]}


class PortfolioTests(unittest.TestCase):
    def test_profit_and_cash_weight(self):
        result = calc.calculate(fixture())
        self.assertEqual(result["totals"]["market_value_base"], "1500.000000")
        self.assertEqual(result["totals"]["unrealized_pnl_base"], "200.000000")
        self.assertEqual(result["totals"]["unrealized_pnl_percent"], "20.000000")
        self.assertEqual(result["holdings"][0]["allocation_percent"], "80.000000")
        self.assertEqual(result["cash"][0]["allocation_percent"], "20.000000")
        self.assertFalse(result["coverage"]["independently_verified_complete_wealth"])

    def test_loss(self):
        data = fixture()
        data["holdings"][0]["current_price"] = "80"
        self.assertEqual(calc.calculate(data)["totals"]["unrealized_pnl_base"], "-200.000000")

    def test_fx_snapshot_conversion(self):
        data = fixture()
        data["holdings"][0].update(cost_currency="USD", price_currency="USD")
        data["fx_rates"] = [{"currency": "USD", "rate_to_base": "1300", "as_of": "2026-10-15",
                             "source": "synthetic FX fixture", "verified": True}]
        result = calc.calculate(data)
        self.assertEqual(result["totals"]["cost_basis_base"], "1300000.000000")
        self.assertEqual(result["totals"]["unrealized_pnl_base"], "260000.000000")

    def test_missing_price_is_not_zero(self):
        data = fixture()
        data["holdings"][0]["current_price"] = None
        result = calc.calculate(data)
        self.assertIsNone(result["totals"]["market_value_base"])
        self.assertEqual(result["totals"]["known_market_value_subtotal_base"], "300.000000")
        self.assertIsNone(result["cash"][0]["allocation_percent"])
        self.assertEqual(result["cash"][0]["known_subset_allocation_percent"], "100.000000")
        self.assertIsNone(result["holdings"][0]["unrealized_pnl_base"])

    def test_missing_fx_is_not_assumed(self):
        data = fixture()
        data["holdings"][0]["price_currency"] = "USD"
        result = calc.calculate(data)
        self.assertIn("missing_fx:USD", result["warnings"])
        self.assertFalse(result["coverage"]["valuation_complete_for_submitted_assets"])

    def test_missing_cost_fx_suppresses_total_pnl(self):
        data = fixture()
        data["holdings"][0]["cost_currency"] = "USD"
        result = calc.calculate(data)
        self.assertTrue(result["coverage"]["valuation_complete_for_submitted_assets"])
        self.assertIsNone(result["totals"]["unrealized_pnl_base"])

    def test_zero_cost_denominator_and_explicit_zero_price(self):
        data = fixture()
        data["holdings"][0]["average_cost"] = "0"
        self.assertIsNone(calc.calculate(data)["totals"]["unrealized_pnl_percent"])
        data["holdings"][0].update(average_cost="100", current_price="0")
        self.assertEqual(calc.calculate(data)["totals"]["unrealized_pnl_percent"], "-100.000000")

    def test_reject_invalid_numbers(self):
        for value in ("-1", "NaN", "Infinity", True):
            with self.subTest(value=value):
                data = fixture()
                data["holdings"][0]["quantity"] = value
                with self.assertRaises(calc.InputError):
                    calc.calculate(data)

    def test_duplicate_listings_and_ids(self):
        for same_id in (True, False):
            data = fixture()
            twin = copy.deepcopy(data["holdings"][0])
            if not same_id:
                twin["id"] = "another-id"
            data["holdings"].append(twin)
            with self.assertRaises(calc.InputError):
                calc.calculate(data)

    def test_same_issuer_aggregates_across_listings(self):
        data = fixture()
        twin = copy.deepcopy(data["holdings"][0])
        twin.update(id="synthetic-b", ticker="SYNTH-B")
        data["holdings"].append(twin)
        groups = calc.calculate(data)["issuer_concentration"]["groups"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["market_value_base"], "2400.000000")

    def test_unknown_issuer_is_not_invented(self):
        data = fixture()
        del data["holdings"][0]["issuer_id"]
        concentration = calc.calculate(data)["issuer_concentration"]
        self.assertFalse(concentration["mapping_complete"])
        self.assertEqual(concentration["groups"], [])

    def test_future_price_rejected(self):
        data = fixture()
        data["holdings"][0]["price_as_of"] = "2026-10-17"
        with self.assertRaises(calc.InputError):
            calc.calculate(data)

    def test_unverified_fx_rejected(self):
        data = fixture()
        data["fx_rates"] = [{"currency": "USD", "rate_to_base": 1300,
                             "as_of": "2026-10-15", "source": "synthetic FX"}]
        with self.assertRaises(calc.InputError):
            calc.calculate(data)

    def test_stale_price_blocks_scenario(self):
        data = fixture()
        data["holdings"][0]["price_as_of"] = "2026-10-01"
        data["targets"] = [{"id": "synthetic-a", "weight_percent": 60}, {"id": "cash-krw", "weight_percent": 40}]
        result = calc.calculate(data)
        self.assertEqual(result["holdings"][0]["price_freshness"], "stale")
        self.assertEqual(result["rebalance"]["status"], "blocked")

    def test_no_threshold_does_not_claim_fresh(self):
        data = fixture()
        del data["max_price_age_days"]
        self.assertEqual(calc.calculate(data)["holdings"][0]["price_freshness"], "not_assessed")

    def test_targets_required_complete_and_exact_sum(self):
        for targets in ([{"id": "synthetic-a", "weight_percent": 100}],
                        [{"id": "synthetic-a", "weight_percent": 50}, {"id": "cash-krw", "weight_percent": 30}]):
            data = fixture()
            data["targets"] = targets
            with self.assertRaises(calc.InputError):
                calc.calculate(data)

    def test_scenario_rounding_and_cost_cash(self):
        data = fixture()
        data["targets"] = [{"id": "synthetic-a", "weight_percent": 100}, {"id": "cash-krw", "weight_percent": 0}]
        result = calc.calculate(data)["rebalance"]
        self.assertEqual(result["holdings"][0]["estimated_whole_share_delta"], "2.000000")
        self.assertEqual(result["cash_after_sells_and_buys_before_costs_base"], "60.000000")
        self.assertIsNone(result["cash_feasible_after_estimated_costs"])
        data["estimated_cost_base"] = 70
        result = calc.calculate(data)["rebalance"]
        self.assertFalse(result["cash_feasible_after_estimated_costs"])

    def test_missing_price_blocks_scenario(self):
        data = fixture()
        data["holdings"][0]["current_price"] = None
        data["targets"] = [{"id": "synthetic-a", "weight_percent": 60}, {"id": "cash-krw", "weight_percent": 40}]
        self.assertIn("incomplete_valuation", calc.calculate(data)["rebalance"]["reasons"])

    def test_fractional_share_sales_do_not_oversell(self):
        data = fixture()
        data["holdings"][0]["quantity"] = "0.8"
        data["targets"] = [{"id": "synthetic-a", "weight_percent": 0}, {"id": "cash-krw", "weight_percent": 100}]
        result = calc.calculate(data)["rebalance"]
        self.assertEqual(Decimal(result["holdings"][0]["estimated_whole_share_delta"]), 0)

    def test_decimal_math_and_empty_cash(self):
        data = fixture()
        data["cash"] = []
        data["holdings"][0].update(quantity="3", average_cost="0.1", current_price="0.2")
        self.assertEqual(calc.calculate(data)["totals"]["unrealized_pnl_base"], "0.300000")

    def test_cash_only_zero_value_has_no_weights(self):
        data = fixture()
        data["holdings"] = []
        data["cash"][0]["amount"] = "0"
        result = calc.calculate(data)
        self.assertIsNone(result["cash"][0]["allocation_percent"])
        self.assertIsNone(result["totals"]["unrealized_pnl_percent"])


if __name__ == "__main__":
    unittest.main()
