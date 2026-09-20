# North Echo - Beginner entry chapters

**Learner-review beta.** Begin with a short basics refresher and one complete
environment-handoff problem before the numbered technical track. Pause at
checkpoints and report missing explanations; a passing grade alone is not mastery.

## Before starting

Use a disposable Linux VM, synthetic data, and an ordinary non-root account.
The repository root is the directory containing `lab-start`, `lab-grade`, and
`course/`. All preparation commands below start there. Do not type exercise
commands on your Mac, and do not put real credentials into a lab.

The v2.0.0-beta.1 appliance and manual include these chapters. The older v1.0.2
appliance does not; merely restarting it will not upgrade the course, by design.
Use a separate new beta VM as described in [VM setup](VM_SETUP.md). Do not extract
over an existing student's directory or migrate their unfinished work silently.

Run `./scripts/attest-course` and `./scripts/linux-preflight` from that copy's
root before starting. Attestation checks canonical files; preflight checks
the supported Linux environment. Neither checks your understanding.

## How to use the instructions

Use the Bash shell inside the VM. Blocks labeled `bash` are commands to type
there, one line followed by Enter unless explicitly shown otherwise. Blocks
labeled `python` show source in the named file; do not paste them into Bash.
Blocks labeled `text` show data or expected output, not commands. A source
listing in this manual is not a substitute for locating that file in your VM;
each guided program now has explicit `pwd`, `ls -l`, and `cat` access steps.

Reading with `cat` displays a file and returns to the prompt. Opening it with
`nano` enters an editor. Running `python3 filename.py` executes its instructions.
Those are three different actions. Lessons say which one you need, when to
save a change, and how to check the saved file before running it again.

At the repository root, run `pwd` and keep its printed path in your notes.
If you lose your place, that is the directory to return to. Do not blindly
repeat `cd .student/...` while already inside a lesson: relative paths start
from your current location. A failed `cd` does not put you in the intended
directory. Stop, check `pwd`, and correct the location before editing a file.

## Choose your entry point

If shell commands, paths, exit status, or small Python edits are unfamiliar,
start with `./lab-start b0.01`. If these are familiar, try
`./lab-start module-b0` as a diagnostic. Passing the practical and explaining
its review questions lets you go directly to `./lab-start b1.01`.

This is not a timed course. Work in short sessions and stop when a prediction
does not match an observation. Read the explanation, predict, run, compare,
then explain in your own words. Exact commands belong in guided practice;
the independent lab removes them only after you have practiced the skills.

`lab-start` resumes an existing workspace without erasing it. `lab-grade` gives
feedback on independent labs; guided lessons use observation checkpoints.
`lab-reset TARGET --dry-run` previews removal; `--yes` confirms it and discards
that target's student work/fixtures. Do not reset work you want to retain.

## What to record for learner review

For each lesson, note your prediction, observed result, an explanation in your
own words, and the first place you needed help. Distinguish unclear teaching
from VM setup trouble. After B1's practical, explain the remaining authority
of the worker. Try it again later with fresh fixtures before calling it learned.
Do not post private terminal history or environment dumps with feedback.

## How the technical explanations are grounded

Each lesson and practical ends with **Sources and scope**: named primary
documentation, the claims it supports, and limits on the lesson's conclusions.
The lesson itself still contains the required teaching. External links are
for verification and optional detail, not homework needed to fill missing steps.

Three kinds of statement are kept separate: documented API/command behavior;
North Echo's chosen example or policy; and results actually observed on a
specific VM. Test results support the third, not a claim about every machine.
The initial review used Ubuntu 24.04.5 arm64, Bash 5.2.21, coreutils 9.4,
Python 3.12.3, and nano 7.2. The lesson links retain that explicit source context.
The [Fedora source companion](SOURCE_TRUTH.md) records the newer guest's actual
versions, corresponding primary interfaces, and repeated behavioral checks.
No Windows or macOS exercise equivalence is implied.

