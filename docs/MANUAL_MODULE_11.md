<!-- PAGEBREAK -->

<!-- source: course/module-11-break-fix-research/README.md format=markdown -->
# Module 11 - Compare and repair a small containment model

Complete Modules 01-10 first. Work through `11.01`, `11.02`, `11.03`, then `module-11`.

The earlier modules attempted operations under Linux controls. This chapter changes scale: you inspect a deliberately small, fixed local model to practice evidence classification, complete repair, preservation, and replay. It is not an external vulnerability-discovery exercise and does not reproduce arbitrary vulnerabilities.

By the end you should be able to:

- distinguish configuration choices, actual local effects, modeled decisions, and unobserved properties;
- generate and replay a seeded combination without treating its name as a diagnosis;
- classify every supplied observation and reject missing evidence;
- repair all known model choices while preserving the allowed operation and opaque identity;
- test idempotence and explain what a successful model comparison does **not** establish.

The harness uses a constant shell marker fixture, one explicitly fake variable, generated sibling files, an unconnected socket, and string-only cleanup candidates. It never interprets arbitrary plan text, contacts a target, or deletes a cleanup candidate. The broker-only branch skips socket creation; it does not install kernel confinement. The resolved-path branch is not race-free, and cleanup selection is not real resource collection. Keep those limitations beside every conclusion.

Estimated work: three guided sessions plus an independent repair lab. Save short evidence notes as you go; a passing JSON comparison is not a substitute for explaining the observation.
<!-- /source -->

---

<!-- source: course/module-11-break-fix-research/lesson-01/README.md format=markdown -->
# 11.01 - Reproduce a seeded weakness without an agent

## Outcomes and prerequisites

Complete Modules 01-10. You will generate a repeatable teaching variant, record its fixed local effects, and separate actual observations from model choices. No autonomous agent, external target, or generated exploit is involved.

## Concepts before commands

A **seed** makes a pseudo-random teaching choice repeatable. It is not a secret and is not suitable for credential generation. A **variant** is one combination of control settings, not a vulnerability identifier.

This harness is a deliberately small model, not the Module 10 runtime. Its evidence mixes real local effects with modeled decisions. That distinction is part of the lesson:

| Field | What this harness establishes |
| --- | --- |
| `shell_marker_created` | A fixed, hard-coded shell fixture created its own marker |
| `credential_visible` | The explicitly fake variable was present in a small child environment |
| `protected_read` | A generated local symlink led to the synthetic sibling under the selected path check |
| `inet_created` | The direct branch created an unconnected socket; the other branch simply skipped creation |
| `cleanup_decoy_selected` | String selection included an unowned decoy; nothing was deleted |
| `allowed_operation` | The modeled read operation and actual generated allowed-file read both succeeded |

In particular, `inet_created: false` here does **not** establish kernel network confinement. Return to Modules 08 and 10 for a real attempted operation under enforced controls. Likewise, `resolved` uses a separate resolve-then-read check and does not solve the race discussed in Module 05.

## Prepare and read both programs

From the course root:

```bash
./lab-start 11.01
cd .student/11.01
pwd
ls -l make_variant.py variant_harness.py
cat make_variant.py
cat variant_harness.py
```

Use `nano` with either filename to navigate the source. The exercises supply only generated synthetic plans. Never put a real command, secret, target, or production path in a plan.

### The seeded generator

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

### Source, line by line

- `SECURE` and `WEAK` enumerate the two modeled choices for each control. Their names are design labels, not proof of enforcement.
- `random.Random(int(...))` creates a local deterministic generator from the supplied integer.
- `dict(SECURE)` copies the baseline so changing this variant does not mutate the shared mapping.
- Sampling sorted names selects two through four distinct controls. It changes only their configured choices.
- The workload contains a harmless operation/resource and shell-looking literal data. The harness never executes that plan text as shell code.
- The output includes a schema version and opaque identity. Sorted, indented JSON makes exact replay comparison straightforward.

### The fixed local harness

