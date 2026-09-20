# 06.02 - Compare errno, kill, and blacklist bypass

## Goal

Install one observable deny rule, compare recoverable `EPERM` with process termination, then bypass a single-syscall blacklist through a related kernel interface.

## Concepts and preparation

Complete 06.01 first. A filter has a default action plus rules for selected calls. **Default allow** permits anything not explicitly denied; **default deny** denies anything not explicitly allowed. These are policy structures, not synonyms for good and bad applications.

For a selected denied call, an **errno action** returns an error to the program without performing the call. A **kill action** terminates the process instead. The program's subsequent error-handling code can run in the first case but not the second. We use only local Unix-domain socket creation in this synthetic observation; no external address or service is contacted.

The **libseccomp** library translates named rules into the kernel's filter format. `pkg-config` supplies build flags for the installed library; it is a build helper, not an enforcement mechanism. Predict whether a rule naming `socket` automatically covers the separate `socketpair` interface.

From the course root inside the Linux VM:

```bash
./lab-start 06.02
cd .student/06.02
pwd
ls -l socket_probe.c deny_socket.c
cat socket_probe.c
cat deny_socket.c
```

The commands prepare and enter the student workspace, confirm filenames, and display every supplied source before execution. C sources are text, not executable programs yet. Use the compile commands below to create binaries. For an edit, run `nano FILENAME` with the actual source name, save with `Ctrl-O`, `Enter`, and leave with `Ctrl-X`; then rebuild. Keep all experiments in this disposable VM and leave SELinux enforcing on Fedora.

## Exercise 1 - Build the probe and filter launcher

Complete probe source:

<!-- source: course/module-06-seccomp/lesson-02/socket_probe.c format=code -->
```c
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 2)
        return 2;
    errno = 0;
    int result;
    if (strcmp(argv[1], "socket") == 0)
        result = socket(AF_UNIX, SOCK_STREAM, 0);
    else {
        int pair[2];
        result = socketpair(AF_UNIX, SOCK_STREAM, 0, pair);
        if (result == 0) {
            close(pair[0]);
            close(pair[1]);
        }
    }
    printf("result=%d errno=%d\n", result, errno);
    return result == -1 ? 1 : 0;
}
```
<!-- /source -->

### Source, line by line

- `errno` records why a failed call returned `-1`.
- `socket` requests one local AF_UNIX endpoint; `socketpair` requests a connected local pair without any external network.
- Successful pair descriptors are closed. The printed result makes filter behavior visible.
- A denied call returns nonzero; an allowed call returns zero.

Complete launcher source:

<!-- source: course/module-06-seccomp/lesson-02/deny_socket.c format=code -->
```c
#include <errno.h>
#include <seccomp.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 3 || (strcmp(argv[1], "errno") != 0 && strcmp(argv[1], "kill") != 0)) {
        fprintf(stderr, "usage: %s errno|kill COMMAND [ARG...]\n", argv[0]);
        return 2;
    }
    uint32_t action = strcmp(argv[1], "kill") == 0
        ? SCMP_ACT_KILL_PROCESS : SCMP_ACT_ERRNO(EPERM);
    scmp_filter_ctx context = seccomp_init(SCMP_ACT_ALLOW);
    if (!context || seccomp_rule_add(context, action, SCMP_SYS(socket), 0) < 0 ||
        seccomp_load(context) < 0) {
        fprintf(stderr, "failed to install filter\n");
        seccomp_release(context);
        return 1;
    }
    seccomp_release(context);
    execv(argv[2], &argv[2]);
    perror("execv");
    return 1;
}
```
<!-- /source -->

### Source, line by line

- `seccomp_init(SCMP_ACT_ALLOW)` creates a blacklist: every syscall is allowed unless a rule says otherwise.
- The selected rule either returns `EPERM` or kills the whole process when `socket` is attempted.
- Every libseccomp operation is checked. Failure cannot fall through to an unfiltered `execv`.
- `seccomp_load` installs the filter on the launcher; seccomp then persists across `exec` into the probe.
- `seccomp_release` frees userspace policy memory, not the loaded kernel filter.

