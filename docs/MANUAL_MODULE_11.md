# North Echo field manual - Module 11

This chapter is self-contained for the randomized break/fix research lessons and independent lab. It repeats every guided command, fixture, and complete source listing. All effects are synthetic and local; the harness does not connect to a target or delete cleanup candidates.

The method is evidence first: reproduce a bounded effect, state the invariant it violates, repair every applicable layer, preserve useful behavior, and rerun the same probe against the hardened counterpart.

<!-- PAGEBREAK -->

## Module overview

# Module 11 - Vulnerable variants and break/fix research

Analyze seeded runtime weaknesses without being told which control changed. Use a deterministic non-agent harness to reproduce effects, map observations to failed invariants, repair the plan, and compare it with a hardened counterpart.

Play in order: `11.01`, `11.02`, `11.03`, then `module-11`.

Outcomes:

- distinguish a configuration difference from evidence of security impact;
- reproduce ambient credentials, shell interpretation, symlink escape, direct IP authority, and unsafe cleanup selection using synthetic local objects;
- map observed effects to stable cross-layer invariants rather than variant labels;
- repair multiple simultaneous weaknesses while preserving the allowed operation and opaque run identity;
- prove a repair is idempotent and survives fresh randomized variants.

The harness never exploits an external target and never deletes its cleanup candidates. Every credential, path, marker, resource, and socket is synthetic and confined to the disposable workspace. Prerequisites are Modules 01, 04, 05, 08, 09, and 10.

<!-- PAGEBREAK -->

## Lesson 11.01

# 11.01 - Reproduce a seeded weakness without an agent

## Goal

Generate a repeatable unknown variant, use a deterministic harness to reproduce its effects, and separate configuration clues from behavioral evidence.

## Exercise 1 - Read the complete generator and harness

```bash
sed -n '1,200p' make_variant.py
sed -n '1,300p' variant_harness.py
```

### Line by line

- `make_variant.py` starts from five hardened controls, uses only an explicit integer seed, and weakens two through four randomly selected controls. The seed makes research replayable; it is not security randomness.
- The workload contains one allowed synthetic read and a literal shell-looking argument. Variant identity is opaque evidence metadata.
- `variant_harness.py` creates a new private directory, allowed file, protected sibling, symlink, and marker.
- Execution mode passes the same literal through either `shell=True` or an argv array. Environment mode launches `/usr/bin/env` with inherited or minimal variables.
- Filesystem mode compares lexical spelling or the resolved target. Network mode creates, but never connects, an IPv4 socket. Cleanup mode selects candidate names but never deletes them.
- The evidence contains observed effects, not the control labels, and preserves allowed-operation success.

## Exercise 2 - Trigger and replay the variant

```bash
python3 make_variant.py 1101 variant.json
NORTH_ECHO_FAKE_CREDENTIAL=FAKE-LESSON-11.01 \
  python3 variant_harness.py variant.json evidence.json run-a
python3 -m json.tool variant.json
python3 -m json.tool evidence.json
```

At least two adverse evidence fields are true. `allowed_operation` remains true. The intentional mistake is to call the changed configuration itself proof: a `direct` field is suspicious, but `inet_created:true` is the reproduced effect.

Replay the exact seed and compare:

```bash
python3 make_variant.py 1101 replay.json
cmp variant.json replay.json
```

The byte-identical plan makes the observation reproducible. A different seed may select a different weakness set without changing the research method.

## Exercise 3 - Prove the harness is bounded

```bash
test ! -e run-a/not-a-workspace
test -e run-a/protected.txt
find run-a -maxdepth 2 -type f -o -type l | sort
rm run-a/allowed/data.txt run-a/allowed/link.txt run-a/protected.txt
test ! -e run-a/shell-marker || rm run-a/shell-marker
rmdir run-a/allowed run-a
rm variant.json replay.json evidence.json
```

The protected file still exists because the reproducer reads but never modifies it. Cleanup evidence is only a selected-name list inside the harness; no service or host object is removed.

## Checkpoint and troubleshooting

- If `run-a` exists, remove only the exact files listed above before replaying; the harness refuses to reuse a directory.
- If no credential is visible in an inherited variant, confirm the explicitly fake variable prefixes the harness command.
- Do not replace the synthetic literal with a command affecting anything outside the generated directory.
- Checkpoint: identify one field that is configuration and one field that is reproduced evidence.

