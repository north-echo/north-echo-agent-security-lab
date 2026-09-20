<!-- PAGEBREAK -->

<!-- source: course/module-12-adaptive-adversary/README.md format=markdown -->
# Module 12 - Bounded decisions, evidence, and reproducible review

Complete Modules 04, 10, and 11, then work through `12.01`, `12.02`, `12.03`, and `module-12`.

The directory keeps its historical “adaptive adversary” name for compatibility. The actual exercise is a **toy bounded dispatcher**: inventory explicitly tells the program which synthetic label to request next. This is not independent vulnerability discovery, agentic research, or a test of a real target.

You will learn to:

- compare a fixed schedule with an observation-dependent choice without overstating either result;
- count every action, preserve its observation, and stop within a small budget;
- distinguish a witnessed failure, missing evidence, and a complete set of favorable observations;
- reject malformed evidence rather than silently calling it safe;
- package known local code and inputs, verify their recorded hashes, and replay from a new directory;
- explain why reproducibility and checksums do not establish truth, trust, or universal security.

The offline evidence-review exercise is the central reasoning task. Its supplied rows stand for observations; they are not new kernel measurements. Return to the earlier modules for actual enforced-control tests. No new external probes, target selection, or exploit generation are part of this chapter.

The final package can be described as a candidate experiment for later review. “Boundary Atlas” is a historical destination label, not a required service, credential, or methodology. Keep all work in the disposable VM with synthetic files.
<!-- /source -->

---

<!-- source: course/module-12-adaptive-adversary/lesson-01/README.md format=markdown -->
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

### Source, line by line

- `PROBES` names the five accepted labels. They are strings, not implementations of security tests.
- The argument guard expects a scenario filename and one accepted request.
- Scenario validation requires the exact shape, integer schema 1, and a known label or JSON null.
- Inventory returns the list and `next_probe`, which is the stored label itself.
- A focused request compares the two labels. Equality produces `observed: true` and a synthetic text marker.
- JSON is printed to stdout. No actual containment control or target is exercised.

### The scripted baseline

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

### Source, line by line

- The interface expects oracle, scenario, and output paths.
- The loop always selects argv, credential, and filesystem in that order.
- Each invocation is a structured argument list, with a three-second timeout and nonzero-status checking.
- Parsed output is retained alongside the requested label, not replaced with a summary guess.
- The first positive row becomes the finding; if none is positive, status is `not_observed`.
- The complete trace is saved with deterministic JSON formatting.

This small trusted-fixture example does not provide a general hostile-process supervisor or a streaming output limit. The named oracle is trusted course code. A timeout or malformed response is an execution error, not a negative security observation.

### The supplied scenario

```json
{"schema":1,"weakness":"network"}
```

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
<!-- /source -->

---

<!-- source: course/module-12-adaptive-adversary/lesson-02/README.md format=markdown -->
# 12.02 - Adapt within an action budget

## Outcomes and prerequisites

Complete 12.01. You will trace one hint-dependent choice, observe a budget that prevents the second action, and use an offline reviewer to distinguish contrary, missing, and favorable evidence.

## Concepts before commands

An **action budget** limits the number of requests. A per-request timeout limits waiting for that invocation; these are different limits. A budget of two does not authorize two arbitrary commands.

This teaching runner calls inventory once, then at most one allowlisted label supplied by inventory. Its “adaptation” is ordinary conditional dispatch. Inventory already names the scenario's configured answer. There is no independent discovery, model service, exploit generation, or real target.

A **calibrated claim** says no more than the observations support. A complete favorable set can support “these supplied checks passed,” not “the system is secure.” An unknown or omitted check cannot support even that narrower conclusion.

## Prepare and read the programs

From the course root:

```bash
./lab-start 12.02
cd .student/12.02
pwd
ls -l adaptive_runner.py network-spec.json review_evidence.py evidence-cases.json
cat adaptive_runner.py
cat network-spec.json
cat review_evidence.py
cat evidence-cases.json
```

Use `nano` to navigate any listed file. The oracle paths in the spec are relative to this prepared workspace. Run from here, not from the course root or the canonical source directory.

### The bounded teaching dispatcher

