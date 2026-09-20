# 04.03 - Inventory and remove ambient launcher authority

## Goal

Inventory the process state inherited by a local agent without printing secret values, reproduce an ambient-environment leak, and repair the child launch with an allowlist.

## Concepts and preparation

Complete 04.01-04.02 and recall 01.02-01.03. **Ambient authority** is usable access arriving from the surrounding process environment instead of being explicitly selected for this task. Examples include inherited credentials, open files, and an unexpectedly sensitive working directory.

An inventory answers "what inputs and handles are present?" It is observation, not enforcement. Listing environment key names avoids deliberately copying their values, but names, directory paths, and other metadata can still be sensitive outside this synthetic VM. Do not publish raw inventories from your real workstation.

From the course root:

```bash
./lab-start 04.03
cd .student/04.03
pwd
ls -l authority_agent.py probe.py FIXTURE.txt
cat authority_agent.py
cat probe.py
cat FIXTURE.txt
```

The first command prepares your student copy. `cd` enters it; `pwd` and `ls -l` verify location and filenames; the `cat` commands read the supplied files before you run them. If a file is absent, check the lesson number and working directory rather than creating a substitute with guessed contents. To edit a source below, use `nano FILENAME` with the actual filename, save with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. Python runs the saved file directly; there is no compile step.

## Exercise 1 - Inventory names and handles, not values

Complete source:

<!-- source: course/module-04-minimal-agent/lesson-03/authority_agent.py format=code -->
```python
#!/usr/bin/env python3
import json
import os
import subprocess
import sys


def inventory() -> dict:
    descriptors = []
    for name in os.listdir("/proc/self/fd"):
        if name.isdigit():
            descriptors.append(int(name))
    return {"cwd": os.getcwd(), "environment_keys": sorted(os.environ), "descriptor_numbers": sorted(descriptors)}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"unsafe", "safe"}:
        print(f"usage: {sys.argv[0]} unsafe|safe", file=sys.stderr)
        return 2
    print("INVENTORY=" + json.dumps(inventory(), sort_keys=True))
    child_env = os.environ.copy() if sys.argv[1] == "unsafe" else {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
    run = subprocess.run(["python3", "probe.py"], env=child_env, text=True, capture_output=True, check=False)
    print(run.stdout, end="")
    return run.returncode


if __name__ == "__main__":
    raise SystemExit(main())
```
<!-- /source -->

### Source, line by line

- `inventory` reads the current working directory, environment key names, and numeric descriptor entries.
- It deliberately does not read environment values or descriptor contents. An inventory should identify authority channels without copying secrets into logs.
- `/proc/self/fd` is a snapshot; the directory scan itself may temporarily use a descriptor.
- The mode must be the exact word `unsafe` or `safe`.
- Unsafe mode copies the entire parent environment. Safe mode constructs two known values.
- The child is launched as a structured argv list, and its output is captured for the observation.

The probe is:

<!-- source: course/module-04-minimal-agent/lesson-03/probe.py format=code -->
```python
#!/usr/bin/env python3
import os

print("NE_AGENT_SECRET=" + os.environ.get("NE_AGENT_SECRET", "<absent>"))
```
<!-- /source -->

- The probe reads one synthetic key and reports absence explicitly.
- Do not adapt this exercise to real credential names or values.

Run the metadata-only inventory:

```bash
export NE_AGENT_SECRET="synthetic-$(awk -F= '/fixture_id/{print $2}' FIXTURE.txt)"
python3 authority_agent.py safe
```

Expected: the inventory lists `NE_AGENT_SECRET` as a key but does not contain its value. The child reports `<absent>`.

`export` deliberately makes this fake value available to child processes. The `awk` command reads the generated fixture identifier, making the observation specific to this attempt. There is no output-redaction filter here: a filter could hide a leak and make a failed control appear successful. Predict which part of the output will change when the mode becomes `unsafe`.

## Exercise 2 - Reproduce ambient authority

```bash
python3 authority_agent.py unsafe | tee unsafe-output.txt
grep -F "$NE_AGENT_SECRET" unsafe-output.txt
```

### Line by line

- Unsafe mode uses `os.environ.copy()`, transferring every inherited value.
- `tee` retains only this synthetic lesson output.
- `grep -F` treats the synthetic value literally and succeeds when the child leaked it.

This reproduces the Module 01 environment lesson inside a tool-using agent. Adding tools did not erase the launcher's inherited authority.

## Exercise 3 - Repair and verify absence

```bash
python3 authority_agent.py safe > safe-output.txt
grep -F 'NE_AGENT_SECRET=<absent>' safe-output.txt
! grep -F "$NE_AGENT_SECRET" safe-output.txt
printf 'absence-check status=%s\n' "$?"
```

### Line by line

- Safe mode constructs a fixed environment at the child-exec boundary.
- The first `grep` requires the explicit absence observation.
- `!` reverses the literal-match command's success status: finding the value makes the assertion fail. Require status 0 **and** the explicit `<absent>` line from the first check. A missing or unreadable output file is an infrastructure error, not evidence of secure absence.
- This repair does not constrain paths, syscalls, CPU, memory, or network access. Later modules add those independent controls.

### Read the inventory and the mode switch

`os.listdir("/proc/self/fd")` returns entry names as strings. `name.isdigit()` selects numeric descriptor entries; `int(name)` turns them into numbers for sorting. The listing can include the transient descriptor used to enumerate the directory, so it is not a stable count of usable inherited files.

`os.getcwd()` reports the current working directory. Relative paths such as `probe.py` depend on that directory, even though the environment has been narrowed. The conditional expression chooses a full environment copy only for the literal mode `unsafe`; `safe` builds a new mapping.

`print(run.stdout, end="")` forwards captured child output without adding another newline. It does not forward captured stderr, so a missing probe can otherwise look like silent failure. Check the return status and the file's existence before calling an empty output "secure." The name `safe` means environment hygiene in this example, not a complete sandbox.

## Checkpoint and troubleshooting

- If the inventory prints values, reduce it to sorted key names before capturing evidence.
- If safe mode cannot locate Python, inspect the fixed VM path with `command -v python3`; do not copy the whole environment.
- If the unsafe grep fails, confirm the variable was exported in the same shell.
- Remove `unsafe-output.txt` after the observation; it contains only a synthetic value, but it is still disposable fixture data.
- Checkpoint: identify which authority is removed by the repair and name at least three channels it does not address.

## Replay and source truth

Run `unset NE_AGENT_SECRET` to remove the synthetic value from this parent shell. From this workspace, `cd ../..` returns to the course root. `./lab-reset 04.03` discards only this lesson's student workspace and generated fixtures after confirmation. Save any notes elsewhere in the disposable VM first. Do not edit canonical `course/` files to repair your attempt.

The [Python subprocess documentation](https://docs.python.org/3.14/library/subprocess.html) defines argv, environment replacement, captured streams, and return codes. These API guarantees are narrower than a containment policy.