```python
#!/usr/bin/env python3
"""Observe fixed synthetic fixtures and model choices, never execute plan text."""

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
    choices = {
        "execution": {"shell", "argv"}, "environment": {"inherit", "minimal"},
        "filesystem": {"lexical", "resolved"}, "network": {"direct", "broker_only"},
        "cleanup": {"prefix", "owned"},
    }
    if not isinstance(plan, dict) or set(plan) != {"schema", "variant_id", "workload", "controls"}:
        raise ValueError("invalid plan shape")
    if type(plan["schema"]) is not int or plan["schema"] != 1 or not isinstance(plan["variant_id"], str):
        raise ValueError("invalid plan identity")
    workload, controls = plan["workload"], plan["controls"]
    if not isinstance(workload, dict) or set(workload) != {"operation", "resource", "literal"}:
        raise ValueError("invalid workload shape")
    if not all(isinstance(value, str) for value in workload.values()):
        raise ValueError("invalid workload values")
    if not isinstance(controls, dict) or set(controls) != set(choices):
        raise ValueError("invalid control shape")
    if any(not isinstance(controls[name], str) or controls[name] not in choices[name] for name in choices):
        raise ValueError("unknown control choice")
    evidence_path, work = Path(sys.argv[2]), Path(sys.argv[3])
    work.mkdir(mode=0o700, parents=True, exist_ok=False)
    allowed = work / "allowed"
    allowed.mkdir()
    (allowed / "data.txt").write_text("allowed\n", encoding="utf-8")
    protected = work / "protected.txt"
    protected.write_text("SYNTHETIC-PROTECTED\n", encoding="utf-8")
    (allowed / "link.txt").symlink_to(protected.resolve())
    marker = work / "shell-marker"
    literal = workload["literal"]
    fixed_env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}

    if controls["execution"] == "shell":
        # Fixed toy only: the plan's literal is never interpreted as shell code.
        subprocess.run(["/bin/sh", "-c", '/usr/bin/printf "%s\\n" "$(/usr/bin/touch "$1")"',
                        "fixed-marker-fixture", str(marker.resolve())], cwd=work,
                       text=True, capture_output=True, check=True, timeout=2, env=fixed_env)
    else:
        subprocess.run(["/usr/bin/printf", "%s\n", literal], cwd=work,
                       text=True, capture_output=True, check=True, timeout=2, env=fixed_env)

    child_env = dict(fixed_env)
    if controls["environment"] == "inherit" and "NORTH_ECHO_FAKE_CREDENTIAL" in os.environ:
        child_env["NORTH_ECHO_FAKE_CREDENTIAL"] = os.environ["NORTH_ECHO_FAKE_CREDENTIAL"]
    environment = subprocess.run(["/usr/bin/env"], text=True, capture_output=True,
                                 check=True, timeout=2, env=child_env).stdout
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
        "allowed_operation": workload["operation"] == "read" and
                             (allowed / "data.txt").read_text(encoding="utf-8") == "allowed\n",
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

### Source, line by line

- The initial checks require exact plan/workload/control shapes and known string choices **before** creating a work directory.
- `mkdir(..., exist_ok=False)` refuses reuse. All fixture files live under this fresh private directory.
- The allowed file and protected sibling contain fixed synthetic text. The symlink deliberately references that sibling, never an external target.
- The shell-mode branch runs a **constant** tiny shell program. Only its exact new marker pathname is passed as a quoted positional argument; arbitrary plan literals are never interpreted.
- The argv branch passes the plan literal as one data argument to printf. Both child executions have a fixed environment and timeout.
- The environment fixture copies only the explicitly fake variable when the inherited-choice branch is selected; it does not forward unrelated parent credentials.
- The filesystem branch compares either path spelling or the resolved object's ancestry, then performs the generated local read if authorized.
- The direct network branch creates and closes a socket without connecting. The broker-only branch is a model selection, not an installed network policy.
- Cleanup candidates are ordinary strings. Choosing one or both has no destructive effect.
- Evidence records these observations and an actual allowed-file read. The harness writes JSON and exits; it installs no persistent service.

## Exercise 1 - Predict, generate, and observe

```bash
python3 make_variant.py 1101 variant.json
python3 -m json.tool variant.json
NORTH_ECHO_FAKE_CREDENTIAL=FAKE-LESSON-11.01 \
  python3 variant_harness.py variant.json evidence.json run-a
python3 -m json.tool evidence.json
```

Before the harness run, predict which adverse fields should be true from the choices. Afterward, compare with observed effects. With the supplied fake variable and working socket API, at least two adverse fields should be true while the allowed operation remains true.

The mistake to avoid is writing “network confinement is broken” solely because a plan says `direct`. The actual positive observation is narrower: this model branch created an unconnected socket. It did not contact anything or test a deployed runtime.

## Exercise 2 - Replay the plan, not a conclusion

```bash
python3 make_variant.py 1101 replay.json
cmp variant.json replay.json
NORTH_ECHO_FAKE_CREDENTIAL=FAKE-LESSON-11.01 \
  python3 variant_harness.py replay.json replay-evidence.json run-b
