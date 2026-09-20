from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import __version__
from .beginner import prepare as prepare_beginner
from .catalog import CATALOG, SCAFFOLDS, course_dir_name, normalize_target, target_dir_name, targets_for_scope
from .cleanup import CleanupPlan, execute_cleanup, plan_cleanup, register_user_unit
from .fixtures import generate
from .grading import evaluate, fresh_evaluation_fixture, load_grader
from .integrity import verify
from .paths import SafetyError, repo_root, safe_child
from .state import entry, lifecycle_lock, load, now, record_grade, save

BANNER = "NORTH ECHO AGENT SECURITY LAB"


def _source(root: Path, target: str) -> Path:
    if target == "capstone":
        return root / "course" / "capstone" / "lab"
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
        if not args.cold:
            raise ValueError("use: ./lab-start capstone --cold")
        target = "capstone"
    else:
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
        prepare_beginner(workspace, target, fixture)
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


def _remove_managed(root: Path, target: str, dry_run: bool, plan: CleanupPlan) -> list[str]:
    actions = list(execute_cleanup(plan, dry_run=dry_run))
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
    existing = [t for t in targets if any((root / area / t).exists() or (root / area / t).is_symlink()
                                         for area in (".student", ".fixtures", ".runtime"))]
    if not existing:
        print("Nothing to reset in that scope. Persistent attempt metadata is unchanged.")
        return 0
    if not (args.yes or args.dry_run):
        answer = input(f"Destroy {len(existing)} disposable workspace(s)? [y/N] ")
        if answer.lower() not in {"y", "yes"}:
            print("Reset cancelled.")
            return 1
    progress = load(root)
    plans = {target: plan_cleanup(root, target) for target in existing}
    for target in existing:
        for area in (".student", ".fixtures"):
            path = safe_child(root, area, target)
            if path.exists() and not path.is_dir():
                raise SafetyError(f"managed workspace is not a directory: {path}")
    all_actions: list[str] = []
    for target in existing:
        all_actions.extend(_remove_managed(root, target, args.dry_run, plans[target]))
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
    if target != "capstone" and (not target.endswith(".lab") or target not in CATALOG):
        raise ValueError("grade a playable module lab, for example: module-01")
    workspace = safe_child(root, ".student", target)
    if not workspace.exists():
        raise ValueError(f"start the lab first: ./lab-start {target}")
    progress = load(root)
    record = entry(progress, target)
    mode = args.mode or record.get("mode", "practice")
    fixture = fresh_evaluation_fixture(target)
    grader = load_grader(root, target.split(".")[0])
    checks = evaluate(grader, workspace, fixture)
    passed = all(check.passed for check in checks)
    record_grade(record, passed, mode, [check.name for check in checks if not check.passed])
    save(root, progress)
    heading = "COLD CAPSTONE" if target == "capstone" else f"MODULE {target.split('.')[0]} INDEPENDENT LAB"
    print(f"{BANNER}\n\n{heading} - {mode.upper()} MODE")
    for index, check in enumerate(checks, 1):
        dots = "." * max(2, 48 - len(check.name))
        print(f"[{index}/{len(checks)}] {check.name} {dots} {'PASS' if check.passed else 'FAIL'}")
    print(f"\nRESULT: {'PASSED' if passed else 'NOT PASSED'}")
    if not passed:
        print("\nFailed properties:")
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
    print("Beginner entry: b0.01 -> module-b0 -> b1.01 -> module-b1 -> 01.01; beta learner review pending.")
    print("TARGET   STATE       STARTS  GRADES  LAST     EVER  MODE      TITLE")
    for target in sorted(CATALOG):
        record = progress["targets"].get(target, {})
        active = (root / ".student" / target).exists()
        current = record.get("last_result") if active and record.get("last_graded_attempt") == record.get("starts") else None
        state = current.upper() if current else "ACTIVE" if active else "READY"
        ever = "yes" if record.get("ever_passed", record.get("passed")) else "no"
        print(f"{target:8} {state:11} {record.get('starts', 0):6}  {record.get('grade_attempts', 0):6}  {record.get('last_result', '-'):8} {ever:4}  {record.get('last_mode', record.get('mode', '-')):8}  {CATALOG[target][1]}")
    print("\nPLAYABLE KERNEL/TOOLING PREREQUISITES")
    print("05       Linux openat2 + Landlock ABI, Linux UAPI headers, static C toolchain")
    print("06       Linux seccomp filter mode, libseccomp development files, pkg-config, static C toolchain")
    print("07       unified cgroup v2 + delegated systemd user manager with cpu, memory, and pids")
    print("08       Linux unprivileged user + network namespaces and filesystem Unix sockets")
    print("09       Python 3 cryptographic standard library + filesystem Unix sockets; fake credentials only")
    print("10       Modules 03-09 prerequisites plus static C toolchain, Landlock, seccomp, namespaces, and delegated cgroup v2")
    print("11       Python 3 standard library; synthetic local evidence harness only")
    print("12       Python 3 standard library; bounded local oracle only")
    print("\nModules 01-12 and the cold capstone are playable.")
    return 0


def cmd_cleanup(args: argparse.Namespace) -> int:
    root = repo_root()
    targets = targets_for_scope("--all" if args.all else args.scope)
    actions = []
    plans = [plan_cleanup(root, target) for target in targets]
    for plan in plans:
        actions.extend(execute_cleanup(plan, dry_run=args.dry_run))
    print("CLEANUP " + ("DRY RUN" if args.dry_run else "COMPLETE"))
    for action in actions:
        print(f"  {action}")
    if not actions:
        print("  no registered runtime resources")
    return 0


def cmd_register_unit(args: argparse.Namespace) -> int:
    root = repo_root()
    target = normalize_target(args.target)
    if target not in CATALOG:
        raise ValueError(f"unknown or not-yet-playable target: {args.target}")
    path = register_user_unit(root, target, args.unit)
    print(f"REGISTERED USER UNIT\n  target: {target}\n  unit: {args.unit}\n  registry: {path}")
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
    register = sub.add_parser("register-unit", help=argparse.SUPPRESS)
    register.add_argument("target")
    register.add_argument("unit")
    register.set_defaults(func=cmd_register_unit)
    return root


def main(argv: list[str] | None = None) -> int:
    try:
        args = parser().parse_args(argv)
        with lifecycle_lock(repo_root()):
            return args.func(args)
    except (ValueError, SafetyError, OSError, subprocess.SubprocessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