The ternary expression `condition ? first : second` chooses the action. `SCMP_SYS(socket)` asks the library for the named call, avoiding a hard-coded architecture-specific integer. The final `0` in `seccomp_rule_add` means no argument comparisons: the rule covers every invocation of that syscall in this filter. It does not inspect a destination or a pathname.

The context is an opaque library handle. `!context` detects allocation failure; the `||` chain short-circuits into the same error return if adding or loading the rule fails. By default libseccomp arranges the no-new-privileges requirement for an unprivileged load. Lesson 06.03 sets that bit explicitly so the ordering is visible in the launcher source.

Use only the documented modes here. A spelling error must not silently select a different failure policy; the argument guard checks `errno` or `kill` before choosing the action.

```bash
cc -std=c11 -Wall -Wextra -Werror -O2 -static socket_probe.c -o socket-probe
cc -std=c11 -Wall -Wextra -Werror -O2 deny_socket.c -o deny-socket $(pkg-config --cflags --libs libseccomp)
```

The first binary is static so its runtime does not complicate this one-rule observation. `pkg-config` supplies the distribution's libseccomp flags.

## Exercise 2 - Observe errno and kill actions

```bash
./deny-socket errno ./socket-probe socket || test "$?" -eq 1
status=0
./deny-socket kill ./socket-probe socket || status=$?
printf 'kill_status=%s\n' "$status"
```

### Line by line

- Errno mode lets the probe continue: expect `result=-1 errno=1` and status 1.
- `status=0` initializes the result; the `||` branch immediately saves the expected nonzero status. This works without changing your interactive shell's error-handling options.
- Kill mode prevents the probe from printing its post-call result. A shell commonly reports `Bad system call`; status is normally 128 plus `SIGSYS`.
- The status proves termination but does not identify a complete policy. A compile failure or nonexistent binary also produces a nonzero status, so confirm that the errno case worked and the kill case reports `SIGSYS`-related termination rather than treating any failure as the desired outcome.

Errno is useful for compatibility and diagnostics; kill is useful when continuing would be unsafe. Policy intent decides, not a blanket rule.

## Exercise 3 - Bypass the one-name blacklist

```bash
./deny-socket errno ./socket-probe socketpair
```

### Line by line

- The launcher denies only syscall `socket`.
- `socketpair` is a different syscall that creates a related communication primitive.
- Expected: `result=0 errno=0`. This is an intentional bypass of the blacklist, entirely local to the process.

Repair the design in Lesson 06.03 with a default-deny policy whose allowlist is derived from the stated workload. Merely adding names whenever a bypass appears tends toward an incomplete blacklist.

## Checkpoint and troubleshooting

```bash
! ./deny-socket errno ./socket-probe socket
./deny-socket errno ./socket-probe socketpair
```

- If `seccomp.h` or `libseccomp.pc` is absent, repair the documented VM provisioning: Fedora uses `libseccomp-devel` and `pkgconf-pkg-config`; Ubuntu uses `libseccomp-dev` and `pkg-config`. Do not guess include paths or disable filtering to get a pass.
- If kill mode emits no probe line, that is expected: the kernel terminates at the denied syscall.
- Checkpoint: explain why both observed actions enforce the same rule but have different failure semantics, and why neither blocks `socketpair`.

## Replay and source truth

From this workspace, `cd ../..` then `./lab-reset 06.02` discards this lesson's generated work after confirmation. A filter installed in a child does not modify your parent shell or global kernel policy; do not attempt a host-wide "seccomp reset."

The kernel's [seccomp filter documentation](https://docs.kernel.org/userspace-api/seccomp_filter.html) defines return actions and filter inheritance. The library's [seccomp_init manual](https://github.com/seccomp/libseccomp/blob/main/doc/man/man3/seccomp_init.3) defines the default action/context.
