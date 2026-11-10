"""Независимая проверка генераторов: ответ проверяется по ТЕКСТУ задачи, а не по параметрам генератора."""
import re
import unittest
from fractions import Fraction as F

from mathgen import TOPICS, from_id, generate
from mathgen.fmt import expr, num, paren

SEEDS = range(250)


def ev(s, **env):
    """Вычислить выражение из текста задачи (дроби, ×, ÷, неявное умножение, x²)."""
    e = s.replace("−", "-")
    e = re.sub(r"(\d+)/(\d+)", r"F(\1,\2)", e)
    e = e.replace("÷", "/").replace("×", "*").replace("x²", "x**2")
    e = re.sub(r"(\d|\))(x|y|\()", r"\1*\2", e)
    return eval(e, {"__builtins__": {}}, {"F": F, **env})


def sides(text):
    lhs, rhs = text.split(": ", 1)[-1].split(" = ")
    return lhs, rhs


def ints(text):
    return [int(t) for t in re.findall(r"\d+", text)]


class TestEveryTopic(unittest.TestCase):
    def each(self):
        for t in TOPICS:
            for lv in (1, 2, 3):
                for s in SEEDS:
                    yield generate(t, lv, s)

    def test_deterministic_and_id_roundtrip(self):
        for t in TOPICS:
            for lv in (1, 2, 3):
                a, b = generate(t, lv, 42), generate(t, lv, 42)
                self.assertEqual((a.text, a.answer, a.steps), (b.text, b.answer, b.steps))
                self.assertEqual(from_id(a.id).text, a.text)
                self.assertEqual(a.id, f"{t}/{lv}/42")

    def test_seeds_give_variety(self):
        for t in TOPICS:
            for lv in (1, 2, 3):
                texts = {generate(t, lv, s).text for s in range(100)}
                self.assertGreater(len(texts), 40, (t, lv))

    def test_last_steps_show_answer(self):
        for p in self.each():
            self.assertTrue(p.steps[-1].startswith("Ответ: "), p.id)
            self.assertEqual(p.steps[-1], "Ответ: " + p.answer_text)
            if p.kind == "number":
                vals = [p.answer]
            elif p.kind == "set":
                vals = list(p.answer)
            else:
                vals = list(p.answer)
            if vals:
                calc = p.steps[-2]
                for v in vals:
                    self.assertIn(num(v), calc, (p.id, calc))

    def test_no_ascii_minus_before_digit(self):
        bad = re.compile(r"(?<![\w)])-\d|\+ −|− −|−0(?!\d)")
        for p in self.each():
            for s in (p.text,) + p.steps:
                self.assertIsNone(bad.search(s), (p.id, s))


class TestLinear(unittest.TestCase):
    def test_root_satisfies_equation_in_text(self):
        for lv in (1, 2, 3):
            for s in SEEDS:
                p = generate("linear", lv, s)
                lhs, rhs = sides(p.text)
                x = p.answer
                self.assertEqual(ev(lhs, x=x), ev(rhs, x=x), p.id)
                g = lambda v: ev(lhs, x=v) - ev(rhs, x=v)
                self.assertNotEqual(g(F(0)), g(F(1)), "уравнение должно иметь единственный корень")

    def test_levels(self):
        for s in SEEDS:
            self.assertEqual(generate("linear", 1, s).answer.denominator, 1)
            self.assertEqual(generate("linear", 2, s).answer.denominator, 1)
            self.assertGreater(generate("linear", 3, s).answer.denominator, 1)
            self.assertIn("(", generate("linear", 3, s).text)
            self.assertNotIn("(", generate("linear", 1, s).text)


class TestQuadratic(unittest.TestCase):
    def test_roots_from_text(self):
        seen = set()
        for lv in (1, 2, 3):
            for s in SEEDS:
                p = generate("quadratic", lv, s)
                lhs, rhs = sides(p.text)
                self.assertEqual(rhs, "0")
                g = lambda x: ev(lhs, x=x)
                a = (g(F(1)) + g(F(-1))) / 2 - g(F(0))
                b = (g(F(1)) - g(F(-1))) / 2
                c = g(F(0))
                self.assertNotEqual(a, 0)
                D = b * b - 4 * a * c
                n_real = 2 if D > 0 else 1 if D == 0 else 0
                self.assertEqual(len(p.answer), n_real, p.id)
                for r in p.answer:
                    self.assertEqual(g(r), 0, p.id)
                seen.add((lv, n_real))
        self.assertEqual(seen, {(1, 2), (2, 2), (3, 2), (3, 1), (3, 0)})

    def test_level_shapes(self):
        for s in SEEDS:
            self.assertTrue(generate("quadratic", 1, s).text.startswith("Решите уравнение: x²"))
            self.assertEqual(len(generate("quadratic", 1, s).answer), 2)
            self.assertFalse(generate("quadratic", 2, s).text.startswith("Решите уравнение: x²"))


