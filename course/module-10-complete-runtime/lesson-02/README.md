# 10.02 - Seal filesystem and syscall policy before exec

## Outcomes and prerequisites

Complete 10.01 and the native-code work in Modules 01, 05, and 06. You will run the same fixed native probe before and after a guard, preserve an allowed read, and observe both protected-file and direct-IP denial. This is the inner guard, not the complete outer runtime.

## Concepts before commands

**Composition** requires controls to remain effective together. A seccomp allowlist must allow the intended workload's syscalls while leaving later policy modification unavailable. A Landlock policy must allow the executable and its required data without exposing unrelated files.

A **static executable** includes the needed library code in its binary. It avoids a dynamic loader needing to open shared libraries after filesystem restrictions are installed. Static linking is a teaching simplification, not a universal security guarantee.

This guard permits read-only observations under the current process's `/proc/self` directory and `/sys/fs/cgroup`. These are explicit exceptions, not a private PID/mount view. It does not grant all of `/proc`. Its own process identity survives `exec`, so the self-directory rule still applies to the final workload.

## Prepare and read both sources

From the course root:

```bash
./lab-start 10.02
cd .student/10.02
pwd
ls -l runtime_guard.c guard_probe.c
cat runtime_guard.c
cat guard_probe.c
```

Use `nano runtime_guard.c` to navigate the C functions. Do not edit canonical course files. Read before compiling.

### The native guard

