# mathgen

*[English version](README.en.md)*

Генератор и проверяющая система для школьных задач по математике. Задачи создаются по темам и уровням сложности, ответы проверяются **точно** (на обыкновенных дробях, без округлений), из задач собираются **листки в PDF с несколькими вариантами и ключом**. Ядро написано на стандартной библиотеке Python; `reportlab` нужен только для PDF.

*English summary below.*

## Что умеет

| Тема (`--topics`) | Уровень 1 | Уровень 2 | Уровень 3 |
|---|---|---|---|
| `linear` — линейные уравнения | `ax + c = e` | `ax + c = dx + e`, целый корень | со скобками, корень — несократимая дробь |
| `quadratic` — квадратные уравнения | `x² + bx + c = 0`, целые корни | `ax² + bx + c = 0` | ещё двойной корень и случай «корней нет» |
| `fractions` — обыкновенные дроби | сложение и вычитание с одним знаменателем | разные знаменатели (НОК) | `×`, `÷` и сложение в одном выражении |
| `percent` — проценты | сколько будет p% от N | сколько процентов составляет a от b | цена после повышения и снижения |
| `system` — системы 2×2 | сложение/вычитание уравнений, целое решение | произвольные коэффициенты, целое решение | дробное решение (метод Крамера) |
| `proportion` — пропорции | `x/a = b/c` | `a/x = b/c` | обратная пропорциональность (текстовая) |
| `motion` — движение | `s = v·t` | встречное движение | «догонит» |

К каждой задаче есть **ход решения** (шаги), а последним шагом всегда идёт «Ответ: …».

## Быстрый старт

Нужен Python 3.10+ (проверено на 3.13).

```bash
git clone <ссылка на этот репозиторий>
cd mathgen
pip install reportlab          # только для PDF; .md и .json работают без него

python -m mathgen worksheet --topics linear,quadratic --levels 1,2,3 --count 10 --variants 4 --seed 7 --out sheet.pdf
```

Получится PDF: четыре варианта по 10 задач (уровни нарастают от первой задачи к последней, повторов нет ни внутри варианта, ни между вариантами), поля для ФИО и даты, место для решения и страницы с ключом. Пример готового файла: [`docs/example_sheet.pdf`](docs/example_sheet.pdf).

### Команды

```bash
python -m mathgen topics                                   # список тем
python -m mathgen show quadratic/3/3 --solution            # задача по id и её решение
python -m mathgen check system/2/7 "x=-7; y=4"             # проверка ответа; код возврата 0 — верно
python -m mathgen worksheet --out sheet.pdf --solutions    # в ключе — полные решения
python -m mathgen worksheet --out sheet.md                 # то же в Markdown (.json — для своих программ)
python -m mathgen drill --topics fractions --levels 2 --count 5    # тренажёр в терминале
```

Параметры `worksheet`: `--topics` (через запятую или `all`), `--levels` (например `1,2,3` или `2`), `--count` (задач в варианте), `--variants`, `--seed`, `--title`, `--solutions`, `--no-key`.

## Как проверяется ответ

Ответ сравнивается точно: `3/4`, `0.75`, `0,75` и `6/8` — один и тот же ответ, а `0.33` вместо `1/3` — нет (с подсказкой «похоже на округлённое значение, нужна точная дробь»). Принимаются:

- дроби и десятичные числа, смешанные числа через пробел (`1 1/2`), минус обычный или «−»;
- подписи и единицы: `x = 5`, `5 ч`, `25%`;
- несколько значений через `;`, «и», «или», запятую с пробелом или пробел; порядок корней не важен, `2,5` — это одно число (десятичная запятая);
- для систем — позиционно (`-7; 4`) или с подписями в любом порядке (`y=4, x=-7`);
- «нет корней» / `∅`, когда корней действительно нет.

Обратная связь конкретная: «найдены не все корни», «есть лишние значения», «значения верны, но перепутан порядок», «проверьте y».

## Воспроизводимость

Любая задача определяется строкой `тема/уровень/seed`, например `linear/3/1`. Эта строка печатается в ключе, поэтому преподаватель может восстановить любую задачу:

