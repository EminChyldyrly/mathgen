"""Генераторы задач. Каждая тема — функция (rng, level) -> dict; уровни 1 (базовый), 2, 3 (сложнее).

Все вычисления — на fractions.Fraction, поэтому ответ точный. Задача полностью определяется
тройкой (тема, уровень, seed): `generate("linear", 2, 12345)` всегда даёт одну и ту же задачу.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from fractions import Fraction
from typing import Callable

from .fmt import MINUS, expr, num, paren
from .problem import Problem

LEVELS = (1, 2, 3)


def _nz(rng: random.Random, lo: int, hi: int) -> int:
    while True:
        v = rng.randint(lo, hi)
        if v:
            return v


def _sgn(c: int) -> str:
    return "+" if c > 0 else MINUS


# ---------------------------------------------------------------- линейные уравнения
def gen_linear(rng, level):
    """A(x + B) + C = D·x + E. Уровень 1: A·x + C = E; 2: A·x + C = D·x + E (целый корень); 3: со скобками."""
    B = 0
    D = 0
    if level == 1:
        A = rng.randint(2, 9)
        x = _nz(rng, -9, 9)
        C = rng.randint(-12, 12)
        E = A * x + C
    elif level == 2:
        A = rng.randint(2, 9)
        D = rng.choice([d for d in range(-5, 10) if d != A and d != 0])
        x = _nz(rng, -9, 9)
        C = rng.randint(-15, 15)
        E = (A - D) * x + C
    else:
        while True:
            A = rng.choice([a for a in range(-7, 10) if abs(a) >= 2])
            B = _nz(rng, -6, 6)
            C = rng.randint(-9, 9)
            D = rng.choice([d for d in range(-5, 10) if d != 0])
            E = rng.randint(-15, 15)
            if A != D and Fraction(E - A * B - C, A - D).denominator > 1:
                break
    x = Fraction(E - A * B - C, A - D)
    if B:
        left = f"{num(A)}(x {_sgn(B)} {abs(B)})" + (f" {_sgn(C)} {abs(C)}" if C else "")
    else:
        left = expr([(A, "x"), (C, "")])
    right = expr([(D, "x"), (E, "")])
    steps = []
    if B:
        steps.append(f"Раскрываем скобки: {expr([(A, 'x'), (A * B, '')])}"
                     + (f" {_sgn(C)} {abs(C)}" if C else "") + f" = {right}")
    rhs = E - A * B - C
    steps.append(f"Переносим слагаемые: {expr([(A - D, 'x')])} = {num(rhs)}")
    steps.append(f"Делим на {paren(A - D)}: x = {num(rhs)} ÷ {paren(A - D)} = {num(x)}")
    return dict(text=f"Решите уравнение: {left} = {right}", answer=x, kind="number", vars=("x",),
                steps=steps, params=dict(A=A, B=B, C=C, D=D, E=E))


# ---------------------------------------------------------------- квадратные уравнения
def gen_quadratic(rng, level):
    """Уровень 1: x² + bx + c = 0 с целыми корнями; 2: a·x² + … ; 3: ещё двойной корень и случай без корней."""
    if level == 1:
        a = 1
        r1, r2 = rng.sample(range(-9, 10), 2)
        b, c = -(r1 + r2), r1 * r2
    elif level == 2:
        a = rng.choice([2, 3, 4])
        r1, r2 = rng.sample(range(-7, 8), 2)
        b, c = -a * (r1 + r2), a * r1 * r2
    else:
        kind = rng.choices(["two", "double", "none"], weights=[4, 2, 3])[0]
        a = rng.choice([-2, -1, 1, 2, 3])
        if kind == "two":
            r1, r2 = rng.sample(range(-7, 8), 2)
            b, c = -a * (r1 + r2), a * r1 * r2
        elif kind == "double":
            r = _nz(rng, -6, 6)
            b, c = -2 * a * r, a * r * r
        else:
            b = rng.randint(-6, 6)
            if a > 0:
                c = b * b // (4 * a) + rng.randint(1, 4)
            else:
                c = -((b * b) // (4 * abs(a))) - rng.randint(1, 4)
    D = b * b - 4 * a * c
    if D > 0:
        s = math.isqrt(D)
        assert s * s == D
        roots = frozenset({Fraction(-b - s, 2 * a), Fraction(-b + s, 2 * a)})
    elif D == 0:
        roots = frozenset({Fraction(-b, 2 * a)})
    else:
        roots = frozenset()
    steps = [f"Коэффициенты: a = {num(a)}, b = {num(b)}, c = {num(c)}",
             f"Дискриминант: D = b² − 4ac = {paren(b)}² − 4·{paren(a)}·{paren(c)} = {num(D)}"]
    if D > 0:
        s = math.isqrt(D)
        lo, hi = sorted(roots)
        steps.append(f"D > 0, два корня; √D = {s}")
        steps.append(f"x = (−b ± √D) / (2a) = ({num(-b)} ± {s}) / {num(2 * a)}: "
                     f"x₁ = {num(lo)}, x₂ = {num(hi)}")
    elif D == 0:
        (r,) = roots
        steps.append(f"D = 0, один корень: x = −b / (2a) = {num(-b)} / {num(2 * a)} = {num(r)}")
    else:
        steps.append("D < 0, действительных корней нет")
    text = f"Решите уравнение: {expr([(a, 'x²'), (b, 'x'), (c, '')])} = 0"
    return dict(text=text, answer=roots, kind="set", vars=("x",), steps=steps,
                params=dict(a=a, b=b, c=c, D=D))


# ---------------------------------------------------------------- обыкновенные дроби
def _fr(n, d):
    return f"{n}/{d}"


def _eq(n, d):
    """Приписка «= сокращённая дробь», если дробь n/d сокращается."""
    v = Fraction(n, d)
    return "" if (v.numerator, v.denominator) == (n, d) else f" = {num(v)}"


def _reduce(n, d):
    e = _eq(n, d)
    return [f"Сокращаем:{e}"] if e else []


def gen_fractions(rng, level):
    if level == 1:
        d = rng.randint(3, 12)
        a, b = rng.randint(1, 2 * d), rng.randint(1, 2 * d)
        op = rng.choice(["+", "−"])
        val = Fraction(a + b if op == "+" else a - b, d)
        text = f"Вычислите: {_fr(a, d)} {op} {_fr(b, d)}"
        steps = [f"Знаменатели равны, действуем с числителями: ({a} {op} {b}) / {d} = "
                 f"{num(a + b if op == '+' else a - b)}/{d}"]
        steps += _reduce(a + b if op == "+" else a - b, d)
    elif level == 2:
        while True:
            b, d = rng.randint(2, 12), rng.randint(2, 12)
            if b != d:
                break
        a, c = rng.randint(1, b + 3), rng.randint(1, d + 3)
        op = rng.choice(["+", "−"])
        L = b * d // math.gcd(b, d)
        x, y = a * (L // b), c * (L // d)
        val = Fraction(a, b) + Fraction(c, d) if op == "+" else Fraction(a, b) - Fraction(c, d)
        text = f"Вычислите: {_fr(a, b)} {op} {_fr(c, d)}"
        steps = [f"Общий знаменатель: НОК({b}, {d}) = {L}",
                 f"{_fr(a, b)} = {_fr(x, L)}, {_fr(c, d)} = {_fr(y, L)}",
                 f"({x} {op} {y}) / {L} = {num(x + y if op == '+' else x - y)}/{L}"]
        steps += _reduce(x + y if op == "+" else x - y, L)
    else:
        a, b, c, d, e, f = (rng.randint(1, 9) for _ in range(6))
        b, d, f = b + 1, d + 1, f + 1
        op1, op2 = rng.choice(["×", "÷"]), rng.choice(["+", "−"])
        first = Fraction(a, b) * Fraction(c, d) if op1 == "×" else Fraction(a, b) / Fraction(c, d)
        val = first + Fraction(e, f) if op2 == "+" else first - Fraction(e, f)
        text = f"Вычислите: {_fr(a, b)} {op1} {_fr(c, d)} {op2} {_fr(e, f)}"
        if op1 == "×":
            steps = [f"Сначала умножение: {_fr(a, b)} · {_fr(c, d)} = {_fr(a * c, b * d)}" + _eq(a * c, b * d)]
        else:
            steps = [f"Сначала деление — умножаем на обратную дробь: {_fr(a, b)} · {_fr(d, c)} = "
                     f"{_fr(a * d, b * c)}" + _eq(a * d, b * c)]
        steps += [f"Затем {'сложение' if op2 == '+' else 'вычитание'}: {num(first)} {op2} {_fr(e, f)} = {num(val)}"]
    return dict(text=text, answer=val, kind="number", vars=("",), steps=steps, params={})


# ---------------------------------------------------------------- проценты
_P1 = [5, 10, 12, 15, 20, 25, 30, 40, 45, 50, 60, 75, 80]


def gen_percent(rng, level):
    unit = ""
    if level == 1:
        p = rng.choice(_P1)
        step = 100 // math.gcd(p, 100)
        N = step * rng.randint(1, max(1, 600 // step))
        ans = Fraction(p * N, 100)
        text = f"Найдите {p}% от числа {N}."
        steps = [f"{p}% = {p}/100", f"{N} · {p} ÷ 100 = {num(ans)}"]
        params = dict(p=p, N=N)
    elif level == 2:
        p = rng.randint(1, 99)
        step = 100 // math.gcd(p, 100)
        b = step * rng.randint(1, max(1, 400 // step))
        a = p * b // 100
        ans = Fraction(a * 100, b)
        text = f"Сколько процентов составляет число {a} от числа {b}?"
        steps = [f"Доля: {a} / {b}", f"В процентах: {a} ÷ {b} · 100 = {num(ans)}"]
        unit = "%"
        params = dict(a=a, b=b)
    else:
        while True:
            P = 100 * rng.randint(2, 40)
            p, q = rng.choice([5, 10, 15, 20, 25, 30, 40, 50]), rng.choice([5, 10, 15, 20, 25, 30, 40, 50])
            ans = Fraction(P) * (100 + p) / 100 * (100 - q) / 100
            if ans.denominator == 1:
                break
        mid = Fraction(P) * (100 + p) / 100
        text = (f"Цена товара {P} руб. Сначала её повысили на {p}%, а затем снизили на {q}%. "
                f"Какой стала цена (в рублях)?")
        steps = [f"После повышения: {P} · {100 + p} ÷ 100 = {num(mid)}",
                 f"После снижения: {num(mid)} · {100 - q} ÷ 100 = {num(ans)}"]
        unit = "руб."
        params = dict(P=P, p=p, q=q)
    return dict(text=text, answer=ans, kind="number", vars=("",), steps=steps, unit=unit, params=params)


# ---------------------------------------------------------------- системы 2×2
def gen_system(rng, level):
    if level == 1:
        x, y = rng.randint(-9, 9), rng.randint(-9, 9)
        a1, b1, a2, b2 = 1, 1, 1, -1
    else:
        hi = 6 if level == 2 else 9
        while True:
            a1, b1, a2, b2 = (_nz(rng, -hi, hi) for _ in range(4))
            if abs(a1 * b2 - a2 * b1) >= (2 if level == 3 else 1):   # при |Δ| = 1 решение всегда целое
                break
        x, y = _nz(rng, -7, 7), _nz(rng, -7, 7)
    if level < 3:
        e, f = a1 * x + b1 * y, a2 * x + b2 * y
    else:
        while True:
            e, f = rng.randint(-20, 20), rng.randint(-20, 20)
            D0 = a1 * b2 - a2 * b1
            sol = (Fraction(e * b2 - f * b1, D0), Fraction(a1 * f - a2 * e, D0))
            if sol[0].denominator > 1 or sol[1].denominator > 1:
                break
    D0 = a1 * b2 - a2 * b1
    dx, dy = e * b2 - f * b1, a1 * f - a2 * e
    X, Y = Fraction(dx, D0), Fraction(dy, D0)
    text = ("Решите систему уравнений:\n"
            f"{expr([(a1, 'x'), (b1, 'y')])} = {num(e)}\n{expr([(a2, 'x'), (b2, 'y')])} = {num(f)}")
    steps = [f"Определитель системы: Δ = {paren(a1)}·{paren(b2)} − {paren(b1)}·{paren(a2)} = {num(D0)}",
             f"Δx = {paren(e)}·{paren(b2)} − {paren(b1)}·{paren(f)} = {num(dx)}",
             f"Δy = {paren(a1)}·{paren(f)} − {paren(e)}·{paren(a2)} = {num(dy)}",
             f"x = Δx ÷ Δ = {num(X)}, y = Δy ÷ Δ = {num(Y)}"]
    return dict(text=text, answer=(X, Y), kind="tuple", vars=("x", "y"), steps=steps,
                params=dict(a1=a1, b1=b1, e=e, a2=a2, b2=b2, f=f))


# ---------------------------------------------------------------- пропорции
def gen_proportion(rng, level):
    if level == 1:
        b, c, s = rng.randint(2, 9), rng.randint(2, 9), rng.randint(2, 9)
        a = c * s
        ans = Fraction(a * b, c)
        text = f"Найдите x из пропорции: x/{a} = {b}/{c}"
        steps = [f"По свойству пропорции: x · {c} = {a} · {b}", f"x = {a * b} ÷ {c} = {num(ans)}"]
    elif level == 2:
        b, c, s = rng.randint(2, 9), rng.randint(2, 12), rng.randint(2, 9)
        a = b * s
        ans = Fraction(a * c, b)
        text = f"Найдите x из пропорции: {a}/x = {b}/{c}"
        steps = [f"По свойству пропорции: {a} · {c} = x · {b}", f"x = {a * c} ÷ {b} = {num(ans)}"]
    else:
        while True:
            n, d = rng.randint(3, 12), rng.randint(2, 15)
            total = n * d
            ms = [m for m in range(2, 25) if m != n and total % m == 0]
            if ms:
                m = rng.choice(ms)
                break
        ans = Fraction(total, m)
        text = (f"{n} рабочих выполняют заказ за {d} дн. За сколько дней выполнят такой же заказ "
                f"{m} рабочих, если все работают с одинаковой производительностью?")
        steps = [f"Работа обратно пропорциональна числу рабочих: {n} · {d} = {m} · x",
                 f"x = {total} ÷ {m} = {num(ans)}"]
    return dict(text=text, answer=ans, kind="number", vars=("x",), steps=steps,
                unit="дн." if level == 3 else "", params={})


# ---------------------------------------------------------------- движение
_MOVERS = [("Автомобиль", "проедет", (50, 110), 5), ("Поезд", "пройдёт", (60, 140), 10),
           ("Велосипедист", "проедет", (12, 25), 1), ("Пешеход", "пройдёт", (4, 6), 1)]


def gen_motion(rng, level):
    if level == 1:
        who, verb, (lo, hi), st = rng.choice(_MOVERS)
        v = rng.randrange(lo, hi + 1, st) if st > 1 else rng.randint(lo, hi)
        t = rng.randint(2, 9)
        ans = Fraction(v * t)
        text = f"{who} движется со скоростью {v} км/ч. Какое расстояние он {verb} за {t} ч?"
        steps = [f"s = v · t = {v} · {t} = {num(ans)}"]
        unit, params = "км", dict(v=v, t=t)
    elif level == 2:
        v1, v2 = rng.randrange(40, 100, 5), rng.randrange(40, 100, 5)
        while True:
            t = Fraction(rng.randint(2, 12), rng.choice([1, 2]))
            S = (v1 + v2) * t
            if S.denominator == 1:
                break
        ans = t
        text = (f"Из двух городов, расстояние между которыми {num(S)} км, одновременно навстречу друг другу "
                f"выехали два автомобиля со скоростями {v1} км/ч и {v2} км/ч. Через сколько часов они встретятся?")
        steps = [f"Скорость сближения: {v1} + {v2} = {v1 + v2} км/ч",
                 f"t = s ÷ v = {num(S)} ÷ {v1 + v2} = {num(ans)}"]
        unit, params = "ч", dict(S=int(S), v1=v1, v2=v2)
    else:
        v1 = rng.randint(10, 20)
        d = rng.choice([2, 3, 4, 5, 6, 8, 10])
        v2, t0 = v1 + d, rng.randint(1, 4)
        ans = Fraction(v1 * t0, d)
        text = (f"Из пункта A выехал велосипедист со скоростью {v1} км/ч. Через {t0} ч вслед за ним выехал "
                f"мотоциклист со скоростью {v2} км/ч. Через сколько часов после своего выезда мотоциклист "
                f"догонит велосипедиста?")
        steps = [f"Расстояние между ними в момент выезда мотоциклиста: {v1} · {t0} = {v1 * t0} км",
                 f"Скорость сближения: {v2} − {v1} = {d} км/ч",
                 f"t = {v1 * t0} ÷ {d} = {num(ans)}"]
        unit, params = "ч", dict(v1=v1, v2=v2, t0=t0)
    return dict(text=text, answer=ans, kind="number", vars=("",), steps=steps, unit=unit, params=params)


# ---------------------------------------------------------------- реестр
@dataclass(frozen=True)
class Topic:
    name: str
    title: str
    gen: Callable


TOPICS = {t.name: t for t in (
    Topic("linear", "Линейные уравнения", gen_linear),
    Topic("quadratic", "Квадратные уравнения", gen_quadratic),
    Topic("fractions", "Обыкновенные дроби", gen_fractions),
    Topic("percent", "Проценты", gen_percent),
    Topic("system", "Системы линейных уравнений", gen_system),
    Topic("proportion", "Пропорции", gen_proportion),
    Topic("motion", "Задачи на движение", gen_motion),
)}


def generate(topic: str, level: int, seed: int) -> Problem:
    if topic not in TOPICS:
        raise ValueError(f"неизвестная тема «{topic}»; доступны: {', '.join(TOPICS)}")
    if level not in LEVELS:
        raise ValueError(f"уровень должен быть 1, 2 или 3, получено {level}")
    d = TOPICS[topic].gen(random.Random(f"{topic}/{level}/{seed}"), level)
    ans = d["answer"]
    if d["kind"] == "number":
        ans = Fraction(ans)
    p = Problem(id=f"{topic}/{level}/{seed}", topic=topic, level=level, text=d["text"], answer=ans,
                kind=d["kind"], steps=tuple(d["steps"]), unit=d.get("unit", ""), vars=d["vars"],
                params=d["params"])
    return Problem(**{**p.__dict__, "steps": p.steps + (f"Ответ: {p.answer_text}",)})


def from_id(pid: str) -> Problem:
    """Воссоздать задачу по идентификатору «тема/уровень/seed»."""
    try:
        topic, level, seed = pid.strip().split("/")
        return generate(topic, int(level), int(seed))
    except ValueError as e:
        raise ValueError(f"неверный идентификатор задачи «{pid}» (ожидается тема/уровень/seed): {e}") from None
