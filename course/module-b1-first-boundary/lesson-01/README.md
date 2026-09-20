# B1.01 - What did the reader receive?

## Outcomes

Distinguish an argument from an environment setting, predict inheritance, and
observe a fake private setting's presence without printing its value.

## Understand first

Imagine a report reader launched by a larger application. It needs the report
path. It does not need every setting belonging to that application.

An **environment** is a collection of named text values supplied to a process.
It is separate from its argument list. Programs often use it for configuration.
When a parent starts a child without choosing a replacement environment, the
child generally receives the parent's settings. The child can inspect them
whether or not its intended job mentions them.

Here, the shell is the parent and Python runs our reader. A shell prefix such
as `NE_PRIVATE_TOKEN=pretend-red command` adds a setting for that one command;
it does not permanently export it in your shell. `pretend-red` is deliberately
fake. Never substitute a real token or dump your whole environment for a lab.

"Private" describes our intended policy, not a special kind of operating-system
variable. Naming a setting `NE_PRIVATE_TOKEN` does not protect it. We are using
an obviously fake value to see whether the handoff follows that policy.

## Before you begin

From the VM repository root:

```bash
./lab-start b1.01
cd .student/b1.01
```

`lab-start` prepares/resumes the copy and synthetic reports; `cd` enters it.
You need B0's path, argument, and process concepts before continuing.

## Read the supplied observer

This lesson has its own `read_report.py`, separate from B0's reader. Locate and
read the copy in the current lesson, without opening an editor:

```bash
pwd
ls -l read_report.py
cat read_report.py
```

Line by line: the path should end in `.student/b1.01`; the listing confirms the
named file is there; `cat` displays the Python source without running it. Do not
edit the observer in this lesson. Compare its contents with the listing below;
the executable command comes later under Exercise 1.

<!-- source: course/module-b1-first-boundary/lesson-01/read_report.py format=code -->
```python
import os
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
print(text, end="")
print("Private setting received:", "NE_PRIVATE_TOKEN" in os.environ)
```
<!-- /source -->

Line by line: `os` provides access to the process environment; `sys` provides
arguments; `Path` reads a file. The read uses the caller's first argument, as in
B0.03. `print(text, end="")` preserves its report text. The final expression
tests whether a key is **in** `os.environ`. It prints `True` or `False`, not
the associated value. This observer intentionally reports an extra line so
we can see the handoff; production report output would normally omit it.

`os.environ` behaves as a mapping from setting names to values. The expression
`"NE_PRIVATE_TOKEN" in os.environ` tests for the name, not whether the value
looks secret. Even a present but empty value would make this check `True`.
The comma in `print` separates two things to display: the label and the boolean
(true/false) result. That is why you see an explanatory label rather than just
a bare `True` or `False`.

## Exercise 1 - Compare two handoffs

Before each invocation, predict the final line:

```bash
python3 read_report.py report.txt
NE_PRIVATE_TOKEN=pretend-red python3 read_report.py report.txt
```

The first starts the reader with the shell's usual environment. In a clean lab
shell it ends with `Private setting received: False`. The second adds our fake
setting for that invocation and ends with `Private setting received: True`.
Both print the same report. Supplying the setting did not change the argument.

Read the longer command in three parts: the assignment prefix supplies a
setting; `python3` runs the interpreter; `read_report.py report.txt` names the
script and its argument. There are no spaces around `=`. Type the entire line
before Enter. It is one invocation, not a request to edit the report or script.

The failure is not that the observer printed a real secret: it did not. The
failure is that the unnecessary setting reached the process at all. Telling a
program "read only the report" would not remove this data from its environment.

## Exercise 2 - Repair this one invocation

```bash
python3 read_report.py "weekend report.txt"
echo $?
```

The prefix is gone, so the setting is not added to this child. The reader should
print the weekend report, `False`, and status `0`. Quotes supply one path, as
before. This confirms the observation, but **omitting a prefix is not a general
repair** for an application that already has private settings. The next lesson
adds a launcher that chooses what to pass on.

## Checkpoint

Draw or describe: shell -> reader, argument path beside the arrow, environment
settings beside the same arrow. Which input changed between the first two runs?
If the reader never called `os.environ`, would the value still have been
available to it? State why measuring presence is enough for this experiment.

## Troubleshooting and finish

If the first run says `True`, your shell already has that named setting. In
this lab terminal, `unset NE_PRIVATE_TOKEN` removes only that setting; repeat
the comparison. Do not clear your entire environment. If you see a missing-file
error, check `pwd` and the report name rather than calling it a security denial.

```bash
cd ../..
```

This returns to the repository root. Optional reset:
`./lab-reset b1.01 --dry-run`, then `./lab-reset b1.01 --yes`. The preview does
not remove anything; confirmation discards this lesson's workspace/fixtures.

## Sources and scope

- [Ubuntu 24.04 Bash manual](https://manpages.ubuntu.com/manpages/noble/man1/bash.1.html),
  ENVIRONMENT: exported settings and assignments preceding an external command.
  This lesson's prefix example invokes Python, not a shell function or special builtin.
- [Python 3.12 os.environ](https://docs.python.org/3.12/library/os.html#os.environ)
  and [mapping membership](https://docs.python.org/3.12/library/stdtypes.html#mapping-types-dict):
  accessing process settings and testing whether a key is present.

The observer's boolean is evidence about that key in this supplied process
at the time of the check. It does not prove that no other data was inherited,
that an untrusted program would report honestly, or that the process cannot
access data through files or other channels. No filesystem or user-identity
boundary is changed here. These limits are part of the lesson, not optional
advanced reading.
