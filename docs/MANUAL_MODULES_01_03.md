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

# Module 01 - Processes, syscalls, and inherited authority

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

## 01.01 - Processes are the boundary you actually launched

### Goals

- Identify a shell and its parent from kernel state.
- Separate library calls from kernel-visible syscalls.
- Read a focused `strace`.
- Observe why one source call need not equal one syscall.

### Exercise 1 - Establish the process facts

```bash
pwd
printf 'shell pid=%s parent=%s\n' "$$" "$PPID"
ps -o pid,ppid,user,stat,comm,args -p $$ -p $PPID
```

### What each line does

- `pwd` confirms the disposable workspace directory.
- `printf` formats two shell variables; `%s` accepts a string and `\n` ends the line.
- `$$` is this shell's PID and `$PPID` is its recorded parent PID.
- Quoting preserves each expanded value as one argument.
- `ps -o ...` selects explicit columns instead of distribution defaults.
- `pid` and `ppid` expose the relationship; `user` is the effective account; `stat` is process state; `comm` is executable name; `args` is the argument vector.
- The repeated `-p` options restrict output to the shell and its parent.

Expected shape:

```text
/path/to/repository/.student/01.01
shell pid=1842 parent=1790
    PID    PPID USER     STAT COMMAND  COMMAND
   1790    1789 student  Ss   terminal ...
   1842    1790 student  S    bash     bash
```

Numbers and names vary. The relationship is the observation: the shell's `PPID` identifies the other row. A process is a kernel object with identity, memory, descriptors, credentials, and namespace memberships. Command text is only input used to launch it.

```bash
readlink /proc/$$/exe
ls -l /proc/$$/ns
```

### What each line does

- `/proc/$$` is procfs state for the current shell.
- `exe` links to the executable object backing the process.
- `readlink` prints the target without executing it.
- `ns` contains one symbolic link per namespace type.
- `ls -l` exposes targets such as `mnt:[4026531841]`; the bracketed identity is useful when comparing processes.

### Exercise 2 - Build and trace a small process

Complete source:

<!-- source: course/module-01-process-authority/lesson-01/hello-syscall.c format=code -->
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
<!-- /source -->

### Source, line by line

- `<stdio.h>` declares `stdout`, `setvbuf`, `puts`, and `perror`.
- `<unistd.h>` declares `write` and `STDOUT_FILENO`.
- `int main(void)` declares an integer result and no command-line parameters.
- `setvbuf(..., _IONBF, 0)` disables stdout buffering for a clearer observation.
- `puts` is a library call. It appends a newline and eventually needs a syscall to make bytes visible.
- The `const char` array contains visible bytes, `\n`, and a terminating NUL.
- Descriptor 1 is stdout by convention.
- `sizeof(message) - 1` excludes the terminating NUL.
- A negative `write` result indicates failure. `perror` explains `errno`.
- Return 1 reports failure; return 0 reports success.

Build and run:

```bash
sed -n '1,200p' hello-syscall.c
cc -std=c11 -Wall -Wextra -O2 hello-syscall.c -o hello-syscall
./hello-syscall
```

### What each line does

- `sed -n` suppresses default output and `'1,200p'` prints source lines 1 through 200.
- `cc` invokes the compiler driver.
- `-std=c11` selects C11; `-Wall -Wextra` enable useful diagnostics; `-O2` enables normal optimization.
- `-o hello-syscall` names the output binary.
- `./` executes the local file instead of searching `PATH`.

Expected:

```text
userspace: about to write
kernel-visible write
```

Trace it:

```bash
strace -f -e trace=execve,write,exit_group ./hello-syscall 2>&1
```

### What each part does

- `strace` observes syscalls made by its target.
- `-f` follows descendants if any are created.
- `-e trace=...` restricts output to execution, writes, and process exit.
- `2>&1` merges trace stderr with stdout for one transcript.

Expected pattern:

```text
execve("./hello-syscall", ["./hello-syscall"], ...) = 0
write(1, "userspace: about to write\n", 26) = 26
write(1, "kernel-visible write\n", 21) = 21
exit_group(0) = ?
```

Lengths can vary. Read each call as arguments followed by a return value.

### Exercise 3 - Break a naive prediction

