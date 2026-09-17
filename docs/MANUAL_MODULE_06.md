# Module 06 - Constrain syscalls with seccomp

Measure a real workload before writing policy, observe the operational difference between errno and kill actions, then launch a static child under a native-architecture default-deny libseccomp filter.

Play in order: `06.01`, `06.02`, `06.03`, then `module-06`.

Outcomes:

- collect and interpret a syscall profile without treating one trace as universal truth;
- compare `SCMP_ACT_ERRNO` and `SCMP_ACT_KILL_PROCESS` using an observable denied call;
- reproduce an alternate-interface bypass against a narrow blacklist;
- construct a native-architecture default-deny filter and prove it is active before `exec`;
- preserve a stated workload while denying socket, socket-pair, ptrace, and an unlisted syscall;
- explain why syscall filtering is not pathname authorization, resource accounting, or network destination policy.

Prerequisites: Modules 01-05, Linux, `strace`, a C compiler with static libc development files, and libseccomp headers/library discoverable through `pkg-config`. All probes are local and unprivileged.

<!-- PAGEBREAK -->

# 06.01 - Measure the workload before filtering

## Goal

Collect the syscalls of one explicit file-copy workload, separate startup activity from application intent, and demonstrate why a profile is evidence for policy design rather than a permanent universal allowlist.

## Exercise 1 - Build and run without tracing

Complete source of `workload.c`:

```c
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s INPUT OUTPUT\n", argv[0]);
        return 2;
    }
    int input = open(argv[1], O_RDONLY);
    int output = open(argv[2], O_WRONLY | O_CREAT | O_TRUNC, 0600);
    if (input == -1 || output == -1) {
        perror("open");
        return 1;
    }
    char buffer[256];
    ssize_t count;
    while ((count = read(input, buffer, sizeof(buffer))) > 0)
        if (write(output, buffer, (size_t)count) != count)
            return 1;
    close(input);
    close(output);
    return count < 0;
}
```

### Source, line by line

- The program requires input and output pathnames and returns usage status 2 for any other interface.
- `open` requests read authority for one path and create/truncate/write authority for the other. The kernel may implement libc `open` with `openat`.
- The fixed buffer bounds each transfer. `read` ends at zero and a negative result becomes failure.
- `write` is checked rather than assumed. Both descriptors are closed on normal completion.

```bash
cc -std=c11 -Wall -Wextra -Werror -O2 workload.c -o workload
printf 'measured-data\n' > input.txt
./workload input.txt output.txt
cmp input.txt output.txt
```

### Line by line

- The compiler rejects warnings and writes only the lesson-local executable.
- `printf` creates synthetic input; `cmp` independently verifies exact output.
- Expected: no output and status zero. This establishes the functional baseline before tracing changes observation.

## Exercise 2 - Capture counts and exact events

```bash
strace -f -qq -c ./workload input.txt output.txt
strace -f -qq -o trace.txt ./workload input.txt output.txt
sed -E 's/^[0-9]+ +([^ (]+).*/\1/' trace.txt | sort -u
```

### Line by line

- `-f` follows children; this workload creates none, but the policy is explicit.
- `-qq` removes attach/detach chatter. `-c` reports aggregate syscall counts and timing.
- The second run writes complete events to `trace.txt` rather than mixing them with workload output.
- `sed` extracts syscall names from PID-prefixed lines; `sort -u` creates the observed set.
- Expect file operations plus dynamic-loader and process-startup calls such as `mmap`, `mprotect`, `brk`, and architecture-dependent setup. Exact names and counts vary by libc, architecture, kernel, and input.

The trace proves calls observed on this run. It does not prove unobserved error paths are unnecessary or that every observed syscall should be broadly allowed.

## Exercise 3 - Break the incomplete profile

Trace a zero-length input and compare it with the nonempty run:

```bash
: > empty.txt
strace -f -qq -o empty-trace.txt ./workload empty.txt empty-output.txt
grep -c 'write(' trace.txt
grep -c 'write(' empty-trace.txt
```

### Line by line

- `:` is a shell builtin that succeeds; redirection truncates `empty.txt` to zero bytes.
- The empty workload never enters its data-write body, so its observed set can omit a write that the nonempty input requires.
- `grep -c` prints counts. A zero count returns status 1, so inspect the number instead of chaining it under `set -e`.