<!-- source: course/module-10-complete-runtime/lesson-02/runtime_guard.c format=code -->
```c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/landlock.h>
#include <linux/close_range.h>
#include <seccomp.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/prctl.h>
#include <sys/socket.h>
#include <sys/syscall.h>
#include <unistd.h>

static int create_ruleset(const struct landlock_ruleset_attr *attr, size_t size, __u32 flags) {
    return syscall(SYS_landlock_create_ruleset, attr, size, flags);
}

static int add_path_rule(int ruleset_fd, const char *path, __u64 access) {
    int path_fd = open(path, O_PATH | O_CLOEXEC);
    if (path_fd == -1)
        return -1;
    struct landlock_path_beneath_attr rule = {.allowed_access = access, .parent_fd = path_fd};
    int result = syscall(SYS_landlock_add_rule, ruleset_fd, LANDLOCK_RULE_PATH_BENEATH, &rule, 0);
    close(path_fd);
    return result;
}

static __u64 supported_rights(int abi) {
    __u64 rights = LANDLOCK_ACCESS_FS_EXECUTE | LANDLOCK_ACCESS_FS_WRITE_FILE |
                   LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_READ_DIR |
                   LANDLOCK_ACCESS_FS_REMOVE_DIR | LANDLOCK_ACCESS_FS_REMOVE_FILE |
                   LANDLOCK_ACCESS_FS_MAKE_CHAR | LANDLOCK_ACCESS_FS_MAKE_DIR |
                   LANDLOCK_ACCESS_FS_MAKE_REG | LANDLOCK_ACCESS_FS_MAKE_SOCK |
                   LANDLOCK_ACCESS_FS_MAKE_FIFO | LANDLOCK_ACCESS_FS_MAKE_BLOCK |
                   LANDLOCK_ACCESS_FS_MAKE_SYM;
    if (abi >= 2)
        rights |= LANDLOCK_ACCESS_FS_REFER;
    if (abi >= 3)
        rights |= LANDLOCK_ACCESS_FS_TRUNCATE;
#ifdef LANDLOCK_ACCESS_FS_IOCTL_DEV
    if (abi >= 5)
        rights |= LANDLOCK_ACCESS_FS_IOCTL_DEV;
#endif
#ifdef LANDLOCK_ACCESS_FS_RESOLVE_UNIX
    if (abi >= 9)
        rights |= LANDLOCK_ACCESS_FS_RESOLVE_UNIX;
#endif
    return rights;
}

static int install_landlock(const char *allowed_root) {
    int abi = create_ruleset(NULL, 0, LANDLOCK_CREATE_RULESET_VERSION);
    if (abi < 1)
        return -1;
    __u64 handled = supported_rights(abi);
    __u64 read_execute = LANDLOCK_ACCESS_FS_EXECUTE | LANDLOCK_ACCESS_FS_READ_FILE |
                          LANDLOCK_ACCESS_FS_READ_DIR;
    __u64 read_only = LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_READ_DIR;
#ifdef LANDLOCK_ACCESS_FS_RESOLVE_UNIX
    /* The broker is intentionally reachable only below the workload root. */
    if (abi >= 9)
        read_execute |= LANDLOCK_ACCESS_FS_RESOLVE_UNIX;
#endif
    fprintf(stderr, "Landlock ABI %d; explicit build-known filesystem policy\n", abi);
    struct landlock_ruleset_attr ruleset = {.handled_access_fs = handled};
    int ruleset_fd = create_ruleset(&ruleset, sizeof(ruleset), 0);
    if (ruleset_fd == -1)
        return -1;
    if (add_path_rule(ruleset_fd, allowed_root, read_execute) == -1 ||
        add_path_rule(ruleset_fd, "/proc/self", read_only) == -1 ||
        add_path_rule(ruleset_fd, "/sys/fs/cgroup", read_only) == -1) {
        close(ruleset_fd);
        return -1;
    }
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) == -1 ||
        syscall(SYS_landlock_restrict_self, ruleset_fd, 0) == -1) {
        close(ruleset_fd);
        return -1;
    }
    close(ruleset_fd);
    return 0;
}

static int allow_name(scmp_filter_ctx context, const char *name) {
    int number = seccomp_syscall_resolve_name(name);
    return number == __NR_SCMP_ERROR ? 0 : seccomp_rule_add(context, SCMP_ACT_ALLOW, number, 0);
}

static int install_seccomp(void) {
    const char *allowed[] = {
        "execve", "read", "write", "close", "openat", "brk", "mmap", "mprotect",
        "munmap", "set_tid_address", "set_robust_list", "prlimit64", "readlink",
        "readlinkat", "getrandom", "rseq", "arch_prctl", "fstat", "newfstatat",
        "faccessat", "lseek", "rt_sigaction", "rt_sigprocmask", "statx", "connect",
        "shutdown", "exit", "exit_group"
    };
    scmp_filter_ctx context = seccomp_init(SCMP_ACT_ERRNO(EPERM));
    if (!context)
        return -1;
    for (size_t index = 0; index < sizeof(allowed) / sizeof(allowed[0]); index++) {
        int error = allow_name(context, allowed[index]);
        if (error < 0) {
            seccomp_release(context);
            errno = -error;
            return -1;
        }
    }
    int socket_number = seccomp_syscall_resolve_name("socket");
    int error = socket_number == __NR_SCMP_ERROR ? -EINVAL :
        seccomp_rule_add(context, SCMP_ACT_ALLOW, socket_number, 1,
                         SCMP_A0(SCMP_CMP_EQ, AF_UNIX));
    if (error == 0)
        error = seccomp_load(context);
    if (error < 0) {
        seccomp_release(context);
        errno = -error;
        return -1;
    }
    seccomp_release(context);
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: %s ALLOWED_ROOT COMMAND [ARG...]\n", argv[0]);
        return 2;
    }
    if (syscall(SYS_close_range, 3U, ~0U, CLOSE_RANGE_CLOEXEC) == -1) {
        perror("mark inherited descriptors close-on-exec");
        return 1;
    }
    if (install_landlock(argv[1]) == -1) {
        perror("install Landlock");
        return 1;
    }
    if (install_seccomp() == -1) {
        perror("install seccomp");
        return 1;
    }
    execv(argv[2], &argv[2]);
    perror("execv");
    return 1;
}
```
<!-- /source -->

### Source, line by line

