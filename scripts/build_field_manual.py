#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "FIELD_MANUAL.md"
SOURCES = [
    ROOT / "docs" / "VM_SETUP.md",
    ROOT / "docs" / "SOURCE_TRUTH.md",
    ROOT / "docs" / "BEGINNER_FIELD_MANUAL.md",
    ROOT / "docs" / "LEARNING_PATH.md",
    ROOT / "docs" / "MANUAL_MODULES_01_03.md",
    *(ROOT / "docs" / f"MANUAL_MODULE_{module:02d}.md" for module in range(4, 13)),
    ROOT / "course" / "capstone" / "lab" / "README.md",
]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
HEADER = f"""# North Echo Agent Security Lab - Complete Field Manual v{VERSION}

Learner-review beta: setup, source/version notes, beginner entry chapters, learning path, twelve rewritten technical modules, and an independent capstone. Use only a disposable Linux VM with synthetic data. Complete source listings and local explanations support guided practice; independent labs withhold implementations. Automated validation does not establish beginner comprehension or production security. See the release's validation records for exact scope.

<!-- PAGEBREAK -->"""


INCLUDE = re.compile(r'<!-- source: ([^\n]+) format=(code|markdown) -->\n.*?<!-- /source -->', re.DOTALL)


def synchronized_chapter(path: Path, ancestors: tuple[Path, ...] = ()) -> str:
    path = path.resolve()
    if path in ancestors:
        raise ValueError(f"cyclic manual include: {path}")
    def expand(match):
        relative, kind = match.group(1, 2)
        source = (ROOT / relative).resolve()
        if (ROOT / "course").resolve() not in source.parents:
            raise ValueError(f"manual source must be within course/: {relative}")
        body = (synchronized_chapter(source, (*ancestors, path)) if kind == "markdown"
                else source.read_text(encoding="utf-8")).rstrip()
        if kind == "code":
            language = {".py": "python", ".c": "c", ".json": "json", ".sh": "bash"}.get(source.suffix, "text")
            body = f"```{language}\n{body}\n```"
        else:
            # Embedded chapters contain expanded listings, not nested include
            # delimiters that would make the next synchronization ambiguous.
            body = re.sub(r"^<!-- (?:source: [^\n]+|/source) -->\n?", "", body, flags=re.MULTILINE).rstrip()
        return f"<!-- source: {relative} format={kind} -->\n{body}\n<!-- /source -->"
    return INCLUDE.sub(expand, path.read_text(encoding="utf-8"))


def render() -> str:
    sections = [HEADER, *(synchronized_chapter(path).rstrip() for path in SOURCES)]
    return "\n\n".join(sections) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if FIELD_MANUAL.md is stale")
    args = parser.parse_args()
    expected = render()
    # Guided README files are readable by themselves in the student workspace,
    # including full listings. Synchronize them as well as their manual embeds.
    course_readmes = sorted((ROOT / "course").glob("**/README.md"))
    stale = [path for path in dict.fromkeys([*course_readmes, *SOURCES])
             if synchronized_chapter(path) != path.read_text(encoding="utf-8")]
    if args.check:
        if stale or not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != expected:
            for path in stale:
                print(f"Canonical source listing is stale: {path.relative_to(ROOT)}")
            print("FIELD_MANUAL.md is stale; run scripts/build_field_manual.py")
            return 1
        print("FIELD_MANUAL.md is synchronized")
        return 0
    for path in stale:
        path.write_text(synchronized_chapter(path), encoding="utf-8")
    OUTPUT.write_text(expected, encoding="utf-8")
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
