# Cold capstone - Process an ordered batch of contained jobs

## Objective and prerequisites

Build `cold_runtime.py`: a batch launcher that completes useful work under different resource ceilings, preserves each job's identity and ordinary failure status, and collects every exact owned runtime. This transfers single-job skills to a new interface; it is not a request to paste the Module 10 launcher unchanged.

Complete B0/B1 as needed, Modules 01-12, their practicals, and the cumulative checkpoints. Before beginning, revisit the **practice**, not a complete capstone solution: the 0/7/0 static worker sequence and validation-order question in 10.03, structured lists/status aggregation in Module 04, and evidence limits in Modules 11-12.

## Prepare a cold workspace and read the starter

From the course root:

```bash
./lab-start capstone --cold
cd .student/capstone
pwd
ls -l cold_runtime.py
cat cold_runtime.py
nano cold_runtime.py
```

Cold start resets an existing capstone attempt; export your notes first if you want to retain them. No guided solution is copied into this workspace. Edit only this prepared source. Ctrl+O then Enter saves in default nano; Ctrl+X exits.

<!-- source: course/capstone/lab/cold_runtime.py format=code -->
```python
#!/usr/bin/env python3
"""Runnable batch starter. Direct execution deliberately lacks outer controls."""
import json
from pathlib import Path
import subprocess
import sys

batch = json.loads(Path(sys.argv[1]).read_text())
rows = []
for job in batch["jobs"]:
    spec = job["runtime"]
    run = subprocess.run([spec["guard"], spec["allowed_root"], *spec["command"]],
                         text=True, capture_output=True, timeout=20)
    rows.append({"id": job["id"], "result": {
        "schema": 1, "status": run.returncode, "stdout": run.stdout,
        "stderr": run.stderr, "unit": None, "attestation": None,
    }})
Path(sys.argv[2]).write_text(json.dumps({"schema": 2, "jobs": rows}) + "\n")
raise SystemExit(any(row["result"]["status"] != 0 for row in rows))
```
<!-- /source -->

### Starter, line by line

- The imports provide JSON, paths, foreground execution, and process arguments.
- The starter parses a batch but does not validate its complete shape before acting.
- The loop visits jobs in input order and constructs guard/workload argv as separate values.
- Direct execution can apply the supplied inner guard but creates no outer unit, resource profile, or fresh namespace.
- Each row retains identity, stdout, stderr, and ordinary child status. Unit and attestation are explicitly missing.
- The final batch is written after the loop. Any nonzero ordinary child status produces nonzero overall status.

That is a functional baseline, not successful containment. Do not remove the guard or hide failed jobs to make the output look successful.

## Batch interface and validation

```text
python3 cold_runtime.py BATCH.json RESULT.json
```

Require exactly `schema: 2` and `jobs`. Schema is an integer, not a Boolean. Jobs is a list of one through eight objects, each with exactly a unique nonempty string `id` and a `runtime` object.

Each runtime has exactly `guard`, `allowed_root`, `command`, `memory_max`, `tasks_max`, and `cpu_percent`. Apply the full single-job contract from Module 10: absolute trusted regular guard, an absolute non-root directory, non-symlink guard/root leaves, structured literal argv whose executable resolves beneath that directory, memory 16 MiB through 1 GiB, tasks 4 through 256, and CPU 10 through 100 percent. Limits must be integers, not Booleans. Operator-controlled setup paths are an assumption, not a race-free same-account boundary.

Validate **the entire batch before any job launches**. A malformed later job must prevent the earlier valid job from running. Reject duplicate identities, empty/oversized lists, extra fields, wrong types, and invalid nested runtime specs without publishing a result or creating a unit.

## Execution, evidence, and lifecycle

Give each valid job a fresh owned unit with its own validated CPU/memory/task limits, zero swap, and finite runtime/stop bounds. Apply the practiced user/network namespaces, privilege floor, clean environment, filesystem/syscall guard, and literal argv handling. Useful work must still succeed.

In the prepared capstone workspace, register ownership with the course platform under target `capstone` and its exact description before launch. In the evaluator's separate temporary directory, retain standalone ownership records as practiced in 10.03; the evaluator's naming convention is `north-echo-UID-10-lab-RANDOM.service`. Adapt lifecycle context deliberately, rather than assuming every copied file is still inside the lesson directory.

Inspect ownership before mutating a remaining unit. A failed manager query is unknown, not absent. Collect on success, failure, and timeout; preserve ownership records if safe cleanup cannot be established. Never stop a unit based only on a matching prefix.

Return:

```json
{"schema": 2, "jobs": [{"id": "original-id", "result": {"schema": 1, "status": 0, "unit": "exact-owned-unit", "stdout": "...", "stderr": "", "attestation": null}}]}
```

This illustrates the shape, not fixed identity or expected output. Preserve rows in input order. Each nested result retains workload status, exact distinct unit, stdout, stderr, and a parsed final-line observation when present. A worker need not emit JSON; preserve its ordinary status/output with null attestation in that case.

Continue after an **ordinary nonzero worker exit** and return nonzero overall if any worker failed. Do not confuse that recoverable job outcome with malformed input, launch failure, timeout, or inability to prove cleanup. Infrastructure/collection failure must fail closed; do not publish a fabricated completed row and proceed as though collection succeeded.

## External checks and their limits

The evaluator checks the practiced kernel-visible properties under two resource profiles. A separate 0/7/0 batch checks ordered identities, continued execution, distinct units, effective per-job memory ceilings, and exact unit absence. Invalid batches include a valid first job followed by an invalid runtime; a harmless local marker at trusted guard entry checks that the earlier launch did not begin.

These checks use synthetic static workers and local brokers. They do not establish production readiness, all-channel credential confidentiality, private PID/mount views, exclusive pathname Unix-socket access on Landlock ABI 7, durable replay state, or hostile multi-user grader isolation. Module 10's explicit limitations still apply.

## Validation and reasoning rubric

```bash
python3 -m py_compile cold_runtime.py
../../lab-grade capstone
../../lab-grade capstone --mode exam
```

Syntax checking launches no workload. The capstone reports property outcomes without a step-by-step repair. If it fails, identify whether the defect is validation, composition, result preservation, or lifecycle. Use the earlier lesson that practiced that property; do not alter the evaluator.

Create `RATIONALE.md` in this workspace. Identify each control's removed authority, explain why useful work succeeds, map claims to actual observations, and state untested limits. Distinguish invalid input, ordinary job failure, and collection failure. Explain why a fresh unit is needed for each job and why a later invalid spec must block all work.

Use the human reasoning rubric in `docs/LEARNING_PATH.md`. Graduation requires both the automated assessment and an evidence-backed explanation; a solo review must be labeled self-assessed. An automated pass does not establish beginner comprehension.

## Cleanup and delayed replay

Preview `../../lab-cleanup capstone --dry-run`, then use `../../lab-cleanup capstone` for registered resources. If ownership cannot be established, stop and inspect the exact record; do not kill by name prefix or disable SELinux.

Save your rationale and any private work you want to keep, return with `cd ../..`, and use `./lab-reset capstone`. Reset intentionally discards the prepared solution and fixtures. Repeat cold after a delay, with the manual closed initially, and record which hints were needed. No real credentials, external targets, or production workloads belong here.
