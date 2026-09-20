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
