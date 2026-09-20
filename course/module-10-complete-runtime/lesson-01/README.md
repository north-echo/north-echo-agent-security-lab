# 10.01 - Order the complete runtime by dependency

## Outcomes and prerequisites

Complete Modules 01-09. You will turn the controls into a dependency plan, observe an invalid ordering, and repair it without mistaking plan validation for kernel enforcement.

## Concepts before commands

A **dependency** means one action needs a state established by another. It is stronger than a stylistic preference. A **partial order** constrains some pairs without requiring every independent action to have one universal position.

For this runtime, cgroup entry must precede namespace/workload creation so descendants begin inside the resource budget. User-namespace setup precedes privilege reduction because mapping a namespace-local root creates capability state that must then be reduced. Landlock setup precedes this seccomp filter because the final syscall allowlist does not include the Landlock setup operations.

The broker must be ready before the caller tries its mediated operation. Starting it before namespace entry is a convenient design dependency here, not a kernel law saying every broker must start before every network namespace. Pathname sockets can remain reachable through a shared filesystem.

Finally, process exit and unit collection are different observations. Requesting `--collect` is not enough by itself; later code checks that the exact unit is absent.

## Prepare and read the validator and data

From the course root:

```bash
./lab-start 10.01
cd .student/10.01
pwd
ls -l check_order.py broken-plan.json repaired-plan.json
cat check_order.py
cat broken-plan.json
cat repaired-plan.json
```

Use `nano check_order.py` or `nano challenge-plan.json` when navigating or editing. The JSON files are data submitted to the validator, not programs that install kernel controls.

### The plan validator

<!-- source: course/module-10-complete-runtime/lesson-01/check_order.py format=code -->
```python
#!/usr/bin/env python3
"""Validate a complete-runtime launch plan against security dependencies."""

import json
import sys
from pathlib import Path

REQUIRED = {
    "start_broker",
    "enter_cgroup",
    "enter_namespaces",
    "drop_privilege",
    "apply_landlock",
    "apply_seccomp",
    "exec_workload",
    "collect_unit",
}

BEFORE = {
    ("start_broker", "enter_namespaces"),
    ("enter_cgroup", "enter_namespaces"),
    ("enter_namespaces", "drop_privilege"),
    ("drop_privilege", "apply_landlock"),
    ("apply_landlock", "apply_seccomp"),
    ("apply_seccomp", "exec_workload"),
    ("exec_workload", "collect_unit"),
}


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} PLAN.json", file=sys.stderr)
        return 2
    try:
        plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"invalid plan: {error}", file=sys.stderr)
        return 1
    if not isinstance(plan, list) or any(not isinstance(item, str) for item in plan):
        print("invalid plan: expected a JSON array of step names", file=sys.stderr)
        return 1
    if len(plan) != len(set(plan)):
        print("invalid plan: duplicate step", file=sys.stderr)
        return 1
    missing = sorted(REQUIRED - set(plan))
    extra = sorted(set(plan) - REQUIRED)
    if missing or extra:
        print(json.dumps({"ok": False, "missing": missing, "extra": extra}, sort_keys=True))
        return 1
    position = {name: index for index, name in enumerate(plan)}
    violations = sorted(f"{left} must precede {right}" for left, right in BEFORE if position[left] > position[right])
    print(json.dumps({"ok": not violations, "violations": violations}, sort_keys=True))
    return bool(violations)


if __name__ == "__main__":
    raise SystemExit(main())
```
<!-- /source -->

### Source, line by line

- `REQUIRED` is a set of permitted, mandatory phase names. It does not encode their order.
- `BEFORE` is a set of two-element tuples. Each tuple represents one directed dependency: its left phase must precede its right phase.
- The argv guard requires one plan filename. File/JSON errors stop before examining order.
- The shape check requires a list of strings. A dictionary with plausible keys is not the expected plan interface.
- Comparing list length with set length detects duplicate phases.
- Set subtraction finds missing and unknown phases. Their sorted output makes diagnostics stable.
- The dictionary comprehension maps each phase to its list index.
- The final comprehension reports every edge whose positions are reversed, not just the first failure.
- `not violations` is true only for an empty violation list. Returning `bool(violations)` gives exit status 1 for an invalid ordering and 0 for a valid one.

