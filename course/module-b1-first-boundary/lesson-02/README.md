# B1.02 - Choose what crosses the handoff

## Outcomes

Launch a child with an explicit environment, preserve its needed public setting,
and test useful work as well as private-setting absence. Prerequisite: B1.01.

## Understand first

We now separate the **launcher** from the **worker**. The launcher starts another
program; the worker does the report reading. Python's `subprocess.run` starts
the child and waits for it to finish. Its `env` argument replaces the child's
environment with the mapping we choose. It does not change the parent's copy.

A Python **dictionary** maps keys to values. `dict(os.environ)` copies all
current environment settings. `{}` is an empty dictionary. An **allowlist**
starts with only the settings required for the job. Deleting known bad keys
from a complete copy instead leaves every unanticipated key in place.

Our reader has one legitimate setting, `NE_REPORT_STYLE`: `plain` prints the
report unchanged and `upper` converts it to uppercase. Thus there are two
obligations: retain the selected public style, and withhold private settings.
Removing everything satisfies neither the job nor the complete lesson outcome.

## Before you begin

From the VM repository root:

```bash
./lab-start b1.02
cd .student/b1.02
```

The helper prepares this lesson; `cd` enters its independent working copy.

## Read the launcher

Stay in `.student/b1.02`. First locate both supplied programs, then read the
launcher from disk:

```bash
pwd
ls -l launch.py read_report.py
cat launch.py
```

Line by line: confirm the lesson directory; list the two existing files;
display the launcher's source. `ls` accepts two filename arguments here.
Neither listing nor reading starts the worker. If either file is missing,
check the lesson preparation rather than creating an empty file in an editor.

<!-- source: course/module-b1-first-boundary/lesson-02/launch.py format=code -->
```python
import os
import subprocess
import sys

child_environment = dict(os.environ)
result = subprocess.run(
    [sys.executable, "read_report.py", sys.argv[1]],
    env=child_environment,
)
raise SystemExit(result.returncode)
```
<!-- /source -->

Line by line: the three imports provide environment access, process launch,
and arguments. `child_environment` is initially a copy of **every** setting.
The list in `subprocess.run` supplies the executable and each argument as
separate elements, preserving path boundaries without constructing a shell
command. `sys.executable` is the Python executable already running this
launcher, so the child does not need `PATH` to find it. `"read_report.py"` names
the supplied worker in the current directory. `sys.argv[1]` forwards the report
path. `env=child_environment` selects the child's settings. The returned object
contains `returncode`; `SystemExit` forwards the ordinary child exit codes used here.
With default stream handling, the child's output and errors reach our terminal.

Follow the two levels of launch:

```text
shell starts launch.py -> launcher starts read_report.py -> reader reads report.txt
```

The shell's prefixes first reach the launcher. The launcher chooses a new
mapping for the worker; it does not ask the worker to remove its own secrets
after startup. `env=child_environment` is a named function argument, selecting
the `env` parameter of `subprocess.run`. It is not a shell prefix.

The square brackets make a Python list of executable/argument strings; no
second shell parses those strings. The parentheses start the function call,
and the indented continuation lines are part of that same call. The assignment
stores its result in `result`. `result.returncode` reads one field of that
result after the worker finishes. The worker is a separate process, not a
function imported into the launcher.

## Read the worker

Still in the same directory:

```bash
cat read_report.py
```

This displays the second program. Leave it unchanged: its job is to perform
the report task and expose the effect of changes to `launch.py`. The complete
listing follows so you can compare the on-disk source with the explanation.

<!-- source: course/module-b1-first-boundary/lesson-02/read_report.py format=code -->
```python
import os
import sys
from pathlib import Path

style = os.environ.get("NE_REPORT_STYLE")
if style not in ("plain", "upper"):
    print("The reader needs NE_REPORT_STYLE=plain or upper.", file=sys.stderr)
    raise SystemExit(2)
try:
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
except OSError:
    print("Could not read that report.", file=sys.stderr)
    raise SystemExit(1)
if style == "upper":
    text = text.upper()
print(text, end="")
print("Private setting received:", "NE_PRIVATE_TOKEN" in os.environ)
```
<!-- /source -->

Line by line: the imports have the same roles as B1.01. `os.environ.get` looks
up the public setting, returning `None` if absent. The membership test accepts
only `plain` or `upper`; otherwise the indented diagnostic and exit report a
configuration error. The `try`/`except OSError` block reads the report or
reports a file error as in B0.03. The `if` calls `text.upper()` only for the
uppercase style. The final prints emit report text and the private-key presence
check. The code checks a key's presence; it never prints the fake private value.

In `if style == "upper"`, `==` compares two values; it does not assign a new
style. `None` from a missing lookup means there is no value for that key, not
the literal text `"None"`. The earlier validation prevents that missing-value
case from silently choosing a default report style.

