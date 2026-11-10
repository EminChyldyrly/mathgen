"""Разбор ответов, введённых человеком: «3/4», «0.75», «1 1/2», «x=2; x=-3», «(2; 3)», «нет корней».

Правила (они же в README):
  * десятичный разделитель — точка или запятая («0,75»);
  * элементы списка разделяются «;», словом «и»/«или», запятой с пробелом («2, 3») или пробелом;
    запятая без пробела между цифрами — десятичная («2,5» — одно число);
  * допускаются подписи «x=», «x1=», «x₁ =» и единицы измерения после числа («5 ч», «25%»);
  * смешанное число пишется через пробел: «1 1/2» = 3/2.
"""
from __future__ import annotations

import re
from fractions import Fraction

_EMPTY = re.compile(r"(нет( корней| решений| решения)?|(действительных )?корней нет|решений нет|решения нет|∅|пусто|\{\s*\})")
_LABEL = re.compile(r"^([a-zа-я]\w{0,2})\s*=\s*(.*)$")
_UNITS = re.compile(r"\s*[a-zа-я%°][a-zа-я%°/.\s²³]*$")


class ParseError(ValueError):
    pass


def normalize(s: str) -> str:
    s = s.strip().lower()
    for ch in "−–—‒":
        s = s.replace(ch, "-")
    s = s.replace(" ", " ")
    return re.sub(r"\s+", " ", s)


def parse_number(s: str) -> tuple[Fraction, bool]:
    """-> (значение, была_ли_десятичная_запись)."""
    t = normalize(s)
    m = _LABEL.match(t)
    if m:
        t = m.group(2)
    if not t:
        raise ParseError("пустой ответ")
    t = _UNITS.sub("", t).strip()
    if t.startswith("+"):
        t = t[1:].strip()
    if not t:
        raise ParseError(f"не удалось разобрать «{s.strip()}» как число")
    m = re.fullmatch(r"(-?)\s*(\d+)\s+(\d+)\s*/\s*(\d+)", t)          # смешанное число
    if m:
        sign, whole, n, d = m.groups()
        if int(d) == 0:
            raise ParseError("знаменатель равен нулю")
        v = int(whole) + Fraction(int(n), int(d))
        return (-v if sign else v), False
    m = re.fullmatch(r"(-?\d+)\s*/\s*(-?\d+)", t)                      # дробь
    if m:
        n, d = int(m.group(1)), int(m.group(2))
        if d == 0:
            raise ParseError("знаменатель равен нулю")
        return Fraction(n, d), False
    m = re.fullmatch(r"-?(\d+([.,]\d*)?|[.,]\d+)", t)                  # целое / десятичная
    if m:
        v = Fraction(t.replace(",", ".").rstrip("."))
        return v, ("." in t or "," in t)
    raise ParseError(f"не удалось разобрать «{s.strip()}» как число")


def _split(t: str) -> list[str]:
    t = re.sub(r"\s*=\s*", "=", re.sub(r"\s*/\s*", "/", t.strip()))
    if len(t) >= 2 and t[0] + t[-1] in ("()", "[]", "{}"):
        t = t[1:-1].strip()
    if ";" in t:
        parts = t.split(";")
    elif re.search(r"\s(и|или)\s", t):
        parts = re.split(r"\s+(?:и|или)\s+", t)
    elif re.search(r",\s", t) or re.search(r",(?=[a-zа-я])", t):
        parts = re.split(r",\s*", t)
    elif re.fullmatch(r"-?\d+\s+\d+/\d+", t):                       # смешанное число
        parts = [t]
    elif re.search(r"\s", t):
        parts = t.split()
    else:
        parts = [t]
    parts = [p.strip() for p in parts if p.strip()]
    if not parts:
        raise ParseError("пустой ответ")
    return parts


def parse_list(s: str) -> list[tuple[str | None, Fraction, bool]]:
    """-> [(подпись|None, значение, десятичная?), ...]. Пустое множество («нет корней») -> []."""
    t = normalize(s)
    if not t:
        raise ParseError("пустой ответ")
    if _EMPTY.fullmatch(t):
        return []
    out = []
    for part in _split(t):
        m = _LABEL.match(part)
        label = m.group(1) if m else None
        v, dec = parse_number(part)
        out.append((label, v, dec))
    return out