<!-- PAGEBREAK -->

## Complete source: `make_variant.py`

Canonical path: `course/module-11-break-fix-research/lesson-01/make_variant.py`

```python
#!/usr/bin/env python3
"""Create a reproducible vulnerable plan from an explicit integer seed."""

import json
import random
import sys
from pathlib import Path

SECURE = {"execution": "argv", "environment": "minimal", "filesystem": "resolved",
          "network": "broker_only", "cleanup": "owned"}
WEAK = {"execution": "shell", "environment": "inherit", "filesystem": "lexical",
        "network": "direct", "cleanup": "prefix"}

if len(sys.argv) != 3:
    raise SystemExit(f"usage: {sys.argv[0]} SEED OUTPUT.json")
rng = random.Random(int(sys.argv[1]))
controls = dict(SECURE)
for name in rng.sample(sorted(WEAK), rng.randint(2, 4)):
    controls[name] = WEAK[name]
plan = {
    "schema": 1,
    "variant_id": f"seed-{sys.argv[1]}",
    "workload": {"operation": "read", "resource": "record:alpha",
                 "literal": "literal $(touch shell-marker)"},
    "controls": controls,
}
Path(sys.argv[2]).write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
```

<!-- PAGEBREAK -->

## Complete source: `variant_harness.py`

Canonical path: `course/module-11-break-fix-research/lesson-01/variant_harness.py`

```python
#!/usr/bin/env python3
"""Reproduce runtime-plan effects without an autonomous agent or external target."""

import json
import os
from pathlib import Path
import socket
import subprocess
import sys


def main() -> int:
    if len(sys.argv) != 4:
        return 2
    plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    evidence_path, work = Path(sys.argv[2]), Path(sys.argv[3])
    work.mkdir(mode=0o700, parents=True, exist_ok=False)
    allowed = work / "allowed"
    allowed.mkdir()
    (allowed / "data.txt").write_text("allowed\n", encoding="utf-8")
    protected = work / "protected.txt"
    protected.write_text("SYNTHETIC-PROTECTED\n", encoding="utf-8")
    (allowed / "link.txt").symlink_to(protected.resolve())
    marker = work / "shell-marker"
    literal = plan["workload"]["literal"].replace("shell-marker", str(marker))
    controls = plan["controls"]

    if controls["execution"] == "shell":
        subprocess.run("/usr/bin/printf '%s\\n' " + literal, shell=True, cwd=work,
                       text=True, capture_output=True, check=False)
    else:
        subprocess.run(["/usr/bin/printf", "%s\n", literal], cwd=work,
                       text=True, capture_output=True, check=False)

    child_env = dict(os.environ) if controls["environment"] == "inherit" else {
        "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"
    }
    environment = subprocess.run(["/usr/bin/env"], text=True, capture_output=True,
                                 check=False, env=child_env).stdout
    credential_visible = "NORTH_ECHO_FAKE_CREDENTIAL=" in environment

    candidate = allowed / "link.txt"
    if controls["filesystem"] == "lexical":
        authorized = str(candidate).startswith(str(allowed) + os.sep)
    else:
        authorized = allowed.resolve() in candidate.resolve().parents
    protected_read = authorized and candidate.read_text(encoding="utf-8").startswith("SYNTHETIC-")

    inet_created = False
    if controls["network"] == "direct":
        stream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        inet_created = stream.fileno() >= 0
        stream.close()

    owned = f"north-echo-{plan['variant_id']}-owned"
    decoy = f"north-echo-{plan['variant_id']}-decoy"
    candidates = [owned, decoy]
    selected = candidates if controls["cleanup"] == "prefix" else [owned]
    evidence = {
        "schema": 1,
        "variant_id": plan["variant_id"],
        "allowed_operation": plan["workload"]["operation"] == "read",
        "shell_marker_created": marker.exists(),
        "credential_visible": credential_visible,
        "protected_read": protected_read,
        "inet_created": inet_created,
        "cleanup_decoy_selected": decoy in selected,
    }
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

<!-- PAGEBREAK -->

## Lesson 11.02

# 11.02 - Identify invariants from an evidence matrix

## Goal

Map observable failure signals to stable invariants, then show why repairing only the most visible symptom does not harden a mixed variant.

## Exercise 1 - Read the classifier and evidence

```bash
sed -n '1,220p' classify_evidence.py
python3 -m json.tool overfit-evidence.json
python3 -m json.tool mixed-evidence.json
```

### Line by line

- `INVARIANTS` maps each bad effect to a positive statement that must remain true across implementations.
- The classifier selects only signals explicitly observed as true. It does not guess at missing fields or inspect a variant's control labels.
- `overfit-evidence.json` has one dramatic shell marker. `mixed-evidence.json` has no marker but shows ambient credential, protected read, and cleanup over-selection.

## Exercise 2 - Make and expose an overfit diagnosis

```bash
python3 classify_evidence.py overfit-evidence.json
python3 classify_evidence.py mixed-evidence.json
```

The first output names the argv invariant. The intentional mistake is to generalize that single diagnosis to all variants. The second output names three different invariants and contains no shell failure. A repair chosen from exploit theatrics rather than a property matrix would miss them.

## Exercise 3 - Build the research matrix

```bash
python3 - <<'PY'
import json
for name in ("overfit-evidence.json", "mixed-evidence.json"):
    value = json.load(open(name))
    bad = sorted(key for key, state in value.items() if key not in {"schema", "variant_id", "allowed_operation"} and state)
    print(name, "allowed=", value["allowed_operation"], "bad=", ",".join(bad) or "none")