cmp evidence.json replay-evidence.json
```

The same seed reproduces the plan, and fresh fixture directories permit a second observation. Byte equality is useful here because this harness's output contains no random paths or timestamps. It does not mean every real experiment must produce byte-identical logs.

## Exercise 3 - Repair an overbroad claim

Write `nano evidence-notes.md`. For one true field, record configuration, observed effect, violated intended invariant, and a limitation. Then write one false field's limited meaning. For the network branch, explicitly distinguish “no socket was created by this branch” from “the kernel denied socket creation.”

The repair is to the **claim**, not to the evidence file. Do not change observations to make the report look safer. Lesson 11.03 will repair the modeled plan and compare a new run.

## Checkpoint and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

evidence = json.loads(Path("evidence.json").read_text())
signals = ("shell_marker_created", "credential_visible", "protected_read",
           "inet_created", "cleanup_decoy_selected")
assert evidence["allowed_operation"] is True
assert sum(evidence[name] is True for name in signals) >= 2
assert json.loads(Path("replay-evidence.json").read_text()) == evidence
assert Path("run-a/protected.txt").read_text() == "SYNTHETIC-PROTECTED\n"
assert not Path("run-a/not-a-workspace").exists()
print("FIXED LOCAL EFFECTS AND REPLAY: PASS")
PY
```

The synthetic protected file remains intact; no cleanup candidate was deleted. If a work directory exists, prepare a new name or reset the lesson rather than reuse stale artifacts. If the fake-variable observation is absent, prefix the command in this same VM shell.

Save your notes, return with `cd ../..`, and use `./lab-reset 11.01` to remove only the prepared workspace and fixtures. Do not extend this harness into a scanner, arbitrary command runner, or destructive cleanup utility.

## Source truth

Python's [random documentation](https://docs.python.org/3.14/library/random.html) distinguishes deterministic pseudo-random generation from security randomness; [subprocess](https://docs.python.org/3.14/library/subprocess.html) defines argv and environment handoffs. Earlier kernel lessons supply enforcement evidence that this small model does not.
<!-- /source -->

---

<!-- source: course/module-11-break-fix-research/lesson-02/README.md format=markdown -->
# 11.02 - Identify invariants from an evidence matrix

## Outcomes and prerequisites

Complete 11.01. You will map supplied observations to intended invariants, avoid diagnosing every case from one dramatic symptom, and reject incomplete evidence instead of treating missing fields as negative observations.

## Concepts before commands

An **invariant** is a property the design intends to preserve across variants. “Arguments remain data” is an invariant; “this variant used the argv option” is a configuration fact. The latter does not automatically establish the former in arbitrary code.

**Overfitting** means tailoring your conclusion to the examples you noticed rather than the underlying property. A conspicuous shell marker can distract from a quieter inherited credential or cleanup over-selection.

These fixed JSON rows are teaching fixtures, not fresh measurements of your current VM. The classifier interprets their content; it does not run a workload or independently verify their provenance. Keep both the observation source and its limitations in your report.

## Prepare and read the classifier and cases

From the course root:

```bash
./lab-start 11.02
cd .student/11.02
pwd
ls -l classify_evidence.py overfit-evidence.json mixed-evidence.json
cat classify_evidence.py
cat overfit-evidence.json
cat mixed-evidence.json
```

Use `nano mixed-evidence.json` to navigate, but leave the shipped case intact. The deliberate missing-field case will use a separate copy.

### The classifier

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
required = {"schema", "variant_id", "allowed_operation", *INVARIANTS}
if (not isinstance(evidence, dict) or set(evidence) != required
        or type(evidence["schema"]) is not int or evidence["schema"] != 1
        or not isinstance(evidence["variant_id"], str)
        or any(type(evidence[name]) is not bool for name in ("allowed_operation", *INVARIANTS))):
    raise SystemExit("invalid or incomplete evidence; absence is not a negative observation")
failed = [{"signal": name, "invariant": statement}
          for name, statement in INVARIANTS.items() if evidence.get(name) is True]
