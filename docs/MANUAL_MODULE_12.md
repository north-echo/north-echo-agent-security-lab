# North Echo field manual - Module 12

This self-contained chapter preserves every guided command and complete source for the bounded adaptive-adversary module. All observations come from a synthetic local oracle.

## README.md

<!-- source: course/module-12-adaptive-adversary/README.md format=markdown -->
# Module 12 - Adaptive adversary and Boundary Atlas graduation

Compare a fixed scripted baseline with a bounded adaptive policy against the same synthetic local oracle. Preserve every action and observation, distinguish non-discovery from evidence of safety, and package a reproducible candidate experiment.

Play in order: `12.01`, `12.02`, `12.03`, then `module-12`.

Outcomes:

- define a deterministic baseline before evaluating adaptation;
- constrain an adaptive policy by probe allowlist, exact argv, action budget, and structured trace;
- discover randomized weakness classes without external targets or exploit generation;
- report `not_observed` without claiming security when evidence is absent;
- package hypothesis, trace, result, limits, and replay command as a Boundary Atlas candidate.

All oracles and observations are synthetic and local. No public, LAN, cloud, employer, or production target is contacted. Prerequisites are Modules 04, 10, and 11.
<!-- /source -->

<!-- PAGEBREAK -->

## lesson-01/README.md

<!-- source: course/module-12-adaptive-adversary/lesson-01/README.md format=markdown -->
# 12.01 - Establish a scripted baseline and its limits

## Goal

Run a fixed probe sequence before adaptation, deliberately miss a weakness outside that sequence, and report non-discovery without claiming safety.

```bash
sed -n '1,180p' local_oracle.py
sed -n '1,180p' scripted_baseline.py
python3 scripted_baseline.py local_oracle.py network-scenario.json baseline.json
python3 -m json.tool baseline.json
```

### Line by line

- The oracle accepts only five named synthetic probes plus `inventory`; it performs no network request.
- The baseline always runs argv, credential, and filesystem probes in that order using exact argv.
- The network scenario is intentionally outside that fixed set, so status is `not_observed` even though a weakness exists.
- The trace preserves every action and observation. This proves what ran, not that untested boundaries are safe.

Intentional mistake: rewrite `not_observed` as `secure`. The trace contradicts that claim because network and cleanup were never probed. Restore the calibrated status.

## Checkpoint and troubleshooting

```bash
test "$(python3 -c 'import json;print(json.load(open("baseline.json"))["status"])')" = not_observed
rm baseline.json
```

- Run from the lesson workspace so scenario paths resolve.
- Checkpoint: name the two untested surfaces and explain why the baseline remains useful for comparison.
<!-- /source -->

<!-- PAGEBREAK -->

## lesson-01/local_oracle.py

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

<!-- PAGEBREAK -->

## lesson-01/scripted_baseline.py

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
                         capture_output=True, check=False)
    observation = json.loads(run.stdout)
    trace.append({"probe": probe, "observation": observation})
finding = next((row for row in trace if row["observation"].get("observed")), None)
Path(output).write_text(json.dumps({"strategy": "scripted", "status": "observed" if finding else "not_observed",
                                   "trace": trace}, indent=2, sort_keys=True) + "\n")
