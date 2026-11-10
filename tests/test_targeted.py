"""Целевые тесты, добавленные по итогам мутационной проверки (scripts/mutate.py)."""
import re
import unittest
from fractions import Fraction as F

from mathgen import check, generate
from mathgen.check import _close

SEEDS = range(400)


class TestCoverage(unittest.TestCase):
    """Генераторы действительно используют заявленные диапазоны (знаки, величины)."""

    def test_linear_level2_ranges(self):
        ps = [generate("linear", 2, s) for s in SEEDS]
        self.assertTrue(any(p.answer < 0 for p in ps) and any(p.answer > 0 for p in ps))
        self.assertTrue(any(p.params["D"] < 0 for p in ps))
        self.assertTrue(any(p.params["C"] < 0 for p in ps) and any(p.params["C"] > 0 for p in ps))
        self.assertTrue(all(p.params["D"] != p.params["A"] for p in ps))

    def test_quadratic_level3_distribution_and_ranges(self):
        ps = [generate("quadratic", 3, s) for s in range(1500)]
        n = len(ps)
        share = lambda k: sum(len(p.answer) == k for p in ps) / n
        self.assertAlmostEqual(share(2), 4 / 9, delta=0.05)
        self.assertAlmostEqual(share(1), 2 / 9, delta=0.05)
        self.assertAlmostEqual(share(0), 3 / 9, delta=0.05)
        for a in (-2, -1, 1, 2, 3):
            self.assertTrue(any(p.params["a"] == a and len(p.answer) == 1 for p in ps), f"двойной корень при a={a}")
            self.assertTrue(any(p.params["a"] == a and len(p.answer) == 0 for p in ps), f"нет корней при a={a}")
        self.assertTrue(any(len(p.answer) == 1 and next(iter(p.answer)) < 0 for p in ps))
        self.assertTrue(any(len(p.answer) == 0 and p.params["b"] < 0 for p in ps))
        self.assertTrue(any(len(p.answer) == 0 and p.params["b"] > 0 for p in ps))

    def test_percent_level3_prices(self):
        for s in SEEDS:
            p = generate("percent", 3, s)
            P, up, down = (int(t) for t in re.findall(r"\d+", p.text)[:1] + re.findall(r"(\d+)%", p.text))
            self.assertEqual(P % 100, 0)
            self.assertGreaterEqual(P, 200)
            mid = F(P * (100 + up), 100)
            self.assertIn(f"{P} · {100 + up} ÷ 100 = {mid}", p.steps[0])       # шаг «после повышения»
            self.assertIn(f"{mid} · {100 - down} ÷ 100 = {p.answer}", p.steps[1])

    def test_system_level3_determinants_start_at_two(self):
        dets = set()
        for s in SEEDS:
            q = generate("system", 3, s).params
            dets.add(abs(q["a1"] * q["b2"] - q["a2"] * q["b1"]))
        self.assertIn(2, dets)
        self.assertNotIn(1, dets)
        self.assertNotIn(0, dets)

    def test_proportion_answers_are_integers_and_units(self):
        for s in SEEDS:
            for lv in (1, 2, 3):
                p = generate("proportion", lv, s)
                self.assertEqual(p.answer.denominator, 1)
                self.assertEqual(p.unit, "дн." if lv == 3 else "")

    def test_fractions_level3_first_step_matches_operation(self):
        for s in SEEDS:
            p = generate("fractions", 3, s)
            if "×" in p.text:
                self.assertTrue(p.steps[0].startswith("Сначала умножение"), p.id)
            else:
                self.assertTrue(p.steps[0].startswith("Сначала деление"), p.id)
                self.assertIn("обратную", p.steps[0])


class TestCheckEdges(unittest.TestCase):
    def test_close_boundaries(self):
        self.assertFalse(_close(F(5), F(5)))                 # равные — не «приближение»
        self.assertTrue(_close(F(101, 100), F(1)))           # ровно 1 % допустим
        self.assertFalse(_close(F(10101, 10000), F(1)))      # чуть больше 1 %
        self.assertTrue(_close(F(2999, 1000), F(3)))
        self.assertFalse(_close(F(35, 10), F(3)))

    def test_approx_message_only_for_decimal_input(self):
        p = generate("linear", 2, 0)
        a = p.answer
        near_dec = f"{float(a) + 0.001}"
        near_frac = f"{int((a + F(1, 1000)) * 1000)}/1000"
        far_dec = f"{float(a) + 5}"
        self.assertIn("округл", check(p, near_dec).message)
        self.assertEqual(check(p, near_frac).message, "Неверно.")
        self.assertEqual(check(p, far_dec).message, "Неверно.")

    def test_set_approx_message(self):
        p = generate("quadratic", 1, 3)                      # x² − 2x − 3 = 0: −1 и 3
        lo, hi = sorted(p.answer)
        self.assertIn("округл", check(p, f"{float(lo) + 0.001}; {hi}").message)
        self.assertEqual(check(p, f"{int(lo * 1000) + 1}/1000; {hi}").message, "Неверно.")
        self.assertEqual(check(p, f"{lo + 5}; {hi}").message, "Неверно.")
        self.assertEqual(check(p, f"{float(lo) + 0.001}; {hi + 7}").message, "Неверно.")

    def test_tuple_approx_message(self):
        p = generate("system", 3, 5)                         # 35/26, −77/39
        self.assertIn("округл", check(p, "1.35; -1.97").message)
        self.assertNotIn("округл", check(p, "1/3; -1.97").message)
        self.assertNotIn("округл", check(p, "1.35; 5").message)
        self.assertNotIn("округл", check(p, "7/5; -77/39").message)       # нет десятичных записей

    def test_indexed_labels(self):
        p = generate("system", 2, 7)                         # x = −7, y = 4
        r = check(p, "x1=-7, y1=4")
        self.assertEqual(r.status, "unparsed")               # раньше здесь было необработанное исключение
        self.assertTrue(check(p, "y=4, x=-7").correct)


if __name__ == "__main__":
    unittest.main()
