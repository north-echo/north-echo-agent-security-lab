# B0.03 - Change one behavior, then test it

## Outcomes

Make a small source edit, verify the reader uses a supplied path, and distinguish
ordinary output from error reporting. Prerequisites: B0.01-02 or their skills.

## Understand first

The useful job is to read the requested delivery report. Printing *a* report is
not enough: a program that always reads yesterday's file can look successful
while doing the wrong work. We will test two different inputs.

Python stores command-line arguments in `sys.argv`. With
`python3 read_report.py "weekend report.txt"`, element zero is `read_report.py`
and element one is `weekend report.txt`. Python itself is not element zero in
this script's list. Quotes keep the filename together in the shell.

Programs have separate **standard output** (results) and **standard error**
(diagnostics). Both normally appear in your terminal, but a caller can collect
them separately. A failed read should report failure, not pretend a blank
report was a successful result.

## Before you begin

From the VM repository root:

```bash
./lab-start b0.03
cd .student/b0.03
```

The helper makes a fresh copy if needed; `cd` enters it. Only edit that copy.

## Read the intentionally incomplete program

Locate the supplied reader before trying to edit it:

```bash
pwd
ls -l read_report.py
cat read_report.py
```

Line by line: confirm the path ends in `.student/b0.03`; list the existing
reader's details; then display its source. These commands neither run nor
change the reader. If the filename is absent, stop and check the preparation
steps instead of creating a replacement. The listing below is the supplied
file's contents; do not paste it at the shell prompt.

<!-- source: course/module-b0-basics/lesson-03/read_report.py format=code -->
```python
import sys
from pathlib import Path

if len(sys.argv) != 2:
    print("usage: python3 read_report.py REPORT", file=sys.stderr)
    raise SystemExit(2)
try:
    text = Path("report.txt").read_text(encoding="utf-8")
except OSError:
    print("Could not read that report.", file=sys.stderr)
    raise SystemExit(1)
print(text, end="")
```
<!-- /source -->

Line by line: `sys` supplies arguments and the error stream. `Path` represents
a filesystem path. `len(sys.argv) != 2` detects anything other than the script
name and one report argument. The indented `print(..., file=sys.stderr)` sends
usage help to the error stream; `SystemExit(2)` stops with nonzero status.
The `try` block attempts the read. `read_text(encoding="utf-8")` turns the file's
bytes into text. `except OSError` handles filesystem failures, prints a short
diagnostic, and exits with status 1. The last `print(text, end="")` emits the
text without adding another newline. A `#` begins a comment, not an operation.

The deliberate defect is `Path("report.txt")`: that literal filename ignores
the argument. All other behavior is supplied so we can focus on one change.

### Keep the inputs and decisions straight

For `python3 read_report.py "weekend report.txt"`, the values inside this script
are:

| Expression | Value | Why it matters |
| --- | --- | --- |
| `sys.argv[0]` | `read_report.py` | The script name occupies position zero. |
| `sys.argv[1]` | `weekend report.txt` | One quoted argument names the desired report. |
| `len(sys.argv)` | `2` | Count includes the script name and the report argument. |

`!=` means "not equal"; `=` assigns a value to a name. They are different
operations. The argument-count check happens before the read so the program
does not try to use a missing position. The `try` block then performs an
operation that can fail. An `OSError` transfers control to the matching
`except` block; the nonzero exit there prevents a success-looking blank report.
On a successful read, that error block is skipped and the final print runs.

`end=""` changes only the ending added by `print`. A file's existing newline
is already part of `text`; printing another would create an extra blank line.
Our reports are valid UTF-8 text with Unix LF line endings, or no final newline.
This text reader is not a byte-for-byte copier for arbitrary file formats:
Python's text I/O can normalize other line endings. We will assess the report
format practiced here, not binary files or malformed encodings.

## Exercise 1 - Establish the failure before editing

```bash
cat "weekend report.txt"
python3 read_report.py "weekend report.txt"
echo $?
```

`cat` shows the requested report. The reader instead prints the daily report,
although `echo` reports `0`. The process succeeded at the wrong task. Comparing
content as well as status makes this defect visible.

