"""Сборка листков: несколько вариантов без повторов, воспроизводимо по seed."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .problem import Problem
from .topics import TOPICS, generate


@dataclass(frozen=True)
class Worksheet:
    title: str
    seed: int
    variants: tuple          # tuple[tuple[Problem, ...], ...]


def problem_seed(master: int, variant: int, index: int, attempt: int) -> int:
    """Стабильный (не зависит от PYTHONHASHSEED) seed отдельной задачи."""
    h = hashlib.sha256(f"{master}/{variant}/{index}/{attempt}".encode()).digest()
    return int.from_bytes(h[:4], "big")


def build_worksheet(topics, levels, count: int, variants: int = 1, seed: int = 0,
                    title: str | None = None) -> Worksheet:
    """`count` задач в каждом из `variants` вариантов.

    Темы чередуются по кругу; уровни нарастают вдоль листка (первые задачи легче). Тексты задач не
    повторяются ни внутри варианта, ни между вариантами."""
    topics, levels = list(topics), list(levels)
    if not topics or not levels:
        raise ValueError("нужна хотя бы одна тема и один уровень")
    if count < 1 or variants < 1:
        raise ValueError("count и variants должны быть положительными")
    for t in topics:
        if t not in TOPICS:
            raise ValueError(f"неизвестная тема «{t}»; доступны: {', '.join(TOPICS)}")
    seen: set[str] = set()
    out = []
    for v in range(variants):
        probs = []
        for i in range(count):
            topic, level = topics[i % len(topics)], levels[min(len(levels) - 1, i * len(levels) // count)]
            for attempt in range(1000):
                p = generate(topic, level, problem_seed(seed, v, i, attempt))
                if p.text not in seen:
                    seen.add(p.text)
                    probs.append(p)
                    break
            else:
                raise RuntimeError(f"не удалось подобрать неповторяющуюся задачу ({topic}, уровень {level}); "
                                   f"уменьшите count или variants")
        out.append(tuple(probs))
    if title is None:
        names = list(dict.fromkeys(topics))
        title = ("Математика: " + ", ".join(TOPICS[t].title.lower() for t in names)) if len(names) <= 2 \
            else "Математика: смешанный листок"
    return Worksheet(title=title, seed=seed, variants=tuple(out))


def to_markdown(ws: Worksheet, solutions: bool = False, key: bool = True) -> str:
    lines = [f"# {ws.title}", ""]
    for v, probs in enumerate(ws.variants, 1):
        lines += [f"## Вариант {v}", ""]
        for i, p in enumerate(probs, 1):
            lines += [f"{i}. " + p.text.replace("\n", "  \n   "), ""]
    if key:
        lines += ["---", "", "# Ключ", ""]
        for v, probs in enumerate(ws.variants, 1):
            lines += [f"## Вариант {v}", ""]
            for i, p in enumerate(probs, 1):
                lines.append(f"{i}. **{p.answer_text}** (`{p.id}`)")
                if solutions:
                    lines += [f"   - {s}" for s in p.steps[:-1]]
            lines.append("")
    return "\n".join(lines)


def to_json(ws: Worksheet) -> str:
    def prob(p: Problem):
        return dict(id=p.id, topic=p.topic, level=p.level, text=p.text, answer=p.answer_text,
                    steps=list(p.steps))
    return json.dumps(dict(title=ws.title, seed=ws.seed,
                           variants=[[prob(p) for p in probs] for probs in ws.variants]),
                      ensure_ascii=False, indent=2)