Predict that one library output call means one `write`, then run:

```bash
strace -e trace=write ./hello-syscall 2>&1 | grep write
```

- The trace filter records only `write` syscalls.
- Redirection exposes trace output to the pipeline.
- `grep` changes display only.

Temporarily change `_IONBF` to `_IOFBF`, rebuild, and trace again. Full buffering may combine or delay writes depending on the destination and C library. Restore `_IONBF` afterward.

The security lesson is not buffering trivia. Policies written in terms of syscalls must be validated against syscalls that actually occur, not those guessed from source function names.

### Troubleshooting and checkpoint

- If `strace` is missing, install it inside the disposable VM.
- If output order surprises you, remember stdout and stderr have different buffering and become one stream only after redirection.
- If namespace links are absent, confirm the environment is Linux and `/proc` is mounted.
- You should now be able to name the process, the `execve`, and the syscall producing visible output.

<!-- PAGEBREAK -->

## 01.02 - Environment inheritance is authority

### Mental model

`execve` conceptually receives `path`, `argv`, and `envp`. `envp` is an array of `KEY=VALUE` strings supplied by the launcher. The new program need not request individual values. Environment entries can influence command lookup, language runtimes, proxy use, locale, library loading, and application configuration.

### Exercise 1 - Observe the inherited value

```bash
export DEMO_AGENT_TOKEN="fake-$(awk -F= '/fixture_id/{print $2}' FIXTURE.txt)"
python3 show-env.py
```

### What each part does

- `export` marks a variable for inheritance by later children.
- The value is deliberately synthetic.
- `$(...)` runs `awk` and substitutes its output.
- `-F=` makes `=` the field separator; the pattern selects the fixture line; `{print $2}` emits its value.
- The outer quotes preserve the result as one argument.
- Python inherits exported variables because no replacement environment is supplied.

Expected:

```text
DEMO_AGENT_TOKEN=fake-<random fixture id>
PATH=<current path>
```

The child did not open a credential store. The parent supplied the string across exec.

```bash
strace -f -e trace=execve python3 show-env.py 2>&1 | head -20
```

- `-f` follows descendants; the trace selector keeps execution transitions.
- `2>&1` exposes trace diagnostics to the pipe.
- `head -20` limits display without changing execution.
- Do not use verbose environment-dumping trace options around real secrets.

### Exercise 2 - Inspect the intentional mistake

Launcher source:

<!-- source: course/module-01-process-authority/lesson-02/launch-insecure.py format=code -->
```python
#!/usr/bin/env python3
import os
import subprocess

# Intentional mistake: copying the full parent environment copies its authority.
child_env = os.environ.copy()
subprocess.run(["python3", "show-env.py"], env=child_env, check=True)
```
<!-- /source -->

### Launcher source, line by line

- The shebang locates Python through `PATH` when the script is directly executable.
- `os` exposes the process environment; `subprocess` exposes child execution.
- `os.environ.copy()` creates a separate dictionary containing every inherited key and value. Memory independence is not authority reduction.
- The list form preserves program and argument boundaries and avoids a shell parser.
- `env=child_env` supplies the full copied environment.
- `check=True` treats a nonzero child status as an exception. It does not make the environment safe.

Observer source:

<!-- source: course/module-01-process-authority/lesson-02/show-env.py format=code -->
```python
#!/usr/bin/env python3
import os

print("DEMO_AGENT_TOKEN=" + os.environ.get("DEMO_AGENT_TOKEN", "<absent>"))
print("PATH=" + os.environ.get("PATH", "<absent>"))
```
<!-- /source -->

### Observer source, line by line

- `os.environ.get` returns the value or the literal default when the key is absent.
- String `+` joins the label and observation.
- The second line confirms that an intentionally retained `PATH` still reaches the child.

Run the vulnerable launcher:

```bash
sed -n '1,160p' launch-insecure.py
python3 launch-insecure.py
```

- Inspect before executing.
- Expected: the token remains. Supplying an explicit `env` argument is not equivalent to restricting that environment.

### Exercise 3 - Construct an allowlist

Replace the copied dictionary with:

```python
child_env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
```