PY
```

### Line by line

- The loop reads both fixed evidence rows rather than relying on memory of one run.
- Metadata and the positive functional signal are separated from adverse booleans.
- Sorting makes comparison stable. The matrix preserves the fact that useful work succeeds even when containment fails.

## Checkpoint and troubleshooting

```bash
test "$(python3 classify_evidence.py mixed-evidence.json | grep -c 'invariant')" -ge 3
```

- If the count differs, inspect the complete JSON rather than changing the classifier to match a desired answer.
- An absence of one signal proves only that probe did not observe that effect; it is not universal proof of safety.
- Checkpoint: state the filesystem invariant without naming `lexical`, `resolved`, or a particular exploit path.

<!-- PAGEBREAK -->

## Complete source: `classify_evidence.py`

Canonical path: `course/module-11-break-fix-research/lesson-02/classify_evidence.py`

```python
#!/usr/bin/env python3
"""Map reproduced effects to invariant statements."""

import json
import sys
from pathlib import Path

INVARIANTS = {
    "shell_marker_created": "argv is data and is never shell syntax",
    "credential_visible": "the workload receives no ambient credential",
    "protected_read": "authorization follows resolved objects, not lexical paths",
    "inet_created": "the workload has no direct IP socket authority",
    "cleanup_decoy_selected": "cleanup selects only exact owned objects",
}

if len(sys.argv) != 2:
    raise SystemExit(f"usage: {sys.argv[0]} EVIDENCE.json")
evidence = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
failed = [{"signal": name, "invariant": statement}
          for name, statement in INVARIANTS.items() if evidence.get(name) is True]
