#!/usr/bin/env python3
"""Run the suite; supported Linux validation must exercise every test."""
import argparse
from pathlib import Path
import sys
import unittest

def main():
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-no-skips", action="store_true")
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.discover(str(root / "tests"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if args.require_no_skips and not result.testsRun:
        print("VALIDATION FAILED: no tests were discovered", file=sys.stderr)
        return 1
    if args.require_no_skips and result.skipped:
        print("VALIDATION FAILED: required tests were skipped", file=sys.stderr)
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