- This is a new dictionary, not a derivative of the parent environment.
- `PATH` permits lookup only in two named directories.
- `LANG` supplies predictable locale behavior.
- Absence is enforced at the authority-transfer point. The child cannot ignore a value it never receives.

Verify:

```bash
python3 launch-insecure.py | grep -F 'DEMO_AGENT_TOKEN=<absent>'
printf 'verification status=%s\n' "$?"
```

- `grep -F` performs a literal match.
- `$?` is the preceding pipeline's status in this shell; zero means the expected line was found.

An environment allowlist is narrow. It does not close descriptors, restrict files, remove credentials, or stop a program from fetching data from another service.

### Troubleshooting and checkpoint

- If Python is not in the allowlisted directories, locate it deliberately with `command -v python3` inside the disposable VM.
- If the token remains, ensure the copied dictionary was replaced rather than followed by a later reassignment.
- Run without `grep` when diagnosing whether the launcher failed or the match was absent.
- You should be able to explain why copying a dictionary changes object identity but preserves authority.

<!-- PAGEBREAK -->

## 01.03 - File descriptors cross exec

### Mental model

Opening a path performs resolution and access checks, creates or references an open file description, and installs a process-local descriptor. Later reads use the descriptor; they do not repeat the original path lookup. A later pathname restriction does not revoke an already-open object.

### Exercise 1 - Observe descriptor authority

Parent source:

<!-- source: course/module-01-process-authority/lesson-03/fd-parent.c format=code -->
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
<!-- /source -->

### Parent source, line by line

- `_GNU_SOURCE` exposes GNU/Linux declarations such as `O_CLOEXEC` before headers are read.
- `<fcntl.h>` declares open flags; `<stdio.h>` diagnostics; `<unistd.h>` POSIX execution interfaces.
- The argument check requires exactly one pathname.
- `open(..., O_RDONLY)` resolves the path and returns read authority as a descriptor.
- A negative descriptor indicates failure.
- `child` is a NUL-terminated argument vector.
- `execvp` searches `PATH`, replaces the program image, and retains descriptors without close-on-exec.
- Code after a successful exec never runs.

Child source:

<!-- source: course/module-01-process-authority/lesson-03/fd-child.py format=code -->
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
<!-- /source -->

### Child source, line by line

- The bounded loop probes descriptor numbers 0 through 31. Production cleanup must not assume this upper bound.
- `/proc/self/fd/N` identifies the object behind descriptor `N`.
- `OSError` is expected for unopened numbers.
- Descriptors 3 and above are rewound when seekable and read directly.
- No protected pathname is opened by the child.
- Decode replacement keeps display robust; ignored errors do not prove a descriptor lacks other authority.

Build and run:

```bash
cc -std=c11 -Wall -Wextra -O2 fd-parent.c -o fd-parent
MANIFEST=$(python3 -c 'import json; print(json.load(open(".north-echo.json"))["fixture_manifest"])')
./fd-parent "$MANIFEST"
```

### What each line does

- The first line compiles the parent with warnings.
- `python3 -c` executes one quoted expression.
- `open` reads workspace metadata, `json.load` parses it, indexing selects the manifest path, and `print` emits it.
- Command substitution stores the printed path in `MANIFEST`.
- Quoting passes the entire path as one argument.

Expected: the child lists a descriptor above 2 pointing to `manifest.json` and can read synthetic fixture data. Descriptor 3 is common, not guaranteed.

### Exercise 2 - Fix at creation time

```c
int fd = open(argv[1], O_RDONLY | O_CLOEXEC);
```

- `O_RDONLY` requests read-only access.
- Bitwise OR combines independent flag bits.
- `O_CLOEXEC` asks the kernel to create the descriptor with `FD_CLOEXEC` atomically.
- Atomic creation avoids a multithreaded race between `open` and a later `fcntl`.

Rebuild and rerun. The protected descriptor should be absent after exec; descriptors 0, 1, and 2 may remain.

### Exercise 3 - Verify before and after exec

Add after `open` and before `execvp`:

```c
int flags = fcntl(fd, F_GETFD);
if (flags < 0) {
    perror("fcntl(F_GETFD)");
    return 1;
}
fprintf(stderr, "FD_CLOEXEC=%s\n", (flags & FD_CLOEXEC) ? "yes" : "no");
```

