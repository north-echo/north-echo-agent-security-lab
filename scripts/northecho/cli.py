from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from . import __version__
from .catalog import CATALOG, SCAFFOLDS, course_dir_name, normalize_target, target_dir_name, targets_for_scope
from .cleanup import cleanup_target
from .fixtures import generate
from .grading import fresh_evaluation_fixture, load_grader
from .integrity import verify
from .paths import SafetyError, repo_root, safe_child
from .state import entry, load, now, save

BANNER = "NORTH ECHO AGENT SECURITY LAB"


def _source(root: Path, target: str) -> Path:
    module = target.split(".")[0]
    return root / "course" / course_dir_name(module) / target_dir_name(target)


def _print_integrity_failure(problems: list[str]) -> None:
    print("Canonical course integrity check failed:", file=sys.stderr)
    for problem in problems:
        print(f"  - {problem}", file=sys.stderr)
    print("Restore the repository before creating a student workspace.", file=sys.stderr)


def cmd_start(args: argparse.Namespace) -> int:
    root = repo_root()
    if args.target == "capstone":
        if args.cold:
            print(f"{BANNER}\n\nCold-start capstone is scaffolded but not implemented in v{__version__}; no workspace was created.")
            return 3
        raise ValueError("use: ./lab-start capstone --cold")
    target = normalize_target(args.target)
    if target not in CATALOG:
        module = target.split(".")[0]
        if module in SCAFFOLDS:
            print(f"Module {module} is scaffolded, not playable in v{__version__}: {SCAFFOLDS[module]}")
            return 3
        raise ValueError(f"unknown target: {args.target}")
    problems = verify(root)
    if problems:
        _print_integrity_failure(problems)
        return 2
    workspace = safe_child(root, ".student", target)
    fixture_dir = safe_child(root, ".fixtures", target)
    progress = load(root)
    record = entry(progress, target)
    if workspace.exists():
        print(f"{BANNER}\n\nRESUME {target} - {CATALOG[target][1]}")
        print(f"Workspace: {workspace}\nMode: {record.get('mode', 'practice')}\nStarts: {record['starts']}")
        return 0
    if fixture_dir.exists():
        raise SafetyError(f"orphan fixture directory exists; run ./lab-reset {target} --yes")
    record["starts"] += 1
    record["mode"] = args.mode
    record["last_started_at"] = now()
    try:
        fixture = generate(fixture_dir, target, record["starts"])
        shutil.copytree(_source(root, target), workspace, symlinks=False)
        metadata = {
            "schema": 1,
            "target": target,
            "attempt": record["starts"],
            "mode": args.mode,
            "fixture_id": fixture["fixture_id"],
            "synthetic_user": fixture["synthetic_user"],
            "synthetic_port": fixture["port"],
            "fixture_manifest": str(fixture_dir / "manifest.json"),
        }
        (workspace / ".north-echo.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        (workspace / "FIXTURE.txt").write_text(
            f"fixture_id={fixture['fixture_id']}\nsynthetic_user={fixture['synthetic_user']}\nsynthetic_port={fixture['port']}\n",
            encoding="utf-8",
        )
        save(root, progress)
    except Exception:
        if workspace.exists() and not workspace.is_symlink():
            shutil.rmtree(workspace)
        if fixture_dir.exists() and not fixture_dir.is_symlink():
            shutil.rmtree(fixture_dir)
        raise
    print(f"{BANNER}\n\nSTART {target} - {CATALOG[target][1]}")
    print("Creating clean workspace... done\nGenerating synthetic fixtures... done\nVerifying canonical course... done")
    print(f"\nREADY\nWorkspace: {workspace}\nMode: {args.mode}\nAttempt: {record['starts']}")
    print("Open README.md in the workspace and begin with Exercise 1.")
    return 0


def _remove_managed(root: Path, target: str, dry_run: bool) -> list[str]:
    actions = cleanup_target(root, target, dry_run=dry_run)
    for area in (".student", ".fixtures"):
        path = safe_child(root, area, target)
        if path.exists() or path.is_symlink():
            if path.is_symlink():
                raise SafetyError(f"refusing reset through symlink: {path}")
            actions.append(f"remove {path}")
            if not dry_run:
                shutil.rmtree(path)
    return actions


def cmd_reset(args: argparse.Namespace) -> int:
    root = repo_root()
    scope = "--all" if args.all else args.scope
    if not scope:
        raise ValueError("provide a lesson, module-NN, or --all")
    targets = targets_for_scope(scope)
    existing = [t for t in targets if (root / ".student" / t).exists() or (root / ".fixtures" / t).exists() or (root / ".runtime" / t).exists()]
    if not existing:
        print("Nothing to reset in that scope. Persistent attempt metadata is unchanged.")
        return 0
    if not (args.yes or args.dry_run):
        answer = input(f"Destroy {len(existing)} disposable workspace(s)? [y/N] ")
        if answer.lower() not in {"y", "yes"}:
            print("Reset cancelled.")
            return 1
    progress = load(root)
    all_actions: list[str] = []
    for target in existing:
        all_actions.extend(_remove_managed(root, target, args.dry_run))
        if not args.dry_run:
            record = entry(progress, target)
            record["resets"] += 1
            record["last_reset_at"] = now()
    if not args.dry_run:
        save(root, progress)
    heading = "DRY RUN" if args.dry_run else "RESET COMPLETE"
    print(f"{BANNER}\n\n{heading}")
    for action in all_actions:
        print(f"  {action}")
    print("\nAttempt/pass metadata was preserved; student source and fixtures were not.")
    return 0


