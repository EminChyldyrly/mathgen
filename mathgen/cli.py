"""Командная строка: python -m mathgen {topics,show,check,worksheet,drill}."""
from __future__ import annotations

import argparse
import sys

from .check import check
from .topics import LEVELS, TOPICS, from_id
from .worksheet import build_worksheet, to_json, to_markdown


def _topics(arg: str):
    names = list(TOPICS) if arg == "all" else [t.strip() for t in arg.split(",") if t.strip()]
    for n in names:
        if n not in TOPICS:
            raise SystemExit(f"неизвестная тема «{n}»; доступны: {', '.join(TOPICS)}")
    return names


def _levels(arg: str):
    try:
        lv = [int(x) for x in arg.split(",") if x.strip()]
    except ValueError:
        raise SystemExit("уровни задаются числами через запятую, например 1,2,3") from None
    if not lv or any(x not in LEVELS for x in lv):
        raise SystemExit("уровень должен быть 1, 2 или 3")
    return lv


def _parser():
    ap = argparse.ArgumentParser(prog="mathgen", description="Генератор и проверка задач по математике")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("topics", help="список тем")
    p = sub.add_parser("show", help="показать задачу по id (тема/уровень/seed)")
    p.add_argument("id")
    p.add_argument("--solution", action="store_true", help="показать ход решения")
    p = sub.add_parser("check", help="проверить ответ; код возврата 0 — верно, 1 — нет")
    p.add_argument("id")
    p.add_argument("answer")
    p = sub.add_parser("worksheet", help="собрать листок с вариантами и ключом")
    p.add_argument("--topics", default="all", help="темы через запятую или all")
    p.add_argument("--levels", default="1,2,3", help="уровни через запятую; нарастают вдоль листка")
    p.add_argument("--count", type=int, default=10, help="задач в варианте")
    p.add_argument("--variants", type=int, default=1)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--title")
    p.add_argument("--out", default="worksheet.pdf", help=".pdf, .md или .json")
    p.add_argument("--solutions", action="store_true", help="в ключе — полные решения")
    p.add_argument("--no-key", action="store_true", help="без ключа")
    p = sub.add_parser("drill", help="тренажёр в терминале")
    p.add_argument("--topics", default="all")
    p.add_argument("--levels", default="1,2")
    p.add_argument("--count", type=int, default=5)
    p.add_argument("--seed", type=int, default=0)
    return ap


def main(argv=None, input_fn=input, out=None) -> int:
    out = out or sys.stdout
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) >= 3 and argv[0] == "check" and argv[2] != "--":
        argv.insert(2, "--")          # чтобы ответ «-23/4» не принимался за опцию
    args = _parser().parse_args(argv)

    def say(*a):
        print(*a, file=out)

    if args.cmd == "topics":
        for t in TOPICS.values():
            say(f"{t.name:11} {t.title}")
        return 0
    if args.cmd == "show":
        try:
            p = from_id(args.id)
        except ValueError as e:
            say(str(e))
            return 2
        say(p.text)
        if args.solution:
            say("")
            for s in p.steps:
                say("  " + s)
        return 0
    if args.cmd == "check":
        try:
            p = from_id(args.id)
        except ValueError as e:
            say(str(e))
            return 2
        r = check(p, args.answer)
        say(r.message)
        return 0 if r.correct else 1
    if args.cmd == "worksheet":
        ws = build_worksheet(_topics(args.topics), _levels(args.levels), args.count, args.variants,
                             args.seed, args.title)
        ext = args.out.rsplit(".", 1)[-1].lower()
        if ext == "pdf":
            from .pdf import write_pdf
            write_pdf(ws, args.out, solutions=args.solutions, key=not args.no_key)
        elif ext in ("md", "json"):
            body = to_markdown(ws, args.solutions, not args.no_key) if ext == "md" else to_json(ws)
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(body)
        else:
            say("формат вывода определяется расширением: .pdf, .md или .json")
            return 2
        say(f"Готово: {args.out} ({args.variants} вар. × {args.count} задач)")
        return 0
    if args.cmd == "drill":
        ws = build_worksheet(_topics(args.topics), _levels(args.levels), args.count, 1, args.seed)
        score, missed = 0, []
        for i, p in enumerate(ws.variants[0], 1):
            say(f"\nЗадача {i}/{args.count}. {p.text}")
            solved = False
            for _ in range(3):
                try:
                    ans = input_fn("Ответ (Enter — пропустить): ")
                except EOFError:
                    ans = ""
                if not ans.strip():
                    break
                r = check(p, ans)
                say(r.message)
                if r.correct:
                    solved = True
                    break
            if solved:
                score += 1
            else:
                missed.append(p)
                say("Решение:")
                for s in p.steps:
                    say("  " + s)
        say(f"\nИтог: {score} из {args.count}.")
        if missed:
            say("Повторить: " + ", ".join(p.id for p in missed))
        return 0
    return 2
