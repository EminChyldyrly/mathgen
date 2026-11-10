"""Мутационная проверка тестов: ломаем исходники по одной правке и смотрим, замечает ли это набор тестов.

    python scripts/mutate.py            # все мутации
Выживший мутант = дыра в тестах (или эквивалентная правка, которую надо разобрать вручную).
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ["mathgen/topics.py", "mathgen/check.py", "mathgen/parse.py", "mathgen/worksheet.py", "mathgen/fmt.py"]
SWAPS = [("+", "-"), ("-", "+"), ("*", "//"), (" == ", " != "), (" != ", " == "), (" < ", " <= "), (" > ", " >= "),
         (" and ", " or "), (" or ", " and "), (">= ", "> "), ("<= ", "< ")]


def candidates(src: str):
    for ln, line in enumerate(src.splitlines()):
        code = line.split("#")[0]
        if not code.strip() or code.lstrip().startswith(('"', "'", "f\"", "f'", "def ", "@", "class ")):
            continue
        if re.search(r'^\s*(f?"|f?\')', code) or '"""' in code:
            continue
        for a, b in SWAPS:
            if a in code and not _inside_string(code, a):
                yield ln, line, line.replace(a, b, 1)


def _inside_string(code: str, token: str) -> bool:
    i = code.find(token)
    return code[:i].count('"') % 2 == 1 or code[:i].count("'") % 2 == 1


def main():
    survivors, total = [], 0
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10**9
    for rel in FILES:
        path = ROOT / rel
        original = path.read_text(encoding="utf-8")
        lines = original.splitlines(keepends=True)
        for ln, old, new in candidates(original):
            if total >= limit:
                break
            total += 1
            lines2 = list(lines)
            lines2[ln] = new + ("\n" if lines[ln].endswith("\n") else "")
            path.write_text("".join(lines2), encoding="utf-8")
            try:
                r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-f"],
                                   cwd=ROOT, capture_output=True, timeout=40,
                                   env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
                killed = r.returncode != 0
            except subprocess.TimeoutExpired:
                killed = True
            finally:
                path.write_text(original, encoding="utf-8")
            if not killed:
                survivors.append((rel, ln + 1, old.strip(), new.strip()))
    print(f"мутаций: {total}, убито: {total - len(survivors)}, выжило: {len(survivors)}")
    for rel, ln, old, new in survivors:
        print(f"  {rel}:{ln}\n    - {old}\n    + {new}")
    return 1 if survivors else 0


if __name__ == "__main__":
    raise SystemExit(main())
