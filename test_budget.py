"""Run with: python3 -m unittest -v"""

import contextlib
import io
from pathlib import Path
import tempfile
import unittest

from budget import Budget, CATEGORIES, EVENTS, Event, Simulation, money, parse_money
from main import save_report, show_history


def sample_budget(funds=300000):
    return Budget(funds, 50000, dict(zip(CATEGORIES, (160000, 50000, 16000, 20000, 14000))))


class BudgetTests(unittest.TestCase):
    def test_decimal_input(self):
        self.assertEqual(parse_money(" 12.34 "), 1234)
        self.assertEqual(parse_money("0"), 0)
        for invalid in ("-1", "nan", "inf", "1.001", "hello", "", "1000001"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                parse_money(invalid)
        self.assertEqual(money(-1234), "-$12.34")

    def test_monthly_budget(self):
        budget = sample_budget()
        self.assertEqual(budget.total, 260000)
        self.assertEqual(budget.remaining, 40000)
        self.assertAlmostEqual(budget.percentage(budget.expenses["rent"]), 53.3333333)
        self.assertIsNone(sample_budget(0).percentage(100))

    def test_savings_are_not_income(self):
        sim = Simulation(sample_budget())
        total_before = sim.available + sim.savings
        sim.apply(Event("Repair", -25000), "savings", 10000)
        self.assertEqual(sim.available, 25000)
        self.assertEqual(sim.savings, 40000)
        self.assertEqual(sim.available + sim.savings, total_before - 25000)

    def test_reduction_is_limited_and_no_double_charge(self):
        sim = Simulation(sample_budget())
        sim.apply(Event("Dinner", -6000, True), "reduce", 6000)
        self.assertEqual(sim.available, 40000)
        self.assertEqual(sim.entertainment, 14000)
        before = sim.report()
        with self.assertRaises(ValueError):
            sim.apply(Event("Dinner", -6000, True), "reduce", 15000)
        self.assertEqual(sim.report(), before)

    def test_skip_only_optional_costs(self):
        sim = Simulation(sample_budget())
        sim.apply(Event("Dinner", -6000, True), "skip")
        self.assertEqual(sim.available, 40000)
        with self.assertRaises(ValueError):
            sim.apply(Event("Repair", -25000), "skip")

    def test_income_and_shortfall(self):
        sim = Simulation(sample_budget(260000))
        sim.apply(Event("Repair", -25000))
        self.assertEqual(sim.level, "BROKE")
        sim.apply(Event("Payment", 18000))
        self.assertEqual(sim.available, -7000)

    def test_level_boundaries(self):
        sim = Simulation(sample_budget(100000))
        for amount, expected in ((-1, "BROKE"), (0, "CAUTION"), (4999, "CAUTION"),
                                 (5000, "STABLE"), (19999, "STABLE"), (20000, "COMFORTABLE")):
            sim.available = amount
            self.assertEqual(sim.level, expected)
        zero = Simulation(Budget(0, 0, dict.fromkeys(CATEGORIES, 0)))
        self.assertEqual(zero.level, "CAUTION")

    def test_events_repeatable_and_distinct(self):
        sim = Simulation(sample_budget())
        self.assertEqual(sim.draw_events(42), sim.draw_events(42))
        self.assertEqual(len(set(sim.draw_events(42))), 4)

    def test_event_mix_has_choices_and_surprises(self):
        sim = Simulation(sample_budget())
        for seed in range(100):
            events = sim.draw_events(seed)
            self.assertEqual(len(set(events)), 4)
            self.assertTrue(any(event.optional for event in events))
            self.assertTrue(any(event.amount > 0 for event in events))
            self.assertTrue(any(event.amount < 0 and not event.optional for event in events))

    def test_alternative_charges_only_alternative_cost(self):
        for event in EVENTS:
            if not event.alternative:
                continue
            with self.subTest(event=event.title):
                sim = Simulation(sample_budget())
                sim.apply(event, "alternative")
                self.assertEqual(sim.available, 40000 - event.alternative_cost)
                self.assertEqual(sim.savings, 50000)
                self.assertEqual(sim.entertainment, 20000)
                self.assertEqual(sim.history[-1]["applied_cents"], -event.alternative_cost)
                self.assertEqual(sim.history[-1]["decision"], event.alternative)

    def test_invalid_alternative_leaves_balances_unchanged(self):
        sim = Simulation(sample_budget())
        before = sim.report()
        with self.assertRaises(ValueError):
            sim.apply(Event("A bill", -5000), "alternative")
        with self.assertRaises(ValueError):
            sim.apply(EVENTS[1], "alternative", 100)
        self.assertEqual(sim.report(), before)

    def test_save_history_and_corrupt_records(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "history.jsonl"
            save_report(Simulation(sample_budget()), path)
            with path.open("a", encoding="utf-8") as handle:
                handle.write('broken json\n[]\n{"final_available_cents": "bad"}\n')
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                show_history(path)
            self.assertIn("STABLE", output.getvalue())
            self.assertEqual(output.getvalue().count("Skipped"), 3)


if __name__ == "__main__":
    unittest.main()