```python
#!/usr/bin/env python3
"""Use one inventory observation to choose one bounded focused probe."""
import json, subprocess, sys
from pathlib import Path

ALLOWED = {"inventory", "argv", "credential", "filesystem", "network", "cleanup"}

def main():
    if len(sys.argv) != 3:
        return 2
    spec = json.loads(Path(sys.argv[1]).read_text())
    if not isinstance(spec, dict) or set(spec) != {"oracle_command", "budget", "run_id"}:
        return 1
    command, budget = spec["oracle_command"], spec["budget"]
    if (not isinstance(command, list) or not command
            or any(not isinstance(x, str) or "\0" in x for x in command)
            or not command[0]):
        return 1
    if type(budget) is not int or not 1 <= budget <= 8 or not isinstance(spec["run_id"], str):
        return 1
    trace = []
    for probe in ("inventory",):
        run = subprocess.run([*command, probe], text=True, capture_output=True, timeout=3, check=False)
        if run.returncode != 0: return 1
        try: observation = json.loads(run.stdout)
        except json.JSONDecodeError: return 1
        if not isinstance(observation, dict) or observation.get("ok") is not True: return 1
        trace.append({"action": len(trace) + 1, "probe": probe, "observation": observation})
    suggested = trace[0]["observation"].get("next_probe")
    if suggested is not None and budget > 1:
        if not isinstance(suggested, str) or suggested not in ALLOWED or suggested == "inventory": return 1
        run = subprocess.run([*command, suggested], text=True, capture_output=True, timeout=3, check=False)
        if run.returncode != 0: return 1
        try: observation = json.loads(run.stdout)
        except json.JSONDecodeError: return 1
        if (not isinstance(observation, dict) or observation.get("ok") is not True
                or observation.get("probe") != suggested
                or type(observation.get("observed")) is not bool): return 1
        trace.append({"action": 2, "probe": suggested, "observation": observation})
    finding = next((row for row in trace if row["observation"].get("observed") is True), None)
    result = {"schema": 1, "run_id": spec["run_id"], "budget": budget,
              "actions_used": len(trace), "status": "observed" if finding else "not_observed",
              "finding": finding, "claim": "bounded probe observed a synthetic effect" if finding else
              "no effect observed within this bounded probe budget; security is not established", "trace": trace}
    Path(sys.argv[2]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0

if __name__ == "__main__": raise SystemExit(main())
```

### Source, line by line

- `ALLOWED` restricts the label added to the trusted operator-supplied oracle argv.
- The exact spec shape separates command, integer budget, and opaque run identity.
- Argument/type checks reject malformed argv, embedded NUL, and Boolean/out-of-range budgets.
- Inventory is the first action. Its nonzero status, invalid JSON, or non-success object prevents a claimed result.
- The complete parsed observation is retained with sequential action number 1.
- A non-null hint and remaining budget permit exactly one focused label. The allowlist prevents inventing additional actions.
- The focused response must identify the requested label and contain a real Boolean observation.
- A positive row becomes the finding. Otherwise the result explicitly says security is not established.
- The result records budget, actual action count, identity, claim, and full trace.

Even a budget of eight causes at most two calls in this particular implementation. The upper bound is not a goal to consume. The command itself is trusted course configuration: an argv list and an allowlisted suffix do **not** make an unknown executable safe. Captured output is not independently byte-bounded; use only the tiny known fixture here.

### The prepared spec

```json
{"oracle_command":["python3","../../course/module-12-adaptive-adversary/lesson-01/local_oracle.py","../../course/module-12-adaptive-adversary/lesson-01/network-scenario.json"],"budget":2,"run_id":"lesson-network"}
```

Its command uses the canonical local label oracle from 12.01. No live network service is involved.

## Exercise 1 - Observe two actions, then deliberately allow only one

```bash
python3 adaptive_runner.py network-spec.json two-actions.json
python3 -m json.tool two-actions.json
python3 - <<'PY'
import json
from pathlib import Path

spec = json.loads(Path("network-spec.json").read_text())
spec["budget"] = 1
Path("one-action-spec.json").write_text(json.dumps(spec) + "\n")
PY
python3 adaptive_runner.py one-action-spec.json one-action.json
python3 -m json.tool one-action.json
python3 adaptive_runner.py network-spec.json repaired-budget.json
cmp two-actions.json repaired-budget.json
```

With budget two, expect inventory followed by network, and an observed synthetic label match. With budget one, inventory still names network, but the runner must not claim the unperformed focused observation. The repair restores the original allowed budget and obtains a fresh second action.

Do not report this as outperforming a real security analyst or independently finding a weakness. The comparison changes both the schedule and access to an answer-providing hint.

