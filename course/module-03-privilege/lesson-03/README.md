# 03.03 - Make privilege non-gainable

Goal: set `no_new_privs` before exec and observe the sticky bit in the child.

## Exercise 1 - Build the one-way transition

```bash
sed -n '1,220p' nnp-launch.c
cc -std=c11 -Wall -Wextra -O2 nnp-launch.c -o nnp-launch
./nnp-launch sh -c 'grep -E "^(NoNewPrivs|CapEff):" /proc/self/status'
```

### Line by line

- `sed` displays the complete small launcher before execution.
- `cc ... nnp-launch.c -o nnp-launch` compiles it with C11 and warning flags.
- `./nnp-launch` starts your launcher; every following token becomes its child command and arguments.
- `sh -c '...'` lets the launched shell run the quoted `grep` expression.
- The regular expression selects only `NoNewPrivs` and `CapEff` from the child's effective status.

Expected:

```text
NoNewPrivs:  1
CapEff:      0000000000000000
```

### Line by line

- `NoNewPrivs: 1` confirms the sticky kernel bit is active in the executed child.
- `CapEff: 000...0` means no effective capability bit is currently set. This line is an observation, not a guarantee about every other authority channel.

`PR_SET_NO_NEW_PRIVS` is inherited across fork and exec and cannot be unset. It promises that exec will not grant privileges the process did not already have.

### Launcher source, line by line

- `#define _GNU_SOURCE` requests GNU/Linux declarations before system headers are included.
- `<sys/prctl.h>` declares `prctl` and `PR_SET_NO_NEW_PRIVS`; `<unistd.h>` declares `execvp`.
- `argc < 2` rejects an invocation that omitted the child command.
- `prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)` asks the kernel to set the calling thread's one-way no-new-privileges bit. The four zero arguments are unused for this operation.
- `!= 0` detects failure; `perror` prints the kernel-provided reason and the function returns before launching untrusted code.
- `execvp(argv[1], &argv[1])` uses the requested command as the new program and passes the command plus remaining arguments as its `argv` array.
- `&argv[1]` points into the original array instead of constructing a new one.
- The final diagnostic runs only when `execvp` fails; success replaces the launcher and never returns.

## Exercise 2 - Make the ordering mistake

Temporarily move the `prctl(PR_SET_NO_NEW_PRIVS, ...)` call after `execvp`. Rebuild.

Expected compiler behavior: code after a successful `execvp` is never reached; the child reports `NoNewPrivs: 0`. Restore the call before exec. Security controls that govern the transition must be established before the transition.

## Exercise 3 - Verify the descendant

```bash
./nnp-launch sh -c 'sh -c "grep ^NoNewPrivs: /proc/self/status"'
```

### Line by line

- The outer `./nnp-launch` sets the bit and executes the first shell.
- The first `sh -c` starts a second shell using the double-quoted command inside its single-quoted program.
- The inner shell runs `grep` against its own `/proc/self/status`.
- Seeing `1` at this second descendant proves inheritance across more than one exec transition.

Expected: the grandchild also reports `1`.

Limit: `no_new_privs` does not remove current authority. It does not close descriptors, erase environment data, empty capabilities, isolate filesystems, or filter syscalls. It is one composable control.
