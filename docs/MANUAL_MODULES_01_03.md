# North Echo Agent Security Lab

## Foundation field manual - Modules 01-03

This is the self-contained teaching manual for the first three playable modules. It assumes no prior systems-programming expertise. The goal is not to memorize commands. The goal is to build a reliable mental model of what authority a Linux process carries and to verify every containment claim from observable kernel state.

The learning rhythm is: predict, run, observe, explain, break, repair, and verify.

> **Safety boundary:** Use only a disposable Linux VM with synthetic fixtures. Do not load personal or employer credentials. Do not target external systems. Run as an ordinary user unless an exercise explicitly creates namespace-local root.

## What this manual contains

- A command-reading primer so punctuation such as `|`, `>`, `$()`, and quotes is never magic.
- Detailed mental models for processes, `execve`, environment inheritance, file descriptors, namespaces, credentials, capabilities, and `no_new_privs`.
- Every guided command for Modules 01-03 followed by a line-by-line explanation.
- Complete guided source listings with explanations of each meaningful C or Python line.
- Expected output patterns, including values that legitimately vary by machine.
- Intentional failures, why they fail, and how to verify the correction.
- Independent lab contracts and verification plans without complete solutions.
- Troubleshooting notes, a glossary, and a compact command reference.

## Starting, resetting, and replaying

From the repository root:

```bash
./scripts/attest-course
./lab-start 01.01
cd .student/01.01
less README.md
```

### What each line does

- `./scripts/attest-course` recomputes hashes for canonical course material. A pass means it matches the recorded manifest.
- `./lab-start 01.01` creates or resumes a disposable workspace for Module 01, Lesson 01.
- `cd .student/01.01` enters the generated editing area. Edit here, not under `course/`.
- `less README.md` opens the workspace instructions. Press `q` to leave.

Return to the repository root before lifecycle commands:

```bash
./lab-status
./lab-reset 01.01 --dry-run
./lab-reset 01.01 --yes
./lab-start 01.01
```

### What each line does

- `lab-status` reads attempt counts, workspace state, and pass state without changing anything.
- `--dry-run` checks reset boundaries and prints intended actions without deleting the workspace.
- `--yes` confirms the scoped reset after the same containment checks pass.
- Starting again produces new synthetic IDs, names, paths, ports, and canaries while retaining only progress metadata.

Reset is part of the pedagogy. After reset, the old solution is gone. A new attempt tests understanding instead of recognition.

# Reading command and code blocks

## Shell command anatomy

A shell expands text, constructs an argument vector, applies redirections, and launches programs. Small punctuation marks can change data flow and authority.

```bash
grep -E '^CapEff:' /proc/self/status
```

### What each token means

- `grep` is the program selected through `PATH`.
- `-E` enables extended regular expressions.
- `'^CapEff:'` is one quoted argument. The shell removes the quotes before launch.
- `^` anchors the expression at the beginning of a line.
- `/proc/self/status` is the input pathname. For the running `grep`, `/proc/self` identifies that process.

### Variables and command substitution

```bash
CURRENT_UID=$(id -u)
printf 'uid=%s\n' "$CURRENT_UID"
```

- `$(id -u)` launches `id`, captures stdout without its trailing newline, and substitutes the result.
- `CURRENT_UID=...` creates a shell variable. It is not inherited unless exported.
- `printf` receives a format string and a value as separate arguments.
- Double quotes permit expansion while preserving the result as one argument.
- `\n` tells `printf` to emit a newline.

### Quoting changes which shell performs expansion

```bash
sh -c 'echo "child pid=$$"'
sh -c "echo child pid=$$"
```

- Single quotes protect `$$` from the outer shell. The child shell expands it to the child's PID.
- Double quotes let the outer shell expand `$$` before `sh` starts. The child receives the parent's number as ordinary text.
- Both outputs can look plausible, so quoting must be reasoned about explicitly.

### Pipes and redirections

```bash
strace -e trace=write ./program 2>&1 | grep write
```

- `strace ... ./program` starts the observed process.
- `2>&1` makes descriptor 2 use the destination currently used by descriptor 1.
- `|` connects the left command's stdout to the right command's stdin.
- `grep write` filters display. It does not change the traced process.
- Pipeline stages are separate processes with separate descriptors and exit statuses.

### Exit status

```bash
command && echo passed
command || echo failed
```

- Processes return a small integer status. Zero conventionally means success.
- `&&` runs the right side only after status zero.
- `||` runs the right side only after nonzero status.
- `;` sequences commands regardless of status.

## C source anatomy

- `#include` supplies declarations from a header.
- `main` is the user-space entry point after the program image is initialized.
- `argc` counts argument pointers; `argv` is a NUL-terminated pointer array.
- Successful `exec` does not create a process and does not return. It replaces the current program image.
- Most syscall wrappers report failure as `-1` and set `errno`; `perror` formats that error.
- File descriptors are process-local integers referring to kernel-managed open objects.
- Bitwise OR (`|`) combines flag bits; bitwise AND (`&`) tests bits. They differ from logical `||` and `&&`.

> **Reading rule:** Identify the authority-transfer point in every launcher. Hygiene and policy that must govern the executed program must be established before `exec`.

<!-- source: course/module-01-process-authority/README.md format=markdown -->
# Module 01 - Processes, syscalls, and inherited authority

You will trace a command from process creation to kernel-visible effects, then remove two authorities that commonly cross `execve(2)` by accident: environment data and open file descriptors.

Play in order: `01.01`, `01.02`, `01.03`, then `module-01`.

## Learning route and limits

Prerequisites: B0 and B1. Continue as your ordinary account inside the disposable Linux VM. The guided lessons introduce their new syntax and interfaces before the independent lab combines them.

01.01 connects source, executable, process, and syscall. 01.02 traces an environment value and practices a constructed C environment. 01.03 traces an already-open reference and practices closing unknown extra descriptors.

Replacing program code does not automatically discard its environment or open descriptors. Explain the difference between a filename and a descriptor, and between fork and exec. Neither environment hygiene nor descriptor closure restricts every future file open.

Before moving on, demonstrate both useful allowed work and the intended restriction, and explain the difference in your own words. A failed compiler command or missing input is not a security success. Use the independent lab's practice feedback to revisit a specific lesson; passing checks does not replace understanding or make the combined program production-ready.
<!-- /source -->

## Module outcome and mental model

You will trace shell text into a process, an `execve` transition, and syscalls. Then you will remove two quiet authority channels: inherited environment values and open file descriptors.

```text
parent process
  -> optional fork or clone
  -> prepare arguments, environment, and descriptors
  -> execve(new program, argv, envp)
  -> new program continues with surviving process authority
```

`fork` creates a process by copying state. `execve` replaces a process image while preserving selected process attributes. A syscall crosses from user space into the kernel. The new executable is not automatically a clean slate.

<!-- PAGEBREAK -->

<!-- source: course/module-01-process-authority/lesson-01/README.md format=markdown -->
# 01.01 - Follow a program into the kernel

## Outcomes and prerequisites

Identify your shell and its parent, compile a supplied C program, and connect
its output to observed system calls. Use the B0 skills of locating files,
saving edits, and checking exit status. Complete B1 before this security track.
The C features needed here are introduced locally; you do not need to write
the program from a blank file.

## Understand first

Python reads source through an interpreter. A C compiler translates source
into an executable first. Saving a source edit does not change an executable
already built from it. Compile again before testing that edit.

A process normally executes instructions in user space. A system call is a
controlled entry into the kernel to request an operation such as writing bytes.
A library function can make several syscalls or postpone one. Its source name
does not tell you exactly what the kernel observed.

`strace` starts our small program and reports selected system calls. This is
observation, not confinement: tracing does not install a rule denying writes.
Module 06 will use this distinction when building a syscall policy.

## Prepare and locate the supplied file

From the repository root inside the disposable VM:

```bash
./lab-start 01.01
cd .student/01.01
pwd
ls -l hello-syscall.c
cat hello-syscall.c
```

`lab-start` creates or resumes the lesson. `cd` enters its editable copy.
`pwd` must end in `.student/01.01`; stop otherwise. `ls -l` shows metadata;
`cat` reads the text without compiling or executing it. Do not create a blank
replacement if the supplied file is missing.

## Read the small C program

```c
#include <stdio.h>
#include <unistd.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    puts("userspace: about to write");
    const char message[] = "kernel-visible write\n";
    if (write(STDOUT_FILENO, message, sizeof(message) - 1) < 0) {
        perror("write");
        return 1;
    }
    return 0;
}
```

`#include` supplies declarations so the compiler knows the named functions
and constants. `int main(void)` defines the entry function with no arguments
in this example and an integer exit result. Braces group statements;
semicolons terminate them. Unlike Python, indentation does not define blocks.

`stdout` is a C-library stream; a descriptor is a process-local reference to
an open object. The stream can buffer bytes before a syscall transfers them.
`const char message[]` is an array of characters; `const` prevents modification
through that declaration. The string contains a newline and a terminating
zero byte. The later source commentary connects these pieces to each call.

This is not a general-purpose write-all routine: `write` can successfully
transfer fewer bytes than requested. Production copying must handle partial
writes and interruptions. Our short message makes the observation manageable.

## Exercise 1 - Establish the process facts

Run:

```bash
pwd
printf 'shell pid=%s parent=%s\n' "$$" "$PPID"
ps -o pid,ppid,user,stat,comm,args -p $$ -p $PPID
```

### Line by line

- `pwd` prints the workspace directory so you can confirm where the exercise is running.
- `printf ... "$$" "$PPID"` formats two shell variables: `$$` is this shell's PID and `$PPID` is its parent's PID. Quoting keeps each expanded value as one argument.
- `ps -o ...` selects explicit columns instead of relying on a distribution's default view. The two `-p` arguments restrict output to the shell and its parent.
- In the format list, `pid` and `ppid` show the relationship, `user` shows the effective account, `stat` shows process state, `comm` shows the executable name, and `args` shows the full argument vector.

Expected pattern: two rows. Your shell's `PPID` identifies its parent. A process is not “the command text”; it is a kernel object with identity, credentials, memory, descriptors, and namespace memberships.

Now inspect the executable and namespace handles:

```bash
readlink /proc/$$/exe
ls -l /proc/$$/ns
```

### Line by line

- `readlink /proc/$$/exe` asks procfs which executable object backs the current shell process.
- `ls -l /proc/$$/ns` lists the shell's namespace handles. `-l` is needed because each entry is a symbolic link whose target contains the namespace type and identity.

Expected pattern: `exe` names your shell; namespace entries look like `mnt:[402653....]`. Those inode-like numbers let you compare namespace membership later.

## Exercise 2 - Compile a process that crosses into the kernel

Inspect and build the starter:

```bash
sed -n '1,200p' hello-syscall.c
cc -std=c11 -Wall -Wextra -O2 hello-syscall.c -o hello-syscall
./hello-syscall
```

### Line by line

- `sed -n '1,200p' ...` displays only lines 1 through 200. `-n` suppresses normal output and `p` explicitly prints the selected range.
- `cc` invokes the C compiler. `-std=c11` selects the language version, `-Wall -Wextra` enable useful warnings, `-O2` enables normal optimization, and `-o hello-syscall` names the output binary.
- `./hello-syscall` executes the file from the current directory; the `./` prevents the shell from searching `PATH` for a different program.

Expected output:

```text
userspace: about to write
kernel-visible write
```

### Source, line by line

