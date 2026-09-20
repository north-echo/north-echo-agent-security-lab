#!/usr/bin/env python3
"""Optional release QA: requires pdfplumber/pypdf, not guest lab prerequisites."""
import json
from pathlib import Path
import sys

import pdfplumber
from pypdf import PdfReader


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_manual_pdf.py MANUAL.pdf")
    path = Path(sys.argv[1])
    version = (Path(__file__).resolve().parents[1] / "VERSION").read_text().strip()
    reader = PdfReader(path)
    if f"v{version}" not in reader.metadata.title:
        raise SystemExit("PDF title/version mismatch")
    problems, locations = [], {}
    needles = ("B0.02 -", "05.02 -", "08.03 -", "09.03 -", "10.03 -",
               "11.02 -", "12.03 -", "Cold capstone -", "Claim-to-mechanism")
    with pdfplumber.open(path) as pdf:
        for index, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            if not text.strip():
                problems.append({"page": index, "issue": "empty page"})
            for needle in needles:
                if needle in text:
                    locations.setdefault(needle, []).append(index)
            for char in page.chars:
                if char["x0"] < 40 or char["x1"] > page.width - 40:
                    problems.append({"page": index, "issue": "horizontal overflow", "text": char["text"]})
                    break
            # ReportLab uses Zapf's "l" at six points for the intentional
            # margin-circle bullets. Other fallback glyphs remain suspicious.
            if any("ZapfDingbats" in char["fontname"] and not (
                    char["text"] == "l" and abs(char["size"] - 6) < .01
                    and abs(char["x0"] - 43.84) < .01) for char in page.chars):
                problems.append({"page": index, "issue": "possible missing glyph"})
    annotations = sum(len(page.get("/Annots", [])) for page in reader.pages)
    if not reader.outline or not annotations:
        problems.append({"issue": "missing navigation"})
    report = {"pdf": path.name, "pages": len(reader.pages), "annotations": annotations,
              "sample_locations": locations, "problems": problems,
              "limit": "Geometry/text checks do not replace rendered-page visual inspection."}
    print(json.dumps(report, indent=2))
    return bool(problems)


if __name__ == "__main__":
    raise SystemExit(main())
