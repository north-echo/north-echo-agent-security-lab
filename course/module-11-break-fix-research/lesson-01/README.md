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

<!-- source: course/module-11-break-fix-research/lesson-01/make_variant.py format=code -->
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
<!-- /source -->

### Source, line by line

- `SECURE` and `WEAK` enumerate the two modeled choices for each control. Their names are design labels, not proof of enforcement.
- `random.Random(int(...))` creates a local deterministic generator from the supplied integer.
- `dict(SECURE)` copies the baseline so changing this variant does not mutate the shared mapping.
- Sampling sorted names selects two through four distinct controls. It changes only their configured choices.
- The workload contains a harmless operation/resource and shell-looking literal data. The harness never executes that plan text as shell code.
- The output includes a schema version and opaque identity. Sorted, indented JSON makes exact replay comparison straightforward.

### The fixed local harness

<!-- source: course/module-11-break-fix-research/lesson-01/variant_harness.py format=code -->
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
<!-- /source -->

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