- `#include <stdio.h>` declares `puts`, `setvbuf`, and `perror`; `#include <unistd.h>` declares `write` and `STDOUT_FILENO`.
- `int main(void)` defines the C entry function with no arguments in this example and an integer exit result.
- `setvbuf(stdout, NULL, _IONBF, 0)` disables userspace buffering for `stdout`, making the observation easier to reason about.
- `puts(...)` is a C library call; it eventually needs a kernel write to make bytes visible.
- `const char message[] = ...` creates immutable message bytes in process memory; `\n` is one newline byte.
- `write(STDOUT_FILENO, message, sizeof(message) - 1)` asks the kernel to write those bytes to descriptor 1. Subtracting 1 excludes C's terminating NUL byte.
- `< 0` tests the syscall wrapper's failure convention; `perror` explains the current `errno` value.
- `return 1` reports failure, while the final `return 0` reports success to the parent process.

Trace it:

```bash
strace -f -e trace=execve,write,exit_group ./hello-syscall 2>&1
```

### Line by line

- `strace` observes syscalls made by the command it launches.
- `-f` follows child processes if the program creates any.
- `-e trace=...` reduces the trace to `execve`, `write`, and `exit_group`, keeping the observation focused.
- `2>&1` redirects file descriptor 2 (stderr, where `strace` writes) to the same destination as file descriptor 1 (stdout).

Expected pattern: an `execve(...) = 0`, one or more `write(...)` calls, then `exit_group(0)`. Library functions are not themselves the security boundary; their eventual syscalls are what enter the kernel.

## Exercise 3 - Make and correct an intentional prediction error

Before running this, predict whether the first source output statement must
produce the first visible line. Run the unchanged program first:

```bash
strace -e trace=write ./hello-syscall 2>&1 | grep write
```

### Line by line

- `strace -e trace=write` records only `write` syscalls.
- `2>&1` combines trace output and program output into one stream.
- `|` connects that stream to the next command.
- `grep write` keeps lines containing the word `write`; it is a display filter, not part of the traced program.

Now open the supplied source:

```bash
nano hello-syscall.c
```

Change only `_IONBF` to `_IOFBF`, selecting full buffering. Save with Ctrl+O,
confirm the existing filename with Enter, and exit with Ctrl+X. These use
Control, not the Mac's Command key. Check the saved file, rebuild, and trace:

```bash
cat hello-syscall.c
cc -std=c11 -Wall -Wextra -O2 hello-syscall.c -o hello-syscall
strace -e trace=write ./hello-syscall
```

Stop on compilation errors: an older executable can otherwise conceal a bad
edit. The direct write can now appear before the earlier `puts` output,
because the C stream retains its bytes until a later flush. Compare actual
events with source order; do not memorize a libc-specific syscall count.
Restore `_IONBF`, save, rebuild, and trace again. Explain why saving without
rebuilding would not repair the executable.

## Checkpoint and troubleshooting

Identify the shell/parent relationship, distinguish source from executable,
and point to the syscall that produced output. Name one fact the trace proves
and one containment claim it does not.

- Missing source: check `pwd` and the prepared workspace; do not edit `course/`.
- Compiler error: inspect the first diagnostic and the edited punctuation;
  do not continue using a stale binary.
- Different write grouping: compare buffering and bytes, not fixed addresses
  or an exact syscall count.
- Tracing denied: rerun preflight in the disposable VM. Do not use sudo,
  disable SELinux, or trace unrelated processes to force progress.

To discard this lesson only, return to the repository root, preview
`./lab-reset 01.01 --dry-run`, then confirm with `./lab-reset 01.01 --yes`
if the listed work is disposable. Reset removes its edits and binaries.

## Sources and scope