class TestFractions(unittest.TestCase):
    def test_value_from_text(self):
        for lv in (1, 2, 3):
            for s in SEEDS:
                p = generate("fractions", lv, s)
                self.assertEqual(ev(p.text.split(": ", 1)[1]), p.answer, p.id)

    def test_level2_has_different_denominators(self):
        for s in SEEDS:
            t = generate("fractions", 2, s).text
            d1, d2 = re.findall(r"/(\d+)", t)
            self.assertNotEqual(d1, d2)


class TestSystem(unittest.TestCase):
    def test_solution_from_text(self):
        for lv in (1, 2, 3):
            for s in SEEDS:
                p = generate("system", lv, s)
                eqs = p.text.split("\n")[1:]
                self.assertEqual(len(eqs), 2)
                x, y = p.answer
                mat = []
                for eq in eqs:
                    lhs, rhs = eq.split(" = ")
                    self.assertEqual(ev(lhs, x=x, y=y), ev(rhs), p.id)
                    ax = ev(lhs, x=F(1), y=F(0)) - ev(lhs, x=F(0), y=F(0))
                    ay = ev(lhs, x=F(0), y=F(1)) - ev(lhs, x=F(0), y=F(0))
                    mat.append((ax, ay))
                det = mat[0][0] * mat[1][1] - mat[0][1] * mat[1][0]
                self.assertNotEqual(det, 0, "система должна иметь единственное решение")
                if lv == 3:
                    self.assertGreaterEqual(abs(det), 2)

    def test_integrality_by_level(self):
        for s in SEEDS:
            for lv in (1, 2):
                self.assertTrue(all(v.denominator == 1 for v in generate("system", lv, s).answer))
            self.assertTrue(any(v.denominator > 1 for v in generate("system", 3, s).answer))


class TestWordTopics(unittest.TestCase):
    def test_percent(self):
        for s in SEEDS:
            n = ints(generate("percent", 1, s).text)
            self.assertEqual(generate("percent", 1, s).answer, F(n[0] * n[1], 100))
            n = ints(generate("percent", 2, s).text)
            p = generate("percent", 2, s)
            self.assertEqual(p.answer, F(100 * n[0], n[1]))
            self.assertEqual(p.unit, "%")
            n = ints(generate("percent", 3, s).text)          # цена, +p%, −q%
            p = generate("percent", 3, s)
            self.assertEqual(p.answer, F(n[0] * (100 + n[1]) * (100 - n[2]), 10000))
            self.assertEqual(p.answer.denominator, 1)

    def test_proportion(self):
        for s in SEEDS:
            a, b, c = ints(generate("proportion", 1, s).text)
            self.assertEqual(generate("proportion", 1, s).answer * c, a * b)
            a, b, c = ints(generate("proportion", 2, s).text)
            self.assertEqual(a * c, generate("proportion", 2, s).answer * b)
            n, d, m = ints(generate("proportion", 3, s).text)
            ans = generate("proportion", 3, s).answer
            self.assertEqual(ans * m, n * d)
            self.assertEqual(ans.denominator, 1)
            self.assertNotEqual(m, n)

    def test_motion(self):
        for s in SEEDS:
            v, t = ints(generate("motion", 1, s).text)
            self.assertEqual(generate("motion", 1, s).answer, v * t)
            S, v1, v2 = ints(generate("motion", 2, s).text)
            self.assertEqual(generate("motion", 2, s).answer * (v1 + v2), S)
            v1, t0, v2 = ints(generate("motion", 3, s).text)
            self.assertGreater(v2, v1)
            self.assertEqual(generate("motion", 3, s).answer * (v2 - v1), v1 * t0)


class TestFormatting(unittest.TestCase):
    def test_num_and_expr(self):
        self.assertEqual(num(F(-3, 4)), "−3/4")
        self.assertEqual(num(F(6, 3)), "2")
        self.assertEqual(paren(-5), "(−5)")
        self.assertEqual(paren(5), "5")
        self.assertEqual(expr([(1, "x"), (-1, ""), (0, "y")]), "x − 1")
        self.assertEqual(expr([(-1, "x"), (2, "")]), "−x + 2")
        self.assertEqual(expr([(0, "x"), (0, "")]), "0")
        self.assertEqual(expr([(3, "x²"), (-4, "x"), (1, "")]), "3x² − 4x + 1")

    def test_bad_arguments(self):
        with self.assertRaises(ValueError):
            generate("nope", 1, 0)
        with self.assertRaises(ValueError):
            generate("linear", 4, 0)
        for bad in ["linear", "linear/1", "linear/x/1", "a/b/c/d"]:
            with self.assertRaises(ValueError):
                from_id(bad)


if __name__ == "__main__":
    unittest.main()