- The headers provide Linux policy constants, syscall numbers, descriptor flags, libseccomp, and normal C error/I/O declarations.
- `create_ruleset` calls the Landlock syscall directly, as in Module 05.
- `add_path_rule` anchors a path with an `O_PATH` descriptor, builds a path-beneath rule, adds it, and closes that temporary descriptor.
- `supported_rights` constructs a bitmask of named filesystem rights. ABI checks gate later rights; preprocessor checks separately gate constants available in build headers.
- `install_landlock` queries the running ABI. It distinguishes the full handled set from the smaller grants: execute/read beneath the workload root and read-only observation directories.
- Filesystem operations covered by handled rights but not granted are denied. Unnamed future rights are not automatically covered; ABI number alone is not proof of complete future-right coverage.
- Unix-socket path resolution is additionally scoped only when **both** ABI 9 support and its build-header constant exist. The validated Fedora ABI 7 baseline does not demonstrate that newer restriction.
- `PR_SET_NO_NEW_PRIVS` precedes self-restriction. Failure returns before workload execution.
- `allow_name` resolves syscall names for the native architecture. Names unavailable on that ABI are not granted; available-rule errors stop setup.
- `install_seccomp` begins with EPERM as the default. Its small allowlist supports the static observation workload and Unix-socket operation, not general Python or shell execution.
- The separate `socket` rule checks argument zero for `AF_UNIX`. Other address families remain denied. Allowing `connect` does not itself authorize the operation carried over a permitted Unix socket.
- libseccomp reports negative error numbers; the helper converts them into `errno` before the caller prints a diagnostic.
- `main` marks inherited descriptors 3 and above close-on-exec. Failure stops rather than leaving inherited authority available.
- Landlock is installed before seccomp. Finally, `execv` replaces the guard with the supplied executable while preserving separate argv elements.
- An `execv` return means execution failed; it prints an error and exits nonzero.

The inner guard does not create namespaces, empty the environment, lower all capability sets, or impose cgroup limits. Those outer steps come in 10.03. A successful inner-guard demonstration must not be described as a complete runtime.

### The observation program

<!-- source: course/module-10-complete-runtime/lesson-02/guard_probe.c format=code -->
```c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

static int readable(const char *path) {
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd == -1)
        return 0;
    char byte;
    int ok = read(fd, &byte, 1) == 1;
    close(fd);
    return ok;
}

static int status_number(const char *name) {
    FILE *stream = fopen("/proc/self/status", "r");
    char line[256];
    int value = -1;
    while (stream && fgets(line, sizeof(line), stream))
        if (sscanf(line, name, &value) == 1)
            break;
    if (stream)
        fclose(stream);
    return value;
}

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s ALLOWED_FILE PROTECTED_FILE\n", argv[0]);
        return 2;
    }
    int allowed = readable(argv[1]);
    errno = 0;
    int protected = readable(argv[2]);
    int protected_errno = errno;
    errno = 0;
    int inet = socket(AF_INET, SOCK_STREAM, 0);
    int inet_errno = errno;
    if (inet != -1)
        close(inet);
    printf("allowed=%d protected=%d protected_errno=%s inet_fd=%d inet_errno=%s nnp=%d seccomp=%d\n",
           allowed, protected, strerror(protected_errno), inet, strerror(inet_errno),
           status_number("NoNewPrivs:\t%d"), status_number("Seccomp:\t%d"));
    return 0;
}
```
<!-- /source -->

### Source, line by line

- `readable` opens a file and attempts a one-byte read. It closes the descriptor whether the read succeeds or not.
- `status_number` opens this process's status file, scans for one named field, and returns -1 when no usable value was observed.
- `main` requires an allowed and protected filename. It performs actual reads, rather than trusting path text or mode bits.
- Resetting and saving `errno` keeps the protected-open and socket observations separate.
- The IPv4 socket is closed if creation succeeds. The probe sends no network traffic.
- The final line prints observed operations and kernel-reported no-new-privileges/seccomp state. The observer returns 0 on completion even when a tested operation was denied; inspect its fields.

