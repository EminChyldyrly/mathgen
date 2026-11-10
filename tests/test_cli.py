import io
import os
import tempfile
import unittest

from mathgen import generate
from mathgen.cli import main


def run(argv, inputs=()):
    out = io.StringIO()
    it = iter(inputs)

    def fake_input(prompt=""):
        try:
            return next(it)
        except StopIteration:
            raise EOFError

    code = main(argv, input_fn=fake_input, out=out)
    return code, out.getvalue()


class TestCli(unittest.TestCase):
    def test_topics(self):
        code, out = run(["topics"])
        self.assertEqual(code, 0)
        self.assertIn("quadratic", out)
        self.assertEqual(len(out.strip().splitlines()), 7)

    def test_show(self):
        p = generate("linear", 2, 7)
        code, out = run(["show", p.id])
        self.assertEqual(code, 0)
        self.assertIn(p.text, out)
        self.assertNotIn("Ответ", out)
        code, out = run(["show", p.id, "--solution"])
        self.assertIn("Ответ: " + p.answer_text, out)
        code, out = run(["show", "bad/id"])
        self.assertEqual(code, 2)
        self.assertIn("неверный идентификатор", out)

    def test_check_exit_codes_and_negative_fraction(self):
        p = generate("linear", 3, 1)                       # x = −23/4
        self.assertEqual(p.answer_text, "x = −23/4")
        self.assertEqual(run(["check", p.id, "-23/4"])[0], 0)
        self.assertEqual(run(["check", p.id, "-5.75"])[0], 0)
        code, out = run(["check", p.id, "23/4"])
        self.assertEqual(code, 1)
        self.assertIn("Неверно", out)
        code, out = run(["check", p.id, "абв"])
        self.assertEqual(code, 1)
        self.assertIn("не удалось разобрать", out)
        self.assertEqual(run(["check", "nope", "1"])[0], 2)

    def test_worksheet_formats(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("a.md", "a.json", "a.pdf"):
                path = os.path.join(d, name)
                code, out = run(["worksheet", "--topics", "linear,system", "--levels", "1,2", "--count", "4",
                                 "--variants", "2", "--seed", "3", "--out", path])
                self.assertEqual(code, 0, out)
                self.assertGreater(os.path.getsize(path), 100)
            self.assertEqual(run(["worksheet", "--out", os.path.join(d, "a.txt")])[0], 2)
            with open(os.path.join(d, "a.md"), encoding="utf-8") as fh:
                self.assertIn("Вариант 2", fh.read())

    def test_worksheet_rejects_bad_args(self):
        for argv in (["worksheet", "--topics", "zzz"], ["worksheet", "--levels", "4"],
                     ["worksheet", "--levels", "a"]):
            with self.assertRaises(SystemExit):
                run(argv)

    def test_drill_scoring(self):
        from mathgen.worksheet import build_worksheet
        ws = build_worksheet(["linear"], [1], 3, 1, 0)
        answers = [ws.variants[0][0].answer_text,          # верно с первой попытки
                   "9999", ws.variants[0][1].answer_text,  # неверно, затем верно
                   ""]                                     # третью пропускаем
        code, out = run(["drill", "--topics", "linear", "--levels", "1", "--count", "3", "--seed", "0"], answers)
        self.assertEqual(code, 0)
        self.assertIn("Итог: 2 из 3.", out)
        self.assertIn("Повторить: " + ws.variants[0][2].id, out)
        self.assertEqual(out.count("Решение:"), 1)

    def test_drill_three_failures_show_solution(self):
        code, out = run(["drill", "--topics", "linear", "--levels", "1", "--count", "1"], ["1000", "2000", "3000"])
        self.assertIn("Итог: 0 из 1.", out)
        self.assertIn("Решение:", out)


if __name__ == "__main__":
    unittest.main()