The [source-review record](dev/BEGINNER_SOURCE_REVIEW.md) maps the reviewed
claims and records corrections for the initial B0/B1 review. The complete beta's
source/version map is separate. Learning effectiveness still needs your walkthrough.

<!-- PAGEBREAK -->

<!-- source: course/module-b0-basics/README.md format=markdown -->
# B0 - Working at the terminal

This optional refresher prepares you to change and test a small Python program.
It is not a replacement for an introductory Linux administration course.

You will locate a file, distinguish a program from a process, interpret success
and failure, and change a reader so it uses the filename you supply.
No prior Python knowledge is assumed; shell basics are introduced as needed.

If you already use the shell comfortably, try the B0 independent lab first.
Passing its automated checks **and** explaining its review questions lets you
skip the guided refresher. If you need help, the failed properties point back
to specific lessons. A failed first attempt is diagnostic, not a penalty.

Work only inside a disposable Linux VM. Start commands run from the repository
root, the directory containing `lab-start`. Each lesson then names its working
directory. Do not edit `course/`. Your copies live under `.student/`.

Sequence: `b0.01`, `b0.02`, `b0.03`, then `module-b0`.
Allow several short sessions; no speed target is part of assessment.
<!-- /source -->

<!-- source: course/module-b0-basics/lesson-01/README.md format=markdown -->
# B0.01 - Locate and read a report

## Outcomes

Find your current directory, identify the file a relative path names, and read
a filename containing a space without accidentally supplying two filenames.

## Understand first

A terminal accepts text and displays results. The **shell** is the program
interpreting the commands you type. A command usually names a program followed
by arguments: information that tells that program what to do. Press Enter to
run one command. Our code blocks omit the shell prompt; type only the commands.

A **file** holds data; a **directory** groups names. The shell has a current
working directory. A relative path is interpreted from there. `..` means the
parent directory. An absolute path begins with `/` and does not depend on the
working directory. Spaces normally separate arguments, so quote a path that
contains a space. Quotes group the argument; they are not part of its name.

The scenario is ordinary on purpose: a delivery team has two reports. Before
we restrict a reader, we need to know which report we actually asked it to read.

## Before you begin

In the VM, return to your repository root. Then:

```bash
./lab-start b0.01
cd .student/b0.01
```

Line by line: `./lab-start` runs the course helper in the current directory and
creates a working copy plus synthetic reports. `cd` changes the shell's working
directory to that copy. Starting again resumes it; it does not erase your work.

The reports already exist: you do not need to create them or type their contents.
`report.txt` and `weekend report.txt` are data to inspect; `README.md` is this
guide. The directory `notes` contains a third text file. A leading `./` means
"in this directory"; `.student` is the course's student-work directory, not a
command. Its leading dot makes it normally hidden in a plain directory listing.

## Exercise 1 - Establish where you are

```bash
pwd
ls
cat report.txt
cat "weekend report.txt"
```

Line by line: `pwd` prints the current directory; its ending should be
`.student/b0.01`. `ls` lists names there. The first `cat` displays the daily
report. The second supplies one quoted filename to display the weekend report.
Expect a generated delivery identifier and parcel counts. Identifiers differ
between attempts; do not compare them against a screenshot or memorize them.

`cat` returns you to the shell after displaying the file. It does not start an
editor, so there is nothing to save or quit. Reading a file is different from
executing instructions in it. Here, parcel-count sentences are just text.
For the daily report, expect this shape (do not type this output):

```text
Delivery report for <generated identifier>
Three parcels arrived.
```

The angle-bracketed phrase represents a changing identifier, not literal file
content. The first line identifies this attempt; the second is the report data.

## Exercise 2 - Make and diagnose a path mistake

Predict which of these commands will fail before running them:

```bash
cd notes
cat location.txt
cat report.txt
cat ../report.txt
cd ..
```

Line by line: `cd notes` enters the child directory. `cat location.txt` reads its
orientation note. `cat report.txt` fails because that name is not in `notes`.
`cat ../report.txt` repairs the lookup by naming the parent's report. `cd ..`
returns to the lesson directory. The missing-file error does **not** show an
access-control denial: we simply asked for the wrong path.