## Exercise 1 - Compile and establish a working baseline

```bash
gcc -O2 -Wall -Wextra -static runtime_guard.c -o runtime_guard -lseccomp
gcc -O2 -Wall -Wextra -static guard_probe.c -o guard_probe
NE_DEMO=$(mktemp -d "$PWD/d.XXXXXX")
mkdir "$NE_DEMO/allowed"
cp guard_probe "$NE_DEMO/allowed/guard_probe"
printf 'allowed\n' > "$NE_DEMO/allowed/input.txt"
printf 'synthetic-protected\n' > "$NE_DEMO/protected.txt"
"$NE_DEMO/allowed/guard_probe" "$NE_DEMO/allowed/input.txt" "$NE_DEMO/protected.txt" > baseline.txt
cat baseline.txt
```

Warnings remain visible; only the guard links libseccomp. The exact new temporary directory is inside this prepared workspace, so scoped lesson reset owns the files. The protected file is synthetic and readable by your account.

Expect `allowed=1 protected=1` and a nonnegative IPv4 descriptor. Existing no-new-privileges/seccomp values depend on the parent environment; do not assume they must start at zero. The intentional incomplete control is launching a trusted observer without enforcing a boundary.

## Exercise 2 - Apply the ordered repair

```bash
./runtime_guard "$NE_DEMO/allowed" "$NE_DEMO/allowed/guard_probe" \
  "$NE_DEMO/allowed/input.txt" "$NE_DEMO/protected.txt" > guarded.txt
cat guarded.txt
```

Expect the equivalent of:

```text
allowed=1 protected=0 protected_errno=Permission denied inet_fd=-1 inet_errno=Operation not permitted nnp=1 seccomp=2
```

The allowed read proves useful functionality remains. The same synthetic protected file was readable in the baseline but is now denied. The IPv4 socket creation is denied separately. Status fields show the restrictions survived `exec`; neither field alone proves policy content.

Error wording can vary with locale; the numeric/Boolean fields are the stable part. The ABI diagnostic goes to stderr, while the observation is saved on stdout.

## Checkpoint, troubleshooting, and replay

```bash
python3 - <<'PY'
from pathlib import Path
import re

baseline = Path("baseline.txt").read_text()
guarded = Path("guarded.txt").read_text()
assert "allowed=1 protected=1" in baseline
assert int(re.search(r"inet_fd=(-?\d+)", baseline).group(1)) >= 0
assert "allowed=1 protected=0" in guarded
assert "inet_fd=-1" in guarded
assert "nnp=1 seccomp=2" in guarded
print("FILESYSTEM AND SYSCALL COMPOSITION: PASS")
PY
```

Explain why successful seccomp installation does not prove a correct pathname policy, and why one protected-file denial says nothing about the availability of a different socket family. Lesson 10.03 will demonstrate the permitted Unix-socket path under the complete composition.

If static linking fails, run `../../scripts/linux-preflight` and inspect the distribution's documented development/static-library prerequisites. On Fedora these include `glibc-static` and `libseccomp-static`; do not weaken filesystem policy to expose dynamic libraries. If `execv` fails, verify that the executable was copied beneath the allowed root. If Landlock is unavailable, repair the supported VM baseline; do not use a permissive fallback.

Return with `cd ../..`; `./lab-reset 10.02` removes the exact prepared workspace, binaries, and synthetic directory. There are no background services. Keep SELinux enforcement enabled.

## Source truth

The [Landlock userspace documentation](https://cdn.kernel.org/doc/html/latest/userspace-api/landlock.html) distinguishes handled rights, grants, and ABI availability. The [seccomp filter documentation](https://docs.kernel.org/userspace-api/seccomp_filter.html) describes syscall/argument filtering. These APIs compose restrictions; they do not certify the completeness of this course's policy.
