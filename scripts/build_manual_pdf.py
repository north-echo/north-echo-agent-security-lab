#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import ListFlowable, ListItem, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline_markup(text: str) -> str:
    value = escape(text)
    value = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    return value


def parse_markdown(markdown: str, styles: dict) -> list:
    story = []
    lines = markdown.splitlines()
    paragraph: list[str] = []
    bullets: list[str] = []
    code: list[str] = []
    table: list[list[str]] = []
    in_code = False
    included_markdown = False

    def flush_paragraph():
        if paragraph:
            text = " ".join(value.strip() for value in paragraph)
            text = inline_markup(text)
            story.append(Paragraph(text, styles["BodyText"]))
            story.append(Spacer(1, 5))
            paragraph.clear()

    def flush_bullets():
        if bullets:
            items = [ListItem(Paragraph(item, styles["BulletText"]), leftIndent=0) for item in bullets]
            story.append(
                ListFlowable(
                    items,
                    bulletType="bullet",
                    start="circle",
                    leftIndent=14,
                    bulletFontName="Helvetica",
                    bulletFontSize=6,
                    bulletOffsetY=1,
                    spaceBefore=5,
                    spaceAfter=5,
                )
            )
            bullets.clear()

    def flush_table():
        if not table:
            return
        columns = len(table[0])
        if any(len(row) != columns for row in table):
            raise ValueError("inconsistent Markdown table column count")
        width = LETTER[0] - 1.44 * inch - 12
        widths = ([width * .23, width * .77] if columns == 2 else [width / columns] * columns)
        rows = [[Paragraph(inline_markup(cell), styles["BodyText"]) for cell in row] for row in table]
        rendered = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
        rendered.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0f2fe")),
            ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.extend([rendered, Spacer(1, 8)])
        table.clear()

    def page_break():
        if story and not isinstance(story[-1], PageBreak):
            story.append(PageBreak())

    for line in lines:
        if not in_code and line.startswith("|") and line.rstrip().endswith("|"):
            flush_paragraph()
            flush_bullets()
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-+:?", cell) for cell in cells):
                table.append(cells)
            continue
        if not in_code:
            flush_table()
        if line.startswith("```"):
            if in_code:
                story.append(Spacer(1, 10))
                if any(len(value) > 104 for value in code):
                    story.append(Paragraph("Display only: long source lines wrap with a &gt; marker; do not type that marker or its display newline.", styles["BulletText"]))
                story.append(Preformatted("\n".join(code), styles["CodeBlock"],
                                          maxLineLength=104, newLineChars="    > "))
                story.append(Spacer(1, 9))
                code.clear()
                in_code = False
            else:
                flush_paragraph()
                flush_bullets()
                in_code = True
            continue
        if in_code:
            code.append(line)
            continue
        if line.startswith("<!-- source:"):
            included_markdown = "format=markdown" in line
            continue
        if line == "<!-- /source -->":
            included_markdown = False
            continue
        if included_markdown and re.match(r"^#{1,4} ", line):
            heading, title = line.split(" ", 1)
            line = "#" * min(4, len(heading) + 1) + " " + title
        if line.strip() == "<!-- PAGEBREAK -->":
            flush_paragraph()
            flush_bullets()
            page_break()
            continue
        if line.startswith("# "):
            flush_paragraph()
            flush_bullets()
            page_break()
            story.append(Paragraph(escape(line[2:]), styles["Title"]))
            story.append(Spacer(1, 12))
        elif line.startswith("## "):
            flush_paragraph()
            flush_bullets()
            story.append(Paragraph(escape(line[3:]), styles["Heading2"]))
        elif line.startswith("### "):
            flush_paragraph()
            flush_bullets()
            story.append(Paragraph(escape(line[4:]), styles["Heading3"]))
        elif line.startswith("#### "):
            flush_paragraph()
            flush_bullets()
            story.append(Paragraph(inline_markup(line[5:]), styles["Heading4"]))
        elif line.startswith("> "):
            flush_paragraph()
            flush_bullets()
            story.append(Paragraph(inline_markup(line[2:]), styles["Callout"]))
            story.append(Spacer(1, 5))
        elif line.startswith("- "):
            flush_paragraph()
            bullets.append(inline_markup(line[2:]))
        elif bullets and line.startswith("  "):
            bullets[-1] += " " + inline_markup(line.strip())
        elif not line.strip():
            flush_paragraph()
            flush_bullets()
        else:
            flush_bullets()
            paragraph.append(line)
    flush_paragraph()
    flush_bullets()
    flush_table()
    return story


