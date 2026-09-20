# Module 12 independent lab - Bounded synthetic dispatch

## Assignment and readiness check

Implement the small hint-dependent protocol practiced in 12.01-12.02. Preserve the exact action record and keep conclusions within the evidence. This is **not** an independent discovery tool: inventory supplies the synthetic label to request.

Before coding, explain the difference between budget and timeout, missing evidence and a negative observation, matching hashes and trustworthy code, and a returned hint and an actually performed focused request.

## Prepare and read the starter

From the course root:

```bash
./lab-start module-12
cd .student/12.lab
pwd
ls -l adaptive_runner.py
cat adaptive_runner.py
nano adaptive_runner.py
```

Edit only the prepared file. Ctrl+O then Enter saves in default nano; Ctrl+X exits.

<!-- source: course/module-12-adaptive-adversary/lab/adaptive_runner.py format=code -->
```python
#!/usr/bin/env python3
"""Module 12 starter: inventory only, with a calibrated non-discovery claim."""
import json, subprocess, sys
from pathlib import Path

if len(sys.argv) != 3: raise SystemExit(2)
spec = json.loads(Path(sys.argv[1]).read_text())
run = subprocess.run([*spec["oracle_command"], "inventory"], text=True, capture_output=True, timeout=3)
observation = json.loads(run.stdout)
Path(sys.argv[2]).write_text(json.dumps({"schema":1,"run_id":spec["run_id"],"budget":spec["budget"],
 "actions_used":1,"status":"not_observed","finding":None,
 "claim":"no effect observed within this bounded probe budget; security is not established",
 "trace":[{"action":1,"probe":"inventory","observation":observation}]})+"\n")
```
<!-- /source -->

### Starter, line by line

- Imports provide JSON, a subprocess, arguments, and paths.
- The interface expects spec and output filenames, but parsing does not yet validate their complete contract.
- One structured invocation requests inventory with a per-call timeout.
- Its output is parsed without the full success/shape checks you must add.
- The result retains the observation and run identity, but never performs the hinted second request.
- The non-discovery claim is appropriately limited even though the implementation is incomplete.

Your task is complete accounting and validation within this fixed teaching protocol, not adding targets, probes, or autonomous exploration.

## Interface and result contract

The grader invokes:

```text
python3 adaptive_runner.py SPEC.json RESULT.json
```

The exact spec fields are `oracle_command`, `budget`, and `run_id`. Require a nonempty list of string argv with no NUL characters and a nonempty executable, an actual integer budget from 1 through 8 (not Boolean), and a string identity. Validate before any call; preserve the spec unchanged.

Only use the trusted local oracle command supplied by the exercise operator, without shell interpretation. Request inventory first. If it supplies a known focused label and budget remains, request that label once. The only labels are inventory, argv, credential, filesystem, network, and cleanup. Do not inspect scenario implementation details, invent more probes, or leave the supplied interface.

Bound every invocation, reject nonzero/invalid responses, and retain each complete parsed observation with sequential action numbers beginning at 1. A focused response must identify the requested label and supply a Boolean `observed` value. Every actual call counts; do not omit failed or inconvenient actions to manufacture a successful trace.

On successful protocol completion, write schema 1, run identity, budget, actual action count, full trace, status, finding, and claim. If a focused row reports true, status is `observed` and finding is that exact row. Otherwise use `not_observed`, null finding, and an explicit statement that security is not established. An execution/validation failure must return nonzero, not publish a fabricated negative result.

No result should imply that the toy oracle measured Linux enforcement. Keep real-control conclusions tied to the earlier modules' actual behavioral tests.

## What the external checks observe

The grader rotates five synthetic labels plus a null-hint case and independently logs the actual oracle calls and parsed responses. It compares your trace to that record, checks the two-action assessment budget, exact identity/input preservation, deterministic repetition, hinted observations, and a calibrated no-observation claim.

The checks are finite, not exhaustive malformed-input certification. Test budget one, wrong types, process failure, and invalid response handling yourself using only small local fixtures. The provided inventory explicitly names the answer; a passing grade is not evidence of independent vulnerability discovery or general research ability.

## Map assessed skills to practice

Fixed schedule and its omissions: 12.01. Structured argv and status handling: Module 04. Conditional choice, action count, and limited claims: 12.02. Evidence completeness: 11.02 and the offline reviewer in 12.02. Reproducible review artifacts: 12.03.

Write `assessment-notes.md` explaining why a one-action run can receive a hint but still report no focused observation. Also include your offline allowed-work-failure case from 12.02. The grader cannot assess the quality of this explanation; learner review must.

## Validate, diagnose, and replay

```bash
python3 -m py_compile adaptive_runner.py
../../lab-grade module-12
../../lab-grade module-12 --mode exam
```

Practice mode reports failed properties with references; exam mode reduces hints. If traces differ, compare **actual requests and observations**, not just your reported count. Do not alter the oracle log or suppress actions to pass.

Save your notes, return with `cd ../..`, and use `./lab-reset module-12`. Only prepared local files and fixtures are removed; no network service or external target exists in this lab.