```python
from mathgen import from_id, check, generate, build_worksheet

p = from_id("linear/3/1")
print(p.text)               # Решите уравнение: 6(x − 1) − 1 = −5x − 13
print(p.steps)              # ход решения
print(check(p, "-6/11"))    # Result(correct=True, status='ok', message='Верно.')

ws = build_worksheet(["linear", "system"], levels=[1, 2], count=6, variants=2, seed=1)
```

Seed отдельных задач получается через SHA-256, а не через `hash()`, поэтому листок с тем же `--seed` совпадает на любой машине и при любом `PYTHONHASHSEED`.

## Как устроена проверка качества

Главный риск такого проекта — задача с неверным ответом в ключе. Поэтому тесты (60 штук, ~2 с) проверяют ответ **независимо от генератора**:

- для уравнений и систем тест берёт **текст** задачи, вычисляет обе части и подставляет корень; из текста же восстанавливаются коэффициенты и проверяется, что решение единственное (определитель системы ≠ 0, дискриминант определяет число корней);
- для дробей выражение из текста вычисляется заново на `Fraction`;
- для текстовых задач числа достаются регулярным выражением из условия и ответ пересчитывается по формуле;
- ответ-эталон, набранный на обычной клавиатуре (`-` вместо `−`), принимается проверкой для каждой из ~5000 сгенерированных задач;
- шаги решения содержат итоговые значения; в тексте и шагах нет `-3` вместо `−3`, `+ −` и «−0»;
- PDF собирается, кириллица и знак «−» извлекаются из него обратно, спецсимволы (`& < >`) экранируются.

Дополнительно `python scripts/mutate.py` ломает исходники по одной правке (смена `+`↔`−`, `==`↔`!=`, `and`↔`or` и т. п.) и проверяет, что тесты это замечают. Результат последнего прогона — в [`docs/QUALITY.md`](docs/QUALITY.md).

```bash
python -m unittest discover -s tests
python scripts/mutate.py           # около 10 минут
```

## Структура

```
mathgen/
  topics.py     генераторы тем и реестр (generate, from_id)
  problem.py    Problem: условие, точный ответ, шаги
  parse.py      разбор ответов, введённых человеком
  check.py      проверка и обратная связь
  worksheet.py  сборка вариантов без повторов, экспорт в Markdown/JSON
  pdf.py        PDF через reportlab (шрифт DejaVu лежит в mathgen/fonts)
  cli.py        командная строка
tests/          unittest, без внешних зависимостей
scripts/mutate.py   мутационная проверка тестов
```

## Ограничения

- Только то, что есть в таблице тем; в ответах нет иррациональных чисел (корни и дискриминанты подобраны так, чтобы `√D` был целым), нет неравенств и графиков.
- Проверяется итоговый ответ, а не ход решения ученика.
- Текстовые задачи используют несколько фиксированных сюжетов; разнообразие достигается числами, а не формулировками.
- Шрифт DejaVu распространяется по собственной свободной лицензии (`mathgen/fonts/LICENSE-DejaVu.txt`).

## English summary

`mathgen` generates school-level math problems (linear and quadratic equations, fractions, percentages, 2×2 systems, proportions, motion word problems) in three difficulty levels, with step-by-step solutions, and checks free-form answers **exactly** using `fractions.Fraction`. It builds PDF worksheets with several non-overlapping variants and an answer key. Every problem is identified by `topic/level/seed`, so any problem can be reproduced. The core has no dependencies; `reportlab` is only needed for PDF output. Tests verify every generated answer independently by re-evaluating the problem *text*, and a small mutation-testing script checks that the tests would catch regressions. User-facing texts are in Russian.

```bash
pip install reportlab
python -m mathgen worksheet --topics linear,quadratic --levels 1,2,3 --count 10 --variants 4 --seed 7 --out sheet.pdf
python -m mathgen check system/2/7 "x=-7; y=4"
```

## Лицензия

MIT, см. [LICENSE](LICENSE).