The Linux man-pages project's [execve](https://man7.org/linux/man-pages/man2/execve.2.html)
documents image replacement; [write](https://man7.org/linux/man-pages/man2/write.2.html)
documents partial transfers; [setvbuf](https://man7.org/linux/man-pages/man3/setbuf.3.html)
documents buffering. Consult `man strace`, `man ps`, and `man proc` in the guest
for the installed tools. Exact PIDs, namespace numbers, paths, and write
grouping are baseline observations, not universal constants.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-01-process-authority/lesson-02/README.md format=markdown -->
# 01.02 - Environment inheritance is authority

## Outcomes and prerequisites

Observe a child receiving data it never requested, replace its inherited
environment, and apply the same idea through C's explicit `envp` interface.
Complete B1's environment handoff and 01.01's compile/run/trace sequence first.

## Understand first

A new executable is not a clean slate. Its launcher supplies arguments and
environment entries during exec. Environment strings can affect configuration,
locale, command lookup, and application behavior. A program need not open a
file to receive a value the parent already copied into its environment.

B1 selected a Python mapping. Here we connect that mapping to the lower-level
array of `KEY=VALUE` strings received at exec, then practice the C interface
needed by the independent lab. A dictionary copy protects neither secrecy nor
authority: different containers can hold exactly the same values.

## Prepare and read the files

From the VM repository root:

```bash
./lab-start 01.02
cd .student/01.02
pwd
ls -l show-env.py launch-insecure.py clean-env.c FIXTURE.txt
cat show-env.py
cat launch-insecure.py
```

The preparation creates an editable copy and synthetic fixtures. Confirm
`.student/01.02` before continuing. The list locates each supplied file;
the two `cat` commands read Python source without executing it.

```python
#!/usr/bin/env python3
import os

print("DEMO_AGENT_TOKEN=" + os.environ.get("DEMO_AGENT_TOKEN", "<absent>"))
print("PATH=" + os.environ.get("PATH", "<absent>"))
```

`import os` provides access to the process environment. `get` returns the
named value or the chosen `<absent>` marker. String `+` joins the label and
value; `print` writes the result. This observer prints only our selected fake
setting and PATH, not every environment value. Never substitute a real secret.

```python
#!/usr/bin/env python3
import os
import subprocess

# Intentional mistake: copying the full parent environment copies its authority.
child_env = os.environ.copy()
subprocess.run(["python3", "show-env.py"], env=child_env, check=True)
```

`subprocess.run` launches the named interpreter and observer as separate argv
elements. `env` selects the child's environment and `check=True` raises an
exception if that child fails. Neither option validates the contents of the
copied mapping. Predict the observer's output before running either program.

## Exercise 1 - Observe the leak

The workspace `FIXTURE.txt` contains a randomized synthetic user. Export a fake token derived from it:

```bash
export DEMO_AGENT_TOKEN="fake-$(awk -F= '/fixture_id/{print $2}' FIXTURE.txt)"
python3 show-env.py
```

### Line by line

- `export` creates or replaces a shell variable and marks it for inheritance by later child processes.
- `DEMO_AGENT_TOKEN=...` names the deliberately fake variable used in this lesson.
- `$(...)` is command substitution: the shell runs the nested `awk` command and inserts its output into the surrounding string.
- `awk -F=` treats `=` as the field separator; the pattern `/fixture_id/` selects the matching line and `{print $2}` emits its value.
- `python3 show-env.py` starts a child process. Without an explicit environment, it inherits every exported variable from the shell.

Expected pattern:

```text
DEMO_AGENT_TOKEN=fake-...
```

The child did not open a credential store. The parent handed the value across `execve` in `envp`.

Confirm at the syscall boundary:

```bash
strace -f -e trace=execve python3 show-env.py 2>&1 | head -20
```

### Line by line

- `-f` follows any child processes Python creates; `-e trace=execve` keeps only program-execution transitions.
- `python3 show-env.py` is the command being traced, not an argument interpreted by `strace` itself.
- `2>&1` makes the syscall trace available to the pipeline.
- `head -20` limits display. A consumer that closes a pipe early can affect its writer; this short trace should fit within the limit, but use the unpiped command when investigating missing output.

Expected pattern: `execve` reports an environment count. `strace -v -s 200` can show more; do not use that option around real secrets.

## Exercise 2 - Make the intentional mistake

Run the starter launcher:

```bash
sed -n '1,160p' launch-insecure.py
python3 launch-insecure.py
```

### Line by line

- `sed` lets you inspect the launcher before trusting or executing it.
- `python3 launch-insecure.py` runs the parent launcher, which then creates the child shown in the source.

Expected: the token is still printed. Passing `env=os.environ.copy()` feels explicit but preserves every inherited variable.

### Launcher source, line by line

- `#!/usr/bin/env python3` lets an executable script locate Python through `PATH`; invoking `python3 file.py` does not depend on this line.
- `import os` exposes the current process environment; `import subprocess` exposes child-process creation.
- `os.environ.copy()` materializes every inherited environment key/value pair in a new dictionary. The copy prevents Python dictionary aliasing, not authority inheritance.
- `subprocess.run([...], env=child_env, check=True)` executes an argument vector without a shell, supplies that full dictionary as the child's environment, and raises an exception if the child exits nonzero.
- The list form `['python3', 'show-env.py']` keeps program and argument boundaries explicit.

### Observer source, line by line

- `os.environ.get("DEMO_AGENT_TOKEN", "<absent>")` reads one variable and substitutes the literal marker only when the key is missing.
- String `+` joins the label and observed value before `print` writes it.
- The second `print` performs the same check for `PATH`, which remains present in the allowlisted version.

Open `nano launch-insecure.py` in this workspace. Replace the copied environment
assignment with only:

```python
child_env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
```

### Line by line

- `child_env =` binds a new Python dictionary; it does not mutate the parent process's environment.
- `PATH` permits only the two named command-search directories.
- `LANG` gives child tools a predictable locale without copying unrelated parent variables.

Save with Ctrl+O, Enter, then exit with Ctrl+X. Run `cat launch-insecure.py`
to check the saved assignment, then `python3 launch-insecure.py`. Expected:
`DEMO_AGENT_TOKEN=<absent>`. Saving the editor buffer is separate from proving
the child received the intended mapping.

## Exercise 3 - Verify, do not assume

```bash
python3 launch-insecure.py | grep -F 'DEMO_AGENT_TOKEN=<absent>'
```

### Line by line

- The launcher writes its child's output to stdout.
- `|` passes that output to `grep`.
- `grep -F` performs a fixed-string match, so angle brackets and punctuation are treated literally rather than as a regular expression.
- A matching line gives `grep` exit status 0; no match gives a nonzero status.

Expected: one matching line and exit status 0. The control is an allowlisted environment constructed at the authority-transfer point, not a promise that children will ignore secrets.

## Exercise 4 - Express the handoff in C

Read the supplied bridge program before compiling it:

```bash
ls -l clean-env.c
cat clean-env.c
```

```c
#include <stdio.h>
#include <unistd.h>

int main(void) {
    char *arguments[] = {"env", NULL};
    char *environment[] = {"PATH=/usr/bin:/bin", "LANG=C.UTF-8", NULL};
    execve("/usr/bin/env", arguments, environment);
    perror("execve");
    return 1;
}
```

### Source, line by line

The headers declare diagnostics and `execve`. `char *arguments[]` is an array
of pointers to strings: each element points at the first character of one
argument. `NULL` ends the array; it is not the text `"NULL"`. The environment
array uses the same shape but contains `KEY=VALUE` strings. `execve` receives
an absolute executable path, the argument array, and this environment array.
Unlike `execvp`, it does not search PATH for the executable. A successful exec
never returns, so `perror` and `return 1` are reached only on failure.

```bash
cc -std=c11 -Wall -Wextra -O2 clean-env.c -o clean-env
DEMO_AGENT_TOKEN=synthetic-only ./clean-env
echo $?
```

The compile command creates the local executable. The shell prefix supplies
the fake token to the launcher. `/usr/bin/env` displays only `PATH=/usr/bin:/bin`
and `LANG=C.UTF-8`, with status 0; the launcher selected those strings instead
of inheriting its own environment. Output order is not the policy.

Changed-case practice: add another fake prefixed setting, such as
`NE_EXTRA_PRIVATE=also-fake`, to the same invocation. Predict and confirm its
absence without changing the program. Explain how an allowlist handles an
unknown parent name. This program deliberately launches one fixed observer;
the independent lab must preserve its general command/argument interface.

## Checkpoint, cleanup, and troubleshooting

Explain where Python's mapping becomes a child environment and how the C array
expresses the same choice. A successful command is not sufficient: check both
useful output and absence of the unwanted value.

- Missing interpreter: inspect `command -v python3`; do not restore the entire
  parent environment just to make command lookup work.
- Token still present: read the saved assignment and ensure you ran the edited
  launcher, not the direct observer.
- No observer output: run without grep and inspect stderr/status. An absent
  observation is not proof of a denied handoff.
- C compile failure: check quotes, commas, semicolons, and the NULL terminator.

Run `unset DEMO_AGENT_TOKEN` to remove the deliberately exported setting from
this shell. Return to the repository root for `./lab-reset 01.02 --dry-run`
and, when ready to discard your edits, `./lab-reset 01.02 --yes`.

## Sources and scope

[Python subprocess](https://docs.python.org/3.14/library/subprocess.html#subprocess.run)
documents replacement environments and child status;
[execve](https://man7.org/linux/man-pages/man2/execve.2.html) defines argv/envp
and image replacement. The guest's `man bash` ENVIRONMENT section describes
export and command-prefix assignments. Environment selection alone does not
close descriptors, restrict file access, or prevent the child from obtaining
data through other channels. The paths and two selected entries are course
policy on the Fedora/Ubuntu baselines, not a universal minimal environment.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-01-process-authority/lesson-03/README.md format=markdown -->
# 01.03 - File descriptors cross exec

## Outcomes and prerequisites

Observe an open descriptor surviving exec, prevent that inheritance, and
practice closing unknown extra descriptors. You need 01.01's C compile cycle
and 01.02's understanding that exec receives inherited state.

## Understand first

A pathname is a name to resolve. A descriptor is a small integer referring
to an already-open object. By convention, 0 is stdin, 1 is stdout, and 2 is
stderr. Other numbers are allocated as needed; descriptor 3 is common, not
a universal identifier for a protected file.

Opening performs pathname lookup and access checks. Later reads use the open
object without repeating that original lookup. A launcher can therefore hand
another program a reference that checking only future pathnames would miss.
We observe this channel using synthetic data, not an actual secret store.

## Prepare and read before executing

From the VM repository root:

```bash
./lab-start 01.03
cd .student/01.03
pwd
ls -l fd-parent.c fd-child.py close-extra.c .north-echo.json
cat fd-parent.c
cat fd-child.py
```

Confirm `.student/01.03`. The metadata file names this attempt's synthetic
fixture. The parent opens it; the observer tries existing descriptors.
Reading the files is not running them.

```c
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: %s PATH\n", argv[0]);
        return 2;
    }
    int fd = open(argv[1], O_RDONLY); /* Intentional mistake: no O_CLOEXEC. */
    if (fd < 0) {
        perror("open");
        return 1;
    }
    char *child[] = {"python3", "fd-child.py", NULL};
    execvp(child[0], child);
    perror("execvp");
    return 1;
}
```

`open` returns a descriptor or -1 on failure. The argument check requires one
pathname. `char *child[]` is an array of string pointers ending in NULL, as in
01.02. `execvp` searches PATH and replaces the program. Follow the error branch
first: a failed open must not be treated as an open reference.

```python
#!/usr/bin/env python3
import os

for fd in range(0, 32):
    try:
        target = os.readlink(f"/proc/self/fd/{fd}")
    except OSError:
        continue
    print(f"fd={fd} target={target}")
    if fd >= 3:
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            print(os.read(fd, 4096).decode(errors="replace"))
        except OSError:
            pass
```

The observer tests descriptor numbers 0-31. `readlink` asks procfs what each
reference names; `continue` skips unopened numbers. For numbers above 2,
`lseek` attempts to rewind a seekable object and `read` requests up to 4096
bytes. Ignoring errors for non-seekable or unreadable objects does not prove
they are harmless. This bounded observer is not a complete inventory algorithm.

## Exercise 1 - Observe descriptor authority

Build and run the intentionally vulnerable launcher. Use the randomized protected fixture created for this attempt:

```bash
cc -std=c11 -Wall -Wextra -O2 fd-parent.c -o fd-parent
./fd-parent "$(python3 -c 'import json; print(json.load(open(".north-echo.json"))["fixture_manifest"])')"
```

### Line by line

- `cc ... fd-parent.c -o fd-parent` compiles the launcher with warnings enabled and writes the binary named `fd-parent`.
- `python3 -c '...'` executes the quoted Python expression without creating another file.
- `open(".north-echo.json")` opens non-secret workspace metadata; `json.load(...)` parses it; `["fixture_manifest"]` selects the generated manifest path; `print(...)` writes that path.
- `$(...)` substitutes the printed path into the outer command.
- The double quotes around `$(...)` keep the entire pathname as one argument even if a directory name contains spaces.

Expected pattern: the child lists descriptors under `/proc/self/fd`; one descriptor points to `manifest.json`, and the child can read it without opening its pathname.

Inspect the source:

```bash
sed -n '1,220p' fd-parent.c
```

### Line by line

- `sed -n` suppresses automatic printing.
- `'1,220p'` prints source lines 1 through 220, which covers this intentionally small program.
- Reading before running is part of the exercise: identify the `open` and `execvp` authority-transfer points.

The intentional mistake is `open(..., O_RDONLY)` followed by `execvp` with no close and no close-on-exec flag.

### Parent source, line by line

- `#define _GNU_SOURCE` exposes GNU/Linux extensions such as `O_CLOEXEC` from the included headers.
- The four `#include` lines declare file flags, diagnostics, general utilities, and POSIX process functions.
- `argc` counts arguments and `argv` holds them; requiring `argc == 2` ensures exactly one pathname was supplied.
- `open(argv[1], O_RDONLY)` asks the kernel to resolve and open that pathname. The returned integer is process-local descriptor authority.
- `if (fd < 0)` handles failure before attempting an exec transition.
- `char *child[] = {..., NULL}` builds the NUL-terminated argument vector required by `execvp`.
- `execvp(child[0], child)` searches `PATH` for Python and replaces the current process image while retaining non-close-on-exec descriptors.
- Code after a successful `execvp` never runs; `perror` and `return 1` handle only failure.

### Child source, line by line

- `for fd in range(0, 32)` tests a bounded set of possible descriptor numbers.
- `os.readlink(f"/proc/self/fd/{fd}")` asks procfs what object a descriptor references; an `OSError` means that number is not open or not inspectable.
- The first `print` reports descriptor number and target.
- For descriptors 3 and above, `os.lseek` rewinds seekable objects and `os.read` attempts to consume bytes without reopening a pathname.
- The second `except OSError` deliberately tolerates descriptors that cannot seek or read. It does not prove those descriptors lack other authority.

## Exercise 2 - Fix at creation time

Open `nano fd-parent.c` in the workspace. Change the open flags to:

```c
O_RDONLY | O_CLOEXEC
```

### Line by line

- `O_RDONLY` requests a read-only descriptor.
- `|` is C's bitwise OR operator; it combines independent flag bits in one integer.
- `O_CLOEXEC` asks the kernel to set close-on-exec atomically when the descriptor is created, avoiding a window between `open` and a later `fcntl`.

Save with Ctrl+O, Enter, then Ctrl+X. Check with `cat fd-parent.c`, rebuild
with the same compiler command, and repeat the fixture invocation. Stop on
compiler errors. Expected: the manifest descriptor is absent after exec;
descriptors 0, 1, and 2 may remain. This flag does not prevent the parent
from using the descriptor before that exec transition.

## Exercise 3 - Verify the flag before exec

Add this immediately after `open` and before `execvp`:

```c
int flags = fcntl(fd, F_GETFD);
if (flags < 0) {
    perror("fcntl(F_GETFD)");
    return 1;
}
fprintf(stderr, "FD_CLOEXEC=%s\n", (flags & FD_CLOEXEC) ? "yes" : "no");
```

### Line by line

- `fcntl(fd, F_GETFD)` reads descriptor flags; the error branch stops before treating failure as a valid mask.
- `flags & FD_CLOEXEC` uses bitwise AND to test whether that specific bit is present.
- `condition ? "yes" : "no"` is C's conditional operator.
- `fprintf(stderr, ...)` sends the diagnostic to standard error, and `\n` terminates the line.

Rebuild. Expected: `FD_CLOEXEC=yes`, followed by no protected manifest in the child. `FD_CLOEXEC` affects the exec transition; it does not prevent the current process from using the descriptor.

Security conclusion: descriptors are capabilities to already-open kernel objects. Path checks and later filesystem policy do not retroactively erase them.

## Exercise 4 - Close descriptors already inherited

`O_CLOEXEC` helps when you control descriptor creation. A general launcher can
already have extra descriptors at startup. Closing only the number seen in
one run does not solve that case. Read the supplied bridge program:

```bash
ls -l close-extra.c
cat close-extra.c
```

```c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>

int main(void) {
    int descriptor = open("/dev/null", O_RDONLY);
    if (descriptor < 0) {
        perror("open");
        return 1;
    }
    printf("Opened descriptor: %d\n", descriptor);
    if (close_range(3, ~0U, 0) != 0) {
        perror("close_range");
        return 1;
    }
    errno = 0;
    int flags = fcntl(descriptor, F_GETFD);
    if (flags != -1 || errno != EBADF) {
        fprintf(stderr, "Expected the descriptor to be closed\n");
        return 1;
    }
    puts("Extra descriptor closed; stdout still works.");
    return 0;
}
```

### Source, line by line

`_GNU_SOURCE` exposes the installed libc's `close_range` declaration. The
headers declare errors, descriptor operations, diagnostics, and range closure.
The program opens only `/dev/null`, a harmless local device whose reads return
end-of-file, and stops if that open fails.

`close_range(3, ~0U, 0)` closes from descriptor 3 through the maximum unsigned
value. `U` makes zero unsigned; bitwise complement `~` sets all its bits. The
final zero requests immediate closure, not close-on-exec marking. Standard
streams 0-2 remain, and no specific extra descriptor number is assumed.

`errno = 0` clears the error indicator before the observation. `F_GETFD` should
then fail with `EBADF`, meaning that descriptor is not open. Checking both the
return and reason avoids treating any error as the expected one. The final
`puts` proves stdout still works.

```bash
cc -std=c11 -Wall -Wextra -O2 close-extra.c -o close-extra
./close-extra
echo $?
```

Expect an opened descriptor above 2, the closure confirmation, and status 0.
Using nano, temporarily remove only the `close_range` error-check block from
the workspace copy. Save, rebuild, and run: verification should now fail
because the descriptor remains open. Restore the block and confirm success.
Do not change the expected-error test to make an incomplete control pass.

The bridge closes descriptors but launches no arbitrary command and does not
alter the environment. The independent lab combines separate practiced skills.

## Checkpoint, troubleshooting, and reset

Explain preventing inheritance of a newly opened descriptor versus closing
extra descriptors already inherited. Why is a literal `close(3)` insufficient?

- Missing manifest: use this attempt's metadata, not a remembered old path.
- No initial leak: inspect flags and whether a resumed workspace was already
  repaired. Reset only if discarding those edits is intended.
- Different number: identify the target object, not just descriptor 3.
- `close_range` unavailable: check the supported VM kernel/libc; do not ignore
  the error and continue to launch a less-confined workload.

Return to the repository root for `./lab-reset 01.03 --dry-run`, then
`./lab-reset 01.03 --yes` when ready to discard the lesson's edits.

## Sources and scope

[open](https://man7.org/linux/man-pages/man2/open.2.html),
[execve](https://man7.org/linux/man-pages/man2/execve.2.html), and
[close_range](https://man7.org/linux/man-pages/man2/close_range.2.html) describe
creation, inheritance, and range closure. Range closure requires Linux 5.9+
and this wrapper requires glibc 2.34+; the Fedora/Ubuntu baselines supply them.
Removing a reference does not prove every other authority channel is closed
or prevent reopening a pathname the process can still access.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-01-process-authority/lab/README.md format=markdown -->
# Module 01 independent lab - Hygienic launcher

Build a small launcher for an untrusted local tool. This is independent work: the exact implementation is intentionally not provided.

## Preparation and planning

Before attempting this lab, complete 01.01-01.03. Use 01.02's explicit C environment array and 01.03's descriptor-closure exercise as mechanisms, not as a ready-made combined launcher. You are deciding how to preserve the command interface while removing unintended inputs.

A denylist for only one known variable meets a narrower goal than an environment allowlist. The randomized grader checks its synthetic token; it does not prove your policy removes every possible sensitive variable. State the policy you actually implemented. Likewise, checking only descriptor 3 is not closing all unknown descriptors above 2.

From the course root:

```bash
./lab-start module-01
cd .student/01.lab
pwd
ls -l launcher.c
cat launcher.c
nano launcher.c
```

`lab-start` creates your editable lab copy. The next three commands enter it and confirm the source name; `cat` reads it, and `nano` opens it for editing. Save with `Ctrl-O`, `Enter`, then leave with `Ctrl-X`. Work only in this student copy. The canonical starter is deliberately incomplete:

```c
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s COMMAND [ARG ...]\n", argv[0]);
        return 2;
    }

    /* Intentional starter flaw: authority is transferred without hygiene. */
    execvp(argv[1], &argv[1]);
    perror("execvp");
    return 1;
}
```

The feature-test macro appears before headers. `stdio.h` supplies diagnostics; `unistd.h` supplies `execvp`. `argc` counts arguments, including the launcher name. The usage block rejects a missing child command. `argv[1]` names that command, while `&argv[1]` forwards its complete argument vector. Successful `execvp` never returns; `perror` and the final nonzero return handle failure. The starter preserves this interface but omits the stated security controls.

## Contract

Edit `launcher.c`. The grader will compile it with a C11 compiler, then invoke it as:

```text
./launcher COMMAND [ARG ...]
```

Your launcher must:

- execute the requested command and preserve its normal stdout/stderr;
- ensure the synthetic variable `NE_LAB_TOKEN` is absent in the executed program;
- ensure every inherited descriptor above 2 is closed before the executed program begins;
- return a nonzero status when it cannot launch the command;
- avoid printing environment values or protected data itself.

The grader changes the token, pathname, and inherited descriptor on every run. Hard-coded values cannot pass the security properties.

## Workflow

```bash
cc -std=c11 -Wall -Wextra -O2 launcher.c -o launcher
./launcher /usr/bin/printf 'child works\n'
../../lab-grade module-01
```

### Test commands, line by line

- `cc` compiles only your current `launcher.c`; the warning flags help catch interface mistakes before grading.
- `./launcher /usr/bin/printf ...` checks the required `COMMAND [ARG ...]` interface with an absolute, harmless command.
- `../../lab-grade module-01` moves no files: the relative path simply reaches the repository's grader from `.student/01.lab`.
- The starter's `execvp(argv[1], &argv[1])` preserves argument boundaries and demonstrates basic execution, but intentionally performs no authority hygiene. The guided lessons contain the required concepts; this lab does not state their complete implementation.

Run the final command from the repository root instead if your shell is not in this workspace:

```bash
./lab-grade module-01
```

Practice mode names failed properties and points back to practiced lessons. Exam mode reports only failed properties:

```bash
./lab-grade module-01 --mode exam
```

- `--mode exam` changes diagnostic detail only. It does not weaken or replace any property check.

## Interpret your result and replay

Run the starter once before editing and record which security properties fail. A compile error is not an observed security denial, and a missing child is not successful containment. After your repair, use both a harmless successful command and a deliberately nonexistent absolute command; the latter must produce a nonzero launcher status.

For the practice grader, read each failed property and revisit its lesson before changing code. Do not alter the grader, canonical files, or generated fixture to force a pass. Passing establishes only the tested contract, not a production-ready sandbox.

From this workspace, `cd ../..` returns to the course root. `./lab-reset module-01` discards this module's student work and generated fixtures after confirmation; copy any notes you want to retain first. Then `./lab-start module-01` creates a fresh randomized attempt. No saved implementation is supplied by this manual.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-02-namespaces/README.md format=markdown -->
# Module 02 - Linux namespaces

Namespaces change which kernel objects a process sees. They do not automatically remove capabilities, filter syscalls, limit resources, or make a complete sandbox.

Play in order: `02.01`, `02.02`, `02.03`, then `module-02`.

## Learning route and limits

Prerequisites: Module 01. Continue as your ordinary account inside the disposable Linux VM. The guided lessons introduce their new syntax and interfaces before the independent lab combines them.

02.01 introduces namespace handles and identity maps. 02.02 changes a child hostname while preserving the parent's and practices argument forwarding through a shell. 02.03 shows why changing PID numbering without replacing procfs creates contradictory observations.

Ask which namespace of which type, not merely whether a process is in a container. Explain why inside UID 0 is not global root, why PID 1 is namespace-relative, and why a fresh PID namespace needs a matching procfs view. Here the parent environment is the VM, not the Mac.

Before moving on, demonstrate both useful allowed work and the intended restriction, and explain the difference in your own words. A failed compiler command or missing input is not a security success. Use the independent lab's practice feedback to revisit a specific lesson; passing checks does not replace understanding or make the combined program production-ready.
<!-- /source -->

## Module outcome and mental model

Namespaces change what a process sees when it uses particular kernel interfaces. They do not form one all-or-nothing container switch. Each namespace type isolates a resource view, and useful containment requires deliberate composition.

- A **user namespace** changes how user and group IDs and capabilities are interpreted.
- A **UTS namespace** isolates hostname and domain-name state.
- A **PID namespace** changes visible process IDs and the process tree.
- A **mount namespace** isolates mount-table changes.
- A **network namespace** isolates interfaces, routes, ports, and network stacks.
- An **IPC namespace** isolates selected System V IPC and POSIX message queues.
- A **cgroup namespace** changes the cgroup hierarchy view; it does not impose resource limits by itself.

Two verification questions apply to every namespace exercise:

- Did the target process receive a namespace handle different from the observer's handle?
- Does the resource view actually match the intended namespace?

The first question checks membership. The second catches stale mounts, incorrect ordering, and a command that mentions `unshare` without achieving the required state.

> **Safety boundary:** These exercises depend on unprivileged user namespaces. If the VM disables them, enable them in the disposable VM. Do not switch to a work host or run the course as host root to force progress.

<!-- PAGEBREAK -->

<!-- source: course/module-02-namespaces/lesson-01/README.md format=markdown -->
# 02.01 - Read namespace identity

## Goals

- Record baseline namespace handles.
- Create a mapped user namespace as an ordinary user.
- Interpret namespace-local UID 0 without confusing it with host root.
- Read the UID mapping that connects inside and outside identities.

## Before you start

Complete Module 01 first. Work as your ordinary user inside the disposable Linux VM. In this chapter, **parent** means the surrounding VM environment, not your Mac. None of these commands belong in the Mac terminal.

A namespace is a kernel object that gives member processes a particular view of one category of state. Joining a UTS namespace changes hostname state; joining a PID namespace changes process-number visibility. A user namespace also defines how user and group IDs map to the parent. Creating one kind does not create all the others.

`/proc` is a kernel-provided filesystem, not a collection of saved reports. `/proc/self` refers to the process accessing it. Thus the `readlink` child below inspects its own membership, inherited from your shell. A namespace handle such as `user:[4026531837]` identifies an object; it is not a user ID and its exact number is not a learning target.

From the course root:

```bash
./lab-start 02.01
cd .student/02.01
pwd
ls -l
```

`lab-start` prepares the editable workspace. `cd` enters it, `pwd` confirms where you are, and `ls -l` shows its contents. This lesson uses shell commands; there is no hidden program you need to find or compile.

## Exercise 1 - Capture the baseline

```bash
printf '%-8s %s\n' TYPE HANDLE
for ns in user uts pid mnt net ipc cgroup; do
  printf '%-8s %s\n' "$ns" "$(readlink /proc/self/ns/$ns)"
done
```

## What each line does

- The first `printf` emits headings. `%-8s` left-aligns a string in an eight-character field.
- `for ns in ...; do` begins a loop and assigns each listed namespace name to `ns` in turn.
- `readlink /proc/self/ns/$ns` asks procfs for this process's handle for the current type.
- `$(...)` substitutes that handle into `printf`.
- Quotes around both expansions preserve one argument per value.
- `done` ends the loop.

Expected shape:

```text
TYPE     HANDLE
user     user:[4026531837]
uts      uts:[4026531838]
pid      pid:[4026531836]
mnt      mnt:[4026531841]
net      net:[4026531992]
ipc      ipc:[4026531839]
cgroup   cgroup:[4026531835]
```

Exact numbers vary. Equal handles mean two processes refer to the same namespace object for that type; unequal handles mean different membership.

## Exercise 2 - Create a mapped user namespace

```bash
unshare --user --map-root-user sh -c '
  echo "inside uid=$(id -u)";
  readlink /proc/self/ns/user;
  cat /proc/self/uid_map
'
```

## What each line does

- `unshare` creates requested namespaces for the command that follows.
- `--user` requests a new user namespace.
- `--map-root-user` maps the invoking ordinary identity to UID and GID 0 inside it.
- `sh -c` starts a shell whose program is the following quoted string.
- Single quotes keep the outer shell from expanding `$(id -u)` or interpreting inner newlines.
- Inside, `id -u` prints the namespace-visible effective UID.
- `readlink` records the new user namespace handle.
- `uid_map` describes how ranges of inside UIDs translate to parent-namespace UIDs.

Typical mapping shape:

```text
inside uid=0
user:[4026532777]
         0       1000          1
```

The mapping line means one ID beginning at inside UID 0 maps to parent UID 1000. The parent value will match your ordinary VM account, not necessarily 1000.

## Exercise 3 - Disprove “UID 0 means global root”

```bash
unshare --user --map-root-user sh -c 'id; ls /root'
```

## What each part does

- The namespace flags reproduce the mapped identity.
- `;` runs the second inner command whether or not `id` succeeds.
- `id` reports namespace-relative UID 0.
- `ls /root` attempts a read-only directory listing through the existing VM filesystem.
- On the course image, `/root` is not readable by your ordinary account. The expected permission denial shows that namespace-local UID 0 did not grant that access. If an administrator made `/root` world-readable, this particular test would not demonstrate a denial; inspect permissions instead of changing them.

User namespaces can grant a process capabilities over resources owned by the new namespace. They do not grant corresponding power over parent-owned resources. A complete identity statement therefore includes the numeric IDs, the user namespace handle, and the ID mappings.

## Troubleshooting and checkpoint

- `Operation not permitted` usually means unprivileged user namespaces are disabled by VM policy.
- An empty or surprising map means the mapping helper failed; inspect stderr instead of assuming root was created.
- Never interpret `id -u` alone as a privilege proof.
- You should be able to compare two namespace handles and explain the three columns in `uid_map`.

Before continuing, predict whether creating only a user namespace also changes the UTS handle. Repeat the baseline loop inside the quoted child command to test your prediction. The repair to the mistaken "root everywhere" interpretation is to record the mapping and namespace, not to add `sudo`.

The child namespace is released when its last process/reference disappears. No global setting needs undoing. To discard lesson work, return to the course root with `cd ../..` and run `./lab-reset 02.01`; that reset deliberately removes this lesson's workspace.

## Source truth

The identity and mapping model is documented in [user_namespaces(7)](https://man7.org/linux/man-pages/man7/user_namespaces.7.html); the command flags are documented in [unshare(1)](https://man7.org/linux/man-pages/man1/unshare.1.html). These explain the mechanism, while the observations above establish what your VM actually allowed.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-02-namespaces/lesson-02/README.md format=markdown -->
# 02.02 - Change UTS state without changing the host

## Goals

- Isolate hostname state in a UTS namespace.
- Understand why namespace creation and authority to modify its state are separate concerns.
- Compare host and child state before and after the change.
- Inspect a live process from another terminal.

## Exercise 1 - Baseline, change, and proof

Complete 02.01 first. A UTS namespace stores a hostname and NIS domain name. It does not create a new network stack, DNS service, or machine. The hostname starts as a copy; changing the copy must leave the parent VM's hostname unchanged.

From the course root, prepare this shell-only lesson:

```bash
./lab-start 02.02
cd .student/02.02
pwd
ls -l
```

The first command creates the student workspace; the next three enter and inspect it. There is no source file to compile. Predict the two `host` lines before running the next block: they should be identical. Here "host" means the parent VM environment, not the Mac.

```bash
HOST_BEFORE=$(hostname)
echo "host before=$HOST_BEFORE"
unshare --user --map-root-user --uts sh -c '
  echo "inside before=$(hostname)";
  hostname north-echo-lab;
  echo "inside after=$(hostname)";
  readlink /proc/self/ns/uts
'
echo "host after=$(hostname)"
```

## What each line does

- The first command substitution captures the parent-visible hostname.
- The variable is local to this shell unless exported.
- `--user --map-root-user` creates namespace-local capability; `--uts` creates an isolated UTS view.
- Single quotes defer inner `hostname` substitutions until the child shell runs.
- The first inner line observes the initial copied hostname.
- `hostname north-echo-lab` changes only the new UTS namespace.
- The second inner observation proves the new value.
- `readlink` records the namespace identity associated with that state.
- The final line runs back in the parent after `unshare` exits and proves the host value is unchanged.

Expected relationship:

```text
host before=<vm hostname>
inside before=<vm hostname>
inside after=north-echo-lab
uts:[different handle]
host after=<same vm hostname>
```

The mapped user namespace gives the process the relevant capability inside the newly owned UTS namespace. It does not create host authority.

## Exercise 2 - Make the incomplete attempt

```bash
unshare --uts hostname broken-attempt
```

- `--uts` requests only a UTS namespace.
- `hostname broken-attempt` is the command to run inside it.
- An ordinary user generally lacks the capability needed for this setup without the mapped user namespace.
- Expected: `Operation not permitted` and no host change.

The failure is useful. Creating a namespace type does not automatically supply every credential needed to configure it.

## Exercise 3 - Inspect a live namespace

In terminal one:

```bash
unshare --user --map-root-user --uts sh -c 'hostname north-echo-hold; echo $$; sleep 60'
```

- The flags create the temporary user and UTS namespaces.
- `hostname` assigns a recognizable value.
- `echo $$` prints the shell's PID as seen from the parent namespace running the terminal.
- `sleep 60` keeps the process and namespace alive. `Ctrl-C` ends it early.

Open a second terminal and enter the **same VM**, using the same `limactl shell INSTANCE_NAME` command you used for terminal one. Do not run the following inspection on the Mac or in a different VM. For example, if the first command printed `12345`, replace `PRINTED_PID` below with `12345`; do not type the placeholder literally. In terminal two:

```bash
readlink /proc/PRINTED_PID/ns/uts
readlink /proc/self/ns/uts
```

- The first line observes the held process's UTS namespace.
- `/proc/self` in the second terminal refers to the inspecting process.
- Different handles prove different membership even if both hostnames happened to contain the same text.

Verification should inspect effective state, not merely search a script for the word `unshare`.

## Exercise 4 - Preserve an argument vector through a shell

The independent lab will accept a command and its arguments. A shell wrapper must preserve their boundaries, including arguments containing spaces. Practice that separately from namespace setup:

```bash
NE_PRACTICE_LABEL=example sh -c '
  printf "label=%s script-name=%s\n" "$NE_PRACTICE_LABEL" "$0"
  exec "$@"
' practice-wrapper /usr/bin/printf '<%s>\n' 'two words' final
```

- The leading assignment puts a synthetic label in this child's environment. Reading a supplied value differs from hard-coding a particular fixture value.
- `sh -c` consumes one argument as its program. The next, `practice-wrapper`, becomes `$0`, the shell's script name. It is **not** part of `$@`.
- The remaining arguments become `$1`, `$2`, and so forth. `"$@"` expands them as separate arguments, preserving the original boundaries.
- `exec` replaces the shell with that argument vector. It does not concatenate and reinterpret a command string.
- `/usr/bin/printf` receives its format followed by two data arguments. Expect `<two words>` on one line and `<final>` on another.

Deliberately change `exec "$@"` to `exec $@` in the command you type and repeat. The unquoted expansion splits `two words` into separate arguments: the output becomes three data lines. Restore the quotes and verify two lines again. This error can be invisible when every test argument is a single word.

For a script file, the corresponding concepts are `#!/bin/sh` on the first line, `$1` for its first supplied argument, and `exec "$@"` to replace it. The starter in the independent lab shows that minimal script. Combine this practiced argument handling with the namespace controls yourself; do not turn the supplied command into text for another shell to parse.

## Troubleshooting and checkpoint

- If the first terminal exits before inspection, rerun with a longer harmless sleep.
- If `/proc/PRINTED_PID` is absent, confirm you used the host-visible PID and that the process is still alive.
- If the handles match, inspect the exact flags and quoting rather than changing the expected result.
- You should be able to state why the parent hostname remains unchanged.

Finish with `hostname` in terminal one after the child exits and compare it with `echo "$HOST_BEFORE"`. That comparison plus the different namespace handles is the checkpoint: a successful command alone does not prove isolation. The deliberately incomplete attempt in Exercise 2 is repaired by the mapped user namespace in Exercise 1, never by running the lesson as global root.

After the child exits, its private hostname disappears with the namespace. If you reset the workspace, run `cd ../..` followed by `./lab-reset 02.02` in terminal one; do not try to "restore" the parent hostname with a privileged command.

## Source truth

See [uts_namespaces(7)](https://man7.org/linux/man-pages/man7/uts_namespaces.7.html) for isolated hostname state and [user_namespaces(7)](https://man7.org/linux/man-pages/man7/user_namespaces.7.html) for the ownership-based capability check.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-02-namespaces/lesson-03/README.md format=markdown -->
# 02.03 - PID namespaces and the procfs mistake

## Goals

- Start a shell as PID 1 inside a new PID namespace.
- Observe why an inherited procfs can show the wrong process view.
- Compose PID and mount namespaces with a matching procfs.
- Recognize the responsibilities assigned to namespace PID 1.

## Exercise 1 - Create the incomplete setup

Complete 02.01 and 02.02 first. A PID is a process identifier **within a PID namespace**. The same process can have one number inside a child namespace and another in its parent. PID 1 is the first process in the child namespace and has special lifecycle responsibilities. A mount namespace separately controls which filesystem mounts are visible. We need both concepts because `ps` obtains its information from a mounted filesystem, `/proc`.

From the course root:

```bash
./lab-start 02.03
cd .student/02.03
pwd
ls -l
```

These commands prepare, enter, and inspect this shell-only workspace. There is no source file to open. Predict whether changing process numbering alone will automatically replace an existing `/proc` mount. Exercise 1 deliberately leaves that second control out.

```bash
unshare --user --map-root-user --pid --fork sh -c '
  echo "shell says pid=$$";
  ps -o pid,ppid,comm | head
'
```

## What each line does

- The mapped user namespace provides safe namespace-local authority.
- `--pid` creates a PID namespace for children, not retroactively for the calling `unshare` process.
- `--fork` creates the child that can enter the new PID namespace.
- The quoted shell runs as the namespace's first process and expands its own `$$`.
- `ps` obtains process data through the currently mounted `/proc`.
- `head` limits display but cannot correct the underlying view.

Expected surprise: the shell reports PID 1 while `ps` may show many host processes or numbers that do not agree. The PID namespace changed, but the inherited procfs mount still represents the parent PID namespace.

## Exercise 2 - Mount a matching procfs

```bash
unshare --user --map-root-user --pid --fork --mount --mount-proc sh -c '
  echo "shell says pid=$$";
  ps -o pid,ppid,comm;
  echo "pid namespace=$(readlink /proc/self/ns/pid)";
  echo "mount namespace=$(readlink /proc/self/ns/mnt)"
'
```

## What each line does

- `--mount` isolates mount-table changes from the parent.
- `--mount-proc` mounts a fresh procfs associated with the new PID namespace.
- `--pid --fork` creates and enters the PID namespace in the required child.
- The shell sees itself as PID 1.
- `ps` now reads the fresh procfs, so its process list should agree with the namespace-local IDs.
- The two `readlink` calls record both namespace identities.

Expected: a small process list containing the shell and observation tools, plus new PID and mount handles. Process counts can vary because `ps`, shells, and pipelines briefly create processes.

## Exercise 3 - Wait for a known child

```bash
unshare --user --map-root-user --pid --fork --mount --mount-proc sh -c '
  (exit 7) &
  child=$!
  wait "$child"
  result=$?
  echo "waited for child=$child status=$result"
  ps -o pid,ppid,stat,comm
'
```

## What each line does

- Parentheses create a subshell; `exit 7` gives it a recognizable nonzero status.
- `&` runs that subshell asynchronously.
- `$!` gives the last background child's PID; save it immediately rather than guessing it from the process list.
- `wait "$child"` collects the status for that child. The shell may already have reaped it internally; `wait` still retrieves the saved result.
- Save `$?` before another command replaces it. The expected status is 7, not a namespace failure.
- The final `ps` shows the remaining processes. Do not expect the exited child to remain in the list.

This demonstrates waiting for a known direct child. It does **not** test orphan adoption, zombie accumulation, or a general-purpose init implementation. A shell may automatically reap children, so a snapshot with no `Z` rows is not proof that an arbitrary application is a suitable init.

Namespace PID 1 has special signal behavior and becomes the adopter for orphaned descendants. A production runtime normally supplies a small init/reaper instead of casually making an arbitrary workload PID 1.

## Why namespace composition matters

A PID namespace without a matching procfs produces contradictory observations. A UTS namespace without suitable namespace-local authority may not be configurable. A mount namespace does not automatically create a private filesystem tree. Namespaces isolate selected views; they are components, not a complete sandbox policy.

## Troubleshooting and checkpoint

- If `--mount-proc` fails, confirm the mapped user namespace was created and the util-linux `unshare` version supports it.
- If `ps` shows the host, compare the mount namespace handle and inspect the active `/proc` mount.
- Do not grade by exact process count; grade by namespace relationships and the procfs view.
- You should be able to explain why `$$` and `ps` disagreed in the incomplete setup.

For your checkpoint, describe the missing control in Exercise 1, run the repaired Exercise 2, and explain why a changed PID handle alone would be insufficient evidence. Never change the VM's real `/proc` mount to repair this lesson. The private mounts vanish with their namespace after the command ends.

To discard the workspace, return with `cd ../..` and run `./lab-reset 02.03`. This does not erase other lessons.

## Source truth

See [pid_namespaces(7)](https://man7.org/linux/man-pages/man7/pid_namespaces.7.html) for PID 1, visibility, and procfs relationships; [unshare(1)](https://man7.org/linux/man-pages/man1/unshare.1.html) for `--fork` and `--mount-proc`; and the VM's `help wait` for the shell builtin.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-02-namespaces/lab/README.md format=markdown -->
# Module 02 independent lab - Namespace launcher

Implement `sandbox.sh` so it launches an arbitrary command in fresh user, UTS, PID, and mount namespaces.

## Preparation and planning

Complete 02.01-02.03 first. This lab combines controls you have observed separately: identity mapping in 02.01, UTS state and argument forwarding in 02.02, and PID/mount/procfs relationships in 02.03. Your job is to order those controls and preserve the caller's interface.

The command must become PID 1, not a child of a shell that unnecessarily remains PID 1. Explain where process replacement is needed before implementing it. An unchanged hostname by itself does not prove shared membership, and a different hostname by itself does not prove separate membership; verify handles as well.

From the course root:

```bash
./lab-start module-02
cd .student/02.lab
pwd
ls -l sandbox.sh
cat sandbox.sh
nano sandbox.sh
```

`lab-start` creates your editable lab copy. The next three commands enter it and confirm the source name; `cat` reads it, and `nano` opens it for editing. Save with `Ctrl-O`, `Enter`, then leave with `Ctrl-X`. Work only in this student copy. The canonical starter is deliberately incomplete:

```bash
#!/bin/sh
set -eu

if [ "$#" -eq 0 ]; then
  echo "usage: $0 COMMAND [ARG ...]" >&2
  exit 2
fi

# Intentional starter flaw: this does not create any isolation.
exec "$@"
```

The interpreter line selects `sh`. `set -eu` enables exit-on-error behavior and errors for unset expansions; neither creates a sandbox. `$#` counts supplied arguments. The `if` block rejects an empty interface, writes usage to stderr with `>&2`, and exits 2. `exec "$@"` preserves arguments and replaces the script, but all namespace setup is missing. Read 02.02's argument-vector exercise before modifying this line.

## Contract

The grader invokes:

```text
NE_EXPECTED_HOSTNAME=randomized-value ./sandbox.sh COMMAND [ARG ...]
```

The launched command must observe:

- the randomized hostname from `NE_EXPECTED_HOSTNAME`;
- a UTS namespace distinct from the grader;
- a PID namespace distinct from the grader, with the command running as namespace PID 1;
- a mount namespace distinct from the grader;
- a procfs that reflects the new PID namespace;
- the command's stdout, stderr, arguments, and exit status.

Do not hard-code a hostname. Do not change the host hostname or mount table. This lab expects an ordinary user in the disposable VM with unprivileged user namespaces enabled.

Useful interfaces have all appeared in the guided lessons. The grader reports properties, not an implementation recipe.

```bash
chmod +x sandbox.sh
./sandbox.sh sh -c 'echo "pid=$$ host=$(hostname)"; ps -o pid,ppid,comm'
../../lab-grade module-02
```

### Test commands, line by line

- `chmod +x sandbox.sh` adds the executable permission needed for the kernel to launch the script directly.
- `./sandbox.sh sh -c '...'` supplies `sh` as the arbitrary command under test; the quoted program observes namespace-local PID, hostname, and procfs state.
- `$$` and `$(hostname)` are intentionally inside single quotes, so the outer shell does not expand them before the sandbox runs.
- `../../lab-grade module-02` invokes the external randomized property grader from the generated workspace.
- The starter's `exec "$@"` preserves the caller's argument vector but creates no namespaces. `$@` is quoted so each original argument stays separate.

## Interpret your result and replay

Run the starter once before editing and record which security properties fail. A compile error is not an observed security denial, and a missing child is not successful containment. After your repair, use both a harmless successful command and a deliberately nonexistent absolute command; the latter must produce a nonzero launcher status.

For the practice grader, read each failed property and revisit its lesson before changing code. Do not alter the grader, canonical files, or generated fixture to force a pass. Passing establishes only the tested contract, not a production-ready sandbox.

From this workspace, `cd ../..` returns to the course root. `./lab-reset module-02` discards this module's student work and generated fixtures after confirmation; copy any notes you want to retain first. Then `./lab-start module-02` creates a fresh randomized attempt. No saved implementation is supplied by this manual.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-03-privilege/README.md format=markdown -->
# Module 03 - Privilege, capabilities, and no_new_privs

You will inspect the actual privilege state carried by a process, remove capability channels, and set a one-way privilege floor before `execve`.

Play in order: `03.01`, `03.02`, `03.03`, then `module-03`.

## Learning route and limits

Prerequisites: Module 02. Continue as your ordinary account inside the disposable Linux VM. The guided lessons introduce their new syntax and interfaces before the independent lab combines them.

03.01 inventories identity and all five capability sets. 03.02 contrasts partial and complete changes, then practices current-set reduction in C. 03.03 installs and observes the inherited no_new_privs restriction.

Separate current authority from the possibility of gaining privilege when executing another file. Explain why a capability-empty process can still read its own files or use inherited descriptors. Do not make setuid binaries, install file capabilities, or run this lab as global root.

Before moving on, demonstrate both useful allowed work and the intended restriction, and explain the difference in your own words. A failed compiler command or missing input is not a security success. Use the independent lab's practice feedback to revisit a specific lesson; passing checks does not replace understanding or make the combined program production-ready.
<!-- /source -->

## Module outcome and mental model

Linux privilege is not a Boolean “root or not root” value. A process's authority can depend on:

- real, effective, saved, and filesystem user and group IDs;
- supplementary groups;
- the effective, permitted, inheritable, bounding, and ambient capability sets;
- the owning user namespace and its ID mappings;
- file capabilities and set-user-ID or set-group-ID transitions;
- the `no_new_privs` bit;
- open descriptors and other authority channels from earlier modules.

Capabilities split many traditional root powers into named bits. That improves precision, but it creates several interacting sets that must be observed separately.

- **Effective:** bits currently considered for capability checks.
- **Permitted:** capabilities the thread may make effective.
- **Inheritable:** input to capability calculations across exec when file capability rules participate.
- **Bounding:** a ceiling that limits capabilities obtained during exec.
- **Ambient:** selected capabilities that can survive exec of ordinary non-privileged programs.

`no_new_privs` adds a one-way rule: an exec transition may not grant privileges the process did not already possess. It does not remove current authority by itself.

<!-- PAGEBREAK -->

<!-- source: course/module-03-privilege/lesson-01/README.md format=markdown -->
# 03.01 - UIDs are not the whole privilege story

## Goals

- Read complete UID, GID, group, capability, and `no_new_privs` state from procfs.
- Decode a hexadecimal capability mask.
- Compare ordinary identity with namespace-local root.
- Find file capabilities that complicate simplistic UID reasoning.

## Exercise 1 - Inspect current credentials

Complete Module 02 first. A UID identifies an account within a user namespace; it is not a complete privilege inventory. Linux splits many traditional root powers into **capabilities**. Each named capability corresponds to a bit in several per-thread sets. Hexadecimal is simply a compact way of writing those bits; you do not need to memorize the numbers.

- **Effective:** capabilities currently considered for capability checks.
- **Permitted:** capabilities the thread may make effective.
- **Inheritable:** a set that participates in capability calculations across execution.
- **Bounding:** a ceiling that limits capability acquisition through file capabilities across execution; it is not the currently effective set.
- **Ambient:** capabilities preserved across execution of ordinary, non-privileged programs, subject to the kernel's rules.

The four `Uid` columns are real, effective, saved-set, and filesystem UID. The analogous `Gid` columns describe group IDs; `Groups` lists supplementary groups. Keep these concepts separate from capabilities and from `NoNewPrivs`, which Lesson 03.03 introduces as a restriction on future execution transitions.

From the course root:

```bash
./lab-start 03.01
cd .student/03.01
pwd
ls -l
```

This prepares and locates the shell-only lesson. No C program is needed yet. Before inspecting, predict whether an ordinary account can have a nonzero bounding set while its effective set is empty.

```bash
id
grep -E '^(Uid|Gid|Groups|Cap(Inh|Prm|Eff|Bnd|Amb)|NoNewPrivs):' /proc/self/status
```

## What each line does

- `id` summarizes the invoking process's user, primary group, and supplementary groups.
- `grep -E` enables extended regular-expression syntax.
- `^` requires a match at the start of a line.
- The outer alternatives select identity, groups, capabilities, or `NoNewPrivs`.
- `Cap(Inh|Prm|Eff|Bnd|Amb)` matches the five capability fields without repeating the prefix.
- `/proc/self/status` is generated by the kernel for the process opening it. The `grep` child inherits the shell's credentials for this observation.

Typical ordinary-user shape:

```text
Uid:    1000    1000    1000    1000
Gid:    1000    1000    1000    1000
Groups: 1000 ...
CapInh: 0000000000000000
CapPrm: 0000000000000000
CapEff: 0000000000000000
CapBnd: 000001ffffffffff
CapAmb: 0000000000000000
NoNewPrivs: 0
```

Values vary by VM and distribution. A nonzero bounding set does not mean those bits are currently effective; it records an upper bound for future transitions.

Decode the effective mask:

```bash
CAP_EFF=$(awk '/^CapEff:/{print $2}' /proc/self/status)
capsh --decode="$CAP_EFF"
```

## What each line does

- The `awk` pattern selects the line beginning `CapEff:`.
- `{print $2}` emits the second whitespace-delimited field, the hexadecimal mask.
- Command substitution stores it in `CAP_EFF`.
- `capsh --decode=` translates set bits into capability names.
- Quoting ensures even an empty or unusual expansion remains one argument.

For a zero mask, expect an empty decoded set. For nonzero masks, record each capability name instead of describing the process merely as “privileged.”

## Exercise 2 - Compare namespace-local root

```bash
unshare --user --map-root-user sh -c '
  id;
  grep -E "^(Uid|Cap(Inh|Prm|Eff|Bnd|Amb)):" /proc/self/status;
  capsh --print
'
```

## What each part does

- `unshare` creates a new user namespace and maps the ordinary caller to UID 0 inside it.
- The child `id` displays namespace-relative identity.
- The child `grep` prints UID and all capability fields.
- `capsh --print` provides a named description of capability and identity state in this child environment. The first exercise already taught decoding a single raw mask; using the built-in report here avoids a second layer of shell/awk quoting.
- Capability bits are meaningful relative to the user namespace that owns the target resource.

Expected: UID 0 and a set of capabilities inside the new user namespace, but no corresponding host-root authority.

## Exercise 3 - Disprove the nonzero-UID simplification

```bash
getcap -r /usr/bin 2>/dev/null | head
```

## What each part does

- `getcap` reads file capability extended attributes.
- `-r /usr/bin` walks that directory recursively.
- `2>/dev/null` discards expected permission or unsupported-file diagnostics. Do not suppress stderr while diagnosing an unexpected failure.
- `head` keeps the display short.

Some systems contain programs with file capabilities such as a narrowly scoped network capability; an empty result on your image is valid. Executing an appropriately attributed file can change capability state even when the caller's effective UID is not zero, unless restrictions such as `no_new_privs` prevent the gain. This command only reads attributes: do not add file capabilities to make a demonstration appear. A review must record IDs, groups, namespace mappings, capability sets, executable attributes, and inherited resources.

## Troubleshooting and checkpoint

- If `capsh` or `getcap` is missing, install the distribution's capability utilities package in the VM.
- Treat an all-zero `CapEff` as one observation, not proof that every authority channel is empty.
- Keep the namespace handle alongside the decoded bits when comparing processes.
- You should be able to explain why `CapBnd` may be nonzero while `CapEff` is zero.

The intentional mistake here is a conclusion: "nonzero UID means no privilege" or "zero effective capabilities means no authority." Repair that conclusion with the complete inventory and with Module 01's inherited-descriptor example. Your checkpoint is an explanation of why the inventory still does not answer which already-open resources are accessible.

No privilege attributes were changed in the parent shell. To discard lesson work, return with `cd ../..` and run `./lab-reset 03.01`.

## Source truth

The set definitions and execution rules come from [capabilities(7)](https://man7.org/linux/man-pages/man7/capabilities.7.html); namespace-relative scope comes from [user_namespaces(7)](https://man7.org/linux/man-pages/man7/user_namespaces.7.html). Use `man capsh` in the VM for its display format.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-03-privilege/lesson-02/README.md format=markdown -->
# 03.02 - Drop capability sets deliberately

## Goals

- Decode all five capability sets rather than reading only `CapEff`.
- Use `setpriv` to establish a capability-empty child.
- Observe why clearing only one set is an incomplete fix.
- Verify the resulting process rather than trusting requested flags.

## Exercise 1 - Decode every set

Complete 03.01 first. "Drop privilege" is a desired outcome, not an operation with one universal meaning. In this lesson you will remove capability channels, then inspect what the child actually received. This does not remove your ordinary account's access to its own files.

From the course root:

```bash
./lab-start 03.02
cd .student/03.02
pwd
ls -l
```

The commands prepare and locate your editable workspace. Start with the shell observations; a small C bridge later connects these observations to the independent launcher lab.

```bash
for field in CapInh CapPrm CapEff CapBnd CapAmb; do
  value=$(awk -v key="$field:" '$1==key{print $2}' /proc/self/status)
  printf '%-7s %s -> ' "$field" "$value"
  capsh --decode="$value"
done
```

## What each line does

- The loop assigns each procfs field name to `field`.
- `awk -v key="$field:"` passes the current field plus its colon into `awk`.
- `$1==key` performs exact first-field equality; `{print $2}` emits the mask.
- Command substitution stores the mask in `value`.
- `printf` aligns the name, prints the raw mask, and deliberately omits a newline.
- `capsh --decode` prints capability names and completes the record.
- `done` closes the loop.

Do not collapse the five results into one adjective. Ask which set controls present checks and which sets constrain or enable future exec transitions.

## Exercise 2 - Launch with empty sets

```bash
unshare --user --map-root-user setpriv \
  --bounding-set=-all \
  --inh-caps=-all \
  --ambient-caps=-all \
  sh -c 'grep -E "^(Groups|Cap(Inh|Prm|Eff|Bnd|Amb)):" /proc/self/status'
```

## What each line does

- The mapped user namespace supplies a safe environment for practicing privilege transitions.
- A trailing backslash tells the shell the same command continues on the next physical line.
- `setpriv` changes process privilege attributes before executing the final command.
- `--bounding-set=-all` subtracts every named capability from the bounding set.
- `--inh-caps=-all` clears the inheritable set.
- `--ambient-caps=-all` clears the ambient set.
- The final shell runs the procfs observation after the transitions and reports supplementary groups separately from capability state.

Expected:

```text
CapInh: 0000000000000000
CapPrm: 0000000000000000
CapEff: 0000000000000000
CapBnd: 0000000000000000
CapAmb: 0000000000000000
```

`setpriv` and the kernel perform linked capability calculations during execution, which is why the resulting permitted and effective sets are also observed rather than assumed.

The `Groups` line need not be empty. For the unprivileged single-ID mapping used here, `setgroups(2)` must be disabled before the GID map can be written. Adding `setpriv --clear-groups` after that transition therefore fails with `Operation not permitted` on the course baselines. Group reduction is a separate launcher responsibility that must happen at a boundary where the caller has authority to change its supplementary groups; this exercise isolates capability-set behavior instead of pretending the two controls are interchangeable.

## Exercise 3 - Make the partial fix

```bash
unshare --user --map-root-user setpriv --inh-caps=-all sh -c 'grep -E "^Cap(Inh|Prm|Eff|Bnd|Amb):" /proc/self/status'
```

- This changes only the inheritable set request.
- The final `grep` deliberately prints all sets.
- Expected: `CapInh` is zero, while other sets need not be empty.

The phrase “drop capabilities” is underspecified. Name every relevant set, state the intended postcondition, and verify the kernel-reported result.

## Exercise 4 - Clear current sets in C

The shell utility is useful for experiments, but the independent lab asks for a C launcher. Read this smaller fixed-purpose program before adapting the mechanism. It clears current capability sets and reports them; it does not implement the lab's arbitrary-command interface or `no_new_privs` control.

```bash
ls -l clear-current.c
cat clear-current.c
```

The first command confirms the file exists in `.student/03.02`; the second displays its complete contents. Open it with `nano clear-current.c` if you want to annotate your student copy.

```c
#define _GNU_SOURCE
#include <linux/capability.h>
#include <stdio.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(void) {
    struct __user_cap_header_struct header = {
        .version = _LINUX_CAPABILITY_VERSION_3,
        .pid = 0
    };
    struct __user_cap_data_struct data[2] = {0};

    if (prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_CLEAR_ALL, 0, 0, 0) != 0) {
        perror("clear ambient capabilities");
        return 1;
    }
    if (syscall(SYS_capset, &header, data) != 0) {
        perror("capset");
        return 1;
    }
    if (syscall(SYS_capget, &header, data) != 0) {
        perror("capget");
        return 1;
    }
    printf("effective=%08x%08x\n", data[1].effective, data[0].effective);
    printf("permitted=%08x%08x\n", data[1].permitted, data[0].permitted);
    printf("inheritable=%08x%08x\n", data[1].inheritable, data[0].inheritable);
    return 0;
}
```

### Read the program

- `_GNU_SOURCE` and the headers expose Linux's syscall numbers, capability structures, `prctl`, and diagnostics. This is Linux-specific C, not a portable POSIX capability API.
- The header's `version` selects the kernel's version-3 capability layout; `pid = 0` means the calling thread. The two data elements each represent 32 bits, covering the 64-bit interface.
- `= {0}` initializes every data field to zero, including effective, permitted, and inheritable masks. Uninitialized structures would not express an empty policy.
- `PR_CAP_AMBIENT_CLEAR_ALL` clears the separate ambient set. Any error stops the program. Ignoring an unsupported operation would silently weaken the intended postcondition.
- `syscall(SYS_capset, ...)` asks the kernel to replace the calling thread's current sets. glibc does not expose a normal `capset` wrapper; this small course example calls the kernel interface directly. Larger software should evaluate the higher-level libcap API.
- `SYS_capget` reads the actual state back into the same array. The program does not treat the requested zero-filled input as evidence that the transition worked.
- Each `printf` prints the high 32-bit half followed by the low half, with eight hexadecimal digits per half. The result is a comparable 16-digit mask, not two unrelated capabilities.
- A successful return here means the calls completed. Inspect the masks as well: effective, permitted, and inheritable must all be zero. The ambient-clear operation is separately checked for success.

Build and compare two starting contexts:

```bash
cc -std=c11 -Wall -Wextra -O2 clear-current.c -o clear-current
./clear-current
unshare --user --map-root-user ./clear-current
```

`cc` builds your current source. The direct invocation begins with the ordinary user's usually empty current sets. The second starts with namespace-local capabilities, then clears them inside the same process. Both should report three zero masks and return 0. No parent-shell capabilities are modified.

For an intentional failure, open `nano clear-current.c`, temporarily remove the entire `SYS_capset` error-check block, save with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. Recompile and repeat the **namespace** invocation. The masks are now nonzero even though the program may return 0. Restore the block, recompile, and verify zero again. This is why testing only an already-unprivileged input can miss a control that does nothing.

This program does not execute another file. Exec can recalculate capabilities, especially for UID 0; a current-state observation is not automatically a post-exec guarantee. Lesson 03.03 adds the restriction on privilege gain across exec. The independent lab preserves the ordinary invoking UID rather than manufacturing root.

## Capability caveats

- Clearing current sets does not close descriptors opened while capabilities were present.
- Dropping the bounding set is a one-way restriction for the process tree, but executable attributes and namespace context still need analysis.
- Supplementary groups are a separate authority channel.
- A zero capability mask does not restrict ordinary permissions granted by UID, GID, ACLs, or open resources.

## Troubleshooting and checkpoint

- If `setpriv` is missing, install util-linux in the disposable VM.
- If an option spelling differs, check the VM's util-linux version rather than silently omitting the property.
- If a transition fails, capture stderr and current sets before changing the exercise.
- You should be able to state which set is used for current checks and which set caps future acquisition across exec.

Repeat the complete Exercise 2 after the partial Exercise 3 and compare every field. Then verify the C bridge's repaired namespace case. These are separate checkpoints for the utility-based transition and the in-process C operation.

To discard student edits, return with `cd ../..` and run `./lab-reset 03.02`. A new child process gets its own starting credentials; do not try to restore a dropped bounding set within the same process.

## Source truth

See [capabilities(7)](https://man7.org/linux/man-pages/man7/capabilities.7.html), [capget/capset(2)](https://man7.org/linux/man-pages/man2/capget.2.html), and [PR_CAP_AMBIENT_CLEAR_ALL(2)](https://man7.org/linux/man-pages/man2/PR_CAP_AMBIENT_CLEAR_ALL.2const.html). `man setpriv` documents the installed utility's flags. Current-state reduction, exec-time restrictions, and supplementary-group changes are different mechanisms.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-03-privilege/lesson-03/README.md format=markdown -->
# 03.03 - Make privilege non-gainable

## Goals

- Set the one-way `no_new_privs` bit before exec.
- Observe that bit in the executed child and a grandchild.
- Understand why ordering around exec is a security property.
- Distinguish non-gainability from removal of existing authority.

## Exercise 1 - Build the launcher

Complete 03.01 and 03.02 first. A program can begin with little privilege but execute a file whose attributes would normally grant more. `no_new_privs` is a one-way promise enforced by the kernel: an exec transition must not grant privilege that was unavailable before that transition. It does not remove authority the process already has. Here we will observe the bit itself, not install a setuid program to demonstrate privilege gain.

From the course root:

```bash
./lab-start 03.03
cd .student/03.03
pwd
ls -l nnp-launch.c
cat nnp-launch.c
grep '^NoNewPrivs:' /proc/self/status
```

The first four commands prepare and locate the editable C source. `cat` opens its contents for reading without editing. The final command records your inherited baseline. If it already reports 1, the deliberate ordering error later cannot make it 0: the bit is sticky. Do not weaken the VM or try to unset it to force an expected screenshot.

Complete source:

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <sys/prctl.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s COMMAND [ARG ...]\n", argv[0]);
        return 2;
    }
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
        perror("prctl(PR_SET_NO_NEW_PRIVS)");
        return 1;
    }
    execvp(argv[1], &argv[1]);
    perror("execvp");
    return 1;
}
```

## Source, line by line

- `_GNU_SOURCE` requests GNU/Linux declarations before headers are included.
- `<stdio.h>` declares diagnostics; `<sys/prctl.h>` declares `prctl` and its operation constants; `<unistd.h>` declares `execvp`.
- `argc < 2` rejects a missing child command.
- The usage message describes the preserved `COMMAND [ARG ...]` interface.
- `prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)` asks the kernel to set the calling thread's one-way bit. The remaining zero arguments are unused for this operation.
- A nonzero return indicates failure, which must stop execution of untrusted code.
- `execvp(argv[1], &argv[1])` searches `PATH`, uses the requested command, and passes the command plus all remaining arguments as the new `argv`.
- `&argv[1]` points into the original pointer array instead of rebuilding it.
- The final diagnostic runs only when exec fails.

Build and observe:

```bash
sed -n '1,220p' nnp-launch.c
cc -std=c11 -Wall -Wextra -O2 nnp-launch.c -o nnp-launch
./nnp-launch sh -c 'grep -E "^(NoNewPrivs|CapEff):" /proc/self/status'
```

## What each line does

- `sed` displays the full small launcher before execution.
- The compile line selects C11, warnings, normal optimization, and the output name.
- Every token after `./nnp-launch` becomes the child command and arguments.
- `sh -c` executes the quoted observation after the launcher sets policy.
- The anchored expression selects only `NoNewPrivs` and `CapEff`.

Expected:

```text
NoNewPrivs:  1
CapEff:      0000000000000000
```

`NoNewPrivs: 1` is the required property. A zero effective set is an additional observation, not proof that every authority channel is empty.

## Exercise 2 - Make the ordering mistake

Open `nano nnp-launch.c`. Move the **entire** `if (prctl(...) != 0) { ... }` block to immediately after the `execvp` call, keeping its failure handling together. Save with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. Run `cat nnp-launch.c` to inspect the saved order, then repeat the compile and observation commands from Exercise 1.

- A successful exec replaces the launcher, so code after it is unreachable on the success path.
- The executed child therefore observes the old `NoNewPrivs` value, normally 0.
- Restore the complete block before exec, save, recompile, and rerun. The repaired child must report 1.

Security controls governing a transition must be established before that transition. Source presence is not enough; control-flow ordering is part of the property.

## Exercise 3 - Verify inheritance in a descendant

```bash
./nnp-launch sh -c 'sh -c "grep ^NoNewPrivs: /proc/self/status"'
```

## What each part does

- The launcher sets the bit and executes the first shell.
- The outer single quotes protect the inner command from the invoking shell.
- The first child shell launches another shell.
- The inner shell reads its own procfs status.
- Seeing 1 proves inheritance across more than one exec transition.

`no_new_privs` cannot be unset and is inherited across fork and exec. It prevents privilege gain from exec mechanisms such as set-user-ID and file capabilities. It does not close descriptors, scrub the environment, empty current capability sets, isolate files, restrict the network, or filter syscalls.

## Troubleshooting and checkpoint

- If `prctl` is undeclared, verify Linux headers and `_GNU_SOURCE` placement.
- If the child reports 0, inspect control-flow ordering before changing the probe.
- If the command does not launch, distinguish `prctl` failure from `execvp` failure using stderr.
- You should be able to explain both what `no_new_privs` guarantees and what it deliberately does not guarantee.

For the checkpoint, compare the repaired child and grandchild, then name two inherited authority channels this bit does not remove. If your initial baseline was already 1, say explicitly that the negative case was masked by an inherited restriction; do not claim you observed a 0-to-1 transition.

Reset only your lesson workspace from the course root: `cd ../..` then `./lab-reset 03.03`. The child set its own bit; the parent shell was not changed.

## Source truth

The kernel's [no_new_privs documentation](https://docs.kernel.org/userspace-api/no_new_privs.html) describes inheritance, irreversibility, and limits. [execve(2)](https://man7.org/linux/man-pages/man2/execve.2.html) explains why successful execution does not return to the old program.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-03-privilege/lab/README.md format=markdown -->
# Module 03 independent lab - Privilege floor

Implement `secure-launch.c`, a launcher that establishes a non-gainable, capability-empty privilege state before executing an arbitrary command.

## Preparation and planning

Complete 03.01-03.03 first. Map the contract to the earlier practice: read identity and all sets in 03.01, clear current sets in C in 03.02, and establish the pre-exec one-way bit in 03.03. The lab combines those pieces without giving you their final arrangement.

The ordinary-user grader typically begins with empty current capability sets. A pass on that input alone is not evidence that a missing clearing operation would handle a more privileged input. Use the namespace-local contrast practiced in 03.02 to understand that limitation; do not change the lab to run as VM root. The contract preserves the invoking account and does not require an empty bounding set or altered supplementary groups.

From the course root:

```bash
./lab-start module-03
cd .student/03.lab
pwd
ls -l secure-launch.c
cat secure-launch.c
nano secure-launch.c
```

`lab-start` creates your editable lab copy. The next three commands enter it and confirm the source name; `cat` reads it, and `nano` opens it for editing. Save with `Ctrl-O`, `Enter`, then leave with `Ctrl-X`. Work only in this student copy. The canonical starter is deliberately incomplete:

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s COMMAND [ARG ...]\n", argv[0]);
        return 2;
    }

    /* Intentional starter flaw: no privilege floor is established. */
    execvp(argv[1], &argv[1]);
    perror("execvp");
    return 1;
}
```

The feature-test macro appears before headers. `stdio.h` supplies diagnostics; `unistd.h` supplies `execvp`. `argc` counts arguments, including the launcher name. The usage block rejects a missing child command. `argv[1]` names that command, while `&argv[1]` forwards its complete argument vector. Successful `execvp` never returns; `perror` and the final nonzero return handle failure. The starter preserves this interface but omits the stated security controls.

## Contract

The grader compiles the file with C11 and invokes:

```text
./secure-launch COMMAND [ARG ...]
```

The executed command must observe:

- `NoNewPrivs: 1`;
- empty effective, permitted, inheritable, and ambient capability sets;
- the same real and effective UID as the ordinary user who invoked the launcher;
- normal command arguments, stdout/stderr, and exit behavior.

The lab must be run as an ordinary user in the disposable VM. Do not add setuid bits or file capabilities. Do not call an external shell to transform the command string.

All required interfaces were practiced in this module. The grader deliberately avoids line-level advice.

```bash
cc -std=c11 -Wall -Wextra -O2 secure-launch.c -o secure-launch
./secure-launch sh -c 'grep -E "^(Uid|CapInh|CapPrm|CapEff|CapAmb|NoNewPrivs):" /proc/self/status'
../../lab-grade module-03
```

### Test commands, line by line

- `cc` builds your C11 launcher with warnings and normal optimization.
- `./secure-launch sh -c 'grep ...'` uses the required arbitrary-command interface and observes the executed child's real state from procfs.
- The anchored regular expression selects only identity, capability, and no-new-privileges fields.
- `../../lab-grade module-03` compiles a fresh evaluation binary and runs a separate probe.
- The starter's `execvp(argv[1], &argv[1])` correctly forwards the command and arguments but intentionally establishes no privilege floor. The exact repair remains independent work.

## Interpret your result and replay

Run the starter once before editing and record which security properties fail. A compile error is not an observed security denial, and a missing child is not successful containment. After your repair, use both a harmless successful command and a deliberately nonexistent absolute command; the latter must produce a nonzero launcher status.

For the practice grader, read each failed property and revisit its lesson before changing code. Do not alter the grader, canonical files, or generated fixture to force a pass. Passing establishes only the tested contract, not a production-ready sandbox.

From this workspace, `cd ../..` returns to the course root. `./lab-reset module-03` discards this module's student work and generated fixtures after confirmation; copy any notes you want to retain first. Then `./lab-start module-03` creates a fresh randomized attempt. No saved implementation is supplied by this manual.
<!-- /source -->

<!-- PAGEBREAK -->

# Integrated understanding

## How the first three modules compose

A minimally disciplined local launcher now has several separate responsibilities:

```text
parent process
  -> select arguments without accidental shell parsing
  -> construct an allowlisted environment
  -> close or mark unwanted descriptors close-on-exec
  -> create and configure namespace views
  -> reduce groups and capability channels
  -> set no_new_privs
  -> exec the workload
  -> verify the workload's effective state externally
```

Ordering matters. A descriptor opened before confinement can bypass later path restrictions. A `prctl` after exec never runs on success. A PID namespace paired with the old procfs gives a contradictory view. A copied environment preserves unknown parent authority.

No single observation proves complete containment. Instead, define properties and collect evidence for each:

- **Execution:** the intended binary and arguments run.
- **Environment:** disallowed keys are absent and required keys remain.
- **Descriptors:** unintended open objects do not survive exec.
- **Namespaces:** handles differ where required and resource views agree.
- **Credentials:** IDs, groups, and all capability sets match the declared floor.
- **Privilege gain:** `NoNewPrivs` is 1 in descendants.
- **Host preservation:** parent hostname, mounts, and process view remain unchanged.

## A disciplined failure-reading loop

When a grader reports a failed property:

- Restate the property without guessing at a line-level fix.
- Reproduce it with the smallest harmless local probe.
- Observe the executed child, not just the launcher's source.
- Separate setup failure from workload failure using stderr and exit status.
- Change one authority channel at a time.
- Rerun the local probe, then the randomized grader.
- Reset and replay to ensure the fix was not tied to one fixture.

# Completion, replay, and reference

## Replay the completed sequence

```bash
./lab-status
./lab-reset --all --dry-run
./lab-reset --all --yes
./lab-start 01.01
```

### What each line does

- Status records the end state before reset.
- The dry run validates every reset target and resource without mutation.
- The confirmed all-scope reset removes disposable student work and generated fixtures while retaining attempt/pass metadata.
- Starting 01.01 creates a fresh attempt with no retained solution.

If the commands feel familiar but the answer is not sitting in front of you, replayability is working.

## Quick command reference

- `ps -o ... -p PID` selects explicit process columns for named PIDs.
- `readlink /proc/PID/ns/TYPE` records namespace membership.
- `grep -E` uses extended regular expressions; `grep -F` matches literal text.
- `strace -f -e trace=LIST` follows descendants and restricts syscall display.
- `unshare` creates specified namespaces for a command.
- `setpriv` changes privilege attributes before executing a command.
- `capsh --decode=MASK` translates a hexadecimal capability mask.
- `getcap -r PATH` finds file capability attributes recursively.
- `fcntl(fd, F_GETFD)` reads descriptor flags.
- `prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)` sets the one-way no-new-privileges bit.

## Glossary

- **Ambient authority:** authority available to a program without an explicit request for each use, such as inherited environment values or descriptors.
- **Argument vector (`argv`):** the ordered, NUL-terminated array of strings supplied to a new program.
- **Capability:** a named Linux privilege bit evaluated in a namespace context.
- **Close-on-exec:** a descriptor flag instructing the kernel to close that descriptor during successful exec.
- **Environment (`envp`):** an array of `KEY=VALUE` strings supplied to an executed program.
- **Exec:** a transition replacing the current process image while preserving defined process state.
- **File descriptor:** a process-local integer reference to an open kernel object.
- **Namespace:** a kernel mechanism giving processes a scoped view of one resource class.
- **Namespace handle:** a procfs link target such as `uts:[4026531838]` identifying a namespace object.
- **PID 1:** the first process in a PID namespace, with special signal and child-reaping responsibilities.
- **procfs:** the `/proc` virtual filesystem exposing kernel-generated process and system views.
- **Property-based grading:** checking externally observable security outcomes rather than matching one source implementation.
- **Syscall:** a controlled transition from user space into the kernel to request an operation.
- **`no_new_privs`:** a sticky process attribute preventing exec from granting new privilege.
- **User namespace mapping:** the translation between IDs visible inside a user namespace and IDs in its parent.

## What comes next

Modules 04-12 continue this course with guided examples, exact commands, line explanations, deliberate failures, randomized fixtures, independent labs, property-based graders, safe reset, and replay. Their chapters follow in the complete manual.

The path moves from a minimal tool-using agent through filesystem and syscall confinement, resource controls, network mediation, credential brokering, a composed runtime, break/fix analysis, bounded evidence interpretation, and a cold batch-runtime capstone. Use the cumulative checkpoints in `docs/LEARNING_PATH.md` before advancing.
