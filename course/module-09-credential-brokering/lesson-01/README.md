# 09.01 - Remove ambient credential authority

## Outcomes and prerequisites

Complete Modules 01, 04, and 08. You will observe a visibly fake credential crossing a process launch, remove it with an explicit environment, and explain what this does not isolate. This revisits B1 with an operation-broker design in mind.

## Concepts before commands

A **credential** is a value a service accepts as evidence of authority. Putting one in a process environment makes it available to that process's code. A child normally inherits the parent's environment unless the launcher supplies a replacement.

An **ambient** credential is available without making a new, operation-specific authorization decision. Its short lifetime may reduce exposure, but does not stop a process reading or copying it while present.

This exercise uses only a string beginning with `FAKE-`. Never substitute an API key, cloud token, password, employer credential, or personal secret. The deliberate disclosure prints only that synthetic value. It demonstrates authority inheritance, not an attack against another process.

## Prepare and read both files

From the course root in the disposable VM:

```bash
./lab-start 09.01
cd .student/09.01
pwd
ls -l credential_probe.py clean_launch.py
cat credential_probe.py
cat clean_launch.py
```

The scripts are already in your prepared workspace. You can inspect them with `nano credential_probe.py` or `nano clean_launch.py`. Reading a source is not executing it; the next exercises run it.

### The synthetic observer

<!-- source: course/module-09-credential-brokering/lesson-01/credential_probe.py format=code -->
```python
#!/usr/bin/env python3
"""Observe whether a synthetic credential crossed exec."""

import json
import os
import sys

name = "NORTH_ECHO_FAKE_CREDENTIAL"
value = os.environ.get(name)
result = {"present": value is not None, "length": len(value) if value else 0}
if len(sys.argv) == 2 and sys.argv[1] == "leak" and value is not None:
    result["leaked_value"] = value
print(json.dumps(result, sort_keys=True))
```
<!-- /source -->

### Source, line by line

- `json` formats the observation; `os` exposes this process's environment; `sys` exposes its arguments.
- `name` selects one explicitly fake variable. `os.environ.get` returns its string value or `None` if absent.
- `value is not None` distinguishes an absent variable from a present empty string. A present empty string still has length zero.
- The dictionary reports presence and length without displaying the value by default.
- Only the exact extra argument `leak`, with a present value, adds `leaked_value` to the result. This is intentionally unsafe display behavior for synthetic evidence.
- `json.dumps(..., sort_keys=True)` serializes the observation. Sorting gives stable output; it is not redaction.

### The minimal-environment launcher

<!-- source: course/module-09-credential-brokering/lesson-01/clean_launch.py format=code -->
```python
#!/usr/bin/env python3
"""Launch exact argv with a small, credential-free environment."""

import os
import subprocess
import sys

if len(sys.argv) < 2:
    raise SystemExit(f"usage: {sys.argv[0]} COMMAND [ARG...]")
clean = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
run = subprocess.run(sys.argv[1:], shell=False, env=clean, check=False)
raise SystemExit(run.returncode)
```
<!-- /source -->

### Source, line by line

- `subprocess` starts the child. The `os` import is retained for the later deliberate comparison with inherited environment.
- The argument guard refuses a missing command before launch.
- `clean` is a new dictionary containing only the selected PATH and locale. It is not a copy with one known secret removed.
- `sys.argv[1:]` preserves separate command arguments. `shell=False` prevents this launcher from treating them as a shell program.
- `env=clean` replaces the child's inherited environment; `check=False` returns a result object instead of raising on an ordinary nonzero child exit.
- `SystemExit(run.returncode)` forwards ordinary child exit codes. This small example is not a complete signal-status or timeout supervisor.

The launcher does **not** remove filesystem access, existing descriptors, network access, or every possible credential source. Environment reduction is one handoff control, not a complete sandbox.

## Exercise 1 - Predict and observe inherited authority

```bash
export NORTH_ECHO_FAKE_CREDENTIAL="FAKE-LESSON-$$-DO-NOT-USE"
python3 credential_probe.py > inherited.json
python3 credential_probe.py leak > disclosed.json
python3 -m json.tool inherited.json
python3 -m json.tool disclosed.json
```

`export` places the value in later child environments. The shell PID contributes a synthetic run label; it has no security significance. Redirection saves each observation separately.

Expect `present: true` and a positive length in both files. Only `disclosed.json` should include the fake value. The child did not need another authorization API to read it: inheritance already conveyed that access. This does not mean all environment values are automatically logged; it means the receiving code can choose to disclose them.

## Exercise 2 - Repair the launch boundary

```bash
python3 clean_launch.py /usr/bin/python3 "$PWD/credential_probe.py" > cleaned.json
python3 clean_launch.py /usr/bin/python3 "$PWD/credential_probe.py" leak > cleaned-leak.json
test -n "$NORTH_ECHO_FAKE_CREDENTIAL"
python3 -m json.tool cleaned.json
python3 -m json.tool cleaned-leak.json
```

The absolute executable path and script path are separate arguments. Both children should report absence and length zero; neither should contain `leaked_value`. The parent-side `test` proves you did not merely erase the parent value before observing the child.

## Exercise 3 - Make the incomplete repair visible

Open `nano clean_launch.py`. Change only `env=clean` to `env=os.environ.copy()`, save, and predict the result:

```bash
python3 clean_launch.py /usr/bin/python3 "$PWD/credential_probe.py" > regressed.json
python3 -m json.tool regressed.json
```

The inherited variable is present again. Explicit argv and `shell=False` did not repair this separate environment mistake. Restore **only** `env=clean`, save, and rerun:

```bash
python3 clean_launch.py /usr/bin/python3 "$PWD/credential_probe.py" leak > repaired.json
```

## Checkpoint, troubleshooting, and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

def result(name):
    return json.loads(Path(name).read_text())

assert result("inherited.json")["present"] is True
assert result("disclosed.json")["leaked_value"].startswith("FAKE-LESSON-")
assert result("regressed.json")["present"] is True
for name in ("cleaned.json", "cleaned-leak.json", "repaired.json"):
    observed = result(name)
    assert observed["present"] is False and observed["length"] == 0
    assert "leaked_value" not in observed
print("CREDENTIAL INHERITANCE AND REPAIR: PASS")
PY
test -n "$NORTH_ECHO_FAKE_CREDENTIAL"
unset NORTH_ECHO_FAKE_CREDENTIAL
```

The assertions compare actual JSON fields rather than a suggestive filename. `unset` removes the fake variable from this shell after the experiment. It does not retroactively erase copies in already-running processes or saved JSON.

If the cleaned child sees the value, inspect the actual `env=` argument and confirm you saved the working copy. If the initial observation is absent, repeat the export in the same shell. No inspection of unrelated processes is needed.

A legitimate task may now lack a credential it needs. The next lessons restore a narrow approved **operation**, not the credential itself. Return with `cd ../..`; `./lab-reset 09.01` removes these synthetic output files and restores the working copy.

## Source truth

Python's [subprocess documentation](https://docs.python.org/3.14/library/subprocess.html) defines explicit environment mappings and argument lists. Its [os environment API](https://docs.python.org/3.14/library/os.html#os.environ) describes the process-local mapping. These sources do not claim that an environment-only launcher provides filesystem or network isolation.
