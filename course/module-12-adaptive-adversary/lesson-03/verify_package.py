#!/usr/bin/env python3
"""Check the fixed local package inventory without executing packaged code."""
import hashlib
import json
from pathlib import Path
import re
import sys

FILES = {"runner.py", "oracle.py", "scenario.json", "expected.json", "spec.json"}


def verify(root):
    manifest = root / "package.json"
    if root.is_symlink() or manifest.is_symlink() or not manifest.is_file():
        raise ValueError("expected an ordinary package directory and manifest")
    package = json.loads(manifest.read_text())
    hashes = package.get("sha256") if isinstance(package, dict) else None
    if not isinstance(hashes, dict) or set(hashes) != FILES:
        raise ValueError("unexpected package inventory")
    for name in sorted(FILES):
        digest = hashes[name]
        path = root / name
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("invalid digest")
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"missing or non-regular package file: {name}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"checksum mismatch: {name}")
    print("PACKAGE BYTES MATCH RECORDED INVENTORY; AUTHENTICITY IS NOT ESTABLISHED")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_package.py DIRECTORY")
    try:
        verify(Path(sys.argv[1]))
    except (OSError, ValueError) as error:
        raise SystemExit(f"package verification failed: {error}")