- `F_GETFD` reads descriptor flags, distinct from file status flags.
- Failure must be handled before treating the result as a mask.
- Bitwise AND tests only the close-on-exec bit.
- The conditional operator selects `yes` or `no`.
- The parent-side diagnostic and child-side absence are complementary evidence.

### Troubleshooting and checkpoint

- If `O_CLOEXEC` is undeclared, confirm `_GNU_SOURCE` precedes all headers and the build is on Linux.
- Distinguish Python's own descriptors from the protected inherited object by target and controlled comparison.
- Never hard-code descriptor 3; the grader randomizes it.
- You should be able to explain why later path confinement cannot revoke a descriptor already handed to the child.

<!-- PAGEBREAK -->

## Module 01 independent practical - Hygienic launcher

Edit `launcher.c`. The grader invokes `./launcher COMMAND [ARG ...]` and requires normal command behavior, absence of synthetic `NE_LAB_TOKEN`, closure of every inherited descriptor above 2, and nonzero status on launch failure.

Starter source:

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

The starter preserves arbitrary arguments but performs no authority hygiene.

```bash
cc -std=c11 -Wall -Wextra -O2 launcher.c -o launcher
./launcher /usr/bin/printf 'child works\n'
../../lab-grade module-01
../../lab-grade module-01 --mode exam
```

### What each line does

- The compile line matches the grader interface and exposes warnings.
- The harmless probe checks execution and argument preservation.
- The relative grader path reaches the repository root from `.student/01.lab`; it copies no solution.
- Practice mode names properties and lesson references. Exam mode reduces hints but tests the same properties.

### Plan and verify without a revealed solution

- Identify where the new environment is selected.
- Construct a small environment instead of subtracting unknown entries from a large one.
- Avoid assuming the randomized descriptor is 3.
- Preserve descriptors 0, 1, and 2.
- Remember that code after `execvp` represents failure only.
- Test functional, environment, descriptor, and failure properties separately.

# Module 02 - Linux namespaces

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

## 02.01 - Read namespace identity

### Goals

- Record baseline namespace handles.
- Create a mapped user namespace as an ordinary user.
- Interpret namespace-local UID 0 without confusing it with host root.
- Read the UID mapping that connects inside and outside identities.

### Exercise 1 - Capture the baseline

```bash
printf '%-8s %s\n' TYPE HANDLE
for ns in user uts pid mnt net ipc cgroup; do
  printf '%-8s %s\n' "$ns" "$(readlink /proc/self/ns/$ns)"
done
```

### What each line does

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

### Exercise 2 - Create a mapped user namespace

```bash
unshare --user --map-root-user sh -c '
  echo "inside uid=$(id -u)";
  readlink /proc/self/ns/user;
  cat /proc/self/uid_map
'
```

### What each line does

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

### Exercise 3 - Disprove “UID 0 means global root”

```bash
unshare --user --map-root-user sh -c 'id; touch /root/north-echo-test'
```

### What each part does

- The namespace flags reproduce the mapped identity.
- `;` runs the second inner command whether or not `id` succeeds.
- `id` reports namespace-relative UID 0.
- `touch` attempts to create a file through the host-mounted `/root` path.
- The expected permission denial shows that credentials are interpreted relative to namespace ownership.

User namespaces can grant a process capabilities over resources owned by the new namespace. They do not grant corresponding power over parent-owned resources. A complete identity statement therefore includes the numeric IDs, the user namespace handle, and the ID mappings.

### Troubleshooting and checkpoint

- `Operation not permitted` usually means unprivileged user namespaces are disabled by VM policy.
- An empty or surprising map means the mapping helper failed; inspect stderr instead of assuming root was created.
- Never interpret `id -u` alone as a privilege proof.
- You should be able to compare two namespace handles and explain the three columns in `uid_map`.

<!-- PAGEBREAK -->

## 02.02 - Change UTS state without changing the host

### Goals

- Isolate hostname state in a UTS namespace.
- Understand why namespace creation and authority to modify its state are separate concerns.
- Compare host and child state before and after the change.
- Inspect a live process from another terminal.

### Exercise 1 - Baseline, change, and proof

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