The complete supplied note is:

```text
You are reading a file inside the notes directory.
The delivery reports are one directory above this one.
```

The first line describes location; the second tells you how the reports relate
to it. Neither line changes the filesystem: this is data, not a command.

## Checkpoint - Try without the command sequence

From the lesson directory, enter `notes`, read the weekend report without
leaving `notes`, and return. Explain why the quotes and `..` solve different
problems. If stuck, revisit Exercise 2 and then try again without looking.

Do not proceed until you can predict the result from your current directory.
There is no automatic grade for guided lessons.

## Troubleshooting and finish

If `./lab-start` is missing, you are not at the repository root. If `cd notes`
fails, check `pwd` and `ls`; do not create a replacement directory to hide the
mistake. Use `cd ..` only when you know which parent you intend to enter.

```bash
cd ../..
```

From the lesson directory this returns to the repository root. You may stop
here and resume later. To discard this lesson's files, run from that root:

```bash
./lab-reset b0.01 --dry-run
./lab-reset b0.01 --yes
```

The first command previews removal. The second removes this lesson's workspace
and fixtures, including your edits. It leaves other lessons alone. Reset is
optional, not a prerequisite for starting the next lesson.

## Sources and scope

- [Ubuntu 24.04 Bash manual](https://manpages.ubuntu.com/manpages/noble/man1/bash.1.html),
  QUOTING and SHELL BUILTIN COMMANDS (`cd`, `pwd`): command interpretation and
  navigation. The lab uses ordinary paths without symlink-navigation edge cases.
- [GNU ls manual shipped by Ubuntu](https://manpages.ubuntu.com/manpages/noble/man1/ls.1.html)
  and [GNU cat manual](https://manpages.ubuntu.com/manpages/noble/man1/cat.1.html):
  listing names and displaying file contents.

Report names and parcel counts are North Echo fixtures, not Linux guarantees.
The relative-path failure is an observed exercise result, not evidence of a
security restriction. References support the explanation; opening them is optional.
<!-- /source -->

<!-- source: course/module-b0-basics/lesson-02/README.md format=markdown -->
# B0.02 - A program is not its running process

## Outcomes

Identify a running program's process and parent, and check failure independently
of the text it printed. Prerequisite: B0.01 or equivalent shell experience.

## Understand first

A **program** is stored instructions. A **process** is one running instance of
those instructions. Running the same file twice normally creates two different
processes. A process ID (**PID**) identifies a process while it exists; it is
not a permanent identity. The parent is the process that launched it. Here,
your shell launches Python, which reads a program file.

The child can print text and then finish with an **exit status**. By convention,
zero means success and a nonzero number means failure. These are different
channels: a cheerful printed message is not proof of success. In the shell,
`$?` expands to the most recent command's status. Check it immediately, before
another command replaces it.

## Before you begin

From the VM repository root:

```bash
./lab-start b0.02
cd .student/b0.02
```

The first command prepares or resumes this lesson. The second enters its
working copy. You do not need to install Python packages or use `sudo`.

## Read the small program

`lab-start` supplied a file named `identify.py` in `.student/b0.02`. You do not
need to create or edit it. Stay in the directory entered above and inspect it:

```bash
pwd
ls -l identify.py
cat identify.py
```

Line by line: `pwd` should end in `.student/b0.02`. `ls -l identify.py` lists
details for that one file: file type/permissions, link count, owner, group,
size, modification time, and name. Those details can vary; the name should be
`identify.py`. We are locating the file, not changing its permissions.
`cat identify.py` prints its contents and returns to the shell. It does **not**
execute the Python statements. If the file is missing, stop and check the
working directory before proceeding; do not open an editor and create a blank
replacement with the same name.

Compare what `cat` prints with the complete source below. This is a listing of
an existing file, not commands to paste into the shell. No editor is needed
in B0.02; B0.03 will explicitly introduce opening, saving, and checking an edit.

```python
import os
import sys

print("This is one running copy of identify.py.")
print("Process ID:", os.getpid())
print("Parent process ID:", os.getppid())
if "fail" in sys.argv[1:]:
    print("I printed a message, but I am reporting failure.")
    raise SystemExit(7)
print("Finished successfully.")
```

Line by line: `import os` loads process-information functions. `import sys`
loads the argument interface. Each `print` writes a line to standard output,
the ordinary result stream. `os.getpid()` asks for this process's ID;
`os.getppid()` asks for its parent's ID. `sys.argv` is the argument list:
element zero names the script, and `[1:]` selects everything after it.
`if` conditionally runs its indented lines. When `fail` is present, the program
prints a message and `raise SystemExit(7)` ends it with status 7. Otherwise it
reaches the last print and ends normally with status zero. Indentation groups
Python statements; keep the supplied spaces when editing later.

### Follow the decision, not just the spelling

`import` makes a library available under a name. A library is reusable program
code: `os` and `sys` are included with Python, so these imports do not download
anything. In `os.getpid()`, the dot selects a function from `os` and the empty
parentheses call it with no arguments. `print` displays the value returned.

An **argument list** is an ordered sequence. Python numbers its positions from
zero. With `python3 identify.py fail`, `sys.argv` contains `identify.py` at
position zero and `fail` at position one. `[1:]` selects the entries starting
at position one. The `in` expression asks whether that selected sequence
contains the text `fail`; it produces a true/false decision.

Read the `if` as: "If that argument is present, do the indented actions."
`SystemExit(7)` supplies the exit condition and `raise` triggers it, so execution
does not continue to the final success print. Without `fail`, Python skips
that indented block and reaches the last line. The number 7 is our chosen
demonstration value, not a universal code for a particular operating-system error.

Before executing, point to the line that changes the exit status. This checks
your interpretation of the source before terminal output can suggest an answer.

## Exercise 1 - Observe two runs

Now run the file, using the same working directory:

```bash
python3 identify.py
echo $?
python3 identify.py
echo $?
```

Each `python3` starts a process running the same file. Each `echo` prints the
preceding status. Expect `Finished successfully.` and status `0` both times.
The process IDs normally differ; the parent ID should be the same shell.
This demonstrates new executions, not a security boundary. The processes end
quickly; you do not need to kill them or inspect a stale PID.

`python3` names the interpreter: the program that executes Python source.
`identify.py` tells it which file to read as instructions. There is no need to
make the `.py` file executable or run `chmod`; we are invoking the interpreter.
After each run, expect this output pattern followed by the status from `echo`:

```text
This is one running copy of identify.py.
Process ID: <number for this run>
Parent process ID: <number for the launching shell>
Finished successfully.
0
```

The placeholder numbers vary. The final `0` is printed by `echo`, not by
`identify.py`. `echo` is itself another command with its own status, which is
why you must check `$?` before running unrelated inspection commands.

## Exercise 2 - Text can accompany failure

Predict the next status, then run:

```bash
python3 identify.py fail
echo $?
```

`fail` is an argument to our script, not a Python option. The program prints its
failure message but exits with `7`. `echo` exposes that result. Repair this
deliberately failing invocation by running `python3 identify.py` with no `fail`
argument, then check `$?` again. Expected repaired status: `0`.

## Checkpoint

Without rerunning, explain whether the file, process, or both changed between
the two successful invocations. Then demonstrate a failed invocation and show
its status without accidentally reporting the status of `echo` instead.
Explain why looking only for a line of output would be a weak test.

## Troubleshooting and finish

An unexpected `0` often means another command ran before `echo $?`. Try the
two-line pair again. If Python cannot find the file, check `pwd` and `ls` as in
B0.01; do not change system Python settings.

```bash
cd ../..
```

This returns from the lesson directory to the repository root. Optional reset:
`./lab-reset b0.02 --dry-run` previews removal; `./lab-reset b0.02 --yes`
discards this lesson's workspace and fixtures. Nothing remains running.

## Sources and scope

- [Python 3.12 os](https://docs.python.org/3.12/library/os.html#os.getpid):
  `getpid()` and `getppid()` identify the current process and its parent.
- [Python 3.12 sys.argv](https://docs.python.org/3.12/library/sys.html#sys.argv),
  [if statements](https://docs.python.org/3.12/tutorial/controlflow.html#if-statements),
  and [SystemExit](https://docs.python.org/3.12/library/exceptions.html#SystemExit):
  script arguments, conditional execution, and the exit mechanism.
- [Python interpreter invocation](https://docs.python.org/3.12/using/cmdline.html#interface-options)
  and [print](https://docs.python.org/3.12/library/functions.html#print): running
  a source file versus displaying text.
- [Ubuntu 24.04 Bash manual](https://manpages.ubuntu.com/manpages/noble/man1/bash.1.html),
  EXIT STATUS: the shell's success convention and `$?`.
- [ls -l](https://manpages.ubuntu.com/manpages/noble/man1/ls.1.html) and
  [cat](https://manpages.ubuntu.com/manpages/noble/man1/cat.1.html): inspecting
  a file's details and contents without executing its Python source.

The displayed messages and choice of status 7 are our example's behavior.
The PID comparison assumes these foreground commands in the same interactive
shell; an ID is not permanent and may later be reused. This is a process
observation, not proof of isolation. Required teaching is above; references
are available for verification and optional depth.
<!-- /source -->

<!-- source: course/module-b0-basics/lesson-03/README.md format=markdown -->
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
<!-- /source -->

<!-- source: course/module-b0-basics/lab/README.md format=markdown -->
# B0 practical - Read the report you were given

## Outcome and preparation

Implement a small report reader without a step-by-step repair. This is an
independent assessment of B0.01-03, or a diagnostic if those skills are familiar.
Python source editing is required; no C, networking, or administrator privileges.

From the repository root in your disposable VM:

```bash
./lab-start module-b0
cd .student/b0.lab
```

The first command prepares/resumes the independent workspace. The second enters
it. Read and edit only its `read_report.py`; the initial implementation is
intentionally incomplete. The reports contain synthetic data.

The practical withholds the implementation, not how to access your files:

```bash
pwd
ls -l read_report.py
cat read_report.py
nano read_report.py
```

Confirm `.student/b0.lab`, locate the starter, read its current contents, then
open it for your own changes. Save with Ctrl+O and Enter, then exit with Ctrl+X.
Use `cat read_report.py` afterward to inspect what was saved. If you only want
to inspect the starter now, stop before the `nano` command. No completed source
is supplied here; revisit B0.03 if you need help choosing the implementation.

## Your task

The interface is `python3 read_report.py REPORT`, where REPORT is one path.

1. Read the report named by the caller, not a fixed filename. A filename may
   contain spaces; the caller will supply it as one argument.
2. On success, write exactly its UTF-8 text to standard output, with no extra
   heading or newline, no error output, and a zero exit status.
3. On a missing argument or a file that cannot be read (including a directory),
   write a diagnostic to standard error, no report to standard output, and exit
   nonzero. Exact error wording is not graded.
4. Test two reports with different content and at least one failed read.

The evaluation uses fresh filenames and contents, including a report with no
final newline. Reports are valid UTF-8 with Unix LF line endings; malformed
encodings, binary files, and preservation of other newline encodings are outside
this task. No new API or algorithm beyond B0.03 is needed. Do not inspect
the grader for a solution; judge the contract above.

## Evaluate and review

```bash
cd ../..
./lab-grade module-b0
```

`cd` returns to the repository root. `lab-grade` runs fresh cases and reports
properties, not a line-for-line source comparison. A first `NOT PASSED` with
the starter is expected. Use its lesson references, repair your working copy,
and repeat. `./lab-grade module-b0 --mode exam` checks the same properties with
fewer hints; it does not erase your work.

Automated checks are not the entire assessment. Explain without reading a
solution: What changes between a program and one running process? Why do we
check both text and exit status? What does quoting a filename accomplish?
If those explanations are unclear, revisit the relevant guided lesson even
if the tests pass.

## Finish

You may keep your work. To discard all B0 student work, preview with
`./lab-reset module-b0 --dry-run`, then use `./lab-reset module-b0 --yes`.
This removes B0's three guided workspaces, lab, and fixtures, not B1 or the
existing numbered course. The next start generates new report identifiers.
Attempt/pass metadata remains; your source does not. Ready? Continue with B1.01.

## Sources and scope

The interfaces are documented in [Python 3.12 sys](https://docs.python.org/3.12/library/sys.html#sys.argv),
[pathlib](https://docs.python.org/3.12/library/pathlib.html#pathlib.Path.read_text),
[print](https://docs.python.org/3.12/library/functions.html#print), and
[filesystem exceptions](https://docs.python.org/3.12/library/exceptions.html#os-exceptions).
The argument/output/error requirements are this lab's contract. The fresh
grader cases check that contract; they do not certify an arbitrary file reader.
The required skills were practiced in B0.01-03, including the directory-read
failure. These references are not extra prerequisite assignments.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-b1-first-boundary/README.md format=markdown -->
# B1 - Useful work with less inherited data

The delivery team wants a tool to read a report. The program that starts it
also holds a fake private setting the reader does not need. Your job is to
control that handoff while keeping the reader useful.

By the end, you should be able to predict which environment settings a child
receives, construct a small allowlist, test required and prohibited behavior,
and state what that repair does **not** isolate.

Prerequisites: locate and quote paths, edit a short Python file, distinguish
program/process, and interpret exit status. Use B0 if any are unfamiliar.
New ideas are introduced here: process environment, parent-to-child handoff,
allowlisting, and positive/negative tests. No namespaces, capabilities, C,
kernel tracing, network service, model, or API key is required.

Three guided lessons build toward one independent practical. The third gives
less help: use the earlier explanation on a changed case before asking for a
hint. The independent lab supplies requirements, not repair instructions.

**Scope:** this is environment hygiene, not a sandbox. The child still runs as
your VM user and can use that user's filesystem and other available resources.
We are not demonstrating that hostile code is contained. Use only the supplied
local workers and synthetic data inside the disposable VM.

Sequence: `b1.01`, `b1.02`, `b1.03`, then `module-b1`.
Pause after the practical to explain the boundary and record any missing steps.
If you can predict the changed case and explain the remaining authority, continue
to Module 01. This beta still needs learner review; a grade alone is not mastery.
<!-- /source -->

<!-- source: course/module-b1-first-boundary/lesson-01/README.md format=markdown -->
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

```python
import os
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
print(text, end="")
print("Private setting received:", "NE_PRIVATE_TOKEN" in os.environ)
```

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
<!-- /source -->

<!-- source: course/module-b1-first-boundary/lesson-02/README.md format=markdown -->
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
<!-- /source -->

<!-- source: course/module-b1-first-boundary/lesson-03/README.md format=markdown -->
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
<!-- /source -->

<!-- source: course/module-b1-first-boundary/lab/README.md format=markdown -->
# B1 practical - A useful reader with a smaller handoff

## Outcome and preparation

Repair an independent launcher using only ideas practiced in B1.01-03. You
will be evaluated on actual child behavior, not specific source text.

From the repository root inside the disposable VM:

```bash
./lab-start module-b1
cd .student/b1.lab
```

The first command prepares/resumes the practical. The second enters its
workspace. Edit `launch.py` there, not canonical course material.

Inspect the actual starter before changing it:

```bash
pwd
ls -l launch.py
cat launch.py
nano launch.py
```

Confirm `.student/b1.lab`, locate the supplied file, display its source, then
open it to implement your chosen repair. Save with Ctrl+O and Enter; exit with
Ctrl+X. Run `cat launch.py` to verify the saved file. Stop before `nano` if
you are only inspecting. Access instructions do not supply the repair itself.

## Task and interface

Invoke the program as `python3 launch.py WORKER REPORT`. WORKER is a supplied
trusted local Python program; REPORT is a path passed as its one argument.
The grader supplies both using fresh names, including paths with spaces.

1. Actually run the selected worker with the selected report argument.
2. Pass the parent's `NE_REPORT_STYLE` value unchanged. It will be `plain` or
   `upper` and is guaranteed to exist for this assessment.
3. Do not copy other parent settings into the child. The parent contains fake
   private values and unrelated settings; their names are not a fixed list.
4. Preserve the worker's standard output, standard error, and ordinary exit code
   (0-255). Signal forwarding is outside this assessment.
   A failed report read must remain a failure. Do not print extra launcher
   messages or any private value.

You are not required to implement a sandbox, support arbitrary executables,
handle malformed argument counts, or defend against a malicious worker. This
lab tests explicit environment inheritance and a reliable subprocess handoff.
Python may introduce an interpreter locale setting of its own; that is not a
copied parent secret. No environment-wide dump is needed to solve this lab.

For local experiments you may reuse the observer from your B1.03 workspace by
supplying its path. The independent grader does not use your edited observer
and does not accept reassuring launcher messages as proof the child ran.

If that workspace still exists, this is a concrete invocation from `.student/b1.lab`:

```bash
ls -l ../b1.03/inspect_reader.py
NE_REPORT_STYLE=plain NE_PRIVATE_TOKEN=pretend-red python3 launch.py ../b1.03/inspect_reader.py report.txt
echo $?
```

`..` reaches `.student`; the rest of the relative path selects the earlier
observer. Check the listing succeeds before running it. If you reset B1.03,
prepare it again from the repository root first; don't invent another worker
to match your launcher. The prefixes and arguments have the meanings practiced
in B1.03. Use the report and presence observations to assess your repair, then
design a changed case yourself. Grading supplies its own worker regardless of
whether you retain this earlier workspace.

## Evaluate

```bash
cd ../..
./lab-grade module-b1
```

`cd` returns to the root. The grader launches fresh cases and reports failed
properties with references in practice mode. Expect the starter to fail the
unapproved-setting checks. Repair the implementation and rerun. Use
`./lab-grade module-b1 --mode exam` for the same checks with reduced hints.

An entirely empty environment must fail the useful-work check. A one-name
deletion must fail changed-key checks. A launcher that fabricates report output
without running the worker must fail the independent execution observation.
The grader is feedback for honest learners, not a hostile multi-user barrier.

## Explain and finish

Before calling this complete, explain in your own words:

- What crossed from parent to child before and after your repair?
- Which observation proves the report job still works?
- Which observation supports the claim that unnecessary settings did not cross?
- What could the child still access? Name a resource this repair does not restrict.
- If the worker fails, why should its caller see that failure too?

These are human review questions, not keyword-graded prose. Record predictions,
actual observations, and where you needed help in your own notes. A green grade
does not by itself establish understanding or containment of hostile code.

Optional `./lab-reset module-b1 --dry-run` previews removal of all B1 student
work. `./lab-reset module-b1 --yes` discards its lessons, lab, and fixtures while
keeping attempt/pass metadata. Reset and retry on a later day to test recall.

Pause here for a learner review. Continue to Module 01 when you can predict and
explain the handoff and its limits, not merely when you obtain a green grade.

## Sources and scope

- [Python 3.12 subprocess](https://docs.python.org/3.12/library/subprocess.html#subprocess.run)
  supports the explicit environment and structured invocation. Its
  [returncode contract](https://docs.python.org/3.12/library/subprocess.html#subprocess.CompletedProcess.returncode)
  distinguishes normal exits from signal termination; our lab covers the former.
- [Python startup locale handling](https://docs.python.org/3.12/using/cmdline.html#envvar-PYTHONCOERCECLOCALE)
  documents that the interpreter can introduce `LC_CTYPE`. "No copied parent
  settings except the public style" is therefore not a promise of an environment
  containing exactly one key after Python starts.

The grader's fresh worker checks selected inherited settings and useful work.
That is not a confidentiality guarantee against malicious same-user code or
evidence of filesystem/network confinement. Our policy and tested cases are
explicit lab choices, not universal requirements imposed by Python.
<!-- /source -->