print(json.dumps({"variant_id": evidence.get("variant_id"), "failed": failed}, indent=2, sort_keys=True))
raise SystemExit(not failed)
```

<!-- PAGEBREAK -->

## Complete fixture: `overfit-evidence.json`

Canonical path: `course/module-11-break-fix-research/lesson-02/overfit-evidence.json`

```json
{"schema":1,"variant_id":"lesson-overfit","allowed_operation":true,"shell_marker_created":true,"credential_visible":false,"protected_read":false,"inet_created":false,"cleanup_decoy_selected":false}
```

<!-- PAGEBREAK -->

## Complete fixture: `mixed-evidence.json`

Canonical path: `course/module-11-break-fix-research/lesson-02/mixed-evidence.json`

```json
{"schema":1,"variant_id":"lesson-mixed","allowed_operation":true,"shell_marker_created":false,"credential_visible":true,"protected_read":true,"inet_created":false,"cleanup_decoy_selected":true}
```

<!-- PAGEBREAK -->

## Lesson 11.03

# 11.03 - Repair and prove the hardened counterpart

## Goal

Repair all known weak controls in one pass, preserve the workload and variant identity, prove behavior with the same harness, and require idempotence.

## Exercise 1 - Read the complete repair tool

```bash
sed -n '1,300p' repair_variant.py
python3 -m json.tool vulnerable-plan.json
```

### Line by line

- `SECURE` expresses the five positive control choices; `ALLOWED` bounds both secure and deliberately weak input values.
- `repair` requires the exact top-level, workload, and control shapes, validates types and known values, copies opaque workload/identity fields, and replaces only the controls.
- `main` parses completely before output, writes a sibling temporary file, and atomically replaces the result. Invalid input leaves no claimed repair.
- Applying the function to an already hardened plan produces the same JSON object: repair is idempotent.

## Exercise 2 - Observe the vulnerable counterpart

```bash
cp vulnerable-plan.json before.json
NORTH_ECHO_FAKE_CREDENTIAL=FAKE-LESSON-11.03 \
  python3 ../../course/module-11-break-fix-research/lesson-01/variant_harness.py \
  before.json before-evidence.json before-run
python3 -m json.tool before-evidence.json
```

All five adverse signals are true while `allowed_operation` is true. This is the intentional vulnerable counterpart, not an instruction to target another system.

## Exercise 3 - Repair and compare

```bash
python3 repair_variant.py before.json after.json
NORTH_ECHO_FAKE_CREDENTIAL=FAKE-LESSON-11.03 \
  python3 ../../course/module-11-break-fix-research/lesson-01/variant_harness.py \
  after.json after-evidence.json after-run
python3 -m json.tool after-evidence.json
python3 repair_variant.py after.json second.json
cmp after.json second.json
```

Expected: the allowed operation stays true and every adverse signal is false. `cmp` proves a second repair does not mutate an already hardened plan.

Clean the exact generated objects:

```bash
rm before-run/allowed/data.txt before-run/allowed/link.txt before-run/protected.txt before-run/shell-marker
rmdir before-run/allowed before-run
rm after-run/allowed/data.txt after-run/allowed/link.txt after-run/protected.txt
rmdir after-run/allowed after-run
rm before.json after.json second.json before-evidence.json after-evidence.json
```

## Checkpoint and troubleshooting

- If the hardened evidence still contains a true adverse field, compare that field with the corresponding invariant before editing another layer.
- If cleanup says a marker is absent, remove it conditionally; only the vulnerable execution mode creates it.
- If relative canonical paths fail, confirm the command is run from `.student/11.03`.
- Checkpoint: explain why preserving workload bytes and allowed behavior matters as much as making adverse signals false.

<!-- PAGEBREAK -->

## Complete source: `repair_variant.py`

Canonical path: `course/module-11-break-fix-research/lesson-03/repair_variant.py`

```python
#!/usr/bin/env python3
"""Repair every known weak control while preserving the workload contract."""

import json
from pathlib import Path
import sys

SECURE = {"execution": "argv", "environment": "minimal", "filesystem": "resolved",
          "network": "broker_only", "cleanup": "owned"}
ALLOWED = {
    "execution": {"argv", "shell"}, "environment": {"minimal", "inherit"},
    "filesystem": {"resolved", "lexical"}, "network": {"broker_only", "direct"},
    "cleanup": {"owned", "prefix"},
}