### The offline evidence reviewer

```python
#!/usr/bin/env python3
"""Interpret fixed local observations. This program never invokes a probe."""
import json
from pathlib import Path
import sys

EXPECTED = {"allowed_work": "success", "protected_read": "denied", "direct_ip": "denied"}


def review(case):
    if (not isinstance(case, dict) or set(case) != {"case_id", "budget", "observations"}
            or not isinstance(case["case_id"], str) or not case["case_id"]
            or type(case["budget"]) is not int or not 1 <= case["budget"] <= 8
            or not isinstance(case["observations"], list)):
        raise ValueError("invalid evidence case")
    observations = case["observations"]
    if len(observations) > case["budget"]:
        raise ValueError("observation budget exceeded")
    seen = {}
    for observation in observations:
        if not isinstance(observation, dict) or set(observation) != {"check", "outcome"}:
            raise ValueError("invalid observation shape")
        name, outcome = observation["check"], observation["outcome"]
        if not isinstance(name, str) or name not in EXPECTED or name in seen:
            raise ValueError("unknown or duplicate check")
        permitted = {"success", "failure", "unknown"} if name == "allowed_work" else {"allowed", "denied", "unknown"}
        if not isinstance(outcome, str) or outcome not in permitted:
            raise ValueError("invalid observation outcome")
        seen[name] = outcome
    failures = sorted(name for name, value in seen.items()
                      if value != "unknown" and value != EXPECTED[name])
    missing = sorted(name for name in EXPECTED if name not in seen or seen[name] == "unknown")
    status = "observed_failure" if failures else "inconclusive" if missing else "passed_observations"
    return {"case_id": case["case_id"], "status": status, "failures": failures,
            "missing": missing, "claim": "limited to the supplied observations; security is not established"}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: review_evidence.py CASES.json")
    cases = json.loads(Path(sys.argv[1]).read_text())
    if not isinstance(cases, list):
        raise SystemExit("cases must be a JSON list")
    print(json.dumps([review(case) for case in cases], indent=2, sort_keys=True))
```

### Source, line by line

- `EXPECTED` describes three intended outcomes: useful work succeeds, protected read is denied, and direct IP is denied.
- Shape, budget, and identity checks validate the supplied case before interpretation.
- Each observation must have exactly a known check and a permitted textual outcome.
- Duplicate checks are rejected instead of allowing the later row to overwrite earlier evidence.
- A contrary known outcome is an observed failure. Missing or explicitly unknown outcomes are recorded separately.
- A failure takes precedence even if some other checks are missing.
- Without failures, missing evidence is inconclusive; only a complete favorable set yields `passed_observations`.
- Every result limits its claim to supplied observations. The reviewer invokes no workload or probe.

### Four supplied cases

```json
[
  {"case_id":"complete-hardened","budget":3,"observations":[{"check":"allowed_work","outcome":"success"},{"check":"protected_read","outcome":"denied"},{"check":"direct_ip","outcome":"denied"}]},
  {"case_id":"complete-seeded","budget":3,"observations":[{"check":"allowed_work","outcome":"success"},{"check":"protected_read","outcome":"allowed"},{"check":"direct_ip","outcome":"denied"}]},
  {"case_id":"incomplete-seeded","budget":3,"observations":[{"check":"allowed_work","outcome":"success"},{"check":"direct_ip","outcome":"denied"}]},
  {"case_id":"ambiguous-hardened","budget":3,"observations":[{"check":"allowed_work","outcome":"success"},{"check":"protected_read","outcome":"unknown"},{"check":"direct_ip","outcome":"denied"}]}
]
```

The case IDs describe author intent but are not decision inputs. A misleading “hardened” label must not override the rows. These are fixed data fixtures, not measurements newly collected from your VM.

## Exercise 2 - Predict all four decisions

```bash
python3 review_evidence.py evidence-cases.json > review.json
python3 -m json.tool review.json
```

Expected statuses, in order: passed observations, observed failure, inconclusive, inconclusive. The second case supplies an allowed protected read. The third omits that observation; the fourth supplies unknown. Missing and unknown have different provenance but neither proves denial.

## Exercise 3 - Construct the missing-plus-failure case