print(json.dumps({"variant_id": evidence.get("variant_id"), "failed": failed}, indent=2, sort_keys=True))
raise SystemExit(0)
```

### Source, line by line

- `INVARIANTS` maps each adverse signal to the positive property it calls into question.
- The argv guard requires one evidence filename; JSON is then parsed into Python data.
- The complete key-set check prevents an omitted signal from silently becoming `False`.
- Schema and Boolean type checks reject values such as the string `"false"` or integer 0 in place of observed Booleans.
- The list comprehension selects only signals whose supplied value is actually `True`.
- Each selected row carries both its signal name and explanatory invariant. Variant identity is retained as metadata, not used to choose the diagnosis.
- Printing the result and returning 0 means classification completed. An empty `failed` list is a data result, not a promise of universal safety.

### Two complete supplied cases

```json
{"schema":1,"variant_id":"lesson-overfit","allowed_operation":true,"shell_marker_created":true,"credential_visible":false,"protected_read":false,"inet_created":false,"cleanup_decoy_selected":false}
```

This row contains one adverse shell-marker observation and successful allowed work.

```json
{"schema":1,"variant_id":"lesson-mixed","allowed_operation":true,"shell_marker_created":false,"credential_visible":true,"protected_read":true,"inet_created":false,"cleanup_decoy_selected":true}
```

This row has no shell marker but three other adverse observations. Neither the variant label nor the absence of one familiar symptom should override those fields.

## Exercise 1 - Diagnose both rows before execution

Predict the failed invariants, then run:

```bash
python3 classify_evidence.py overfit-evidence.json > overfit-result.json
python3 classify_evidence.py mixed-evidence.json > mixed-result.json
python3 -m json.tool overfit-result.json
python3 -m json.tool mixed-result.json
```

The first result should contain only `shell_marker_created`. The second should contain `credential_visible`, `protected_read`, and `cleanup_decoy_selected`.

The intentional diagnostic mistake is applying the first case's repair to every case. Repair the explanation by mapping **each** true signal to its invariant. Preserve the positive allowed-operation observation; disabling all useful work would not be a successful repair.

## Exercise 2 - Build a comparison matrix

```bash
python3 - <<'PY'
import json
from pathlib import Path

signals = ("shell_marker_created", "credential_visible", "protected_read",
           "inet_created", "cleanup_decoy_selected")
for name in ("overfit-evidence.json", "mixed-evidence.json"):
    value = json.loads(Path(name).read_text())
    adverse = [signal for signal in signals if value[signal] is True]
    print(name, "allowed=", value["allowed_operation"], "adverse=", ",".join(adverse) or "none")
PY
```

The program names the exact expected signal columns. It does not treat arbitrary metadata values as truthy failures. A consistent row structure makes differences visible without turning labels into evidence.

Remember 11.01's scope table: the network and cleanup branches model decisions, and pathname resolution is not a race-free kernel policy. State that distinction when using the matrix.

## Exercise 3 - Deliberately omit an observation

```bash
python3 - <<'PY'
import json
from pathlib import Path

value = json.loads(Path("mixed-evidence.json").read_text())
del value["protected_read"]
Path("incomplete.json").write_text(json.dumps(value) + "\n")
PY
NE_INCOMPLETE_STATUS=0
python3 classify_evidence.py incomplete.json > incomplete-result.json 2> incomplete.err || NE_INCOMPLETE_STATUS=$?
cat incomplete.err
test "$NE_INCOMPLETE_STATUS" -ne 0
test ! -s incomplete-result.json
python3 classify_evidence.py mixed-evidence.json > repaired-result.json
```

The omitted field is unknown, not false. The classifier refuses the incomplete row instead of silently reducing the failure count. Repair the analysis by returning to the complete supplied evidence, not by inventing a replacement observation.

## Checkpoint and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

def signals(name):
    return {row["signal"] for row in json.loads(Path(name).read_text())["failed"]}

assert signals("overfit-result.json") == {"shell_marker_created"}
assert signals("mixed-result.json") == {
    "credential_visible", "protected_read", "cleanup_decoy_selected"
}
assert signals("repaired-result.json") == signals("mixed-result.json")
assert "incomplete evidence" in Path("incomplete.err").read_text()
print("INVARIANT MATRIX AND MISSING-EVIDENCE REFUSAL: PASS")
PY
```