def make_footer(version: str):
    def footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#cbd5e1"))
        canvas.line(0.72 * inch, 0.54 * inch, 7.78 * inch, 0.54 * inch)
        canvas.setFillColor(colors.HexColor("#475569"))
        canvas.setFont("Helvetica", 8)
        canvas.drawString(0.72 * inch, 0.36 * inch, f"North Echo Agent Security Lab - v{version} field manual")
        canvas.drawRightString(7.78 * inch, 0.36 * inch, f"{document.page}")
        canvas.restoreState()

    return footer


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: build_manual_pdf.py INPUT.md OUTPUT.pdf", file=sys.stderr)
        return 2
    source, output = map(Path, sys.argv[1:])
    output.parent.mkdir(parents=True, exist_ok=True)
    markdown = source.read_text(encoding="utf-8")
    version_match = re.search(r"^# North Echo Agent Security Lab - Complete Field Manual v([0-9]+\.[0-9]+\.[0-9]+)$", markdown, re.MULTILINE)
    if version_match is None:
        print("field manual title does not contain a semantic version", file=sys.stderr)
        return 2
    version = version_match.group(1)
    sample = getSampleStyleSheet()
    styles = {
        "Title": ParagraphStyle("NE Title", parent=sample["Title"], fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=colors.HexColor("#0f172a"), alignment=TA_LEFT, spaceAfter=10),
        "Heading2": ParagraphStyle("NE H2", parent=sample["Heading2"], fontName="Helvetica-Bold", fontSize=14, leading=17, textColor=colors.HexColor("#075985"), spaceBefore=10, keepWithNext=True),
        "Heading3": ParagraphStyle("NE H3", parent=sample["Heading3"], fontName="Helvetica-Bold", fontSize=11.5, leading=14, textColor=colors.HexColor("#0f4c6e"), spaceBefore=8, keepWithNext=True),
        "Heading4": ParagraphStyle("NE H4", parent=sample["Heading4"], fontName="Helvetica-Bold", fontSize=9.8, leading=12, textColor=colors.HexColor("#334155"), spaceBefore=6, keepWithNext=True),
        "BodyText": ParagraphStyle("NE Body", parent=sample["BodyText"], fontName="Helvetica", fontSize=9.4, leading=13.6, textColor=colors.HexColor("#1e293b")),
        "BulletText": ParagraphStyle("NE Bullet", parent=sample["BodyText"], fontName="Helvetica", fontSize=9.1, leading=13.2, textColor=colors.HexColor("#1e293b"), spaceAfter=2),
        "Callout": ParagraphStyle("NE Callout", parent=sample["BodyText"], fontName="Helvetica", fontSize=9.1, leading=13.2, textColor=colors.HexColor("#0f172a"), backColor=colors.HexColor("#e0f2fe"), borderColor=colors.HexColor("#7dd3fc"), borderWidth=0.6, borderPadding=7, spaceBefore=3, spaceAfter=4),
        "CodeBlock": ParagraphStyle("NE Code", fontName="Courier", fontSize=7.5, leading=9.5, leftIndent=8, rightIndent=8, borderColor=colors.HexColor("#cbd5e1"), borderWidth=0.5, borderPadding=7, backColor=colors.HexColor("#f8fafc"), textColor=colors.HexColor("#0f172a")),
    }
    document = SimpleDocTemplate(
        str(output), pagesize=LETTER, leftMargin=0.72 * inch, rightMargin=0.72 * inch,
        topMargin=0.68 * inch, bottomMargin=0.72 * inch,
        title=f"North Echo Agent Security Lab v{version} Field Manual",
        author="North Echo",
        subject="Hands-on Linux containment training, Modules 01-12",
    )
    story = parse_markdown(markdown, styles)
    footer = make_footer(version)
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