### The deliberately broken plan

<!-- source: course/module-10-complete-runtime/lesson-01/broken-plan.json format=code -->
```json
[
  "start_broker",
  "enter_cgroup",
  "enter_namespaces",
  "drop_privilege",
  "apply_seccomp",
  "apply_landlock",
  "exec_workload",
  "collect_unit"
]
```
<!-- /source -->

Every required name is present exactly once. The mistake is the relative position of `apply_seccomp` and `apply_landlock`. A checklist that merely searches for both words would miss it.

### The repaired plan

<!-- source: course/module-10-complete-runtime/lesson-01/repaired-plan.json format=code -->
```json
[
  "start_broker",
  "enter_cgroup",
  "enter_namespaces",
  "drop_privilege",
  "apply_landlock",
  "apply_seccomp",
  "exec_workload",
  "collect_unit"
]
```
<!-- /source -->

The repaired list places the filesystem setup before the final syscall restriction. `start_broker` and `enter_cgroup` both precede namespace entry; this graph does not require an edge between those two independent preparations.

## Exercise 1 - Predict the rejected edge

```bash
NE_BROKEN_STATUS=0
python3 check_order.py broken-plan.json > broken-result.json || NE_BROKEN_STATUS=$?
python3 -m json.tool broken-result.json
test "$NE_BROKEN_STATUS" -eq 1
python3 check_order.py repaired-plan.json > repaired-result.json
python3 -m json.tool repaired-result.json
```

Saving the expected failure through `||` avoids changing your interactive shell's error options. Expect `apply_landlock must precede apply_seccomp` in the broken result and an empty violation list in the repaired result.

These are statements about a data structure. No Landlock rules or seccomp filter have been installed by this script. The next lesson tests the actual ordered controls.

## Exercise 2 - Make a different ordering mistake

Copy the known plan, then move cgroup entry too late:

```bash
cp repaired-plan.json challenge-plan.json
python3 - <<'PY'
import json
from pathlib import Path

path = Path("challenge-plan.json")
steps = json.loads(path.read_text())
steps.remove("enter_cgroup")
steps.insert(3, "enter_cgroup")
path.write_text(json.dumps(steps) + "\n")
PY
NE_CHALLENGE_STATUS=0
python3 check_order.py challenge-plan.json > challenge-result.json || NE_CHALLENGE_STATUS=$?
python3 -m json.tool challenge-result.json
test "$NE_CHALLENGE_STATUS" -eq 1
```

`remove` deletes the earlier position; `insert(3,...)` places it after namespace/privilege setup in this list. The plan is still syntactically valid and contains all phases, but violates the requirement to establish resource containment before those descendants.

Open `nano challenge-plan.json`, move `enter_cgroup` before `enter_namespaces`, preserve commas and quoted strings, and save. Then run:

```bash
python3 check_order.py challenge-plan.json > challenge-repaired.json
python3 -m json.tool challenge-repaired.json
```

## Checkpoint, troubleshooting, and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

def result(name):
    return json.loads(Path(name).read_text())

assert "apply_landlock must precede apply_seccomp" in result("broken-result.json")["violations"]
assert "enter_cgroup must precede enter_namespaces" in result("challenge-result.json")["violations"]
for name in ("repaired-result.json", "challenge-repaired.json"):
    assert result(name) == {"ok": True, "violations": []}
print("LAUNCH DEPENDENCIES: PASS")
PY
```

For each edge, explain what the earlier action establishes or what the later action removes. Do not answer merely “because the list says so.” Also name one property this validator cannot prove: effective resource limits, actual privilege reduction, successful policy installation, or teardown.

If parsing fails, restore a JSON array; a syntax error is not the intended ordering observation. If an edge seems unnecessary, distinguish this particular implementation's requirements from universal kernel rules.

Return with `cd ../..`; `./lab-reset 10.01` removes the challenge and results. No service or kernel policy was created.

## Source truth

The [kernel seccomp documentation](https://docs.kernel.org/userspace-api/seccomp_filter.html) and [Landlock documentation](https://cdn.kernel.org/doc/html/latest/userspace-api/landlock.html) describe the mechanisms being composed. The dependency graph itself is this course runtime's design; a passing graph check is not evidence those mechanisms were applied.