In `nano matrix-notes.md`, explain an invariant without naming the implementation option that supposedly enforces it. Then identify one additional observation needed before claiming kernel enforcement rather than model selection.

If a count differs, inspect all input fields and their types. Do not modify the classifier to produce a preferred answer. Save notes, return with `cd ../..`, and use `./lab-reset 11.02` to remove this prepared workspace. No service was launched.

## Source truth

Python's [JSON documentation](https://docs.python.org/3.14/library/json.html) defines parsing and serialization, not the truth of a record's claims. The invariant mapping and fixture limitations are course-defined. Modules 05, 08, and 10 show the separate behavioral observations needed to support enforcement conclusions.
<!-- /source -->

---

<!-- source: course/module-11-break-fix-research/lesson-03/README.md format=markdown -->
# 11.03 - Repair and prove the hardened counterpart

## Outcomes and prerequisites

Complete 11.01-11.02. You will validate and repair every modeled control, preserve identity/workload data, compare before/after fixture observations, and test idempotence. “Hardened counterpart” here means the known-good **model choices**, not a newly certified kernel runtime.

## Concepts before commands

A repair must preserve the intended work as well as remove adverse effects. Changing the resource, deleting the workload, or suppressing inconvenient evidence would change the question instead of answering it.

An **idempotent** repair produces the same result when applied again to its own output. This makes repeated application predictable. It does not prove every security property.

An **atomic replacement** makes a complete new file appear at the destination rather than exposing a half-written JSON document. It is not a claim of crash durability; that would require additional synchronization and filesystem assumptions.

## Prepare and read the source and fixture

From the course root:

```bash
./lab-start 11.03
cd .student/11.03
pwd
ls -l repair_variant.py vulnerable-plan.json
cat repair_variant.py
cat vulnerable-plan.json
```

The harness is the same fixed local program read in 11.01. The commands below reference its canonical copy for consistent comparison; do not modify it to make a repair pass.

### The repair tool

```python
#!/usr/bin/env python3
"""Repair every known weak control while preserving the workload contract."""

import json
import os
from pathlib import Path
import sys
import tempfile

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
    if type(value["schema"]) is not int or value["schema"] != 1 or not isinstance(value["variant_id"], str) or not value["variant_id"]:
        raise ValueError("invalid plan identity")
    workload, controls = value["workload"], value["controls"]
    if not isinstance(workload, dict) or set(workload) != {"operation", "resource", "literal"}:
        raise ValueError("invalid workload")
    if not all(isinstance(item, str) for item in workload.values()):
        raise ValueError("invalid workload values")
    if not isinstance(controls, dict) or set(controls) != set(SECURE):
        raise ValueError("invalid controls")
    if any(not isinstance(controls[name], str) or controls[name] not in ALLOWED[name] for name in SECURE):
        raise ValueError("unknown control value")
    return {"schema": 1, "variant_id": value["variant_id"],
            "workload": dict(workload), "controls": dict(SECURE)}


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    output = Path(sys.argv[2])
    try:
        if output.resolve() == Path(sys.argv[1]).resolve() or output.is_symlink():
            raise ValueError("output must be separate from input and not a symlink")
        source = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        repaired = repair(source)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"repair denied: {error}", file=sys.stderr)
        return 1
    fd, name = tempfile.mkstemp(prefix=".repair-", dir=output.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(repaired, indent=2, sort_keys=True) + "\n")
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### Source, line by line

- `SECURE` holds the five intended model choices. `ALLOWED` enumerates valid input choices, including the deliberately weak alternatives.
- `repair` checks the exact top-level shape, integer schema, nonempty identity, workload shape, and textual values.
- Control names must match the complete set; each control must be a known string. A list or unknown value is rejected, not coerced.
- The result copies opaque identity and workload values and replaces only the control mapping.
- `main` refuses an output that resolves to the input or is a symlink. Validation completes before any temporary output is created.
- `mkstemp` creates an exclusive unpredictable temporary file in the output directory, avoiding a reused predictable sibling name.
- `os.fdopen` writes through the already-created descriptor. Closing the stream completes this process's write before replacement.
- `replace` publishes the complete JSON at the destination on the same filesystem.
- `finally` removes only that exact owned temporary path if an error leaves it behind.
- Invalid input returns nonzero with a diagnostic; it does not publish a claimed repair.

### The deliberately mixed plan

```json
{"schema":1,"variant_id":"lesson-repair","workload":{"operation":"read","resource":"record:alpha","literal":"literal $(touch shell-marker)"},"controls":{"execution":"shell","environment":"inherit","filesystem":"lexical","network":"direct","cleanup":"prefix"}}
```

All five choices are weak in this fixture. Its resource and literal are synthetic metadata. Neither the repairer nor the harness is an interface for executing arbitrary plan text.

## Exercise 1 - Record the before case

```bash
cp vulnerable-plan.json before.json
NORTH_ECHO_FAKE_CREDENTIAL=FAKE-LESSON-11.03 \
  python3 ../../course/module-11-break-fix-research/lesson-01/variant_harness.py \
  before.json before-evidence.json before-run
