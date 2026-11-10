# mathgen

*[Русская версия](README.md)*

A problem generator and checker for school-level mathematics. Problems are created by topic and difficulty level, answers are checked **exactly** (with rational numbers, no rounding), and the problems are assembled into **PDF worksheets with several variants and an answer key**. The core uses only the Python standard library; `reportlab` is needed only for PDF output. Problem texts and output are in Russian.

## What it does

| Topic (`--topics`) | Level 1 | Level 2 | Level 3 |
|---|---|---|---|
| `linear` — linear equations | `ax + c = e` | `ax + c = dx + e`, integer root | with brackets, the root is a reduced fraction |
| `quadratic` — quadratic equations | `x² + bx + c = 0`, integer roots | `ax² + bx + c = 0` | also a double root and the "no real roots" case |
| `fractions` — common fractions | addition and subtraction, same denominator | different denominators (LCM) | `×`, `÷` and addition in one expression |
| `percent` — percentages | p% of N | what percent a is of b | price after an increase and a decrease |
| `system` — 2×2 systems | add/subtract the equations, integer solution | arbitrary coefficients, integer solution | fractional solution (Cramer's rule) |
| `proportion` — proportions | `x/a = b/c` | `a/x = b/c` | inverse proportionality (word problem) |
| `motion` — motion problems | `s = v·t` | approaching each other | "catches up" |

Every problem comes with a **step-by-step solution**, and the last step is always "Ответ: …" (the answer).

## Quick start

Python 3.10+ is required (tested on 3.13).

```bash
git clone https://github.com/EminChyldyrly/mathgen
cd mathgen
pip install reportlab          # only for PDF; .md and .json work without it

python -m mathgen worksheet --topics linear,quadratic --levels 1,2,3 --count 10 --variants 4 --seed 7 --out sheet.pdf
```

This produces a PDF with four variants of 10 problems each (levels rise from the first problem to the last, with no repeats within a variant or between variants), fields for name and date, space for the solution, and answer-key pages. A sample file: [`docs/example_sheet.pdf`](docs/example_sheet.pdf).

### Commands

```bash
python -m mathgen topics                                   # list topics
python -m mathgen show quadratic/3/3 --solution            # a problem by id and its solution
python -m mathgen check system/2/7 "x=-7; y=4"             # check an answer; exit code 0 means correct
python -m mathgen worksheet --out sheet.pdf --solutions    # full solutions in the key
python -m mathgen worksheet --out sheet.md                 # the same as Markdown (.json for your own programs)
python -m mathgen drill --topics fractions --levels 2 --count 5    # terminal drill
```

`worksheet` options: `--topics` (comma-separated or `all`), `--levels` (for example `1,2,3` or `2`), `--count` (problems per variant), `--variants`, `--seed`, `--title`, `--solutions`, `--no-key`.

## How an answer is checked

An answer is compared exactly: `3/4`, `0.75`, `0,75` and `6/8` are the same answer, while `0.33` instead of `1/3` is not (with a hint: "looks like a rounded value, an exact fraction is needed"). Accepted:

- fractions and decimals, mixed numbers separated by a space (`1 1/2`), an ordinary minus or "−";
- labels and units: `x = 5`, `5 ч`, `25%`;
- several values separated by `;`, the word "и"/"или" (and/or), a comma followed by a space, or a space; the order of roots does not matter, and `2,5` is one number (decimal comma);
- for systems, positionally (`-7; 4`) or with labels in any order (`y=4, x=-7`);
- "нет корней" (no roots) or `∅` when there really are no roots.

Feedback is specific: "not all roots found", "there are extra values", "the values are right but the order may be mixed up", "check y".

## Reproducibility

Every problem is defined by a string `topic/level/seed`, for example `linear/3/1`. The string is printed in the key, so a teacher can recreate any problem:

```python
from mathgen import from_id, check, generate, build_worksheet

p = from_id("linear/3/1")
print(p.text)               # problem text (in Russian)
print(p.steps)              # the solution steps
print(check(p, "-6/11"))    # Result(correct=..., status=..., message=...)

ws = build_worksheet(["linear", "system"], levels=[1, 2], count=6, variants=2, seed=1)
```

Seeds of individual problems are derived through SHA-256 rather than `hash()`, so a worksheet with the same `--seed` is identical on any machine and under any `PYTHONHASHSEED`.

## How quality is verified

The main risk of a project like this is a problem with a wrong answer in the key. So the tests (71, about 2.5 s) check the answer **independently of the generator**:

- for equations and systems, the test takes the **text** of the problem, evaluates both sides and substitutes the root; the coefficients are also recovered from the text to confirm that the solution is unique (system determinant ≠ 0, the discriminant determines the number of roots);
- for fractions, the expression from the text is evaluated again with `Fraction`;
- for word problems, the numbers are pulled out of the statement with a regular expression and the answer is recomputed by a formula;
- the reference answer typed on an ordinary keyboard (`-` instead of `−`) is accepted by the checker for each of ~5000 generated problems;
- solution steps contain the final values; the text and steps contain no `-3` instead of `−3`, no `+ −` and no "−0";
- a PDF is built, Cyrillic text and the "−" sign can be extracted back from it, and special characters (`& < >`) are escaped.

In addition, `python scripts/mutate.py` breaks the source one edit at a time (`+`↔`−`, `==`↔`!=`, `and`↔`or`, and so on) and checks that the tests notice. Results of the latest run are in [`docs/QUALITY.md`](docs/QUALITY.md): 229 mutations, 221 caught, 8 survived, all 8 equivalent to the original code. The first run (232 mutations, 200 caught) also found a real bug in answer checking, which was fixed.

```bash
python -m unittest discover -s tests
python scripts/mutate.py           # about 10 minutes
```

## Structure

```
mathgen/
  topics.py     topic generators and the registry (generate, from_id)
  problem.py    Problem: statement, exact answer, steps
  parse.py      parsing of answers typed by a person
  check.py      checking and feedback
  worksheet.py  building variants without repeats, export to Markdown/JSON
  pdf.py        PDF via reportlab (the DejaVu font is bundled in mathgen/fonts)
  cli.py        command line
tests/          unittest, no external dependencies
scripts/mutate.py   mutation testing of the tests
```

## Limitations

- Only what is in the topic table; there are no irrational numbers in answers (roots and discriminants are chosen so that `√D` is an integer), no inequalities and no graphs.
- Only the final answer is checked, not the learner's working.
- Word problems use a few fixed scenarios; variety comes from the numbers, not the wording.
- The difficulty levels were judged only by problem structure (integer or fractional answer, brackets, number of steps), not tested on real learners.
- The DejaVu font is distributed under its own free license (`mathgen/fonts/LICENSE-DejaVu.txt`).

## License

MIT, see [LICENSE](LICENSE).