### What each line does

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

### Exercise 2 - Make the incomplete attempt

```bash
unshare --uts hostname broken-attempt
```

- `--uts` requests only a UTS namespace.
- `hostname broken-attempt` is the command to run inside it.
- An ordinary user generally lacks the capability needed for this setup without the mapped user namespace.
- Expected: `Operation not permitted` and no host change.

The failure is useful. Creating a namespace type does not automatically supply every credential needed to configure it.

### Exercise 3 - Inspect a live namespace

In terminal one:

```bash
unshare --user --map-root-user --uts sh -c 'hostname north-echo-hold; echo $$; sleep 60'
```

- The flags create the temporary user and UTS namespaces.
- `hostname` assigns a recognizable value.
- `echo $$` prints the shell's PID as seen from the parent namespace running the terminal.
- `sleep 60` keeps the process and namespace alive. `Ctrl-C` ends it early.

In terminal two, substitute the printed decimal PID:

```bash
readlink /proc/PRINTED_PID/ns/uts
readlink /proc/self/ns/uts
```

- The first line observes the held process's UTS namespace.
- `/proc/self` in the second terminal refers to the inspecting process.
- Different handles prove different membership even if both hostnames happened to contain the same text.

Verification should inspect effective state, not merely search a script for the word `unshare`.

### Troubleshooting and checkpoint

- If the first terminal exits before inspection, rerun with a longer harmless sleep.
- If `/proc/PRINTED_PID` is absent, confirm you used the host-visible PID and that the process is still alive.
- If the handles match, inspect the exact flags and quoting rather than changing the expected result.
- You should be able to state why the parent hostname remains unchanged.

<!-- PAGEBREAK -->

## 02.03 - PID namespaces and the procfs mistake

### Goals

- Start a shell as PID 1 inside a new PID namespace.
- Observe why an inherited procfs can show the wrong process view.
- Compose PID and mount namespaces with a matching procfs.
- Recognize the responsibilities assigned to namespace PID 1.

### Exercise 1 - Create the incomplete setup

```bash
unshare --user --map-root-user --pid --fork sh -c '
  echo "shell says pid=$$";
  ps -o pid,ppid,comm | head
'
```

### What each line does

- The mapped user namespace provides safe namespace-local authority.
- `--pid` creates a PID namespace for children, not retroactively for the calling `unshare` process.
- `--fork` creates the child that can enter the new PID namespace.
- The quoted shell runs as the namespace's first process and expands its own `$$`.
- `ps` obtains process data through the currently mounted `/proc`.
- `head` limits display but cannot correct the underlying view.

Expected surprise: the shell reports PID 1 while `ps` may show many host processes or numbers that do not agree. The PID namespace changed, but the inherited procfs mount still represents the parent PID namespace.

### Exercise 2 - Mount a matching procfs

```bash
unshare --user --map-root-user --pid --fork --mount --mount-proc sh -c '
  echo "shell says pid=$$";
  ps -o pid,ppid,comm;
  echo "pid namespace=$(readlink /proc/self/ns/pid)";
  echo "mount namespace=$(readlink /proc/self/ns/mnt)"
'
```

### What each line does

- `--mount` isolates mount-table changes from the parent.
- `--mount-proc` mounts a fresh procfs associated with the new PID namespace.
- `--pid --fork` creates and enters the PID namespace in the required child.
- The shell sees itself as PID 1.
- `ps` now reads the fresh procfs, so its process list should agree with the namespace-local IDs.
- The two `readlink` calls record both namespace identities.

Expected: a small process list containing the shell and observation tools, plus new PID and mount handles. Process counts can vary because `ps`, shells, and pipelines briefly create processes.

### Exercise 3 - Observe PID 1 responsibility

```bash
unshare --user --map-root-user --pid --fork --mount --mount-proc sh -c '
  (exit 0) &
  sleep 0.2
  ps -o pid,ppid,stat,comm
'
```

### What each line does

- Parentheses create a subshell; `exit 0` makes it terminate successfully.
- `&` runs that subshell asynchronously.
- `sleep 0.2` gives exit processing time to occur.
- The `stat` column exposes a zombie as `Z` if a dead child has not been reaped.

