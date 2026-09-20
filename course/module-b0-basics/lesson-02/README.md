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

<!-- source: course/module-b0-basics/lesson-02/identify.py format=code -->
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
<!-- /source -->

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
