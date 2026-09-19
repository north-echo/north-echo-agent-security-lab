#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "FIELD_MANUAL.md"
SOURCES = [
    ROOT / "docs" / "MANUAL_MODULES_01_03.md",
    *(ROOT / "docs" / f"MANUAL_MODULE_{module:02d}.md" for module in range(4, 13)),
]
HEADER = """# North Echo Agent Security Lab - Complete Field Manual v1.0.1

This release manual combines the twelve validated module chapters. The cold capstone contract is in the repository and deliberately contains no guided solution.

<!-- PAGEBREAK -->"""


def render() -> str:
    sections = [HEADER, *(path.read_text(encoding="utf-8").rstrip() for path in SOURCES)]
    return "\n\n".join(sections) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if FIELD_MANUAL.md is stale")
    args = parser.parse_args()
    expected = render()
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != expected:
            print("FIELD_MANUAL.md is stale; run scripts/build_field_manual.py")
            return 1
        print("FIELD_MANUAL.md is synchronized")
        return 0
    OUTPUT.write_text(expected, encoding="utf-8")
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
