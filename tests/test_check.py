import unittest
from fractions import Fraction as F

from mathgen import TOPICS, check, generate
from mathgen.fmt import num


def ascii_answer(p):
    """Ответ так, как его набирает человек на обычной клавиатуре."""
    return p.answer_text.replace("−", "-")


class TestRoundTrip(unittest.TestCase):
    def test_reference_answer_always_accepted(self):
        for t in TOPICS:
            for lv in (1, 2, 3):
                for s in range(150):
                    p = generate(t, lv, s)
                    for text in (p.answer_text, ascii_answer(p)):
                        r = check(p, text)
                        self.assertTrue(r.correct, (p.id, text, r))

    def test_wrong_number_rejected(self):
        for t in ("linear", "fractions", "percent", "proportion", "motion"):
            for s in range(100):
                p = generate(t, 2, s)
                for delta in (F(1), F(-1), F(1, 7)):
                    self.assertFalse(check(p, num(p.answer + delta)).correct, p.id)

    def test_unit_and_decimal_forms(self):
        p = generate("motion", 1, 3)
        self.assertTrue(check(p, f"{p.answer} км").correct)
        self.assertTrue(check(p, f"{p.answer}.0").correct)
        self.assertFalse(check(p, f"{p.answer + 1} км").correct)


class TestMessages(unittest.TestCase):
    def test_unparsed(self):
        p = generate("linear", 1, 1)
        for bad in ["", "abc", "1/0", "2; 3"]:
            r = check(p, bad)
            self.assertEqual((r.correct, r.status), (False, "unparsed"), bad)

    def test_approximate_decimal_is_flagged_not_accepted(self):
        p = next(q for q in (generate("linear", 3, s) for s in range(500)) if q.answer.denominator == 3)
        approx = f"{float(p.answer):.2f}"
        r = check(p, approx)
        self.assertFalse(r.correct)
        self.assertIn("округл", r.message)
        # а точная десятичная запись принимается
        q = next(q for q in (generate("linear", 3, s) for s in range(500)) if q.answer.denominator in (2, 4, 5))
        self.assertTrue(check(q, str(float(q.answer))).correct)

    def test_set_messages(self):
        p = next(q for q in (generate("quadratic", 1, s) for s in range(50)))
        a, b = sorted(p.answer)
        self.assertTrue(check(p, f"{num(b)}; {num(a)}").correct)             # порядок не важен
        self.assertTrue(check(p, f"{num(a)} и {num(b)}").correct)
        self.assertIn("не все", check(p, num(a)).message)
        self.assertIn("лишние", check(p, f"{num(a)}; {num(b)}; 100").message)
        self.assertFalse(check(p, f"{num(a)}; {num(b + 1)}").correct)
        self.assertIn("корни у уравнения есть", check(p, "нет корней").message)

    def test_no_roots(self):
        p = next(q for q in (generate("quadratic", 3, s) for s in range(100)) if not q.answer)
        self.assertTrue(check(p, "нет корней").correct)
        self.assertTrue(check(p, "∅").correct)
        r = check(p, "1")
        self.assertFalse(r.correct)
        self.assertIn("корней нет", r.message)

    def test_double_root(self):
        p = next(q for q in (generate("quadratic", 3, s) for s in range(200)) if len(q.answer) == 1)
        (r,) = p.answer
        self.assertTrue(check(p, num(r)).correct)
        self.assertTrue(check(p, f"{num(r)}; {num(r)}").correct)
        self.assertFalse(check(p, "нет корней").correct)

    def test_tuple_forms(self):
        p = generate("system", 2, 7)               # x = −7, y = 4
        self.assertEqual(p.answer, (F(-7), F(4)))
        for ok in ["-7; 4", "(-7; 4)", "-7, 4", "-7 4", "x=-7, y=4", "y=4; x=-7", "x = −7 y = 4"]:
            self.assertTrue(check(p, ok).correct, ok)
        r = check(p, "4; -7")
        self.assertFalse(r.correct)
        self.assertIn("порядок", r.message)
        r = check(p, "-7; 5")
        self.assertFalse(r.correct)
        self.assertIn("y", r.message)
        self.assertNotIn("x", r.message.split("проверьте")[-1])
        self.assertEqual(check(p, "-7").status, "unparsed")
        self.assertEqual(check(p, "a=1; b=2").status, "unparsed")
        self.assertFalse(check(p, "y=-7; x=4").correct)       # подписи важнее порядка

    def test_tuple_fractions(self):
        p = generate("system", 3, 5)               # x = 35/26, y = −77/39
        self.assertTrue(check(p, "35/26; -77/39").correct)
        self.assertFalse(check(p, f"{float(p.answer[0]):.3f}; -77/39").correct)   # округление не принимается
        self.assertFalse(check(p, "1,35; -1,97").correct)


if __name__ == "__main__":
    unittest.main()
