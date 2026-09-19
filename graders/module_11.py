from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from northecho.grading import Check, result_object, run_bounded

SECURE = {"execution": "argv", "environment": "minimal", "filesystem": "resolved",
          "network": "broker_only", "cleanup": "owned"}
WEAK = {"execution": "shell", "environment": "inherit", "filesystem": "lexical",
        "network": "direct", "cleanup": "prefix"}


def _run(agent: Path, source: Path, output: Path, cwd: Path):
    try:
        return run_bounded([sys.executable, str(agent), str(source), str(output)], cwd=cwd,
                              text=True, capture_output=True, timeout=5)
    except subprocess.TimeoutExpired:
        return None


def _load(path: Path):
    try:
        return result_object(path)
    except (OSError, ValueError):
        return None


def grade(workspace: Path, fixture: dict) -> list[Check]:
    source = workspace / "repair_variant.py"
    if not source.is_file():
        return [Check("A variant repair tool is present", False, "Module 11 lab contract")]
    results = {name: True for name in ("shape", "preserve", "function", "shell", "environment",
                                       "filesystem", "network", "cleanup", "all", "idempotent")}
    with tempfile.TemporaryDirectory(prefix="north-echo-grade-11-") as raw:
        work = Path(raw)
        agent = work / "repair_variant.py"
        shutil.copy2(source, agent)
        agent.chmod(0o444)
        harness = Path(__file__).resolve().parents[1] / "course/module-11-break-fix-research/lesson-01/variant_harness.py"
        rng = random.Random(fixture["hostname"] + fixture["canary"])
        variants = []
        for index in range(6):
            controls = dict(SECURE)
            chosen = rng.sample(sorted(WEAK), 1 + index % len(WEAK))
            for name in chosen:
                controls[name] = WEAK[name]
            variants.append({
                "schema": 1, "variant_id": f"{fixture['hostname']}-{index}",
                "workload": {"operation": "read", "resource": f"record:{index}",
                             "literal": f"literal {fixture['hostname']} $(touch shell-marker)"},
                "controls": controls,
            })
        for index, variant in enumerate(variants):
            input_path, output_path = work / f"input-{index}.json", work / f"output-{index}.json"
            input_path.write_text(json.dumps(variant), encoding="utf-8")
            before = input_path.read_bytes()
            run = _run(agent, input_path, output_path, work)
            repaired = _load(output_path)
            results["shape"] &= bool(run and run.returncode == 0 and isinstance(repaired, dict))
            if not isinstance(repaired, dict):
                for name in results:
                    results[name] = False
                continue
            results["preserve"] &= (input_path.read_bytes() == before and
                                    repaired.get("variant_id") == variant["variant_id"] and
                                    repaired.get("workload") == variant["workload"])
            results["all"] &= repaired.get("controls") == SECURE
            evidence_path = work / f"evidence-{index}.json"
            harness_work = work / f"harness-{index}"
            environment = dict(os.environ)
            environment["NORTH_ECHO_FAKE_CREDENTIAL"] = "FAKE-" + fixture["canary"]
            observed = run_bounded([sys.executable, str(harness), str(output_path),
                                       str(evidence_path), str(harness_work)], text=True,
                                      capture_output=True, timeout=5, env=environment)
            evidence = _load(evidence_path)
            results["function"] &= bool(observed.returncode == 0 and evidence and evidence.get("allowed_operation") is True)
            for name, signal in (("shell", "shell_marker_created"),
                                 ("environment", "credential_visible"),
                                 ("filesystem", "protected_read"),
                                 ("network", "inet_created"),
                                 ("cleanup", "cleanup_decoy_selected")):
                results[name] &= bool(evidence and evidence.get(signal) is False)
            second = work / f"second-{index}.json"
            rerun = _run(agent, output_path, second, work)
            results["idempotent"] &= bool(rerun and rerun.returncode == 0 and _load(second) == repaired)

        invalid = work / "invalid.json"
        invalid.write_text('{"schema":1,"controls":{}}\n', encoding="utf-8")
        invalid_output = work / "invalid-output.json"
        invalid_run = _run(agent, invalid, invalid_output, work)
        results["invalid"] = bool(invalid_run and invalid_run.returncode != 0 and not invalid_output.exists())

    return [
        Check("Every randomized plan produces a valid repaired plan", results["shape"], "Module 11 lesson 03"),
        Check("Variant identity, workload, and input file are preserved", results["preserve"], "Module 11 lesson 03"),
        Check("The allowed synthetic operation still works", results["function"], "Module 11 lessons 01 and 03"),
        Check("Literal argv cannot create a shell marker", results["shell"], "Module 11 lesson 01; Module 04"),
        Check("The child cannot observe the fake ambient credential", results["environment"], "Module 11 lesson 02; Module 09"),
        Check("The protected symlink target cannot be read", results["filesystem"], "Module 11 lesson 02; Module 05"),
        Check("The workload receives no direct IPv4 socket authority", results["network"], "Module 11 lesson 02; Module 08"),
        Check("Cleanup excludes the unowned prefix-matching decoy", results["cleanup"], "Module 11 lesson 02; platform cleanup contract"),
        Check("All simultaneous seeded weaknesses are repaired", results["all"], "Module 11 lesson 03"),
        Check("Repair is idempotent on a hardened plan", results["idempotent"], "Module 11 lesson 03"),
        Check("Malformed or unknown plans fail without output", results["invalid"], "Module 11 lab contract"),
    ]