Namespace PID 1 has special signal behavior and becomes the adopter for orphaned descendants. A production runtime normally supplies a small init/reaper instead of casually making an arbitrary workload PID 1.

### Why namespace composition matters

A PID namespace without a matching procfs produces contradictory observations. A UTS namespace without suitable namespace-local authority may not be configurable. A mount namespace does not automatically create a private filesystem tree. Namespaces isolate selected views; they are components, not a complete sandbox policy.

### Troubleshooting and checkpoint

- If `--mount-proc` fails, confirm the mapped user namespace was created and the util-linux `unshare` version supports it.
- If `ps` shows the host, compare the mount namespace handle and inspect the active `/proc` mount.
- Do not grade by exact process count; grade by namespace relationships and the procfs view.
- You should be able to explain why `$$` and `ps` disagreed in the incomplete setup.

<!-- PAGEBREAK -->

## Module 02 independent practical - Namespace launcher

Implement `sandbox.sh`. The grader invokes:

```text
NE_EXPECTED_HOSTNAME=randomized-value ./sandbox.sh COMMAND [ARG ...]
```

The command must receive fresh user, UTS, PID, and mount namespaces; the randomized hostname; namespace PID 1; a procfs matching the new PID namespace; and unchanged argument, stream, and exit behavior. The host hostname and mount table must remain unchanged.

Starter source:

<!-- source: course/module-02-namespaces/lab/sandbox.sh format=code -->
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
<!-- /source -->

### Starter source, line by line

- `#!/bin/sh` selects a POSIX shell interpreter.
- `set -e` exits after unhandled command failure; `-u` rejects unset-variable expansion.
- `$#` is the number of supplied arguments.
- `[ ... ]` is a test command; `-eq` performs integer equality.
- `$0` is the script name. `>&2` sends usage text to stderr.
- `exec "$@"` replaces the script with the requested command and preserves each original argument.
- The starter has good forwarding behavior but no namespace isolation.

Probe and grade:

```bash
chmod +x sandbox.sh
./sandbox.sh sh -c 'echo "pid=$$ host=$(hostname)"; ps -o pid,ppid,comm'
../../lab-grade module-02
```

### What each line does

- `chmod +x` adds executable permission.
- The probe supplies `sh` as the arbitrary command under test.
- Single quotes defer `$$` and `$(hostname)` until the sandboxed shell runs.
- `ps` tests whether procfs agrees with namespace-local PID state.
- The grader compares actual namespace handles and process state with its own; the word `unshare` alone cannot pass.

### Plan and verify without a revealed solution

- Identify which namespace provides authority to configure the others as an ordinary user.
- Preserve `COMMAND [ARG ...]` as separate arguments.
- Ensure the hostname value comes from the randomized environment variable, not a constant.
- Ensure mount changes occur in a distinct mount namespace.
- Verify PID membership and the procfs view independently.
- Check that the launched command's exit status reaches the caller.

The independent lab withholds exact flag ordering and implementation. Every required interface has appeared in the guided exercises.

# Module 03 - Privilege, capabilities, and no_new_privs

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

## 03.01 - UIDs are not the whole privilege story

### Goals

- Read complete UID, GID, group, capability, and `no_new_privs` state from procfs.
- Decode a hexadecimal capability mask.
- Compare ordinary identity with namespace-local root.
- Find file capabilities that complicate simplistic UID reasoning.

### Exercise 1 - Inspect current credentials

```bash
id
grep -E '^(Uid|Gid|Groups|Cap(Inh|Prm|Eff|Bnd|Amb)|NoNewPrivs):' /proc/self/status
```

### What each line does

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

### What each line does

- The `awk` pattern selects the line beginning `CapEff:`.
- `{print $2}` emits the second whitespace-delimited field, the hexadecimal mask.
- Command substitution stores it in `CAP_EFF`.
- `capsh --decode=` translates set bits into capability names.
- Quoting ensures even an empty or unusual expansion remains one argument.

For a zero mask, expect an empty decoded set. For nonzero masks, record each capability name instead of describing the process merely as “privileged.”

### Exercise 2 - Compare namespace-local root

