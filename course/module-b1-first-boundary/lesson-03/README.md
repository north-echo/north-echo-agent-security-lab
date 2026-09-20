# B1.03 - Does the repair survive a changed case?

## Outcomes

Apply the previous lesson without a replacement line to copy, handle a second
unnecessary setting, and preserve child failures. Prerequisite: B1.02.

## Understand first

A test can be too narrow. If you remove only the private key you happened to
see, a differently named setting still passes through. The intended rule is
not "remove one spelling"; it is "pass only what this job requires."

We also change the interface: the caller now supplies a worker path as well as
a report path. An argument list preserves these boundaries even when either
path contains a space. This is not permission to run arbitrary downloaded
workers. Use only the supplied local observer in this disposable VM.

## Before you begin

From the VM repository root:

```bash
./lab-start b1.03
cd .student/b1.03
```

The first creates/resumes a separate attempt. The second enters its directory.
Your previous lesson's repair does not automatically appear in this new copy.

## Read the partial repair

Locate both supplied files in this new workspace, then inspect the launcher:

```bash
pwd
ls -l launch.py inspect_reader.py
cat launch.py
```

Line by line: confirm `.student/b1.03`; confirm both files exist; display the
launcher's source without executing it. This is a different student copy from
B1.02. Compare it with the listing below before deciding what to change.

<!-- source: course/module-b1-first-boundary/lesson-03/launch.py format=code -->
```python
import os
import subprocess
import sys

# A partial repair: it removes one known name, not other private settings.
child_environment = dict(os.environ)
child_environment.pop("NE_PRIVATE_TOKEN", None)
result = subprocess.run(
    [sys.executable, sys.argv[1], sys.argv[2]],
    env=child_environment,
)
raise SystemExit(result.returncode)
```
<!-- /source -->

Line by line: the imports match B1.02. The dictionary assignment copies the
parent settings; `.pop("NE_PRIVATE_TOKEN", None)` removes that specific key
if present and does nothing if absent. The run list uses the current Python
executable, argument one as the worker path, and argument two as the report
path. `env` supplies the edited copy. The last line forwards the child's ordinary
exit code. This is a deliberately incomplete repair to investigate, not a model
solution.

## Read the observer

From the same workspace:

```bash
cat inspect_reader.py
```

This prints the observer's source. Read it, but do not edit it: we will change
the launcher and keep the measurement program unchanged.

<!-- source: course/module-b1-first-boundary/lesson-03/inspect_reader.py format=code -->
```python
import os
import sys
from pathlib import Path

style = os.environ.get("NE_REPORT_STYLE")
if style not in ("plain", "upper"):
    print("Missing or invalid report style.", file=sys.stderr)
    raise SystemExit(2)
try:
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
except OSError:
    print("Could not read that report.", file=sys.stderr)
    raise SystemExit(1)
if style == "upper":
    text = text.upper()
print(text, end="")
print("Original private setting received:", "NE_PRIVATE_TOKEN" in os.environ)
print("New private setting received:", "NE_OTHER_PRIVATE" in os.environ)
```
<!-- /source -->

Line by line: imports and public-style validation match B1.02. The read's
`try`/`except` preserves the missing-file error path; uppercase conversion is
conditional. The report print preserves content. The final two lines check
two distinct keys in the environment, without disclosing their values. A
`False` for one key says nothing about the second key unless we measure it too.

## Exercise 1 - Predict and observe the changed case

```bash
NE_REPORT_STYLE=upper NE_PRIVATE_TOKEN=pretend-red NE_OTHER_PRIVATE=pretend-blue python3 launch.py inspect_reader.py "weekend report.txt"
echo $?
```

The three prefixes supply one needed setting and two unnecessary ones. The
launcher receives the observer path and quoted report path as separate
arguments. Expect uppercase report text, the first private check `False`, the
second `True`, and status `0`. The earlier single-key check would miss this.

## Exercise 2 - Repair, with less help

Edit the launcher so it passes the selected public style and no other parent
setting. Do not edit the observer to make its output reassuring. Write down
the rule you intend to enforce before writing code. Use B1.02 if you need a
hint, then close it and apply the idea here.

Use `nano launch.py` to open the file, Ctrl+O and Enter to save, and Ctrl+X to
return to the shell. Run `cat launch.py` to check the saved contents. Those
editing steps are not the answer: you still need to choose what the handoff
should contain and implement that choice yourself.

Repeat Exercise 1. Expected: correct uppercase report, both private checks
`False`, status `0`. Repeat with `plain` and the daily report; it must preserve
that choice too. A constant `upper` value is not a complete repair.

## Exercise 3 - Keep failure honest

```bash
NE_REPORT_STYLE=plain python3 launch.py inspect_reader.py absent.txt
echo $?
```

The worker receives a missing report path and should emit its diagnostic and
exit `1`; the launcher must also exit `1`. This invocation intentionally tests
failure, not a second security mechanism. Repair the input by replacing
`absent.txt` with `report.txt` and confirm report output plus status `0`.

## Checkpoint

Without consulting earlier code, explain why the starting `.pop` was too narrow.
What if a third unrelated setting appeared tomorrow? Why would suppressing all
output or always returning zero make a poor test pass? Demonstrate both a useful
run and a withheld-data observation. Then attempt the independent practical.

## Troubleshooting and finish

If the worker path is accidentally treated as the report path, review positions
one and two in `sys.argv`. If the original fake key is absent but the second is
present, the behavior is still a single-name deletion, not selection by need.
If a failed child appears successful, inspect the launcher's final exit line.

```bash
cd ../..
```

This returns to the root. Optional `./lab-reset b1.03 --dry-run` previews
removal; `./lab-reset b1.03 --yes` discards this lesson's work and fixtures.

## Sources and scope

- [Python 3.12 dictionary pop and lookup](https://docs.python.org/3.12/library/stdtypes.html#mapping-types-dict):
  deleting a named key differs from selecting the keys to retain.
- [sys.argv](https://docs.python.org/3.12/library/sys.html#sys.argv) and
  [subprocess](https://docs.python.org/3.12/library/subprocess.html#subprocess.run):
  the two caller arguments, a structured child argument list, explicit
  environment, and an ordinary exit result.
- [OSError](https://docs.python.org/3.12/library/exceptions.html#OSError): the
  report-read failure family. Status 1 and the two observer labels are choices
  in our supplied worker, not standardized Python diagnostic text.

The test varies two key names and the public style; it is evidence for these
cases, not exhaustive proof about all programs. Reading the selected mapping
explains why a third unselected parent key would also be omitted. The program
still runs with the VM user's other authority. Signal termination, arbitrary
worker arguments, and hostile-worker containment remain outside this first-boundary exercise.
