"""Форматирование чисел и выражений для текста задач (с настоящим минусом «−»)."""
from __future__ import annotations

from fractions import Fraction

MINUS = "−"


def num(x) -> str:
    """Число как строка: целое или несократимая дробь «3/4»; минус — «−»."""
    x = Fraction(x)
    body = str(abs(x.numerator)) if x.denominator == 1 else f"{abs(x.numerator)}/{x.denominator}"
    return (MINUS if x < 0 else "") + body


def paren(x) -> str:
    """Число в скобках, если оно отрицательное: «(−5)»."""
    s = num(x)
    return f"({s})" if s.startswith(MINUS) else s


def expr(terms) -> str:
    """Многочлен из пар (целый коэффициент, символ): [(2,'x'), (-3,'')] -> «2x − 3».

    Единичный коэффициент при символе опускается, нулевые слагаемые пропускаются."""
    out = ""
    for c, sym in terms:
        if c == 0:
            continue
        mag = abs(c)
        body = (str(mag) if (sym == "" or mag != 1) else "") + sym
        if not out:
            out = (MINUS if c < 0 else "") + body
        else:
            out += (f" {MINUS} " if c < 0 else " + ") + body
    return out or "0"
