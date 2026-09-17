# 01.01 - Processes are the boundary you actually launched

Goal: connect a source-level operation to a process, an `execve` transition, and syscalls. Work only inside this generated workspace.

## Exercise 1 - Establish the process facts

Run:

```bash
pwd
printf 'shell pid=%s parent=%s\n' "$$" "$PPID"
ps -o pid,ppid,user,stat,comm,args -p $$ -p $PPID
```

Expected pattern: two rows. Your shell's `PPID` identifies its parent. A process is not “the command text”; it is a kernel object with identity, credentials, memory, descriptors, and namespace memberships.

Now inspect the executable and namespace handles:

```bash
readlink /proc/$$/exe
ls -l /proc/$$/ns
```

Expected pattern: `exe` names your shell; namespace entries look like `mnt:[402653....]`. Those inode-like numbers let you compare namespace membership later.

## Exercise 2 - Compile a process that crosses into the kernel

Inspect and build the starter:

```bash
sed -n '1,200p' hello-syscall.c
cc -std=c11 -Wall -Wextra -O2 hello-syscall.c -o hello-syscall
./hello-syscall
```

Expected output:

```text
userspace: about to write
kernel-visible write
```

Trace it:

```bash
strace -f -e trace=execve,write,exit_group ./hello-syscall 2>&1
```

Expected pattern: an `execve(...) = 0`, one or more `write(...)` calls, then `exit_group(0)`. Library functions are not themselves the security boundary; their eventual syscalls are what enter the kernel.

## Exercise 3 - Make and correct an intentional prediction error

Before running this, predict “one `printf` means one `write` syscall.” Then run:

```bash
strace -e trace=write ./hello-syscall 2>&1 | grep write
```

If buffering combines or rearranges output, your prediction fails. Change `setvbuf(stdout, NULL, _IONBF, 0);` to use `_IOFBF`, rebuild, and trace again. The lesson is not the buffering trivia: source-level operations and kernel operations are different layers. Restore `_IONBF` before finishing.

Checkpoint: you should be able to point to the process, the `execve`, and the syscall that produced the visible effect.