## Exercise 2 - Repair the source

```bash
nano read_report.py
```

This opens the student file in a terminal editor. Move with the arrow keys.
Change only `Path("report.txt")` to `Path(sys.argv[1])`. Press Ctrl+O, Enter
to save, then Ctrl+X to exit. `^` in nano's help means the Ctrl key. Preserve
the spaces before the line. You can use another familiar editor instead.

Hold Ctrl while pressing the letter; do not type the characters `Ctrl+O` into
the file. Check that nano's save prompt names `read_report.py` before Enter.
When the shell prompt returns, inspect what was actually saved:

```bash
cat read_report.py
```

This prints the on-disk file. Confirm the read line contains `sys.argv[1]` and
the surrounding error handling is still present. Merely changing text on the
editor screen does not establish that it was saved. If you accidentally opened
an empty buffer or changed unrelated lines, exit without saving and recheck
the path; do not overwrite the supplied program with an empty file.

Now `Path` receives the caller's argument rather than a fixed name. The
complete repaired read line is:

```python
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
```

The four leading spaces keep the assignment inside `try`. The right side
reads the named file; `=` assigns the resulting text to `text` for the final
print. This is an input-handling repair, not filesystem confinement.

## Exercise 3 - Verify more than the happy path

```bash
python3 read_report.py "weekend report.txt"
echo $?
python3 read_report.py report.txt
echo $?
python3 read_report.py absent.txt
echo $?
python3 read_report.py
echo $?
```

The first pair should print the weekend report and `0`; the second the daily
report and `0`. The missing path should produce the read diagnostic and `1`.
Omitting the argument should produce usage help and `2`. Each `echo` must
immediately follow the invocation it checks. You have tested correct selection
and two failures; a single successful output would not establish all three.

The practical also asks you to handle a directory supplied where a report is
expected. Practice that case now:

```bash
python3 read_report.py .
echo $?
```

`.` names the current directory, which cannot be read as an ordinary report.
Expect the read diagnostic and status `1`, as for the missing-file test.
The two failures have different causes but both belong to the filesystem-error family
handled by `OSError`; neither proves that a security policy blocked access.

## Checkpoint

Explain what `sys.argv[1]` contains when a filename includes a space. Explain
why a missing file must not return success. Close this guide and sketch the
reader's three decisions in words: argument count, read result, output.
You will recreate these behaviors independently in the practical lab.

## Troubleshooting and finish

An `IndentationError` usually means a line moved out of its block; compare the
supplied indentation. A `SyntaxError` can mean a missing quote or bracket.
Read the named line and make one repair at a time. If nano is unavailable, use
an installed editor or have the VM's shared package prerequisites installed;
do not modify your Mac's Python to repair a VM exercise.

```bash
cd ../..
```

This returns to the root. Optional `./lab-reset b0.03 --dry-run` previews;
`./lab-reset b0.03 --yes` discards only this lesson's work and fixtures.

## Sources and scope

- [sys.argv and streams](https://docs.python.org/3.12/library/sys.html#sys.argv),
  [len and print](https://docs.python.org/3.12/library/functions.html#print),
  [Path.read_text](https://docs.python.org/3.12/library/pathlib.html#pathlib.Path.read_text),
  and [exception handling](https://docs.python.org/3.12/tutorial/errors.html#handling-exceptions)
  support the argument, output, read, and failure explanations.
- [TextIOWrapper newline behavior](https://docs.python.org/3.12/library/io.html#io.TextIOWrapper)
  explains why this is text preservation for our LF reports, not arbitrary byte
  preservation. [OSError subclasses](https://docs.python.org/3.12/library/exceptions.html#os-exceptions)
  include missing-file and directory-as-file errors.
- [GNU nano 7.2 manual](https://www.nano-editor.org/dist/v7/nano.html), Editor
  Basics and the Write-Out command, supports the editor workflow. The built-in
  Ctrl+G help identifies the active key bindings; customized editors may differ.

The particular diagnostics and statuses 1/2 are North Echo interface choices.
Checking them validates our reader, not every Python program. References are
optional; this lesson supplies the explanation needed for the practical.