def repair(value: object) -> dict:
    if not isinstance(value, dict) or set(value) != {"schema", "variant_id", "workload", "controls"}:
        raise ValueError("invalid plan shape")
    if value["schema"] != 1 or not isinstance(value["variant_id"], str) or not value["variant_id"]:
        raise ValueError("invalid plan identity")
    workload, controls = value["workload"], value["controls"]
    if not isinstance(workload, dict) or set(workload) != {"operation", "resource", "literal"}:
        raise ValueError("invalid workload")
    if not all(isinstance(item, str) for item in workload.values()):
        raise ValueError("invalid workload values")
    if not isinstance(controls, dict) or set(controls) != set(SECURE):
        raise ValueError("invalid controls")
    if any(controls[name] not in ALLOWED[name] for name in SECURE):
        raise ValueError("unknown control value")
    return {"schema": 1, "variant_id": value["variant_id"],
            "workload": dict(workload), "controls": dict(SECURE)}


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    output = Path(sys.argv[2])
    try:
        source = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        repaired = repair(source)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"repair denied: {error}", file=sys.stderr)
        return 1
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(json.dumps(repaired, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

<!-- PAGEBREAK -->

## Complete fixture: `vulnerable-plan.json`

Canonical path: `course/module-11-break-fix-research/lesson-03/vulnerable-plan.json`

```json
{"schema":1,"variant_id":"lesson-repair","workload":{"operation":"read","resource":"record:alpha","literal":"literal $(touch shell-marker)"},"controls":{"execution":"shell","environment":"inherit","filesystem":"lexical","network":"direct","cleanup":"prefix"}}
```

<!-- PAGEBREAK -->

## Module 11 independent lab

# Module 11 independent lab - Repair randomized runtime variants

Implement `repair_variant.py`. The grader invokes:

```text
python3 repair_variant.py INPUT.json OUTPUT.json
```

Input is a schema-1 object with opaque `variant_id`, an exact workload object (`operation`, `resource`, `literal`), and five controls: execution, environment, filesystem, network, and cleanup. Each control contains either the hardened value practiced in Lesson 11.03 or its deliberately weak counterpart. One through five weaknesses may coexist.

Validate the complete shape and known values before writing output. Preserve the input file, variant identity, and workload exactly. Repair every control, not only the first observed weakness. Write a valid plan atomically. A malformed or unknown plan must return nonzero without output. Applying the repair to its own output must be idempotent.

The external grader uses fresh identities, resources, literals, canaries, and six weakness combinations. It evaluates each output with the canonical non-agent harness. The allowed operation must still work; literal argv must not create a marker; the fake credential must be absent; the protected symlink target must not be read; direct IPv4 socket authority must be absent; and cleanup must exclude an unowned prefix-matching decoy. The harness never connects, deletes a candidate, or touches an external target.

The starter repairs only execution mode, so it is functional but fails mixed variants. The lab withholds the full repair implementation.

```bash
python3 -m py_compile repair_variant.py
../../lab-grade module-11
../../lab-grade module-11 --mode exam
```

- Syntax checking creates no research object.
- Practice mode reports failed properties with lesson references.
- Exam mode repeats fresh variants while withholding repair hints.

Use only generated synthetic plans. Do not turn the evidence harness into an external scanner or destructive cleanup tool.

<!-- PAGEBREAK -->

## Integrated research method

A variant label is not a finding. The generator supplies a replayable hypothesis; the non-agent harness produces effects; the evidence matrix maps effects to invariants; and the repair is accepted only after the same harness shows useful behavior remains while every adverse signal becomes false.

The five invariants deliberately span earlier modules:

- argv is data, never shell syntax;
- the workload receives no ambient credential;
- filesystem authorization follows resolved objects;
- the workload has no direct IP socket authority;
- cleanup selects only exact owned objects.

Multiple failures can coexist. Repairing the most dramatic signal is overfitting. The lab varies combination size and order, checks preservation, then applies the repair again to prove convergence rather than repeated mutation.

## Interpretation limits

A false signal means this bounded probe did not reproduce that effect for this plan. It is not universal assurance, exploit absence, or a claim about unrelated implementations. A true signal is sufficient evidence that the corresponding invariant failed in the synthetic harness. The module favors small reproducible observations over novelty or exploit spectacle.

## Safety and cleanup

The shell marker is constrained to a fresh lesson directory. IPv4 testing creates an unconnected socket only. The fake credential has no external authority. The protected file contains a literal synthetic string. Cleanup candidates are compared as strings and never removed by the harness. Lesson cleanup names exact generated paths; platform reset handles student work and fixtures.

## Optional primary references

Required teaching is above. Optional depth: `subprocess(3)` Python documentation, `openat2(2)`, `unix(7)`, `network_namespaces(7)`, and the earlier North Echo module chapters governing each invariant.

## Completion checkpoint

A credible repair package contains the input plan, bounded reproducer, before evidence, invariant statement, repaired plan, after evidence, functional preservation, idempotence result, and exact cleanup record. Removing any one of these weakens the conclusion.