```bash
unshare --user --map-root-user sh -c '
  id;
  grep -E "^(Uid|Cap(Inh|Prm|Eff|Bnd|Amb)):" /proc/self/status;
  capsh --decode=$(awk "/^CapEff:/{print \\$2}" /proc/self/status)
'
```

### What each part does

- `unshare` creates a new user namespace and maps the ordinary caller to UID 0 inside it.
- The child `id` displays namespace-relative identity.
- The child `grep` prints UID and all capability fields.
- Nested `awk` extracts `CapEff` for decoding.
- The backslash before `$2` prevents the outer shell from consuming it before inner `awk` runs.
- Capability bits are meaningful relative to the user namespace that owns the target resource.

Expected: UID 0 and a set of capabilities inside the new user namespace, but no corresponding host-root authority.

### Exercise 3 - Disprove the nonzero-UID simplification

```bash
getcap -r /usr/bin 2>/dev/null | head
```

### What each part does

- `getcap` reads file capability extended attributes.
- `-r /usr/bin` walks that directory recursively.
- `2>/dev/null` discards expected permission or unsupported-file diagnostics. Do not suppress stderr while diagnosing an unexpected failure.
- `head` keeps the display short.

Many systems contain programs with file capabilities such as a narrowly scoped network capability. Executing one can change capability state even when the caller's effective UID is not zero. A review must record IDs, groups, namespace mappings, capability sets, executable attributes, and inherited resources.

### Troubleshooting and checkpoint

- If `capsh` or `getcap` is missing, install the distribution's capability utilities package in the VM.
- Treat an all-zero `CapEff` as one observation, not proof that every authority channel is empty.
- Keep the namespace handle alongside the decoded bits when comparing processes.
- You should be able to explain why `CapBnd` may be nonzero while `CapEff` is zero.

## 03.02 - Drop capability sets deliberately

### Goals

- Decode all five capability sets rather than reading only `CapEff`.
- Use `setpriv` to establish a capability-empty child.
- Observe why clearing only one set is an incomplete fix.
- Verify the resulting process rather than trusting requested flags.

### Exercise 1 - Decode every set

```bash
for field in CapInh CapPrm CapEff CapBnd CapAmb; do
  value=$(awk -v key="$field:" '$1==key{print $2}' /proc/self/status)
  printf '%-7s %s -> ' "$field" "$value"
  capsh --decode="$value"
done
```

### What each line does

- The loop assigns each procfs field name to `field`.
- `awk -v key="$field:"` passes the current field plus its colon into `awk`.
- `$1==key` performs exact first-field equality; `{print $2}` emits the mask.
- Command substitution stores the mask in `value`.
- `printf` aligns the name, prints the raw mask, and deliberately omits a newline.
- `capsh --decode` prints capability names and completes the record.
- `done` closes the loop.

Do not collapse the five results into one adjective. Ask which set controls present checks and which sets constrain or enable future exec transitions.

### Exercise 2 - Launch with empty sets

```bash
unshare --user --map-root-user setpriv \
  --bounding-set=-all \
  --inh-caps=-all \
  --ambient-caps=-all \
  sh -c 'grep -E "^(Groups|Cap(Inh|Prm|Eff|Bnd|Amb)):" /proc/self/status'
```

### What each line does

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

The `Groups` line need not be empty. `--map-root-user` uses the kernel's safe single-ID mapping path, which disables later `setgroups(2)` calls before writing the GID map. Adding `setpriv --clear-groups` after that transition therefore fails with `Operation not permitted` on current Ubuntu kernels. Group reduction is a separate launcher responsibility that must happen at a boundary where the caller has authority to change its supplementary groups; this exercise isolates capability-set behavior instead of pretending the two controls are interchangeable.

### Exercise 3 - Make the partial fix

```bash
unshare --user --map-root-user setpriv --inh-caps=-all sh -c 'grep -E "^Cap(Inh|Prm|Eff|Bnd|Amb):" /proc/self/status'
```

- This changes only the inheritable set request.
- The final `grep` deliberately prints all sets.
- Expected: `CapInh` is zero, while other sets need not be empty.

The phrase “drop capabilities” is underspecified. Name every relevant set, state the intended postcondition, and verify the kernel-reported result.

### Capability caveats