def cmd_grade(args: argparse.Namespace) -> int:
    root = repo_root()
    target = normalize_target(args.target)
    if not target.endswith(".lab") or target not in CATALOG:
        raise ValueError("grade a playable module lab, for example: module-01")
    workspace = safe_child(root, ".student", target)
    if not workspace.exists():
        raise ValueError(f"start the lab first: ./lab-start {target}")
    progress = load(root)
    record = entry(progress, target)
    mode = args.mode or record.get("mode", "practice")
    fixture = fresh_evaluation_fixture(target)
    grader = load_grader(root, target.split(".")[0])
    checks = grader.grade(workspace, fixture)
    passed = all(check.passed for check in checks)
    record["grade_attempts"] += 1
    record["last_graded_at"] = now()
    if passed:
        record["passed"] = True
        record["passed_at"] = now()
    save(root, progress)
    print(f"{BANNER}\n\nMODULE {target.split('.')[0]} INDEPENDENT LAB - {mode.upper()} MODE")
    for index, check in enumerate(checks, 1):
        dots = "." * max(2, 48 - len(check.name))
        print(f"[{index}/{len(checks)}] {check.name} {dots} {'PASS' if check.passed else 'FAIL'}")
    print(f"\nRESULT: {'PASSED' if passed else 'NOT PASSED'}")
    if not passed:
        print("\nFailed security properties:")
        for check in checks:
            if not check.passed:
                print(f"  - {check.name}")
                if mode == "practice" and check.practice_hint:
                    print(f"    Review: {check.practice_hint}")
        if mode == "exam":
            print("\nExam mode withholds lesson references and implementation hints.")
    return 0 if passed else 1


def cmd_status(args: argparse.Namespace) -> int:
    root = repo_root()
    progress = load(root)
    print(f"{BANNER}\n\nv{__version__} COURSE STATUS")
    print("TARGET   STATE       STARTS  GRADES  MODE      TITLE")
    for target in sorted(CATALOG):
        record = progress["targets"].get(target, {})
        active = (root / ".student" / target).exists()
        state = "PASSED" if record.get("passed") else "ACTIVE" if active else "READY"
        print(f"{target:8} {state:11} {record.get('starts', 0):6}  {record.get('grade_attempts', 0):6}  {record.get('mode', '-'):8}  {CATALOG[target][1]}")
    print("\nPLAYABLE KERNEL/TOOLING PREREQUISITES")
    print("05       Linux openat2 + Landlock ABI, Linux UAPI headers, static C toolchain")
    print("06       Linux seccomp filter mode, libseccomp development files, pkg-config, static C toolchain")
    print("\nModules 01-06: playable. Modules 07-12: scaffolded. Capstone: planned (--cold accepted as a concept check).")
    return 0


def cmd_cleanup(args: argparse.Namespace) -> int:
    root = repo_root()
    targets = targets_for_scope("--all" if args.all else args.scope)
    actions = []
    for target in targets:
        actions.extend(cleanup_target(root, target, dry_run=args.dry_run))
    print("CLEANUP " + ("DRY RUN" if args.dry_run else "COMPLETE"))
    for action in actions:
        print(f"  {action}")
    if not actions:
        print("  no registered runtime resources")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="labctl")
    root.add_argument("--version", action="version", version=__version__)
    sub = root.add_subparsers(dest="command", required=True)
    start = sub.add_parser("start")
    start.add_argument("target")
    start.add_argument("--mode", choices=("practice", "exam"), default="practice")
    start.add_argument("--cold", action="store_true")
    start.set_defaults(func=cmd_start)
    reset = sub.add_parser("reset")
    reset.add_argument("scope", nargs="?")
    reset.add_argument("--all", action="store_true")
    reset.add_argument("--yes", action="store_true")
    reset.add_argument("--dry-run", action="store_true")
    reset.set_defaults(func=cmd_reset)
    grade = sub.add_parser("grade")
    grade.add_argument("target")
    grade.add_argument("--mode", choices=("practice", "exam"))
    grade.set_defaults(func=cmd_grade)
    status = sub.add_parser("status")
    status.set_defaults(func=cmd_status)
    cleanup = sub.add_parser("cleanup")
    cleanup.add_argument("scope", nargs="?", default="--all")
    cleanup.add_argument("--all", action="store_true")
    cleanup.add_argument("--dry-run", action="store_true")
    cleanup.set_defaults(func=cmd_cleanup)
    return root


def main(argv: list[str] | None = None) -> int:
    try:
        args = parser().parse_args(argv)
        return args.func(args)
    except (ValueError, SafetyError, FileNotFoundError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