Intentional mistake: treat only `empty-trace.txt` as the policy specification. The nonempty workload would then fail. Repair the reasoning by defining representative success and error cases first, combining their measurements, and reviewing each allowed call against the workload contract.

## Checkpoint and troubleshooting

```bash
cmp input.txt output.txt
grep -q 'openat(' trace.txt
grep -q 'read(' trace.txt
```

- If `strace` is blocked, use the documented disposable VM; do not weaken a work host.
- A libc may use `openat` even though the source says `open`; policy applies to kernel ABI calls, not C function spelling.
- Checkpoint: name one observed loader syscall and one input-dependent syscall, and explain why measurement alone is not least privilege.

<!-- PAGEBREAK -->

# 06.02 - Compare errno, kill, and blacklist bypass

## Goal

Install one observable deny rule, compare recoverable `EPERM` with process termination, then bypass a single-syscall blacklist through a related kernel interface.

## Exercise 1 - Build the probe and filter launcher

Complete probe source:

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

### Source, line by line

- `errno` records why a failed call returned `-1`.
- `socket` requests one local AF_UNIX endpoint; `socketpair` requests a connected local pair without any external network.
- Successful pair descriptors are closed. The printed result makes filter behavior visible.
- A denied call returns nonzero; an allowed call returns zero.

Complete launcher source:

```c
#include <errno.h>
#include <seccomp.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 3) {
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

### Source, line by line

- `seccomp_init(SCMP_ACT_ALLOW)` creates a blacklist: every syscall is allowed unless a rule says otherwise.
- The selected rule either returns `EPERM` or kills the whole process when `socket` is attempted.
- Every libseccomp operation is checked. Failure cannot fall through to an unfiltered `execv`.
- `seccomp_load` installs the filter on the launcher; seccomp then persists across `exec` into the probe.
- `seccomp_release` frees userspace policy memory, not the loaded kernel filter.

```bash
cc -std=c11 -Wall -Wextra -Werror -O2 -static socket_probe.c -o socket-probe
cc -std=c11 -Wall -Wextra -Werror -O2 deny_socket.c -o deny-socket $(pkg-config --cflags --libs libseccomp)
```

The first binary is static so its runtime does not complicate this one-rule observation. `pkg-config` supplies the distribution's libseccomp flags.

## Exercise 2 - Observe errno and kill actions

```bash
./deny-socket errno ./socket-probe socket || test "$?" -eq 1
set +e
./deny-socket kill ./socket-probe socket
status=$?
set -e
printf 'kill_status=%s\n' "$status"
```

### Line by line

- Errno mode lets the probe continue: expect `result=-1 errno=1` and status 1.
- `set +e` permits the shell to observe an expected fatal signal rather than aborting a scripted session.
- Kill mode prevents the probe from printing its post-call result. A shell commonly reports `Bad system call`; status is normally 128 plus `SIGSYS`.
- `set -e` restores fail-fast behavior. The status proves termination but does not identify a complete policy.

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

- If `seccomp.h` or `libseccomp.pc` is absent, install the documented `libseccomp-dev` and `pkg-config` packages in the disposable VM.
- If kill mode emits no probe line, that is expected: the kernel terminates at the denied syscall.
- Checkpoint: explain why both observed actions enforce the same rule but have different failure semantics, and why neither blocks `socketpair`.

<!-- PAGEBREAK -->

# 06.03 - Launch with a native default-deny filter

## Goal

Turn the measured workload into a native-architecture allowlist, prove filter state inside the child, and preserve file access while denying unlisted kernel interfaces.

## Exercise 1 - Read the observation probe

Complete `policy_probe.c`:

```c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/ptrace.h>
#include <sys/socket.h>
#include <sys/syscall.h>
#include <unistd.h>

static void report(long result) {
    char line[96];
    int count = snprintf(line, sizeof(line), "result=%ld errno=%d\n", result, errno);
    if (write(STDOUT_FILENO, line, (size_t)count) != count)
        _exit(1);
}

