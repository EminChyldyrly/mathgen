"""PDF-листки (reportlab). Шрифт DejaVu лежит в пакете, поэтому кириллица и «−» работают везде."""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from .worksheet import Worksheet

_FONTS = Path(__file__).with_name("fonts")
_SPACE_CM = {1: 1.6, 2: 2.2, 3: 3.0}


def _register():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    if "DejaVu" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("DejaVu", str(_FONTS / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(_FONTS / "DejaVuSans-Bold.ttf")))
        pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold")


def write_pdf(ws: Worksheet, path, solutions: bool = False, key: bool = True) -> None:
    try:
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                        Table, TableStyle)
    except ImportError as e:                                           # pragma: no cover
        raise RuntimeError("для PDF нужен пакет reportlab: pip install reportlab "
                           "(форматы .md и .json работают без него)") from e
    _register()
    base = ParagraphStyle("base", fontName="DejaVu", fontSize=11, leading=16)
    h1 = ParagraphStyle("h1", parent=base, fontName="DejaVu-Bold", fontSize=15, leading=20, spaceAfter=4)
    small = ParagraphStyle("small", parent=base, fontSize=8.5, leading=11, textColor="#555555")
    step = ParagraphStyle("step", parent=base, fontSize=9, leading=12, leftIndent=18, textColor="#333333")
    center = ParagraphStyle("center", parent=base, alignment=TA_CENTER)

    def para(text, style):
        return Paragraph(escape(text).replace("\n", "<br/>"), style)

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("DejaVu", 8)
        canvas.setFillGray(0.5)
        canvas.drawString(2 * cm, 1.2 * cm, f"mathgen · seed {ws.seed}")
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"стр. {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=1.8 * cm, bottomMargin=2 * cm, title=ws.title, author="mathgen")
    flow = []
    for v, probs in enumerate(ws.variants, 1):
        if v > 1:
            flow.append(PageBreak())
        flow += [para(ws.title, h1), para(f"Вариант {v}", base),
                 para("ФИО ______________________________   Группа ________   Дата __________", base),
                 Spacer(1, 0.5 * cm)]
        for i, p in enumerate(probs, 1):
            flow.append(KeepTogether([para(f"{i}. {p.text}", base),
                                      Spacer(1, _SPACE_CM[p.level] * cm * (1.4 if p.topic == "system" else 1))]))
    if key:
        for v, probs in enumerate(ws.variants, 1):
            flow += [PageBreak(), para(f"Ключ — вариант {v}", h1), Spacer(1, 0.3 * cm)]
            if not solutions:
                rows = [["№", "Ответ", "Задача (id)"]] + [[str(i), p.answer_text, p.id] for i, p in enumerate(probs, 1)]
                t = Table([[Paragraph(escape(c), base if r else small) for c in row] for r, row in enumerate(rows)],
                          colWidths=[1.2 * cm, 8 * cm, 6.5 * cm], repeatRows=1)
                t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.25, "#bbbbbb"),
                                       ("VALIGN", (0, 0), (-1, -1), "TOP")]))
                flow.append(t)
            else:
                for i, p in enumerate(probs, 1):
                    block = [para(f"{i}. {p.text}", base)] + [para(s, step) for s in p.steps]
                    block += [para(p.id, small), Spacer(1, 0.3 * cm)]
                    flow.append(KeepTogether(block))
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)
