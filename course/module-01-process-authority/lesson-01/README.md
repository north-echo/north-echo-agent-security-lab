# 01.01 - Processes are the boundary you actually launched

Goal: connect a source-level operation to a process, an `execve` transition, and syscalls. Work only inside this generated workspace.

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
- `int main(void)` is the process entry point and promises an integer exit status with no command-line arguments.
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

Before running this, predict “one `printf` means one `write` syscall.” Then run:

```bash
strace -e trace=write ./hello-syscall 2>&1 | grep write
```

### Line by line

- `strace -e trace=write` records only `write` syscalls.
- `2>&1` combines trace output and program output into one stream.
- `|` connects that stream to the next command.
- `grep write` keeps lines containing the word `write`; it is a display filter, not part of the traced program.

If buffering combines or rearranges output, your prediction fails. Change `setvbuf(stdout, NULL, _IONBF, 0);` to use `_IOFBF`, rebuild, and trace again. The lesson is not the buffering trivia: source-level operations and kernel operations are different layers. Restore `_IONBF` before finishing.

Checkpoint: you should be able to point to the process, the `execve`, and the syscall that produced the visible effect.
