import unittest
from fractions import Fraction as F

from mathgen.parse import ParseError, parse_list, parse_number


class TestNumber(unittest.TestCase):
    def test_forms(self):
        cases = {"3": F(3), "-3": F(-3), "+3": F(3), "−3": F(-3), "3/4": F(3, 4), "-3/4": F(-3, 4),
                 "3 / 4": F(3, 4), "6/8": F(3, 4), "0.75": F(3, 4), "0,75": F(3, 4), ".5": F(1, 2),
                 "2.": F(2), "1 1/2": F(3, 2), "-1 1/2": F(-3, 2), "x = 5": F(5), "x=-2": F(-2),
                 "5 ч": F(5), "630 км": F(630), "25%": F(25), "2688 руб.": F(2688), "  7  ": F(7),
                 "x = 9 дн.": F(9), "7/-2": F(-7, 2)}
        for s, v in cases.items():
            with self.subTest(s):
                self.assertEqual(parse_number(s)[0], v)

    def test_decimal_flag(self):
        self.assertTrue(parse_number("0,5")[1])
        self.assertTrue(parse_number("0.5")[1])
        self.assertFalse(parse_number("1/2")[1])
        self.assertFalse(parse_number("5")[1])

    def test_errors(self):
        for s in ["", "   ", "abc", "1/0", "1 1/0", "--3", "3/", "/3", "1.2.3", "x ="]:
            with self.subTest(s):
                with self.assertRaises(ParseError):
                    parse_number(s)

    def test_error_messages(self):
        with self.assertRaisesRegex(ParseError, "пустой"):
            parse_number("  ")
        with self.assertRaisesRegex(ParseError, "не удалось разобрать «абв»"):
            parse_number("абв")

    def test_mixed_sign_applies_to_whole(self):
        self.assertEqual(parse_number("-2 3/4")[0], F(-11, 4))


class TestList(unittest.TestCase):
    def vals(self, s):
        return [v for _, v, _ in parse_list(s)]

    def test_separators(self):
        for s in ["2; 3", "2;3", "2, 3", "2 3", "2 и 3", "2 или 3", "(2; 3)", "{2, 3}", "[2; 3]", "x=2, x=3",
                  "x1 = 2; x2 = 3", "x₁=2, x₂=3", "x = 2 или x = 3", "x=2,x=3"]:
            with self.subTest(s):
                self.assertEqual(self.vals(s), [F(2), F(3)])

    def test_decimal_comma_is_one_number(self):
        self.assertEqual(self.vals("2,5"), [F(5, 2)])
        self.assertEqual(self.vals("2,5; 1,5"), [F(5, 2), F(3, 2)])

    def test_fractions_and_negatives(self):
        self.assertEqual(self.vals("-1/2; 3/4"), [F(-1, 2), F(3, 4)])
        self.assertEqual(self.vals("x = −1/2, y = 3 / 4"), [F(-1, 2), F(3, 4)])
        self.assertEqual(self.vals("−2 3"), [F(-2), F(3)])

    def test_labels(self):
        self.assertEqual([l for l, _, _ in parse_list("x = 2, y = 3")], ["x", "y"])
        self.assertEqual([l for l, _, _ in parse_list("2; 3")], [None, None])

    def test_mixed_number_not_split(self):
        self.assertEqual(self.vals("1 1/2"), [F(3, 2)])

    def test_empty_set(self):
        for s in ["нет корней", "Нет", "корней нет", "действительных корней нет", "∅", "{}", "пусто",
                  "нет решений"]:
            with self.subTest(s):
                self.assertEqual(parse_list(s), [])

    def test_errors(self):
        for s in ["", "  ", "a; b", "2; ; x"]:
            with self.subTest(s):
                with self.assertRaises(ParseError):
                    parse_list(s)


if __name__ == "__main__":
    unittest.main()
