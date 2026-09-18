# North Echo field manual - Module 12

This self-contained chapter preserves every guided command and complete source for the bounded adaptive-adversary module. All observations come from a synthetic local oracle.

## README.md

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

<!-- PAGEBREAK -->

## lesson-01/README.md

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

<!-- PAGEBREAK -->

## lesson-01/local_oracle.py

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

<!-- PAGEBREAK -->

## lesson-01/scripted_baseline.py

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

<!-- PAGEBREAK -->

## lesson-01/network-scenario.json

```json
{"schema":1,"weakness":"network"}
```

<!-- PAGEBREAK -->

## lesson-02/README.md

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

<!-- PAGEBREAK -->

## lesson-02/adaptive_runner.py

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

<!-- PAGEBREAK -->

## lesson-02/network-spec.json

```json
{"oracle_command":["python3","../../course/module-12-adaptive-adversary/lesson-01/local_oracle.py","../../course/module-12-adaptive-adversary/lesson-01/network-scenario.json"],"budget":2,"run_id":"lesson-network"}
```

<!-- PAGEBREAK -->

## lesson-03/README.md

# 12.03 - Package a calibrated candidate experiment

## Goal

Turn a bounded result into a replayable experiment candidate without expanding its claim beyond the evidence.

```bash
sed -n '1,180p' package_experiment.py
python3 ../../course/module-12-adaptive-adversary/lesson-02/adaptive_runner.py \
  ../../course/module-12-adaptive-adversary/lesson-02/network-spec.json result.json
python3 package_experiment.py result.json candidate-12 package.json
python3 -m json.tool package.json
```

### Line by line

- The packager accepts only a schema-1 observed/not-observed result.
- It preserves the trace and claim, adds a falsifiable bounded hypothesis, lists four interpretation limits, and supplies structured replay argv.
- `candidate_id` labels this package; it is not a vulnerability identifier or publication claim.

Intentional mistake: remove the `non-discovery is not proof` limit. The package then invites an inference its evidence cannot support. Restore all limits and verify:

```bash
grep -F 'non-discovery is not proof' package.json
python3 package_experiment.py result.json candidate-12 second.json
cmp package.json second.json
rm result.json package.json second.json
```

## Checkpoint and troubleshooting

- Package the raw trace, not a prose-only summary.
- A promising observation remains a candidate until independently reproduced under a broader protocol.
- Checkpoint: distinguish the package hypothesis, observed result, and stated limits.

<!-- PAGEBREAK -->

## lesson-03/package_experiment.py

```python
#!/usr/bin/env python3
"""Package a runner result as a replayable candidate experiment."""
import json, sys
from pathlib import Path

if len(sys.argv) != 4: raise SystemExit(2)
result = json.loads(Path(sys.argv[1]).read_text())
if result.get("schema") != 1 or result.get("status") not in {"observed", "not_observed"}:
    raise SystemExit("invalid result")
package = {"schema": 1, "candidate_id": sys.argv[2],
           "hypothesis": "a bounded focused probe can reproduce the indicated synthetic boundary effect",
           "result_status": result["status"], "claim": result["claim"], "trace": result["trace"],
           "limits": ["synthetic local oracle", "single run", "bounded probe set", "non-discovery is not proof"],
           "replay": ["python3", "adaptive_runner.py", "SPEC.json", "RESULT.json"]}
Path(sys.argv[3]).write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")
```

<!-- PAGEBREAK -->

## lab/README.md

# Module 12 independent lab - Bounded adaptive runner

Implement `adaptive_runner.py`; the grader calls `python3 adaptive_runner.py SPEC.json RESULT.json`. The spec contains exact `oracle_command` argv, integer action `budget`, and opaque `run_id`.

Validate before acting. Invoke only `inventory`, `argv`, `credential`, `filesystem`, `network`, or `cleanup`, using exact argv without a shell and with bounded execution. Record sequential action numbers and complete parsed observations. Never exceed budget. Preserve run identity. For an observed focused effect, return its trace row as the finding. If no effect is observed, use `not_observed` and explicitly say security is not established.

The grader rotates five hidden synthetic weakness classes plus a no-weakness case. It checks discovery within two actions, allowlisting, trace integrity, calibrated non-discovery, determinism, and identity preservation. The starter inventories only and therefore misses every weakness.

```bash
python3 -m py_compile adaptive_runner.py
../../lab-grade module-12
../../lab-grade module-12 --mode exam
```

Do not inspect, modify, or target anything outside the supplied local oracle command.

<!-- PAGEBREAK -->

## Integrated interpretation

The scripted and adaptive runs share an oracle and evidence schema. Adaptation changes probe selection, not the target or success definition. Budget, allowlist, exact argv, deterministic trace, and calibrated claims keep comparison meaningful. A `not_observed` result says only that this bounded run found no effect; it never establishes security.

## Safety and graduation

The oracle is local, synthetic, deterministic, and non-destructive. The module creates no network connection, credential, service, or persistent resource. A Boundary Atlas candidate is a reproducible experiment package—not a vulnerability announcement. It preserves hypothesis, trace, result, replay argv, and interpretation limits for independent review.