```bash
python3 - <<'PY'
import json
from pathlib import Path

case = {"case_id": "named-hardened-but-incomplete", "budget": 3,
        "observations": [{"check": "allowed_work", "outcome": "success"},
                         {"check": "protected_read", "outcome": "allowed"}]}
Path("new-case.json").write_text(json.dumps([case]) + "\n")
bad = dict(case, observations=case["observations"] + [case["observations"][0]])
Path("duplicate-case.json").write_text(json.dumps([bad]) + "\n")
PY
python3 review_evidence.py new-case.json > new-review.json
NE_DUPLICATE_STATUS=0
python3 review_evidence.py duplicate-case.json > rejected.json 2> rejected.err || NE_DUPLICATE_STATUS=$?
test "$NE_DUPLICATE_STATUS" -ne 0
test ! -s rejected.json
python3 review_evidence.py new-case.json > repaired-review.json
cmp new-review.json repaired-review.json
```

The new case is an observed failure with direct IP still missing. Missing evidence does not erase a witnessed failure. The deliberate duplicate is malformed and must be rejected, not counted as a third independent observation. Repair by returning to the valid case, never by fabricating a denial.

## Checkpoint and faded practice

```bash
python3 - <<'PY'
import json
from pathlib import Path

def load(name):
    return json.loads(Path(name).read_text())

one, two = load("one-action.json"), load("two-actions.json")
assert one["actions_used"] == 1 and one["finding"] is None
assert one["status"] == "not_observed" and "not established" in one["claim"]
assert [row["probe"] for row in two["trace"]] == ["inventory", "network"]
assert two["actions_used"] == 2 and two["finding"] == two["trace"][1]
assert [row["status"] for row in load("review.json")] == [
    "passed_observations", "observed_failure", "inconclusive", "inconclusive"]
new = load("new-review.json")[0]
assert new["status"] == "observed_failure"
assert new["failures"] == ["protected_read"] and new["missing"] == ["direct_ip"]
print("BUDGET, FAILURE, AND MISSING-EVIDENCE DISTINCTIONS: PASS")
PY
```

Write `evidence-notes.md`. Design one additional **offline JSON case** that tests allowed work failing while denials succeed. Predict the status, run the reviewer, and explain why disabling all useful work is not successful containment. Change only data in this prepared workspace; do not add probes or targets.

If a runner invocation fails, inspect stderr and distinguish setup failure from an observed negative result. If a reviewer refuses a case, fix the malformed shape rather than weakening the reviewer. Save notes, return with `cd ../..`, and use `./lab-reset 12.02`. No background resources were created.

## Source truth

Python's [subprocess](https://docs.python.org/3.14/library/subprocess.html) and [JSON](https://docs.python.org/3.14/library/json.html) references explain execution and serialization mechanics. The decision table is an explicit course evidence policy, not a statistical proof or an external certification standard.
<!-- /source -->

---

<!-- source: course/module-12-adaptive-adversary/lesson-03/README.md format=markdown -->
# 12.03 - Package a calibrated candidate experiment

## Outcomes and prerequisites

Complete 12.01-12.02. You will package known local code, inputs, and observations; verify their recorded bytes; detect a missing or changed input before replay; and repeat the experiment from a relocated directory.

## Concepts before commands

**Reproducibility** requires the inputs and procedure, not just the conclusion. A result without the code and scenario may be impossible to interpret later.

A **checksum** describes bytes. Comparing a file to its recorded SHA-256 detects a mismatch, but an attacker who can replace both file and inventory can make them agree. This package is not signed, and matching hashes do not establish authorship, trustworthy behavior, or the truth of a claim.

Only replay the known course sources you have just read. Never execute an unknown downloaded “experiment” because its self-supplied manifest verifies. Even an exact argv list can launch harmful code.

## Prepare and read both programs

From the course root:

```bash
./lab-start 12.03
cd .student/12.03
pwd
ls -l package_experiment.py verify_package.py
cat package_experiment.py
cat verify_package.py
```

Use `nano` with the exact filename to navigate. The input runner and oracle remain the known synthetic programs from 12.01-12.02, not a new probing tool.

### The packager