int main(int argc, char **argv) {
    if (argc < 2)
        return 2;
    if (strcmp(argv[1], "status") == 0) {
        char buffer[4096] = {0};
        int fd = open("/proc/self/status", O_RDONLY);
        ssize_t count = read(fd, buffer, sizeof(buffer) - 1);
        close(fd);
        if (count < 0)
            return 1;
        char *nnp = strstr(buffer, "NoNewPrivs:");
        char *seccomp = strstr(buffer, "Seccomp:");
        dprintf(STDOUT_FILENO, "%.13s\n%.10s\n", nnp, seccomp);
        return 0;
    }
    if (strcmp(argv[1], "file") == 0 && argc == 3) {
        int fd = open(argv[2], O_RDONLY);
        char buffer[256];
        ssize_t count = read(fd, buffer, sizeof(buffer));
        return count > 0 && write(STDOUT_FILENO, buffer, (size_t)count) == count ? 0 : 1;
    }
    errno = 0;
    if (strcmp(argv[1], "socket") == 0)
        report(socket(AF_UNIX, SOCK_STREAM, 0));
    else if (strcmp(argv[1], "socketpair") == 0) {
        int pair[2];
        report(socketpair(AF_UNIX, SOCK_STREAM, 0, pair));
    } else if (strcmp(argv[1], "ptrace") == 0)
        report(ptrace(PTRACE_TRACEME, 0, NULL, NULL));
    else
        report(syscall(SYS_getppid));
    return 0;
}
```

### Line by line

- `status` reads kernel-reported process state from procfs after `exec`; the launcher cannot substitute its own pre-filter claim.
- `file` uses normal libc `open`, which becomes the kernel's `openat` on this platform.
- The denial modes invoke distinct syscalls and report raw result plus `errno` through allowed output.
- The fallback uses raw `SYS_getppid`, a harmless syscall intentionally absent from the allowlist.

Read the full small source before compiling:

```bash
sed -n '1,240p' policy_probe.c
cc -std=c11 -Wall -Wextra -Werror -O2 -static policy_probe.c -o policy-probe
```

- `sed` displays the complete source; no required behavior is hidden.
- The static binary makes its startup surface stable enough for this VM exercise.

## Exercise 2 - Build and inspect the policy

Complete `allowlist.c`:

```c
#define _GNU_SOURCE
#include <errno.h>
#include <seccomp.h>
#include <stdio.h>
#include <string.h>
#include <sys/prctl.h>
#include <unistd.h>

