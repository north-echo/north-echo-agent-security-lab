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
from reportlab.platypus import KeepTogether, ListFlowable, ListItem, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer


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
    in_code = False

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

    for line in lines:
        if line.startswith("```"):
            if in_code:
                story.append(Spacer(1, 10))
                story.append(KeepTogether([Preformatted("\n".join(code), styles["CodeBlock"])]))
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
        if line.strip() == "<!-- PAGEBREAK -->":
            flush_paragraph()
            flush_bullets()
            story.append(PageBreak())
            continue
        if line.startswith("# "):
            flush_paragraph()
            flush_bullets()
            if story:
                story.append(PageBreak())
            story.append(Paragraph(escape(line[2:]), styles["Title"]))
            story.append(Spacer(1, 12))
        elif line.startswith("## "):
            flush_paragraph()
            flush_bullets()
            story.append(Paragraph(escape(line[3:]), styles["Heading2"]))
            story.append(Spacer(1, 5))
        elif line.startswith("### "):
            flush_paragraph()
            flush_bullets()
            story.append(Paragraph(escape(line[4:]), styles["Heading3"]))
            story.append(Spacer(1, 3))
        elif line.startswith("#### "):
            flush_paragraph()
            flush_bullets()
            story.append(Paragraph(inline_markup(line[5:]), styles["Heading4"]))
            story.append(Spacer(1, 2))
        elif line.startswith("> "):
            flush_paragraph()
            flush_bullets()
            story.append(Paragraph(inline_markup(line[2:]), styles["Callout"]))
            story.append(Spacer(1, 5))
        elif line.startswith("- "):
            flush_paragraph()
            bullets.append(inline_markup(line[2:]))
        elif not line.strip():
            flush_paragraph()
            flush_bullets()
        else:
            flush_bullets()
            paragraph.append(line)
    flush_paragraph()
    flush_bullets()
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