- Clearing current sets does not close descriptors opened while capabilities were present.
- Dropping the bounding set is a one-way restriction for the process tree, but executable attributes and namespace context still need analysis.
- Supplementary groups are a separate authority channel.
- A zero capability mask does not restrict ordinary permissions granted by UID, GID, ACLs, or open resources.

### Troubleshooting and checkpoint

- If `setpriv` is missing, install util-linux in the disposable VM.
- If an option spelling differs, check the VM's util-linux version rather than silently omitting the property.
- If a transition fails, capture stderr and current sets before changing the exercise.
- You should be able to state which set is used for current checks and which set caps future acquisition across exec.

<!-- PAGEBREAK -->

## 03.03 - Make privilege non-gainable

### Goals

- Set the one-way `no_new_privs` bit before exec.
- Observe that bit in the executed child and a grandchild.
- Understand why ordering around exec is a security property.
- Distinguish non-gainability from removal of existing authority.

### Exercise 1 - Build the launcher

Complete source:

<!-- source: course/module-03-privilege/lesson-03/nnp-launch.c format=code -->
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
<!-- /source -->

### Source, line by line

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

### What each line does

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

### Exercise 2 - Make the ordering mistake

Temporarily move the `prctl` block after `execvp`, rebuild, and rerun.

- A successful exec replaces the launcher, so code after it is unreachable on the success path.
- The executed child therefore observes the old `NoNewPrivs` value, normally 0.
- Restore the call before exec.

Security controls governing a transition must be established before that transition. Source presence is not enough; control-flow ordering is part of the property.

### Exercise 3 - Verify inheritance in a descendant

```bash
./nnp-launch sh -c 'sh -c "grep ^NoNewPrivs: /proc/self/status"'
```

### What each part does

- The launcher sets the bit and executes the first shell.
- The outer single quotes protect the inner command from the invoking shell.
- The first child shell launches another shell.
- The inner shell reads its own procfs status.
- Seeing 1 proves inheritance across more than one exec transition.

`no_new_privs` cannot be unset and is inherited across fork and exec. It prevents privilege gain from exec mechanisms such as set-user-ID and file capabilities. It does not close descriptors, scrub the environment, empty current capability sets, isolate files, restrict the network, or filter syscalls.

### Troubleshooting and checkpoint

- If `prctl` is undeclared, verify Linux headers and `_GNU_SOURCE` placement.
- If the child reports 0, inspect control-flow ordering before changing the probe.
- If the command does not launch, distinguish `prctl` failure from `execvp` failure using stderr.
- You should be able to explain both what `no_new_privs` guarantees and what it deliberately does not guarantee.

<!-- PAGEBREAK -->

## Module 03 independent practical - Privilege floor

Implement `secure-launch.c`. The grader compiles it and invokes:

```text
./secure-launch COMMAND [ARG ...]
```

The executed command must observe `NoNewPrivs: 1`, empty effective/permitted/inheritable/ambient capability sets, the invoking ordinary user's real and effective UID, normal arguments and streams, and normal exit behavior. Do not add set-user-ID bits or file capabilities. Do not transform the command through an external shell.

Starter source:

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

Probe and grade:

```bash
cc -std=c11 -Wall -Wextra -O2 secure-launch.c -o secure-launch
./secure-launch sh -c \
  'grep -E "^(Uid|CapInh|CapPrm|CapEff|CapAmb|NoNewPrivs):" /proc/self/status'
../../lab-grade module-03
```

### What each line does

- The compile line checks the same source interface used by the grader.
- The continuation backslash keeps the probe readable while remaining one shell command.
- The local probe reads the executed child's kernel-reported state rather than trusting source intent.
- The anchored expression selects identity, four required capability sets, and `NoNewPrivs`.
- The external grader creates fresh evaluation details and tests properties independently.

### Plan and verify without a revealed solution

- Identify every state transition that must occur before exec.
- Treat `no_new_privs` and capability removal as distinct properties.
- Preserve the original command and arguments without shell reparsing.
- Handle failure for every security-relevant transition; do not continue in a partially configured state.
- Verify UID fields and every required capability field in the executed process.
- Remember that the module contract does not claim to close descriptors or sanitize the environment; those are separate controls from Module 01.

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