python3 -m json.tool before-evidence.json
```

With the supplied fake variable, expect all five adverse fields to be true and allowed work to succeed. The real effects are limited to the fixed local fixtures; the network/cleanup limitations from 11.01 still apply.

## Exercise 2 - Repair every choice and compare

```bash
python3 repair_variant.py before.json after.json
NORTH_ECHO_FAKE_CREDENTIAL=FAKE-LESSON-11.03 \
  python3 ../../course/module-11-break-fix-research/lesson-01/variant_harness.py \
  after.json after-evidence.json after-run
python3 -m json.tool after-evidence.json
python3 repair_variant.py after.json second.json
cmp after.json second.json
cmp vulnerable-plan.json before.json
```

The allowed read should remain true and every adverse field should be false. The second repair must produce identical bytes under this deterministic serializer. The original copied plan must remain unchanged.

Do not generalize the false network field into kernel denial: this modeled broker-only branch simply did not create an IP socket. Nor is the resolve-then-read branch a replacement for descriptor-relative lookup or Landlock.

## Exercise 3 - Try a partial repair, then restore completeness

```bash
python3 - <<'PY'
import json
from pathlib import Path

value = json.loads(Path("before.json").read_text())
value["controls"]["execution"] = "argv"
Path("partial.json").write_text(json.dumps(value) + "\n")
PY
NORTH_ECHO_FAKE_CREDENTIAL=FAKE-LESSON-11.03 \
  python3 ../../course/module-11-break-fix-research/lesson-01/variant_harness.py \
  partial.json partial-evidence.json partial-run
python3 -m json.tool partial-evidence.json
python3 repair_variant.py partial.json partial-repaired.json
cmp after.json partial-repaired.json
```

The intentional mistake fixes only the most visible shell fixture. Four adverse fields remain. The full repair converges to the same intended model without changing identity or workload.

## Checkpoint and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

def value(name):
    return json.loads(Path(name).read_text())

signals = ("shell_marker_created", "credential_visible", "protected_read",
           "inet_created", "cleanup_decoy_selected")
assert all(value("before-evidence.json")[name] is True for name in signals)
assert all(value("after-evidence.json")[name] is False for name in signals)
assert value("after-evidence.json")["allowed_operation"] is True
assert value("partial-evidence.json")["shell_marker_created"] is False
assert sum(value("partial-evidence.json")[name] is True for name in signals) == 4
for field in ("variant_id", "workload"):
    assert value("before.json")[field] == value("after.json")[field]
assert value("after.json") == value("second.json")
print("COMPLETE MODEL REPAIR, PRESERVATION, AND IDEMPOTENCE: PASS")
PY
```

Write `repair-notes.md` describing preserved functionality, every changed control, and the limits of the evidence. “All fields false” is not a sufficient explanation.

If a work directory already exists, reset this lesson or choose a fresh exact name. If input validation fails, repair the input shape rather than removing validation. Save notes, return with `cd ../..`, and use `./lab-reset 11.03` to remove the generated local files. The harness has created no background service and deleted no cleanup candidate.

## Source truth

Python's [tempfile documentation](https://docs.python.org/3.14/library/tempfile.html) explains exclusive temporary-file creation; [os.replace](https://docs.python.org/3.14/library/os.html#os.replace) describes replacement semantics. These file-publication mechanisms do not establish that the repaired policy itself is sufficient; that requires the scoped behavioral comparison and earlier kernel lessons.
<!-- /source -->

---

<!-- source: course/module-11-break-fix-research/lab/README.md format=markdown -->
# Module 11 independent lab - Repair randomized model variants

## Assignment and readiness check

