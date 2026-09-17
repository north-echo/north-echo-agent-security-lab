#!/usr/bin/env python3
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} ROOT REQUEST", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve(strict=True)
    candidate = (root / sys.argv[2]).resolve(strict=True)
    try:
        candidate.relative_to(root)
    except ValueError:
        print("DENIED: resolved object is outside root", file=sys.stderr)
        return 1
    print(candidate.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