```
<!-- /source -->

<!-- PAGEBREAK -->

## lesson-01/network-scenario.json

<!-- source: course/module-12-adaptive-adversary/lesson-01/network-scenario.json format=code -->
```json
{"schema":1,"weakness":"network"}
```
<!-- /source -->

<!-- PAGEBREAK -->

## lesson-02/README.md

<!-- source: course/module-12-adaptive-adversary/lesson-02/README.md format=markdown -->
# 12.02 - Adapt within an action budget

## Goal

Use one inventory observation to choose one focused probe, preserve an auditable trace, and discover the same network weakness in two actions.

```bash
sed -n '1,260p' adaptive_runner.py
python3 adaptive_runner.py network-spec.json result.json
python3 -m json.tool result.json
```

### Line by line

- The runner validates the exact spec, structured oracle command, integer budget, and run identity.
- Action one is always `inventory`. Its `next_probe` value must be in the fixed allowlist.
- If budget remains, action two invokes that probe with exact argv and a timeout; no shell or generated exploit is used.
- Finding, calibrated claim, budget use, and the complete observations are written together.

Expected status is `observed`, actions used is 2, and finding probe is `network`.

Intentional failure and repair:

```bash
python3 -c 'import json;p=json.load(open("network-spec.json"));p["budget"]=1;open("short.json","w").write(json.dumps(p))'
python3 adaptive_runner.py short.json short-result.json
grep 'not established' short-result.json
python3 adaptive_runner.py network-spec.json result.json
rm short.json short-result.json result.json
```

Budget one cannot run the focused probe; the repair restores budget two rather than overstating inventory evidence.

## Checkpoint and troubleshooting

- If the oracle path fails, preserve the three argv elements in `oracle_command`; do not join them into a shell string.
- Checkpoint: show which observation caused action two and which field proves the budget was respected.

## Exercise 2 - Interpret incomplete evidence without an answer hint

The introductory oracle names `next_probe`; that teaches bounded dispatch, not
independent diagnosis. Now inspect four fixed local records derived from the
control/effect distinction in Module 10. No program here runs a probe or contacts
a target. Before execution, predict a verdict and a missing observation for each
row. All cases have the same three-observation budget. Case labels are teaching
ground truth, not input to the classifier's decision.

```bash
sed -n '1,180p' review_evidence.py
python3 -m json.tool evidence-cases.json
python3 review_evidence.py evidence-cases.json
```

### Line by line

- `EXPECTED` pairs a useful operation with two intended denials. A denial-only
  record cannot establish that useful work survived.
- `review` rejects an exceeded budget, duplicate observations, and unknown check
  names. Its decision reads observations, never the case label.
- A contrary observed effect produces `observed_failure`. Missing or `unknown`
  effects produce `inconclusive`, even when no failure was seen.
- Complete matching observations produce `passed_observations`; the claim stays
  scoped to those observations. The code never labels a system universally secure.
- Sorting makes the evidence summary stable for comparison and replay.

Expected statuses, in order: `passed_observations`, `observed_failure`,
`inconclusive`, `inconclusive`. The third case illustrates a missed seeded failure;
the fourth shows that uncertainty is also possible for a hardened case.

Intentional error and repair: on a copy of the reviewer, treat missing observations
as passed. Predict which row becomes falsely reassuring, run it, then restore
`inconclusive`. Do not change the input to obtain the desired verdict.

Faded exercise: replace one observation with `unknown` in a workspace copy of
the JSON. Explain the smallest additional observation needed to resolve it before
running the reviewer. Independent checkpoint: provide an evidence matrix for a
new three-check case and explain both the verdict and its limits. Case labels and
configured controls alone are never proof of an observed effect.
<!-- /source -->

<!-- PAGEBREAK -->

## lesson-02/adaptive_runner.py

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
    if not isinstance(command, list) or not command or any(not isinstance(x, str) for x in command):
        return 1
    if type(budget) is not int or not 1 <= budget <= 8 or not isinstance(spec["run_id"], str):
        return 1
    trace = []
    for probe in ("inventory",):
        run = subprocess.run([*command, probe], text=True, capture_output=True, timeout=3, check=False)
        try: observation = json.loads(run.stdout)
        except json.JSONDecodeError: return 1
        trace.append({"action": len(trace) + 1, "probe": probe, "observation": observation})
    suggested = trace[0]["observation"].get("next_probe")
    if suggested is not None and budget > 1:
        if suggested not in ALLOWED or suggested == "inventory": return 1
        run = subprocess.run([*command, suggested], text=True, capture_output=True, timeout=3, check=False)
        try: observation = json.loads(run.stdout)
        except json.JSONDecodeError: return 1
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

<!-- PAGEBREAK -->

## lesson-02/network-spec.json

<!-- source: course/module-12-adaptive-adversary/lesson-02/network-spec.json format=code -->
```json
{"oracle_command":["python3","../../course/module-12-adaptive-adversary/lesson-01/local_oracle.py","../../course/module-12-adaptive-adversary/lesson-01/network-scenario.json"],"budget":2,"run_id":"lesson-network"}
```
<!-- /source -->

<!-- PAGEBREAK -->

## Offline evidence reviewer: complete source

<!-- source: course/module-12-adaptive-adversary/lesson-02/review_evidence.py format=code -->
```python
#!/usr/bin/env python3
"""Interpret fixed local observations. This program never invokes a probe."""
import json
from pathlib import Path
import sys

EXPECTED = {"allowed_work": "success", "protected_read": "denied", "direct_ip": "denied"}


def review(case):
    observations = case["observations"]
    if len(observations) > case["budget"]:
        raise ValueError("observation budget exceeded")
    seen = {}
    for observation in observations:
        name, outcome = observation["check"], observation["outcome"]
        if name not in EXPECTED or name in seen:
            raise ValueError("unknown or duplicate check")
        seen[name] = outcome
    failures = sorted(name for name, value in seen.items()
                      if value != "unknown" and value != EXPECTED[name])
    missing = sorted(name for name in EXPECTED if name not in seen or seen[name] == "unknown")
    status = "observed_failure" if failures else "inconclusive" if missing else "passed_observations"
    return {"case_id": case["case_id"], "status": status, "failures": failures,
            "missing": missing, "claim": "limited to the supplied observations; security is not established"}


if __name__ == "__main__":
    cases = json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps([review(case) for case in cases], indent=2, sort_keys=True))
