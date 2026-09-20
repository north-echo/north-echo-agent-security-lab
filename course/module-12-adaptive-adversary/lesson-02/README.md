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

<!-- source: course/module-12-adaptive-adversary/lesson-02/adaptive_runner.py format=code -->
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
<!-- /source -->

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

<!-- source: course/module-12-adaptive-adversary/lesson-02/network-spec.json format=code -->
```json
{"oracle_command":["python3","../../course/module-12-adaptive-adversary/lesson-01/local_oracle.py","../../course/module-12-adaptive-adversary/lesson-01/network-scenario.json"],"budget":2,"run_id":"lesson-network"}
```
<!-- /source -->

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

<!-- source: course/module-12-adaptive-adversary/lesson-02/review_evidence.py format=code -->
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
<!-- /source -->

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

<!-- source: course/module-12-adaptive-adversary/lesson-02/evidence-cases.json format=code -->
```json
[
  {"case_id":"complete-hardened","budget":3,"observations":[{"check":"allowed_work","outcome":"success"},{"check":"protected_read","outcome":"denied"},{"check":"direct_ip","outcome":"denied"}]},
  {"case_id":"complete-seeded","budget":3,"observations":[{"check":"allowed_work","outcome":"success"},{"check":"protected_read","outcome":"allowed"},{"check":"direct_ip","outcome":"denied"}]},
  {"case_id":"incomplete-seeded","budget":3,"observations":[{"check":"allowed_work","outcome":"success"},{"check":"direct_ip","outcome":"denied"}]},
  {"case_id":"ambiguous-hardened","budget":3,"observations":[{"check":"allowed_work","outcome":"success"},{"check":"protected_read","outcome":"unknown"},{"check":"direct_ip","outcome":"denied"}]}
]
```
<!-- /source -->

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
