# 12.01 - Establish a scripted baseline and its limits

## Outcomes and prerequisites

Complete Module 11. You will read a fixed synthetic oracle, predict a baseline's three requests, record what was and was not observed, and repair an overbroad conclusion without inventing evidence.

## Concepts before commands

An **oracle** is an interface that returns an answer to a question. This oracle is unusually simple: it compares a requested label to a value stored in a JSON file. It does not attempt a filesystem read, create a network connection, inspect credentials, or measure containment.

A **baseline** is a deliberately fixed comparison procedure. Keeping its behavior stable helps explain a later difference. It does not make the procedure complete or fair for every objective.

Here, the fixed schedule omits two labels. A “not observed” result can therefore mean “we never asked.” The next lesson's inventory response actually supplies the answer. A two-call result there is evidence of following a hint, not independent discovery or general agent intelligence.

## Prepare and access the files

From the course root:

```bash
./lab-start 12.01
cd .student/12.01
pwd
ls -l local_oracle.py scripted_baseline.py network-scenario.json
cat local_oracle.py
cat scripted_baseline.py
cat network-scenario.json
```

Use `nano` with a filename to navigate the source. Leave these known teaching files intact; create separate scenario files when changing input. Never replace the oracle command with an unknown executable or a real target.

### The fixed synthetic oracle

<!-- source: course/module-12-adaptive-adversary/lesson-01/local_oracle.py format=code -->
```python
#!/usr/bin/env python3
"""Synthetic one-weakness oracle: JSON scenario plus one named probe."""
import json, sys
from pathlib import Path

PROBES = ("argv", "credential", "filesystem", "network", "cleanup")
if len(sys.argv) != 3 or sys.argv[2] not in ("inventory", *PROBES):
    raise SystemExit(2)
scenario = json.loads(Path(sys.argv[1]).read_text())
if (not isinstance(scenario, dict) or set(scenario) != {"schema", "weakness"}
        or type(scenario["schema"]) is not int or scenario["schema"] != 1
        or (scenario["weakness"] is not None and scenario["weakness"] not in PROBES)):
    raise SystemExit("invalid synthetic scenario")
weakness = scenario.get("weakness")
probe = sys.argv[2]
if probe == "inventory":
    value = {"ok": True, "surface": list(PROBES), "next_probe": weakness}
else:
    value = {"ok": True, "probe": probe, "observed": probe == weakness,
             "evidence": f"synthetic-{probe}-effect" if probe == weakness else None}
print(json.dumps(value, sort_keys=True))
```
<!-- /source -->

### Source, line by line

- `PROBES` names the five accepted labels. They are strings, not implementations of security tests.
- The argument guard expects a scenario filename and one accepted request.
- Scenario validation requires the exact shape, integer schema 1, and a known label or JSON null.
- Inventory returns the list and `next_probe`, which is the stored label itself.
- A focused request compares the two labels. Equality produces `observed: true` and a synthetic text marker.
- JSON is printed to stdout. No actual containment control or target is exercised.

### The scripted baseline

<!-- source: course/module-12-adaptive-adversary/lesson-01/scripted_baseline.py format=code -->
```python
#!/usr/bin/env python3
"""Run the same fixed probes in the same order for every scenario."""
import json, subprocess, sys
from pathlib import Path

if len(sys.argv) != 4:
    raise SystemExit(2)
oracle, scenario, output = sys.argv[1:]
trace = []
for probe in ("argv", "credential", "filesystem"):
    run = subprocess.run([sys.executable, oracle, scenario, probe], text=True,
                         capture_output=True, check=True, timeout=3)
    observation = json.loads(run.stdout)
    trace.append({"probe": probe, "observation": observation})
finding = next((row for row in trace if row["observation"].get("observed")), None)
Path(output).write_text(json.dumps({"strategy": "scripted", "status": "observed" if finding else "not_observed",
                                   "trace": trace}, indent=2, sort_keys=True) + "\n")
```
<!-- /source -->

### Source, line by line

- The interface expects oracle, scenario, and output paths.
- The loop always selects argv, credential, and filesystem in that order.
- Each invocation is a structured argument list, with a three-second timeout and nonzero-status checking.
- Parsed output is retained alongside the requested label, not replaced with a summary guess.
- The first positive row becomes the finding; if none is positive, status is `not_observed`.
- The complete trace is saved with deterministic JSON formatting.

This small trusted-fixture example does not provide a general hostile-process supervisor or a streaming output limit. The named oracle is trusted course code. A timeout or malformed response is an execution error, not a negative security observation.

### The supplied scenario

<!-- source: course/module-12-adaptive-adversary/lesson-01/network-scenario.json format=code -->
```json
{"schema":1,"weakness":"network"}
```
<!-- /source -->

The label is `network`. No network operation accompanies that name.

## Exercise 1 - Predict and run the baseline

```bash
python3 scripted_baseline.py local_oracle.py network-scenario.json baseline.json
python3 -m json.tool baseline.json
```

Predict the three rows before execution. All should contain `observed: false`, and the result should be `not_observed`. There is no network row because the schedule did not ask that question.

The intentional mistake is to write “the network boundary is secure.” Repair that statement to “the three requested synthetic labels did not match; the network label was not requested.” Do not repair the result by adding a fabricated row.

## Exercise 2 - Ask the omitted question explicitly

```bash
python3 local_oracle.py network-scenario.json network > focused.json
python3 local_oracle.py network-scenario.json inventory > inventory.json
python3 -m json.tool focused.json
python3 -m json.tool inventory.json
```

The focused answer should be true and inventory should name `network`. These are **two additional actions**, not part of the baseline's original three. Count them separately in your notes. The positive result establishes only the oracle's configured label match.

## Exercise 3 - Change input, retain the schedule

```bash
python3 - <<'PY'
import json
from pathlib import Path

Path("argv-scenario.json").write_text(json.dumps({"schema": 1, "weakness": "argv"}) + "\n")
Path("none-scenario.json").write_text(json.dumps({"schema": 1, "weakness": None}) + "\n")
PY
python3 scripted_baseline.py local_oracle.py argv-scenario.json argv-result.json
python3 scripted_baseline.py local_oracle.py none-scenario.json none-result.json
```

The same schedule reports observed for the argv label and not observed for null. Thus the original negative result alone cannot distinguish an omitted matching label from a no-label scenario.

## Checkpoint and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

def load(name):
    return json.loads(Path(name).read_text())

baseline = load("baseline.json")
assert [row["probe"] for row in baseline["trace"]] == ["argv", "credential", "filesystem"]
assert baseline["status"] == "not_observed"
assert load("focused.json")["observed"] is True
assert load("inventory.json")["next_probe"] == "network"
assert load("argv-result.json")["status"] == "observed"
assert load("none-result.json")["status"] == "not_observed"
print("FIXED SCHEDULE AND OMITTED-QUESTION LIMIT: PASS")
PY
```

In `baseline-notes.md`, record the procedure, actual trace, omitted question, revised claim, and why inventory makes the later task easier. Explain why this exercise cannot establish a real network-control failure.

If JSON parsing fails, inspect stderr and the exact scenario path. Do not turn process errors into `observed: false`. Save notes, return with `cd ../..`, then use `./lab-reset 12.01` for a clean replay. No service or network endpoint was started.

## Source truth

Python's [subprocess documentation](https://docs.python.org/3.14/library/subprocess.html) defines argument lists, status checking, and timeouts; [JSON documentation](https://docs.python.org/3.14/library/json.html) defines data parsing. The label oracle and the meaning of its fields are course-defined, not properties of Linux security controls.