```python
#!/usr/bin/env python3
"""Bundle explicit local inputs and sources for replay from a clean directory."""
import hashlib
import json
from pathlib import Path
import sys


def main():
    if len(sys.argv) != 6:
        raise SystemExit("usage: package_experiment.py RESULT SPEC RUNNER CANDIDATE_ID DIRECTORY")
    result_path, spec_path, runner = map(Path, sys.argv[1:4])
    result = json.loads(result_path.read_text())
    spec = json.loads(spec_path.read_text())
    if (not isinstance(spec, dict) or set(spec) != {"oracle_command", "budget", "run_id"}
            or type(spec["budget"]) is not int or not 1 <= spec["budget"] <= 8
            or not isinstance(spec["run_id"], str)
            or not isinstance(result, dict)):
        raise SystemExit("invalid spec or result shape")
    command = spec["oracle_command"]
    if (not isinstance(command, list) or len(command) != 3
            or any(not isinstance(item, str) or not item for item in command)):
        raise SystemExit("packaging supports only the explicit local Python oracle plus scenario interface")
    oracle, scenario = map(Path, command[1:])
    trace = result.get("trace", [])
    if (type(result.get("schema")) is not int or result.get("schema") != 1
            or result.get("status") not in ("observed", "not_observed")
            or not isinstance(trace, list) or not isinstance(result.get("claim"), str)
            or type(result.get("actions_used")) is not int
            or result.get("run_id") != spec["run_id"]
            or result.get("actions_used") != len(trace) or not 1 <= len(trace) <= spec["budget"]):
        raise SystemExit("invalid result, run identity, or budget")
    files = {"runner.py": runner.read_bytes(), "oracle.py": oracle.read_bytes(),
             "scenario.json": scenario.read_bytes(), "expected.json": result_path.read_bytes()}
    portable = dict(spec, oracle_command=["python3", "oracle.py", "scenario.json"])
    files["spec.json"] = (json.dumps(portable, indent=2, sort_keys=True) + "\n").encode()
    package = {"schema": 2, "candidate_id": sys.argv[4], "run_id": spec["run_id"],
               "hypothesis": "The recorded local scenario permits the reported observation within this budget.",
               "result_status": result["status"], "claim": result["claim"],
               "limits": ["synthetic local oracle", "single run", "bounded probe set", "non-discovery is not proof"],
               "replay": ["python3", "runner.py", "spec.json", "result.json"],
               "sha256": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}
    output = Path(sys.argv[5])
    output.mkdir()  # Never overwrite an existing experiment or student work.
    for name, data in files.items():
        (output / name).write_bytes(data)
    (output / "package.json").write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
```

### Source, line by line

- Five arguments identify the existing result, spec, runner, local candidate label, and new destination.
- Spec/result checks require the known schema, matching run identity, and a trace count within budget. They do not independently authenticate or remeasure observations.
- The command must have the local Python-oracle-plus-scenario shape. The packager does not discover arbitrary program dependencies or prove the supplied executable trustworthy.
- The files mapping reads the known sources, scenario, and expected result as bytes.
- A portable spec names the copied files relative to the package directory; it does not preserve a workstation-specific absolute repository path.
- SHA-256 is calculated over each packaged file's exact bytes.
- The package records hypothesis, claim, limits, and a replay argv. These are review metadata, not a certification or publication.
- `mkdir()` refuses an existing destination. Writing occurs only inside this newly created directory.
- An interrupted write can leave an incomplete directory. Verification must reject missing content; do not overwrite the directory to disguise that failure.

The packager assumes small trusted local inputs. It is neither a dependency manager nor a general safe archive extractor.

### The non-executing verifier

```python
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
```

### Source, line by line

- `FILES` is an exact allowlist, not a set of arbitrary paths taken from a manifest.
- The directory/manifest leaf checks refuse symbolic links and missing regular input.
- Parsing requires a mapping with exactly the five expected hash entries.
- Each hash must be a lowercase 64-character hexadecimal string.
- Each expected file must be a regular non-symlink leaf; its bytes are hashed and compared.
- The success message states the limit: matching inventory does not establish authenticity.
- Exceptions produce nonzero status and a diagnostic. No packaged program is imported or executed.

This verifier does not claim race-free behavior against a concurrent same-account mutator, validate every metadata field, or inventory unrelated extra files. Keep the prepared directory under your control.

## Exercise 1 - Produce and package known evidence

```bash
NE_RUNNER=../../course/module-12-adaptive-adversary/lesson-02/adaptive_runner.py
NE_SPEC=../../course/module-12-adaptive-adversary/lesson-02/network-spec.json
python3 "$NE_RUNNER" "$NE_SPEC" result.json
python3 package_experiment.py result.json "$NE_SPEC" "$NE_RUNNER" candidate-12 package
python3 -m json.tool package/package.json
python3 verify_package.py package
```

The two variables name sources you already read. Quoting keeps each pathname one argument. `candidate-12` is merely your local label, not a vulnerability identifier.

