"""Задача: условие, точный ответ, шаги решения."""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

from .fmt import num

KINDS = ("number", "set", "tuple")


@dataclass(frozen=True)
class Problem:
    id: str                      # «тема/уровень/seed» — по нему задачу можно воссоздать
    topic: str
    level: int
    text: str
    answer: object               # Fraction | frozenset[Fraction] | tuple[Fraction, ...]
    kind: str                    # number | set | tuple
    steps: tuple = ()
    unit: str = ""
    vars: tuple = ()
    params: dict = field(default_factory=dict)

    @property
    def answer_text(self) -> str:
        u = self.unit
        suffix = "" if not u else (u if u == "%" else " " + u)
        if self.kind == "number":
            lab = f"{self.vars[0]} = " if self.vars and self.vars[0] else ""
            return lab + num(self.answer) + suffix
        if self.kind == "set":
            if not self.answer:
                return "действительных корней нет"
            roots = sorted(self.answer)
            if len(roots) == 1:
                return f"{self.vars[0]} = {num(roots[0])}"
            return "; ".join(f"{self.vars[0]}{_sub(i + 1)} = {num(r)}" for i, r in enumerate(roots))
        if self.kind == "tuple":
            return ", ".join(f"{v} = {num(a)}" for v, a in zip(self.vars, self.answer))
        raise ValueError(self.kind)


def _sub(i: int) -> str:
    return "".join("₀₁₂₃₄₅₆₇₈₉"[int(ch)] for ch in str(i))
