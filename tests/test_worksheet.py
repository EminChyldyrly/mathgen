import json
import os
import shutil
import subprocess
import tempfile
import unittest

from mathgen import TOPICS, build_worksheet, from_id, to_json, to_markdown
from mathgen.worksheet import problem_seed

try:
    import reportlab  # noqa: F401
    HAVE_PDF = True
except ImportError:                                           # pragma: no cover
    HAVE_PDF = False


class TestBuild(unittest.TestCase):
    def test_shape_and_ramp(self):
        ws = build_worksheet(["linear", "fractions"], [1, 2, 3], count=12, variants=3, seed=1)
        self.assertEqual(len(ws.variants), 3)
        for probs in ws.variants:
            self.assertEqual(len(probs), 12)
            levels = [p.level for p in probs]
            self.assertEqual(levels, sorted(levels))
            self.assertEqual(set(levels), {1, 2, 3})
            self.assertEqual([p.topic for p in probs], ["linear", "fractions"] * 6)

    def test_single_level_and_topics_rotation(self):
        ws = build_worksheet(list(TOPICS), [2], count=14, seed=3)
        self.assertTrue(all(p.level == 2 for p in ws.variants[0]))
        self.assertEqual([p.topic for p in ws.variants[0]], list(TOPICS) * 2)

    def test_no_duplicates_anywhere(self):
        ws = build_worksheet(["percent", "proportion"], [1], count=15, variants=6, seed=9)
        texts = [p.text for probs in ws.variants for p in probs]
        self.assertEqual(len(texts), len(set(texts)))

    def test_reproducible_and_seed_sensitive(self):
        a = build_worksheet(["linear"], [1, 2], 6, 2, seed=5)
        b = build_worksheet(["linear"], [1, 2], 6, 2, seed=5)
        c = build_worksheet(["linear"], [1, 2], 6, 2, seed=6)
        self.assertEqual([[p.id for p in v] for v in a.variants], [[p.id for p in v] for v in b.variants])
        self.assertNotEqual([[p.id for p in v] for v in a.variants], [[p.id for p in v] for v in c.variants])
        self.assertNotEqual({p.id for p in a.variants[0]}, {p.id for p in a.variants[1]})

    def test_problem_seed_is_stable_across_runs(self):
        # sha256-производный seed не должен зависеть от PYTHONHASHSEED
        out = subprocess.run(["python3", "-c", "from mathgen.worksheet import problem_seed;print(problem_seed(5,1,2,3))"],
                             capture_output=True, text=True, env={**os.environ, "PYTHONHASHSEED": "123"},
                             cwd=os.path.dirname(os.path.dirname(__file__))).stdout.strip()
        self.assertEqual(int(out), problem_seed(5, 1, 2, 3))

    def test_ids_recreate_problems(self):
        ws = build_worksheet(list(TOPICS), [1, 2, 3], 10, 2, seed=4)
        for probs in ws.variants:
            for p in probs:
                q = from_id(p.id)
                self.assertEqual((q.text, q.answer), (p.text, p.answer))

    def test_errors(self):
        with self.assertRaises(ValueError):
            build_worksheet(["nope"], [1], 3)
        with self.assertRaises(ValueError):
            build_worksheet([], [1], 3)
        with self.assertRaises(ValueError):
            build_worksheet(["linear"], [1], 0)
        with self.assertRaises(ValueError):
            build_worksheet(["linear"], [1], 3, variants=0)

    def test_impossible_uniqueness_reports_clearly(self):
        # у mоtion уровня 1 всего несколько сотен различных условий — сотни тысяч задач их исчерпают
        with self.assertRaises(RuntimeError):
            build_worksheet(["proportion"], [1], count=800, variants=1, seed=0)

    def test_title(self):
        self.assertEqual(build_worksheet(["linear"], [1], 1).title, "Математика: линейные уравнения")
        self.assertEqual(build_worksheet(list(TOPICS), [1], 7).title, "Математика: смешанный листок")
        self.assertEqual(build_worksheet(["linear"], [1], 1, title="Т").title, "Т")


class TestExport(unittest.TestCase):
    def setUp(self):
        self.ws = build_worksheet(["system", "linear"], [1, 2], 4, 2, seed=2)

    def test_markdown(self):
        md = to_markdown(self.ws, solutions=True)
        self.assertIn("## Вариант 2", md)
        self.assertIn("# Ключ", md)
        self.assertIn(self.ws.variants[0][0].id, md)
        self.assertIn("Делим на", md)
        self.assertNotIn("# Ключ", to_markdown(self.ws, key=False))
        first = self.ws.variants[0][0]
        self.assertIn(first.answer_text, md)

    def test_json(self):
        data = json.loads(to_json(self.ws))
        self.assertEqual(len(data["variants"]), 2)
        p = data["variants"][0][0]
        self.assertEqual(p["answer"], self.ws.variants[0][0].answer_text)
        self.assertEqual(p["steps"][-1], "Ответ: " + p["answer"])

    @unittest.skipUnless(HAVE_PDF, "нет reportlab")
    def test_pdf_written_and_contains_cyrillic(self):
        from mathgen.pdf import write_pdf
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "w.pdf")
            write_pdf(self.ws, path)
            with open(path, "rb") as fh:
                data = fh.read()
            self.assertTrue(data.startswith(b"%PDF"))
            self.assertGreater(len(data), 5000)
            if shutil.which("pdftotext"):
                text = subprocess.run(["pdftotext", path, "-"], capture_output=True, text=True).stdout
                self.assertIn("Вариант 2", text)
                self.assertIn("Ключ — вариант 1", text)
                self.assertIn("−", "".join(p.text for v in self.ws.variants for p in v) + "−")
                for p in self.ws.variants[1]:
                    self.assertIn(p.text.split("\n")[0][:25], text)
                self.assertIn(self.ws.variants[0][0].id, text)

    @unittest.skipUnless(HAVE_PDF, "нет reportlab")
    def test_pdf_without_key_and_with_solutions(self):
        from mathgen.pdf import write_pdf
        with tempfile.TemporaryDirectory() as d:
            a, b, c = (os.path.join(d, n) for n in "abc")
            write_pdf(self.ws, a, key=False)
            write_pdf(self.ws, b, key=True)
            write_pdf(self.ws, c, key=True, solutions=True)
            sa, sb, sc = (os.path.getsize(x) for x in (a, b, c))
            self.assertLess(sa, sb)
            self.assertLess(sb, sc)
            if shutil.which("pdftotext"):
                t = lambda x: subprocess.run(["pdftotext", x, "-"], capture_output=True, text=True).stdout
                self.assertNotIn("Ключ", t(a))
                self.assertIn("Делим на", t(c))
                self.assertNotIn("Делим на", t(b))

    @unittest.skipUnless(HAVE_PDF, "нет reportlab")
    def test_special_characters_are_escaped(self):
        from mathgen.pdf import write_pdf
        ws = build_worksheet(["linear"], [1], 1, title="A & B <i>x</i>")
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "e.pdf")
            write_pdf(ws, path)
            if shutil.which("pdftotext"):
                text = subprocess.run(["pdftotext", path, "-"], capture_output=True, text=True).stdout
                self.assertIn("A & B <i>x</i>", text)


if __name__ == "__main__":
    unittest.main()
