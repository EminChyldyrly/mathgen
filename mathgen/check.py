"""Проверка ответа ученика: точное сравнение, понятная обратная связь."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .parse import ParseError, parse_list, parse_number
from .problem import Problem

_APPROX = "Похоже на округлённое значение — ответ нужен точным (дробью, например 7/3)."


@dataclass(frozen=True)
class Result:
    correct: bool
    status: str        # ok | wrong | unparsed
    message: str


def check(problem: Problem, text: str) -> Result:
    """Сравнивает ответ `text` с эталоном. Дробь и десятичная запись равны, если равны точно."""
    try:
        if problem.kind == "number":
            return _check_number(problem, text)
        if problem.kind == "set":
            return _check_set(problem, text)
        if problem.kind == "tuple":
            return _check_tuple(problem, text)
    except ParseError as e:
        return Result(False, "unparsed", str(e))
    raise ValueError(problem.kind)


def _close(a: Fraction, b: Fraction) -> bool:
    return a != b and abs(a - b) <= Fraction(1, 100) * max(1, abs(b))


def _check_number(p, text):
    v, dec = parse_number(text)
    if v == p.answer:
        return Result(True, "ok", "Верно.")
    if dec and _close(v, p.answer):
        return Result(False, "wrong", _APPROX)
    return Result(False, "wrong", "Неверно.")


def _check_set(p, text):
    items = parse_list(text)
    got = frozenset(v for _, v, _ in items)
    if got == p.answer:
        return Result(True, "ok", "Верно.")
    if not p.answer:
        return Result(False, "wrong", "Неверно: у этого уравнения действительных корней нет.")
    if not got:
        return Result(False, "wrong", "Неверно: корни у уравнения есть.")
    if got < p.answer:
        return Result(False, "wrong", "Найдены не все корни.")
    if got > p.answer:
        return Result(False, "wrong", "Среди ответов есть лишние значения.")
    if any(d for _, _, d in items) and all(any(_close(g, a) or g == a for a in p.answer) for g in got):
        return Result(False, "wrong", _APPROX)
    return Result(False, "wrong", "Неверно.")


def _check_tuple(p, text):
    items = parse_list(text)
    n = len(p.vars)
    if len(items) != n:
        raise ParseError(f"нужно {n} значения(й): {', '.join(p.vars)}; получено {len(items)}")
    labels = [lab for lab, _, _ in items]
    if all(labels):
        if set(labels) == set(p.vars):
            by = {lab: v for lab, v, _ in items}
            got = tuple(by[name] for name in p.vars)
        else:
            raise ParseError(f"неизвестные обозначения: {', '.join(labels)} (ожидалось {', '.join(p.vars)})")
    else:
        got = tuple(v for _, v, _ in items)
    if got == tuple(p.answer):
        return Result(True, "ok", "Верно.")
    if sorted(got) == sorted(p.answer) and not all(labels):
        return Result(False, "wrong", "Значения верны, но, возможно, перепутан порядок: сначала x, затем y.")
    if any(d for _, _, d in items) and all(g == a or _close(g, a) for g, a in zip(got, p.answer)):
        return Result(False, "wrong", _APPROX)
    wrong = [v for v, g, a in zip(p.vars, got, p.answer) if g != a]
    return Result(False, "wrong", f"Неверно: проверьте {', '.join(wrong)}.")