```
<!-- /source -->

The `EXPECTED` mapping states the three observed outcomes needed for this limited
comparison. `review` records each check once, separates contrary evidence from
missing evidence, and returns the narrowest supported conclusion. The caller
reads the fixed JSON cases and prints stable summaries; it executes no probes.

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

Each case has the same budget. The two incomplete rows intentionally do not
support a safety conclusion, regardless of the teaching label.

<!-- PAGEBREAK -->

## lesson-03/README.md

<!-- source: course/module-12-adaptive-adversary/lesson-03/README.md format=markdown -->
# 12.03 - Package a calibrated candidate experiment

## Goal

Turn a bounded result into a portable experiment directory, replay it without
the repository, and keep its claim within the evidence.

```bash
sed -n '1,180p' package_experiment.py
RUNNER=../../course/module-12-adaptive-adversary/lesson-02/adaptive_runner.py
SPEC=../../course/module-12-adaptive-adversary/lesson-02/network-spec.json
python3 "$RUNNER" "$SPEC" result.json
python3 package_experiment.py result.json "$SPEC" "$RUNNER" candidate-12 package
python3 -m json.tool package/package.json
(cd package && python3 runner.py spec.json result.json && cmp expected.json result.json)
```

### Line by line

- `RUNNER` and `SPEC` name the actual source and inputs that produced the result.
  Quotes keep each pathname one argument.
- The packager checks result shape, run identity, and action budget. It supports
  exactly the lesson's local Python oracle plus scenario interface; it does not
  guess dependencies for arbitrary commands.
- The result, runner, oracle, and scenario are copied; the spec uses relative
  paths inside the package. A SHA-256 inventory records their exact bytes.
- `mkdir` refuses an existing directory, so packaging never replaces student work.
- The subshell enters only the new package, runs its own copies, and compares the
  replay against the original result. No repository path is needed for replay.
- `candidate_id` is a local label, not a vulnerability identifier or publication claim.

Intentional mistake: rename `package/scenario.json` to `package/scenario.saved`.
Replay fails because the package is incomplete. Restore the filename and replay
successfully. A JSON summary alone is not a reproducible experiment.

Now prove packaging is deterministic and clean the exact generated artifacts:

```bash
grep -F 'non-discovery is not proof' package/package.json
python3 package_experiment.py result.json "$SPEC" "$RUNNER" candidate-12 second
cmp package/package.json second/package.json
rm package/runner.py package/oracle.py package/scenario.json package/spec.json package/expected.json package/result.json package/package.json
rm second/runner.py second/oracle.py second/scenario.json second/spec.json second/expected.json second/package.json
rmdir package second
rm result.json
```

## Checkpoint and troubleshooting

- Package the raw trace, not a prose-only summary.
- A promising observation remains a candidate until independently reproduced under a broader protocol.
- Checkpoint: distinguish the package hypothesis, observed result, and stated limits.
- Independent checkpoint: move a completed package to another directory and replay
  it there; explain why hashing the report alone would not identify its inputs.
<!-- /source -->

<!-- PAGEBREAK -->

## lesson-03/package_experiment.py

<!-- source: course/module-12-adaptive-adversary/lesson-03/package_experiment.py format=code -->
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
    command = spec["oracle_command"]
    if not isinstance(command, list) or len(command) != 3:
        raise SystemExit("packaging supports only the explicit local Python oracle plus scenario interface")
    oracle, scenario = map(Path, command[1:])
    trace = result.get("trace", [])
    if (result.get("schema") != 1 or result.get("status") not in {"observed", "not_observed"}
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
<!-- /source -->

<!-- PAGEBREAK -->

## lab/README.md

<!-- source: course/module-12-adaptive-adversary/lab/README.md format=markdown -->
# Module 12 independent lab - Bounded adaptive runner

Implement `adaptive_runner.py`; the grader calls `python3 adaptive_runner.py SPEC.json RESULT.json`. The spec contains exact `oracle_command` argv, integer action `budget`, and opaque `run_id`.

Validate before acting. Invoke only `inventory`, `argv`, `credential`, `filesystem`, `network`, or `cleanup`, using exact argv without a shell and with bounded execution. Record sequential action numbers and complete parsed observations. Never exceed budget. Preserve run identity. For an observed focused effect, return its trace row as the finding. If no effect is observed, use `not_observed` and explicitly say security is not established.

The grader rotates five synthetic weakness classes plus a no-weakness case. Its oracle independently records actual calls and observations; the reported count and complete trace must match that record. This is an introductory bounded-dispatch assessment: the inventory names the focused synthetic probe. It is not evidence of independent vulnerability discovery. Lesson 12.02's separate offline evidence matrix assesses interpretation when observations are incomplete. The starter inventories only and therefore misses every weakness.

```bash
python3 -m py_compile adaptive_runner.py
../../lab-grade module-12
../../lab-grade module-12 --mode exam
```

Do not inspect, modify, or target anything outside the supplied local oracle command.
<!-- /source -->

<!-- PAGEBREAK -->

## Integrated interpretation

The scripted and adaptive runs share an oracle and evidence schema. Adaptation changes probe selection, not the target or success definition. Budget, allowlist, exact argv, deterministic trace, and calibrated claims keep comparison meaningful. A `not_observed` result says only that this bounded run found no effect; it never establishes security.

## Safety and graduation

The oracle is local, synthetic, deterministic, and non-destructive. The module creates no network connection, credential, service, or persistent resource. A Boundary Atlas candidate is a reproducible experiment package—not a vulnerability announcement. It preserves hypothesis, trace, result, replay argv, and interpretation limits for independent review.