static int allow_name(scmp_filter_ctx context, const char *name) {
    int number = seccomp_syscall_resolve_name(name);
    return number == __NR_SCMP_ERROR ? 0 : seccomp_rule_add(context, SCMP_ACT_ALLOW, number, 0);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s COMMAND [ARG...]\n", argv[0]);
        return 2;
    }
    const char *allowed[] = {
        "execve", "read", "write", "close", "openat", "brk", "mmap", "mprotect",
        "munmap", "set_tid_address", "set_robust_list", "prlimit64", "readlink", "readlinkat",
        "getrandom", "rseq", "arch_prctl", "fstat", "newfstatat", "faccessat",
        "exit", "exit_group"
    };
    scmp_filter_ctx context = seccomp_init(SCMP_ACT_ERRNO(EPERM));
    uint32_t native = seccomp_arch_native();
    if (!context || native == 0 || seccomp_arch_exist(context, native) < 0) {
        fprintf(stderr, "native architecture unavailable\n");
        seccomp_release(context);
        return 1;
    }
    for (size_t index = 0; index < sizeof(allowed) / sizeof(allowed[0]); index++) {
        if (allow_name(context, allowed[index]) < 0) {
            fprintf(stderr, "cannot allow %s\n", allowed[index]);
            seccomp_release(context);
            return 1;
        }
    }
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0 || seccomp_load(context) < 0) {
        perror("install seccomp");
        seccomp_release(context);
        return 1;
    }
    seccomp_release(context);
    execv(argv[1], &argv[1]);
    perror("execv");
    return 1;
}
```

### Line by line

- `SCMP_ACT_ERRNO(EPERM)` is the default, so an omitted syscall is denied rather than silently allowed.
- `seccomp_arch_native` obtains libseccomp's token for the running architecture; `seccomp_arch_exist` verifies the context contains it.
- Names are resolved for the native architecture. A name absent from that architecture is skipped, while a rule failure for a present syscall stops setup. This keeps the measured static-startup set portable between the supported arm64 and x86-64 baselines without hard-coded numbers.
- The list includes static startup, exact argv execution, proc/file reads, output, memory setup, and exit. It deliberately omits socket, socketpair, ptrace, and getppid.
- `no_new_privs` is explicit before loading. Both calls are checked, and `execv` is reachable only after a successful load.
- libseccomp generates the BPF architecture check and syscall-number comparisons; hand-coded numeric syscall tables are avoided.

Display the full source and build it:

```bash
sed -n '1,260p' allowlist.c
cc -std=c11 -Wall -Wextra -Werror -O2 allowlist.c -o allowlist $(pkg-config --cflags --libs libseccomp)
```

## Exercise 3 - Verify effective state and denials

```bash
./allowlist ./policy-probe status
printf 'allowed-file\n' > note.txt
./allowlist ./policy-probe file note.txt
./allowlist ./policy-probe socket
./allowlist ./policy-probe socketpair
./allowlist ./policy-probe ptrace
./allowlist ./policy-probe unexpected
```

### Line by line

- Status must show `NoNewPrivs: 1` and `Seccomp: 2`; mode 2 is filter mode.
- The file workload succeeds because `openat`, `read`, `write`, and `close` are in scope.
- Every denial probe should report `result=-1 errno=1`, including both socket interfaces and the unlisted harmless syscall.
- The probes return normally because the default action is errno. This permits evidence collection.

Intentional failure: create a temporary copy that adds `"getppid",` to the allowed-name array, rebuild it, and run `unexpected`. It returns a real parent PID, proving that default-deny still depends on a justified allowlist. Delete the temporary copy, return to the shipped list, and require `result=-1 errno=1`.

The file test is also a boundary lesson: seccomp allowed `openat`, so it cannot distinguish `note.txt` from another pathname. Compose it with Module 05's `openat2`/Landlock layer for pathname policy. It likewise does not meter CPU/memory or authorize network destinations.

## Checkpoint and troubleshooting

```bash
./allowlist ./policy-probe status | grep -q 'Seccomp:[[:space:]]*2'
test "$(./allowlist ./policy-probe unexpected)" = 'result=-1 errno=1'
```

- If the static probe fails before output, compare its `strace` surface with the allowlist on this supported VM and add only justified startup calls.
- `EPERM` from `seccomp_load` usually means `no_new_privs` was not set or policy setup was reordered.
- Checkpoint: identify the functional syscalls, startup syscalls, deliberately denied syscalls, and the separate pathname assumption.

<!-- PAGEBREAK -->

# Module 06 independent lab - Default-deny syscall launcher

Implement `seccomp_guard.c`. The grader builds and invokes:

```text
seccomp-guard COMMAND [ARG...]
```

The command is an exact executable path to a static local observation probe. Your launcher must:

- validate the interface and preserve the structured argv vector;
- create a libseccomp context whose default action returns `EPERM`;
- explicitly confirm the context's native architecture;
- allow only the calls needed for static startup, exact `execve`, status/file reads, bounded output, memory setup, and exit as practiced in Lesson 06.03;
- set `PR_SET_NO_NEW_PRIVS` and successfully load the filter before `exec`;
- fail closed if any context, architecture, syscall-resolution, rule, privilege-floor, filter-load, or exec step fails.

The fresh external grader compiles a static probe and checks functional execution, `/proc/self/status` evidence, an allowed file read, direct socket denial, socket-pair denial, ptrace denial, and denial of a harmless syscall omitted from the workload. It evaluates a read-only copy of your source.

The starter only validates argv and calls `execv`, so the workload runs but every confinement property fails. Use libseccomp names rather than architecture-specific numeric syscall constants. Do not add network access, privilege, or a kill action; errno results are required so the grader can observe every denial.

```bash
cc -std=c11 -Wall -Wextra -Werror -O2 seccomp_guard.c -o seccomp-guard $(pkg-config --cflags --libs libseccomp)
../../lab-grade module-06
../../lab-grade module-06 --mode exam
```

### Test commands, line by line

- The compiler and warning flags match the guided launcher; `pkg-config` supplies only the local libseccomp build flags.
- Practice mode creates a fresh probe and names failed properties with lesson references.
- Exam mode repeats fresh behavior checks but suppresses repair-oriented references.

The lab deliberately withholds a complete implementation. Start from the ordering and justified call set you measured and explained in Lesson 06.03. Seccomp is one runtime layer: this lab does not claim pathname policy, resource accounting, network destination authorization, or protection from already-open descriptors.