## Exercise 1 - Observe the incomplete control

```bash
NE_REPORT_STYLE=upper NE_PRIVATE_TOKEN=pretend-red python3 launch.py report.txt
echo $?
```

The two prefixes provide settings to the launcher for this run. Its full copy
passes both to the worker. Expect an uppercase report, private presence `True`,
and status `0`. The job works, but the unnecessary data crossed the handoff.

## Exercise 2 - See why removing everything is insufficient

Open the launcher you just inspected, not the worker:

```bash
nano launch.py
```

This edits the local student copy. Change the environment assignment to:

```python
child_environment = {}
```

This constructs an empty mapping. Save with Ctrl+O, Enter; exit with Ctrl+X.
Then inspect the saved file:

```bash
cat launch.py
```

Confirm the assignment is now empty and the child-run/exit lines remain.
Repeat the two commands in Exercise 1. Expect the worker's style diagnostic,
no report, and status `2`. A worker that cannot do its job is not a successful
security repair. Keep the test that exposed this regression.

## Exercise 3 - Make the narrow repair

Reopen the same student file with `nano launch.py`, replace that assignment
with the line below, save with Ctrl+O and Enter, and exit with Ctrl+X:

```python
child_environment = {"NE_REPORT_STYLE": os.environ["NE_REPORT_STYLE"]}
```

The dictionary contains one key. Its value comes from the launcher's current
public setting, not a hard-coded style. The brackets perform a required-key
lookup; this exercise always supplies the public setting. No private key is
copied. This controls inheritance; it does not delete anything from the parent.

Run `cat launch.py` once more to confirm the saved line before testing it.
If your editor still shows unsaved changes, the next Python invocation would
read the old file from disk, not what you see in the editor.

```bash
NE_REPORT_STYLE=upper NE_PRIVATE_TOKEN=pretend-red python3 launch.py report.txt
echo $?
NE_REPORT_STYLE=plain NE_PRIVATE_TOKEN=pretend-red python3 launch.py "weekend report.txt"
echo $?
```

The first should print uppercase content, `False`, and `0`. The second should
print ordinary-case weekend content, `False`, and `0`. Changing the style and
path checks that the repair still honors caller choices.

## Checkpoint

Explain the observed difference among a full copy, an empty dictionary, and
the one-key dictionary. Which observation checks useful work? Which checks
withheld data? Could the worker still read a different file accessible to your
VM user? Yes: we have imposed no filesystem restriction. Explain that limit
before continuing.

| Chosen handoff | Useful report | Observed private key |
| --- | --- | --- |
| All parent settings | Works | Present |
| No settings | Fails style validation | Not checked: worker exits before its observer line |
| Selected public setting | Works | Absent |

The middle row matters: no private-key line is **not** an observed `False`.
It is missing evidence because the worker stopped early. Always check that the
intended observer actually ran before interpreting its absence as a denial.

## Troubleshooting and finish

A `KeyError` for `NE_REPORT_STYLE` means the required public prefix is missing;
repeat the complete invocation. A `SyntaxError` often means an unmatched brace,
quote, or bracket in the edit. Do not repair a failed observation by removing
the observer's print. Check what reached the worker instead.

```bash
cd ../..
```

Return to the root. Optional `./lab-reset b1.02 --dry-run` previews cleanup;
`./lab-reset b1.02 --yes` removes this lesson's edits and generated fixtures.

## Sources and scope

- [Python 3.12 subprocess.run](https://docs.python.org/3.12/library/subprocess.html#subprocess.run):
  waiting for a child, explicit `env` replacing default inheritance, argument
  sequences, and default stream behavior. [sys.executable](https://docs.python.org/3.12/library/sys.html#sys.executable)
  identifies the running interpreter; it is usable on our tested installation.
- [Dictionary operations](https://docs.python.org/3.12/library/stdtypes.html#mapping-types-dict)
  and [os.environ](https://docs.python.org/3.12/library/os.html#os.environ): copying
  the environment versus constructing a selected mapping.
- [CompletedProcess.returncode](https://docs.python.org/3.12/library/subprocess.html#subprocess.CompletedProcess.returncode)
  distinguishes ordinary exits from negative signal results on POSIX. This
  example forwards the ordinary 0/1/2 exit codes only; it is not a general
  signal-forwarding supervisor.
- [GNU nano 7.2](https://www.nano-editor.org/dist/v7/nano.html): opening a named
  file and saving/exiting, as also shown by its built-in Ctrl+G help.

The allowlist is our policy choice for this worker, not a universal list for
every application. Clearing `env` does not change the child's user, filesystem
permissions, or network access. The supplied-worker checks are local evidence
of the handoff, not proof that hostile code is contained.