Predict the five hashed files and compare with the printed inventory. The manifest is not included in its own hash list. The original result is copied as `expected.json`; a later replay will create a separate `result.json`.

## Exercise 2 - Deliberately remove an input, then repair it

```bash
mv package/scenario.json package/scenario.saved
NE_MISSING_STATUS=0
python3 verify_package.py package > missing.out 2> missing.err || NE_MISSING_STATUS=$?
test "$NE_MISSING_STATUS" -ne 0
cat missing.err
mv package/scenario.saved package/scenario.json
python3 verify_package.py package
```

Verification must fail before any replay command is run. Restore the **same** saved file, then verify again. A metadata summary cannot replace a missing scenario.

Now change only the scenario's formatting, retaining the same JSON meaning:

```bash
cp package/scenario.json original-scenario.json
python3 - <<'PY'
from pathlib import Path

path = Path("package/scenario.json")
path.write_bytes(path.read_bytes() + b"\n")
PY
NE_CHANGED_STATUS=0
python3 verify_package.py package > changed.out 2> changed.err || NE_CHANGED_STATUS=$?
test "$NE_CHANGED_STATUS" -ne 0
cat changed.err
cp original-scenario.json package/scenario.json
python3 verify_package.py package
```

The checksum changes even though JSON parsing would yield the same object. It identifies bytes, not semantic equivalence. Repair by restoring the recorded source, not by silently changing the hash to fit an unexplained modification.

## Exercise 3 - Relocate and replay

```bash
mv package relocated-package
python3 verify_package.py relocated-package
(
  cd relocated-package
  python3 runner.py spec.json result.json
  cmp expected.json result.json
)
python3 package_experiment.py result.json "$NE_SPEC" "$NE_RUNNER" candidate-12 second-package
cmp relocated-package/package.json second-package/package.json
NE_EXISTING_STATUS=0
python3 package_experiment.py result.json "$NE_SPEC" "$NE_RUNNER" candidate-12 second-package \
  > existing.out 2> existing.err || NE_EXISTING_STATUS=$?
test "$NE_EXISTING_STATUS" -ne 0
python3 verify_package.py second-package
```

The parentheses create a subshell; its directory change does not move your outer lesson shell. Replay uses only the copied runner, oracle, scenario, and spec. The Python runtime remains an environmental dependency; this is source portability, not a bootable or hermetic environment.

The second package has identical metadata for identical inputs. Repeating into its existing directory fails without overwriting it. Byte-identical results are possible because this tiny oracle omits timestamps and real-world variability; do not demand that property from every legitimate experiment.

## Checkpoint and independent explanation

```bash
python3 - <<'PY'
import json
from pathlib import Path

root = Path("relocated-package")
package = json.loads((root / "package.json").read_text())
assert package["candidate_id"] == "candidate-12"
assert package["replay"] == ["python3", "runner.py", "spec.json", "result.json"]
assert json.loads((root / "spec.json").read_text())["oracle_command"] == [
    "python3", "oracle.py", "scenario.json"]
assert (root / "expected.json").read_bytes() == (root / "result.json").read_bytes()
assert "non-discovery is not proof" in package["limits"]
assert "checksum mismatch" in Path("changed.err").read_text()
assert "missing or non-regular" in Path("missing.err").read_text()
print("PORTABLE REPLAY AND NON-EXECUTING INTEGRITY CHECKS: PASS")
PY
```

Write `review-notes.md` separating hypothesis, observed result, interpretation, limits, and proposed next **review** question. Explain why a forged result could still be packaged and why matching hashes do not authorize running unfamiliar code. No external submission is required.

If replay fails, compare the interpreter version and verified inputs before changing the expected result. If a package already exists, use a new exact destination or reset the lesson after saving your notes. Do not remove files by a broad prefix.

Save any package you want to keep, return with `cd ../..`, then use `./lab-reset 12.03` to discard the prepared workspace. The course reset removes generated local files after ownership checks; this exercise creates no background service.

## Source truth

Python's [hashlib documentation](https://docs.python.org/3.14/library/hashlib.html) defines the byte digest used here. [JSON documentation](https://docs.python.org/3.14/library/json.html) explains serialization, which is distinct from byte identity and from the truth of evidence. Package format and claim limits are course-defined.
<!-- /source -->

---

<!-- source: course/module-12-adaptive-adversary/lab/README.md format=markdown -->
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
<!-- /source -->
