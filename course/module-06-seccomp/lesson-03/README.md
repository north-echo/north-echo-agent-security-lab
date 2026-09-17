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