Build a strict, deterministic repairer for the small model from 11.01-11.03. Preserve useful work and identity while correcting **every** known control choice. You are not implementing a new Linux sandbox.

Before coding, explain why a missing observation is not false, why a network branch that skips a socket is not kernel denial, and why repairing only the most conspicuous symptom leaves mixed variants incomplete.

## Prepare and read the starter

From the course root:

```bash
./lab-start module-11
cd .student/11.lab
pwd
ls -l repair_variant.py
cat repair_variant.py
nano repair_variant.py
```

Edit only this prepared copy. In the default nano configuration, Ctrl+O then Enter saves; Ctrl+X exits.

```python
#!/usr/bin/env python3
"""Module 11 starter: repairs only one visible weakness."""

import json
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit(2)
plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
plan["controls"]["execution"] = "argv"
Path(sys.argv[2]).write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
```

### Starter, line by line

- The imports provide JSON parsing, paths, and command arguments.
- The argument-count guard expects an input and an output filename.
- Parsing JSON alone does not validate the model's schema or known values.
- The single assignment repairs execution only. Other weak choices survive.
- Direct writing publishes a file without the complete validation and atomic publication required here.

The starter can produce useful-looking output while still failing most mixed variants. Your job includes failure handling, not just adding four assignments.

## Input and output contract

The grader invokes:

```text
python3 repair_variant.py INPUT.json OUTPUT.json
```

Require exactly the top-level keys `schema`, `variant_id`, `workload`, and `controls`. Schema must be integer 1, not Boolean true. Identity must be a nonempty string. Workload has exactly `operation`, `resource`, and `literal`, all strings. Treat those values as opaque data, never shell commands.

The controls must have exactly these known choices:

| Control | Intended model choice | Deliberately weak choice |
| --- | --- | --- |
| execution | argv | shell |
| environment | minimal | inherit |
| filesystem | resolved | lexical |
| network | broker_only | direct |
| cleanup | owned | prefix |

Validate the complete plan before creating output. Unknown fields, missing fields, wrong types, and unknown choices must fail nonzero. A rejected plan must not create a new output or modify an existing output. Refuse an output that aliases the input or is a symlink.

Preserve the input bytes, variant identity, and workload values. Correct all five control choices. Publish complete JSON through an exclusive temporary file in the destination directory and atomic replacement; clean only that exact owned temporary path on failure. This is atomic visibility, not a crash-durability guarantee. Setup paths belong to the exercise operator; this is not a race-free defense against a concurrent same-account mutator.

Repairing the result again must produce the same data. Use deterministic formatting so you can also compare bytes during your own tests. Return 0 only after successful publication.

## What the external checks observe

The grader rotates identities, resources, literals, fake canaries, and six combinations containing one through five weak choices. It compares preserved input/workload, complete controls, idempotence, malformed-input refusal, and fixed local harness results.

Allowed synthetic work must remain successful. The constant shell marker fixture must not run; the explicitly fake ambient variable must be absent; the generated protected sibling must not be read; the broker-only model branch must skip socket creation; and the cleanup selection must exclude the unowned string decoy.

These are finite model observations. The check does not prove kernel network denial, race-free filesystem confinement, actual cleanup ownership, or complete coverage of every malformed plan. Test your validation/publication edge cases yourself. No candidate is deleted and no socket connects.

## Map the work to practice

Plan shape and data preservation: 11.01 and 11.03. Evidence completeness and calibrated claims: 11.02. Exclusive temporary output, atomic publication, and idempotence: 11.03. Structured input and error status: Module 04.

Write `design-notes.md` describing one partial repair, the remaining observations, and how your complete repair preserves useful work. The independent lab intentionally withholds a complete implementation.

## Validate and replay

```bash
python3 -m py_compile repair_variant.py
../../lab-grade module-11
../../lab-grade module-11 --mode exam
```

Syntax checking does not execute a plan. Practice grading reports failed properties with lesson references; exam grading reduces hints and uses fresh fixtures.

If the allowed operation fails, inspect preserved workload data before changing the harness. If malformed input leaves output, inspect validation order and publication. Never replace missing observations with invented negative values.

Save notes, return with `cd ../..`, and use `./lab-reset module-11` to remove this prepared workspace and generated fixtures. There is no background service to kill. Do not extend the harness into an external scanner, arbitrary command runner, or destructive cleanup tool.
<!-- /source -->
