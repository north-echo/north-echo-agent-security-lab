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

<!-- source: course/module-11-break-fix-research/lesson-03/repair_variant.py format=code -->
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
<!-- /source -->

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

<!-- source: course/module-11-break-fix-research/lesson-03/vulnerable-plan.json format=code -->
```json
{"schema":1,"variant_id":"lesson-repair","workload":{"operation":"read","resource":"record:alpha","literal":"literal $(touch shell-marker)"},"controls":{"execution":"shell","environment":"inherit","filesystem":"lexical","network":"direct","cleanup":"prefix"}}
```
<!-- /source -->

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
