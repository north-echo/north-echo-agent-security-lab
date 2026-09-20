<!-- source: course/module-10-complete-runtime/README.md format=markdown -->
# Module 10 - Compose a complete agent runtime

Assemble the controls from Modules 01-09 in dependency order, then ask a known workload and kernel for evidence of their combined effects. This instrumented teaching runtime has bounded workload resources, fresh user/network namespaces, reduced capabilities, `no_new_privs`, Landlock filesystem policy, default-deny seccomp, an intended capability-mediated Unix-socket exchange, a fixed workload environment, and exact owned-unit collection checks. It is not a production general-purpose agent sandbox.

Play in order: `10.01`, `10.02`, `10.03`, then `module-10`.

Outcomes:

- distinguish launch dependencies from an arbitrary checklist order;
- apply pathname policy before a syscall filter can remove the setup syscalls;
- keep the broker outside the restricted network namespace while demonstrating the intended pathname Unix-socket operation;
- place the launcher and every descendant under cgroup limits before workload creation;
- attest effective namespaces, capabilities, Landlock effects, seccomp mode, cgroup values, credential absence, and broker success;
- propagate workload failure and synchronously collect the exact transient unit.

All data, credentials, capabilities, services, paths, and requests are synthetic and local. The module creates no veth pair, route, firewall rule, public request, real credential, or production target. Prerequisites are Modules 01-09 and the Linux features reported by `./scripts/linux-preflight`.

## Learning route and limits

First validate a dependency plan without claiming it installed controls. Next
compare a native observer before and after the inner guard. Finally compose the
outer layers and compare separate evidence for workload effects, synthetic
broker use, and exact unit/socket teardown. A small static worker bridges to
ordered batch practice without supplying a capstone implementation.

This design does not create private PID/mount views. It permits selected
read-only observations and, on the validated Landlock ABI 7 kernel, does not
enforce ABI 9 pathname Unix-socket-resolution restrictions. Do not claim the
intended broker is the only reachable Unix socket. The tiny opaque-token broker
is a composition fixture, not the full Module 09 authorization protocol.

An attestation here is a local report from known teaching code, not cryptographic
remote attestation or proof that arbitrary workload code tells the truth.
Launcher output capture is not independently byte-bounded. Keep the exercises
small, synthetic, and inside the disposable VM; preserve SELinux enforcement.
<!-- /source -->

---

<!-- source: course/module-10-complete-runtime/lesson-01/README.md format=markdown -->
# 10.01 - Order the complete runtime by dependency

## Outcomes and prerequisites

Complete Modules 01-09. You will turn the controls into a dependency plan, observe an invalid ordering, and repair it without mistaking plan validation for kernel enforcement.

## Concepts before commands

A **dependency** means one action needs a state established by another. It is stronger than a stylistic preference. A **partial order** constrains some pairs without requiring every independent action to have one universal position.

For this runtime, cgroup entry must precede namespace/workload creation so descendants begin inside the resource budget. User-namespace setup precedes privilege reduction because mapping a namespace-local root creates capability state that must then be reduced. Landlock setup precedes this seccomp filter because the final syscall allowlist does not include the Landlock setup operations.

The broker must be ready before the caller tries its mediated operation. Starting it before namespace entry is a convenient design dependency here, not a kernel law saying every broker must start before every network namespace. Pathname sockets can remain reachable through a shared filesystem.

Finally, process exit and unit collection are different observations. Requesting `--collect` is not enough by itself; later code checks that the exact unit is absent.

## Prepare and read the validator and data

From the course root:

```bash
./lab-start 10.01
cd .student/10.01
pwd
ls -l check_order.py broken-plan.json repaired-plan.json
cat check_order.py
cat broken-plan.json
cat repaired-plan.json
```

Use `nano check_order.py` or `nano challenge-plan.json` when navigating or editing. The JSON files are data submitted to the validator, not programs that install kernel controls.

### The plan validator

```python
#!/usr/bin/env python3
"""Validate a complete-runtime launch plan against security dependencies."""

import json
import sys
from pathlib import Path

REQUIRED = {
    "start_broker",
    "enter_cgroup",
    "enter_namespaces",
    "drop_privilege",
    "apply_landlock",
    "apply_seccomp",
    "exec_workload",
    "collect_unit",
}

BEFORE = {
    ("start_broker", "enter_namespaces"),
    ("enter_cgroup", "enter_namespaces"),
    ("enter_namespaces", "drop_privilege"),
    ("drop_privilege", "apply_landlock"),
    ("apply_landlock", "apply_seccomp"),
    ("apply_seccomp", "exec_workload"),
    ("exec_workload", "collect_unit"),
}


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} PLAN.json", file=sys.stderr)
        return 2
    try:
        plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"invalid plan: {error}", file=sys.stderr)
        return 1
    if not isinstance(plan, list) or any(not isinstance(item, str) for item in plan):
        print("invalid plan: expected a JSON array of step names", file=sys.stderr)
        return 1
    if len(plan) != len(set(plan)):
        print("invalid plan: duplicate step", file=sys.stderr)
        return 1
    missing = sorted(REQUIRED - set(plan))
    extra = sorted(set(plan) - REQUIRED)
    if missing or extra:
        print(json.dumps({"ok": False, "missing": missing, "extra": extra}, sort_keys=True))
        return 1
    position = {name: index for index, name in enumerate(plan)}
    violations = sorted(f"{left} must precede {right}" for left, right in BEFORE if position[left] > position[right])
    print(json.dumps({"ok": not violations, "violations": violations}, sort_keys=True))
    return bool(violations)


if __name__ == "__main__":
    raise SystemExit(main())
```

### Source, line by line

- `REQUIRED` is a set of permitted, mandatory phase names. It does not encode their order.
- `BEFORE` is a set of two-element tuples. Each tuple represents one directed dependency: its left phase must precede its right phase.
- The argv guard requires one plan filename. File/JSON errors stop before examining order.
- The shape check requires a list of strings. A dictionary with plausible keys is not the expected plan interface.
- Comparing list length with set length detects duplicate phases.
- Set subtraction finds missing and unknown phases. Their sorted output makes diagnostics stable.
- The dictionary comprehension maps each phase to its list index.
- The final comprehension reports every edge whose positions are reversed, not just the first failure.
- `not violations` is true only for an empty violation list. Returning `bool(violations)` gives exit status 1 for an invalid ordering and 0 for a valid one.

### The deliberately broken plan

```json
[
  "start_broker",
  "enter_cgroup",
  "enter_namespaces",
  "drop_privilege",
  "apply_seccomp",
  "apply_landlock",
  "exec_workload",
  "collect_unit"
]
```

Every required name is present exactly once. The mistake is the relative position of `apply_seccomp` and `apply_landlock`. A checklist that merely searches for both words would miss it.

### The repaired plan

```json
[
  "start_broker",
  "enter_cgroup",
  "enter_namespaces",
  "drop_privilege",
  "apply_landlock",
  "apply_seccomp",
  "exec_workload",
  "collect_unit"
]
```

The repaired list places the filesystem setup before the final syscall restriction. `start_broker` and `enter_cgroup` both precede namespace entry; this graph does not require an edge between those two independent preparations.

## Exercise 1 - Predict the rejected edge

```bash
NE_BROKEN_STATUS=0
python3 check_order.py broken-plan.json > broken-result.json || NE_BROKEN_STATUS=$?
python3 -m json.tool broken-result.json
test "$NE_BROKEN_STATUS" -eq 1
python3 check_order.py repaired-plan.json > repaired-result.json
python3 -m json.tool repaired-result.json
```

Saving the expected failure through `||` avoids changing your interactive shell's error options. Expect `apply_landlock must precede apply_seccomp` in the broken result and an empty violation list in the repaired result.

These are statements about a data structure. No Landlock rules or seccomp filter have been installed by this script. The next lesson tests the actual ordered controls.

## Exercise 2 - Make a different ordering mistake

Copy the known plan, then move cgroup entry too late:

```bash
cp repaired-plan.json challenge-plan.json
python3 - <<'PY'
import json
from pathlib import Path

path = Path("challenge-plan.json")
steps = json.loads(path.read_text())
steps.remove("enter_cgroup")
steps.insert(3, "enter_cgroup")
path.write_text(json.dumps(steps) + "\n")
PY
NE_CHALLENGE_STATUS=0
python3 check_order.py challenge-plan.json > challenge-result.json || NE_CHALLENGE_STATUS=$?
python3 -m json.tool challenge-result.json
test "$NE_CHALLENGE_STATUS" -eq 1
```

`remove` deletes the earlier position; `insert(3,...)` places it after namespace/privilege setup in this list. The plan is still syntactically valid and contains all phases, but violates the requirement to establish resource containment before those descendants.

Open `nano challenge-plan.json`, move `enter_cgroup` before `enter_namespaces`, preserve commas and quoted strings, and save. Then run:

```bash
python3 check_order.py challenge-plan.json > challenge-repaired.json
python3 -m json.tool challenge-repaired.json
```

## Checkpoint, troubleshooting, and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

def result(name):
    return json.loads(Path(name).read_text())

assert "apply_landlock must precede apply_seccomp" in result("broken-result.json")["violations"]
assert "enter_cgroup must precede enter_namespaces" in result("challenge-result.json")["violations"]
for name in ("repaired-result.json", "challenge-repaired.json"):
    assert result(name) == {"ok": True, "violations": []}
print("LAUNCH DEPENDENCIES: PASS")
PY
```

For each edge, explain what the earlier action establishes or what the later action removes. Do not answer merely “because the list says so.” Also name one property this validator cannot prove: effective resource limits, actual privilege reduction, successful policy installation, or teardown.

If parsing fails, restore a JSON array; a syntax error is not the intended ordering observation. If an edge seems unnecessary, distinguish this particular implementation's requirements from universal kernel rules.

Return with `cd ../..`; `./lab-reset 10.01` removes the challenge and results. No service or kernel policy was created.

## Source truth

The [kernel seccomp documentation](https://docs.kernel.org/userspace-api/seccomp_filter.html) and [Landlock documentation](https://cdn.kernel.org/doc/html/latest/userspace-api/landlock.html) describe the mechanisms being composed. The dependency graph itself is this course runtime's design; a passing graph check is not evidence those mechanisms were applied.
<!-- /source -->

---

<!-- source: course/module-10-complete-runtime/lesson-02/README.md format=markdown -->
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
<!-- /source -->

---

<!-- source: course/module-10-complete-runtime/lesson-03/README.md format=markdown -->
# 10.03 - Launch, observe, and collect the composed runtime

## Outcomes and prerequisites

Complete 10.01-10.02 and Modules 01-09. You will compare an incomplete inner-only launch with the outer composition, interpret each effective-state field, and verify exact service collection. The final exercise bridges single-job execution to the independent batch capstone.

## Concepts before commands

The composition has several jobs: constrain resources before descendants start, create private user/network views, reduce privilege, clear the workload environment, install filesystem/syscall policy, permit one intended broker exchange, then collect owned runtime objects.

A **trusted computing base (TCB)** is the code and configuration whose correctness the design relies on. Here it includes the VM kernel, user service manager, launcher, guard, and broker. A valid filename does not establish that a guard's contents are trustworthy; the exercise supplies trusted code.

The word **attestation** in this small program means a local structured observation. It is not a hardware-signed report or proof that arbitrary malicious workload code tells the truth. The grader compiles its own known observer to check behavior independently.

Keep the baseline limits visible. This composition creates user/network namespaces, not private mount/PID namespaces. Its Landlock policy permits selected read-only observation paths. On the validated Fedora ABI 7 baseline, Landlock does not enforce the newer ABI 9 pathname Unix-socket-resolution right. Successful access to the intended broker is therefore **not proof that no other pathname Unix socket is reachable**. The minimal static workload and finite checks are not a production general-purpose agent sandbox.

## Prepare and locate the sources

From the course root:

```bash
./lab-start 10.03
cd .student/10.03
pwd
ls -l complete_runtime.py runtime_probe.c demo_broker.py batch_worker.c
cat complete_runtime.py
cat runtime_probe.c
cat demo_broker.py
cat batch_worker.c
```

The guard source from 10.02 remains available under the course tree for compilation. You read it in that lesson; do not edit it there. Every new local source is reproduced below.

### The outer launcher

```python
#!/usr/bin/env python3
"""Launch one synthetic workload through the North Echo containment stack."""

import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time


def integer(spec: dict, name: str, minimum: int, maximum: int) -> int:
    value = spec.get(name)
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer from {minimum} through {maximum}")
    return value


def validated(spec: dict) -> tuple[Path, Path, list[str], int, int, int]:
    fields = {"guard", "allowed_root", "command", "memory_max", "tasks_max", "cpu_percent"}
    if not isinstance(spec, dict) or set(spec) != fields:
        raise ValueError("spec must be an object with exactly the documented fields")
    if not all(isinstance(spec[name], str) for name in ("guard", "allowed_root")):
        raise ValueError("guard and allowed_root must be path strings")
    guard, root = Path(spec["guard"]), Path(spec["allowed_root"])
    command = spec["command"]
    if not guard.is_absolute() or not guard.is_file() or guard.is_symlink():
        raise ValueError("guard must be an absolute regular non-symlink path")
    if not root.is_absolute() or not root.is_dir() or root.is_symlink():
        raise ValueError("allowed_root must be an absolute directory without a symlink leaf")
    if not isinstance(command, list) or not command or any(
            not isinstance(item, str) or "\x00" in item for item in command):
        raise ValueError("command must be a nonempty argv string array")
    if not Path(command[0]).is_absolute():
        raise ValueError("command executable must be absolute")
    root = root.resolve(strict=True)
    if root == Path("/"):
        raise ValueError("the whole filesystem cannot be the workload root")
    executable = Path(command[0]).resolve(strict=True)
    if os.path.commonpath((root, executable)) != str(root) or not executable.is_file():
        raise ValueError("command executable must resolve beneath allowed_root")
    return (
        guard.resolve(strict=True), root, [str(executable), *command[1:]],
        integer(spec, "memory_max", 16 * 1024 * 1024, 1024 * 1024 * 1024),
        integer(spec, "tasks_max", 4, 256),
        integer(spec, "cpu_percent", 10, 100),
    )


def register_owner(client_env: dict) -> dict:
    workspace = Path(__file__).resolve().parent
    prepared = workspace.parent.name == ".student"
    target = workspace.name if prepared else "10.lab"
    if target not in {"10.03", "10.lab"}:
        raise ValueError("unsupported prepared runtime workspace")
    unit = f"north-echo-{os.getuid()}-{target.replace('.', '-')}-{secrets.token_hex(6)}.service"
    owner = {"unit": unit, "uid": os.getuid(),
             "description": f"North Echo {target} workspace={workspace}", "record": None}
    if prepared:
        control = workspace.parent.parent / "scripts/labctl.py"
        subprocess.run([sys.executable, str(control), "register-unit", target, unit],
                       check=True, capture_output=True, text=True, timeout=5, env=client_env)
    else:
        # The external grader copies this file into a separate owned directory.
        runtime = workspace / ".runtime"
        if runtime.is_symlink():
            raise ValueError("refusing a symlinked ownership directory")
        runtime.mkdir(mode=0o700, exist_ok=True)
        record = runtime / (unit + ".json")
        with record.open("x", encoding="utf-8") as stream:
            json.dump(owner, stream, sort_keys=True)
        owner["record"] = record
    return owner


def inspect_unit(owner: dict, client_env: dict) -> dict | None:
    run = subprocess.run(
        ["systemctl", "--user", "show", owner["unit"], "--property=LoadState",
         "--property=Description", "--property=ControlGroup"],
        text=True, capture_output=True, timeout=5, env=client_env,
    )
    properties = dict(line.split("=", 1) for line in run.stdout.splitlines() if "=" in line)
    if properties.get("LoadState") == "not-found":
        return None
    if run.returncode or not properties.get("LoadState"):
        raise RuntimeError("unit state could not be established; ownership record retained")
    return properties


def collect_owned(owner: dict, client_env: dict) -> None:
    properties = inspect_unit(owner, client_env)
    if properties is not None:
        group = properties.get("ControlGroup", "")
        prefix = f"/user.slice/user-{owner['uid']}.slice/user@{owner['uid']}.service/"
        if (properties.get("Description") != owner["description"]
                or not group.startswith(prefix) or not group.endswith("/" + owner["unit"])):
            raise RuntimeError("unit ownership mismatch; refusing stop and retaining record")
        subprocess.run(["systemctl", "--user", "stop", owner["unit"]],
                       check=True, capture_output=True, timeout=5, env=client_env)
        for _ in range(20):
            if inspect_unit(owner, client_env) is None:
                break
            time.sleep(0.05)
        else:
            raise RuntimeError("unit remains after stop; ownership record retained")
        if Path("/sys/fs/cgroup" + group).exists():
            raise RuntimeError("owned cgroup remains; ownership record retained")
    if owner["record"] is not None:
        owner["record"].unlink()


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} SPEC.json RESULT.json", file=sys.stderr)
        return 2
    result_path = Path(sys.argv[2])
    try:
        spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        guard, root, command, memory, tasks, cpu = validated(spec)
    except (OSError, ValueError, TypeError) as error:
        print(f"runtime specification denied: {error}", file=sys.stderr)
        return 1

    client_env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
    for name in ("XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS"):
        if name in os.environ:
            client_env[name] = os.environ[name]
    try:
        owner = register_owner(client_env)
        unit = owner["unit"]
        argv = [
            "systemd-run", "--user", "--wait", "--pipe", "--collect", "--quiet",
            "--expand-environment=no", f"--unit={unit}", f"--description={owner['description']}",
            "--property=KillMode=control-group", "--property=TimeoutStopSec=2s",
            "--property=RuntimeMaxSec=15s", "--property=CPUQuotaPeriodSec=100ms",
            f"--property=CPUQuota={cpu}%", f"--property=MemoryMax={memory}",
            "--property=MemorySwapMax=0", f"--property=TasksMax={tasks}",
            "--property=UnsetEnvironment=NORTH_ECHO_FAKE_CREDENTIAL",
            "--setenv=PATH=/usr/bin:/bin", "--setenv=LANG=C.UTF-8", "--setenv=LC_ALL=C.UTF-8",
            "--", "/usr/bin/unshare", "--user", "--map-root-user", "--net", "--",
            "/usr/bin/setpriv", "--bounding-set=-all", "--inh-caps=-all", "--ambient-caps=-all",
            "--no-new-privs", "--", "/usr/bin/env", "-i", "PATH=/usr/bin:/bin",
            "LANG=C.UTF-8", "LC_ALL=C.UTF-8", str(guard), str(root), *command,
        ]
        try:
            run = subprocess.run(argv, text=True, capture_output=True, check=False,
                                 timeout=20, env=client_env)
        finally:
            collect_owned(owner, client_env)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"runtime launch or collection failed: {error}", file=sys.stderr)
        return 1

    attestation = None
    try:
        attestation = json.loads(run.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        pass
    result_path.write_text(json.dumps({
        "schema": 1, "status": run.returncode, "unit": unit,
        "stdout": run.stdout, "stderr": run.stderr, "attestation": attestation,
    }, sort_keys=True) + "\n", encoding="utf-8")
    return int(run.returncode != 0)


if __name__ == "__main__":
    raise SystemExit(main())
```

### Source, line by line

- `integer` enforces bounds and rejects Boolean values. `validated` requires the exact spec fields before creating a unit or result.
- Guard/root fields must be absolute paths of the expected kind. The guard is trusted setup input, not an executable chosen by an untrusted tool request.
- Command arguments must be separate strings without NUL characters. Its executable must be absolute and resolve beneath the allowed root; the whole filesystem is refused as a root.
- `commonpath` compares path components, not textual prefixes. These checks assume operator-controlled setup paths; they are not race-free validation against a concurrent directory writer.
- `register_owner` records exact name, UID, and workspace description before launch. In prepared 10.03/10.lab workspaces it uses the course runtime registry; `module-10` is a CLI alias, not the directory name.
- The external grader copies the file into its own directory without the course launcher. That case writes an exclusive ownership record in a local `.runtime` directory.
- `inspect_unit` asks the user manager for exact-unit properties. Explicit `LoadState=not-found` means absent; a manager error is not absence.
- `collect_owned` verifies description and delegated cgroup path before stopping a remaining unit. It waits for observed absence and checks the recorded cgroup is gone. Unknown ownership keeps evidence and refuses mutation.
- `client_env` preserves only fixed locale/path plus the IPC variables needed to reach the user manager. These are for the trusted systemd client, not the final workload.
- The argv list uses `--expand-environment=no`. A Python list alone would not prevent systemd's own environment-reference expansion.
- `--wait --pipe --collect` waits for completion and captures output. CPU period is explicitly 100 ms; CPU/memory/swap/tasks and runtime/stop limits are set before descendants start.
- `unshare` establishes the private user/network views. `setpriv` then clears bounding, inheritable, and ambient sets and sets no-new-privileges. The observer checks all five capability sets after execution.
- `env -i` constructs the final fixed workload environment. The native guard then marks extra descriptors close-on-exec, applies Landlock, applies seccomp, and executes exact workload argv.
- The `finally` around execution runs owned collection on normal return, failure, or client timeout. A result is not published as a completed run if launch/collection raises an error.
- The last stdout line is parsed as an observation when possible. The result separately retains status, full stdout/stderr, and unit identity; the launcher does not infer every security property from status alone.

This teaching launcher captures output in memory. Its time and workload-resource limits are not a separate strict byte quota on the outer launcher's capture buffer. Use the supplied small observers; a production runner needs bounded streaming, stronger setup-file trust, and additional threat-model work.

### The confined observer

```c
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <unistd.h>

static int read_text(const char *path, char *buffer, size_t size) {
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd == -1)
        return -1;
    ssize_t count = read(fd, buffer, size - 1);
    close(fd);
    if (count < 0)
        return -1;
    buffer[count] = '\0';
    return 0;
}

static int status_value(const char *status, const char *name, unsigned long long *value) {
    const char *line = strstr(status, name);
    if (!line)
        return -1;
    return sscanf(line + strlen(name), "%llx", value) == 1 ? 0 : -1;
}

static int status_decimal(const char *status, const char *name, int *value) {
    const char *line = strstr(status, name);
    if (!line)
        return -1;
    return sscanf(line + strlen(name), "%d", value) == 1 ? 0 : -1;
}

static int read_cgroup_value(const char *name, char *value, size_t size) {
    char membership[4096], relative[PATH_MAX], path[PATH_MAX];
    if (read_text("/proc/self/cgroup", membership, sizeof(membership)) == -1)
        return -1;
    char *line = strstr(membership, "0::");
    if (!line || sscanf(line, "0::%4095[^\n]", relative) != 1)
        return -1;
    if (snprintf(path, sizeof(path), "/sys/fs/cgroup%s/%s", relative, name) >= (int)sizeof(path))
        return -1;
    if (read_text(path, value, size) == -1)
        return -1;
    value[strcspn(value, "\n")] = '\0';
    return 0;
}

static int broker_request(const char *socket_path, const char *request_path,
                          const char *forbidden_marker, char *response, size_t size) {
    char request[16384];
    if (read_text(request_path, request, sizeof(request)) == -1)
        return 0;
    size_t length = strlen(request);
    if (length == 0 || request[length - 1] != '\n')
        return 0;
    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd == -1)
        return 0;
    struct sockaddr_un address = {.sun_family = AF_UNIX};
    if (strlen(socket_path) >= sizeof(address.sun_path)) {
        close(fd);
        return 0;
    }
    strcpy(address.sun_path, socket_path);
    if (connect(fd, (struct sockaddr *)&address, sizeof(address)) == -1 ||
        write(fd, request, length) != (ssize_t)length) {
        close(fd);
        return 0;
    }
    shutdown(fd, SHUT_WR);
    size_t used = 0;
    while (used < size - 1) {
        ssize_t count = read(fd, response + used, size - 1 - used);
        if (count == -1 && errno == EINTR)
            continue;
        if (count < 0) {
            close(fd);
            return 0;
        }
        if (count == 0)
            break;
        used += (size_t)count;
        if (memchr(response, '\n', used))
            break;
    }
    close(fd);
    if (used == 0 || used == size - 1)
        return 0;
    response[used] = '\0';
    return strcmp(response, "{\"ok\":true,\"result\":{\"value\":\"synthetic-result\"}}\n") == 0
           && strstr(response, forbidden_marker) == NULL;
}

int main(int argc, char **argv) {
    if (argc != 8) {
        fprintf(stderr, "usage: %s ALLOWED PROTECTED BROKER REQUEST HOST_NET_INODE HOST_USER_INODE FORBIDDEN_MARKER\n", argv[0]);
        return 2;
    }
    char byte[8], status[16384], cpu[128] = "?", memory[128] = "?";
    char swap[128] = "?", pids[128] = "?", broker_response[65536];
    int allowed_read = read_text(argv[1], byte, sizeof(byte)) == 0;
    errno = 0;
    int protected_fd = open(argv[2], O_RDONLY | O_CLOEXEC);
    int protected_denied = protected_fd == -1 && (errno == EACCES || errno == EPERM);
    if (protected_fd != -1)
        close(protected_fd);

    int inet_fd = socket(AF_INET, SOCK_STREAM, 0);
    int inet_denied = inet_fd == -1 && errno == EPERM;
    if (inet_fd != -1)
        close(inet_fd);

    struct stat net_stat, user_stat;
    unsigned long long host_net = strtoull(argv[5], NULL, 10);
    int private_net = stat("/proc/self/ns/net", &net_stat) == 0 &&
                      (unsigned long long)net_stat.st_ino != host_net;
    unsigned long long host_user = strtoull(argv[6], NULL, 10);
    int private_user = stat("/proc/self/ns/user", &user_stat) == 0 &&
                       (unsigned long long)user_stat.st_ino != host_user;

    unsigned long long cap_eff = 1, cap_bnd = 1, cap_amb = 1, cap_prm = 1, cap_inh = 1;
    int no_new_privs = 0, seccomp = 0;
    int status_ok = read_text("/proc/self/status", status, sizeof(status)) == 0 &&
                    status_value(status, "CapEff:\t", &cap_eff) == 0 &&
                    status_value(status, "CapBnd:\t", &cap_bnd) == 0 &&
                    status_value(status, "CapAmb:\t", &cap_amb) == 0 &&
                    status_value(status, "CapPrm:\t", &cap_prm) == 0 &&
                    status_value(status, "CapInh:\t", &cap_inh) == 0 &&
                    status_decimal(status, "NoNewPrivs:\t", &no_new_privs) == 0 &&
                    status_decimal(status, "Seccomp:\t", &seccomp) == 0;
    read_cgroup_value("cpu.max", cpu, sizeof(cpu));
    read_cgroup_value("memory.max", memory, sizeof(memory));
    read_cgroup_value("memory.swap.max", swap, sizeof(swap));
    read_cgroup_value("pids.max", pids, sizeof(pids));
    int broker_ok = broker_request(argv[3], argv[4], argv[7], broker_response, sizeof(broker_response));
    int credential_absent = getenv("NORTH_ECHO_FAKE_CREDENTIAL") == NULL;

    printf("{\"allowed_read\":%s,\"protected_denied\":%s,\"inet_denied\":%s,"
           "\"private_net\":%s,\"private_user\":%s,\"caps_zero\":%s,\"no_new_privs\":%d,"
           "\"seccomp\":%d,\"cpu\":\"%s\",\"memory\":\"%s\","
           "\"swap\":\"%s\",\"pids\":\"%s\",\"broker_ok\":%s,"
           "\"credential_absent\":%s}\n",
           allowed_read ? "true" : "false", protected_denied ? "true" : "false",
           inet_denied ? "true" : "false", private_net ? "true" : "false",
           private_user ? "true" : "false",
           status_ok && cap_eff == 0 && cap_bnd == 0 && cap_amb == 0 &&
           cap_prm == 0 && cap_inh == 0 ? "true" : "false",
           no_new_privs, seccomp, cpu, memory, swap, pids,
           broker_ok ? "true" : "false", credential_absent ? "true" : "false");
    return !(allowed_read && protected_denied && inet_denied && private_net && private_user &&
             status_ok && cap_eff == 0 && cap_bnd == 0 && cap_amb == 0 &&
             cap_prm == 0 && cap_inh == 0 &&
             no_new_privs == 1 && seccomp == 2 && broker_ok && credential_absent);
}
```

### Source, block by block

- `read_text` opens a path, reads a bounded buffer, closes the descriptor, and terminates the C string.
- Status helpers locate hexadecimal capability fields and decimal policy fields in this process's status text.
- `read_cgroup_value` derives the process's own unified cgroup path from `0::...`, then reads controller files. It does not infer effective values from the launch spec.
- `broker_request` reads a small prebuilt request, requires its newline, checks pathname length, and creates an AF_UNIX socket.
- The response read loops over a byte stream rather than assuming one read is a whole message. Its final comparison expects the exact compact synthetic response from this fixture; it is not a general JSON parser.
- The main observer performs allowed/protected reads and an AF_INET socket attempt. It records actual denials, not just the existence of policy APIs.
- Namespace inode numbers are compared with saved parent observations. Different numbers establish different namespace objects, not every desired property of their contents.
- Effective, permitted, inheritable, bounding, and ambient capabilities are checked along with no-new-privileges and seccomp mode.
- CPU, memory, swap, and task values are printed for an external checkpoint to compare against the requested profile.
- A successful intended broker exchange and absence of the named fake environment variable are separate fields.
- The exit status aggregates the fixed Boolean checks. Resource-profile equality still requires comparing the printed values with the spec.

### The outside synthetic broker

```python
#!/usr/bin/env python3
"""One-shot synthetic operation broker for the composition lesson."""

import hashlib
import json
import os
from pathlib import Path
import socket
import signal
import sys


def stop(_signum, _frame):
    raise SystemExit(0)


def main() -> int:
    if len(sys.argv) != 5:
        return 2
    socket_path, token_path, credential_path, event_path = map(Path, sys.argv[1:])
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    token = token_path.read_text(encoding="utf-8").strip()
    credential = credential_path.read_text(encoding="utf-8").strip()
    if socket_path.exists() or socket_path.is_symlink():
        raise SystemExit("broker socket path already exists")
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        listener.bind(str(socket_path))
        os.chmod(socket_path, 0o600)
        listener.listen(1)
        listener.settimeout(300)
        peer, _ = listener.accept()
        with peer:
            peer.settimeout(2)
            with peer.makefile("rb") as incoming:
                line = incoming.readline(16385)
            if len(line) > 16384 or not line.endswith(b"\n"):
                raise ValueError("request must be one bounded line")
            request = json.loads(line)
            expected = {"operation": "read", "resource": "synthetic:record", "token": token}
            if request != expected:
                response = {"ok": False, "error": "capability denied"}
            else:
                proof = hashlib.sha256((credential + ":read:synthetic:record").encode()).hexdigest()
                event_path.write_text(json.dumps({"credential_used": True, "proof": proof}) + "\n",
                                      encoding="utf-8")
                response = {"ok": True, "result": {"value": "synthetic-result"}}
            peer.sendall(json.dumps(response, sort_keys=True, separators=(",", ":")).encode() + b"\n")
    finally:
        listener.close()
        socket_path.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### Source, line by line

- The broker reads a random opaque token and a fake credential from files outside the workload root.
- It creates a mode-0600 pathname socket below the workload root, where the intended caller can reach it.
- It accepts one bounded request with a peer timeout, requiring the exact token, operation, and resource.
- Success hashes the fake credential plus fixed operation context into a separate event and returns only the harmless synthetic value.
- This event demonstrates use of the fake value by trusted teaching code. There is no separate credential-protected upstream in this smaller composition fixture; 09.03 supplied that fuller example.
- The token is an opaque one-operation teaching grant, **not** the full HMAC/expiry/replay protocol from Module 09. Do not claim this fixture reimplements that protocol.
- The listener is one-shot, and normal SIGTERM/SIGINT cleanup removes its socket. The runtime backstop limits an abandoned instance.

### A small worker for later batch practice

```c
#define _GNU_SOURCE
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv) {
    if (argc != 2)
        return 2;
    char *end;
    long status = strtol(argv[1], &end, 10);
    if (!*argv[1] || *end || status < 0 || status > 125)
        return 2;
    FILE *membership = fopen("/proc/self/cgroup", "r");
    char line[PATH_MAX], relative[PATH_MAX], path[PATH_MAX];
    int found = 0;
    while (membership && fgets(line, sizeof(line), membership)) {
        if (sscanf(line, "0::%4095[^\n]", relative) == 1) {
            found = 1;
            break;
        }
    }
    if (membership)
        fclose(membership);
    if (!found || snprintf(path, sizeof(path), "/sys/fs/cgroup%s/memory.max", relative)
            >= (int)sizeof(path))
        return 2;
    FILE *limit = fopen(path, "r");
    unsigned long long memory;
    int observed = limit && fscanf(limit, "%llu", &memory) == 1;
    if (limit)
        fclose(limit);
    if (!observed)
        return 2;
    printf("{\"requested_status\":%ld,\"memory\":%llu}\n", status, memory);
    return (int)status;
}
```

### Source, line by line

- `strtol` parses a requested ordinary exit code from 0 through 125 and rejects trailing text.
- The membership loop finds this process's unified cgroup path and closes its file.
- Bounded `snprintf` constructs the memory-controller filename, refusing truncation.
- Reading an integer from `memory.max` requires a finite numeric limit; `max` would not be accepted as a number.
- The final JSON reports the requested status and the **observed** memory ceiling, then exits with that status. This worker does not need a broker.

## Exercise 1 - Build local synthetic fixtures

```bash
NE_DEMO=$(mktemp -d "$PWD/d.XXXXXX")
mkdir "$NE_DEMO/allowed"
gcc -O2 -Wall -Wextra -static \
  ../../course/module-10-complete-runtime/lesson-02/runtime_guard.c \
  -o "$NE_DEMO/runtime_guard" -lseccomp
gcc -O2 -Wall -Wextra -static runtime_probe.c -o "$NE_DEMO/allowed/runtime_probe"
gcc -O2 -Wall -Wextra -static batch_worker.c -o "$NE_DEMO/allowed/batch_worker"
python3 - "$NE_DEMO" <<'PY'
import json
from pathlib import Path
import secrets
import sys

root = Path(sys.argv[1])
token = "CAP-" + secrets.token_hex(16)
credential = "FAKE-CREDENTIAL-" + secrets.token_hex(16)
(root / "allowed/allowed.txt").write_text("allowed\n")
(root / "protected.txt").write_text("synthetic-protected\n")
for name, value in (("token.txt", token), ("credential.txt", credential)):
    with (root / name).open("x") as stream:
        stream.write(value + "\n")
    (root / name).chmod(0o600)
(root / "allowed/request.json").write_text(json.dumps({
    "operation": "read", "resource": "synthetic:record", "token": token
}, sort_keys=True, separators=(",", ":")) + "\n")
PY
NE_HOST_NET=$(stat -Lc '%i' /proc/self/ns/net)
NE_HOST_USER=$(stat -Lc '%i' /proc/self/ns/user)
```

The new directory is inside this prepared workspace. Static binaries avoid dynamic-loader exceptions. Random token/credential values stay synthetic; only the narrow request goes below the workload root. `stat -L` follows the namespace link to obtain the parent namespace object's inode for comparison.

Define a registered helper for the outside broker:

```bash
start_demo_broker() {
  NE_BROKER_UNIT="north-echo-$(id -u)-10-03-$(python3 -c 'import secrets; print(secrets.token_hex(4))').service"
  ../../scripts/labctl.py register-unit 10.03 "$NE_BROKER_UNIT" || return
  systemd-run --user --collect --quiet --expand-environment=no --service-type=exec \
    --unit="$NE_BROKER_UNIT" --description="North Echo 10.03 workspace=$PWD" \
    --property=RuntimeMaxSec=300s --property=TimeoutStopSec=3s \
    --property=MemoryMax=67108864 --property=MemorySwapMax=0 \
    --property=TasksMax=16 --property=CPUQuota=50% -- \
    /usr/bin/python3 "$PWD/demo_broker.py" "$NE_DEMO/allowed/broker.sock" \
    "$NE_DEMO/token.txt" "$NE_DEMO/credential.txt" "$1"
  for attempt in {1..50}; do test -S "$NE_DEMO/allowed/broker.sock" && break; sleep 0.1; done
  test -S "$NE_DEMO/allowed/broker.sock"
}
```

This uses the owned lifecycle from Modules 07-09. Its argument selects the exact event filename. A failed readiness check is setup failure; inspect `journalctl --user -u "$NE_BROKER_UNIT" --no-pager`, then clean up before continuing.

## Exercise 2 - Observe an incomplete inner-only launch

```bash
start_demo_broker "$NE_DEMO/direct-event.json"
NE_DIRECT_STATUS=0
NORTH_ECHO_FAKE_CREDENTIAL="$(head -n 1 "$NE_DEMO/credential.txt")" \
  timeout 5s "$NE_DEMO/runtime_guard" "$NE_DEMO/allowed" "$NE_DEMO/allowed/runtime_probe" \
  "$NE_DEMO/allowed/allowed.txt" "$NE_DEMO/protected.txt" "$NE_DEMO/allowed/broker.sock" \
  "$NE_DEMO/allowed/request.json" "$NE_HOST_NET" "$NE_HOST_USER" 'FAKE-CREDENTIAL-' \
  > "$NE_DEMO/direct.json" || NE_DIRECT_STATUS=$?
python3 -m json.tool "$NE_DEMO/direct.json"
test "$NE_DIRECT_STATUS" -eq 1
../../lab-cleanup 10.03
test ! -e "$NE_DEMO/allowed/broker.sock"
```

The temporary assignment deliberately gives this one launch the **fake** ambient credential. The guard enforces its filesystem/syscall controls and the intended broker operation works, but `private_net`, `private_user`, and `credential_absent` are false. Resource values come from the parent rather than this lesson's desired profile.

Expected status is 1 from the observer's failed conjunction, not timeout status 124 or a missing executable. Partial success is not complete composition. The broker is one-shot, so the repair needs a fresh instance.

## Exercise 3 - Generate the spec and run the composition

```bash
python3 - "$NE_DEMO" "$NE_HOST_NET" "$NE_HOST_USER" <<'PY'
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
spec = {
    "guard": str(root / "runtime_guard"), "allowed_root": str(root / "allowed"),
    "command": [str(root / "allowed/runtime_probe"),
                str(root / "allowed/allowed.txt"), str(root / "protected.txt"),
                str(root / "allowed/broker.sock"), str(root / "allowed/request.json"),
                sys.argv[2], sys.argv[3], "FAKE-CREDENTIAL-"],
    "memory_max": 50331648, "tasks_max": 16, "cpu_percent": 50
}
(root / "spec.json").write_text(json.dumps(spec) + "\n")
PY
start_demo_broker "$NE_DEMO/event.json"
NORTH_ECHO_FAKE_CREDENTIAL="$(head -n 1 "$NE_DEMO/credential.txt")" \
  python3 complete_runtime.py "$NE_DEMO/spec.json" "$NE_DEMO/result.json"
python3 -m json.tool "$NE_DEMO/result.json"
python3 -m json.tool "$NE_DEMO/event.json"
../../lab-cleanup 10.03
```

Python serializes structured values instead of building JSON by shell string concatenation. The fake credential is still present in the launcher's environment, so observed absence in the final workload tests the actual handoff repair.

The result should retain status 0 and a final observation in which every intended Boolean is true. Expected resource strings are CPU `50000 100000`, memory `50331648`, swap `0`, and tasks `16`. Cleanup checks both the already-collected workload and the separate outside broker through their registered ownership.

## Checkpoint - Compare effects and verify the exact unit

```bash
python3 - "$NE_DEMO" <<'PY'
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1])
direct = json.loads((root / "direct.json").read_text())
assert direct["private_net"] is False and direct["private_user"] is False
assert direct["credential_absent"] is False
assert direct["allowed_read"] is True and direct["protected_denied"] is True
result = json.loads((root / "result.json").read_text())
observed = result["attestation"]
assert result["status"] == 0
for field in ("allowed_read", "protected_denied", "inet_denied", "private_net",
              "private_user", "caps_zero", "broker_ok", "credential_absent"):
    assert observed[field] is True, field
assert observed["no_new_privs"] == 1 and observed["seccomp"] == 2
assert (observed["cpu"], observed["memory"], observed["swap"], observed["pids"]) == (
    "50000 100000", "50331648", "0", "16")
credential = (root / "credential.txt").read_text().strip()
event = json.loads((root / "event.json").read_text())
expected = hashlib.sha256((credential + ":read:synthetic:record").encode()).hexdigest()
assert event == {"credential_used": True, "proof": expected}
assert credential not in (root / "result.json").read_text()
unit = subprocess.run(["systemctl", "--user", "show", result["unit"],
                       "--property=LoadState"], capture_output=True, text=True, check=False)
assert unit.stdout.strip() == "LoadState=not-found", unit.stdout + unit.stderr
assert not (root / "allowed/broker.sock").exists()
print("COMPOSED EFFECTS AND EXACT COLLECTION: PASS")
PY
```

The checker compares effective state, recomputes the synthetic broker event, and asks about the **exact** returned unit. An empty wildcard listing or a failed manager command cannot substitute for that observed absence.

This evidence concerns the supplied code and fixtures. It does not certify arbitrary workload output, every possible secret channel, future Landlock rights, or exclusive access to one Unix socket on older ABIs.

## Faded practice - One job, then three

The batch worker is already compiled. Create three single-job specs from the known-good outer spec, with desired exit statuses 0, 7, and 0:

```bash
python3 - "$NE_DEMO" <<'PY'
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
base = json.loads((root / "spec.json").read_text())
for index, status in enumerate((0, 7, 0), start=1):
    spec = dict(base)
    spec["command"] = [str(root / "allowed/batch_worker"), str(status)]
    spec["memory_max"] = 33554432 if index == 2 else 50331648
    (root / f"job-{index}.json").write_text(json.dumps(spec) + "\n")
PY
python3 complete_runtime.py "$NE_DEMO/job-1.json" "$NE_DEMO/job-1-result.json"
NE_JOB_TWO_STATUS=0
python3 complete_runtime.py "$NE_DEMO/job-2.json" "$NE_DEMO/job-2-result.json" || NE_JOB_TWO_STATUS=$?
test "$NE_JOB_TWO_STATUS" -ne 0
python3 complete_runtime.py "$NE_DEMO/job-3.json" "$NE_DEMO/job-3-result.json"
```

No broker is needed for this worker. The outer launcher reports nonzero for the middle workload, while its saved `status` is 7. The third valid job still runs. Inspect each result's observed memory value; the middle one must report 33554432, not merely inherit the input filename.

Now write `batch-notes.md` and design your own ordered batch interface using Module 04's list/trace skills. Give jobs unique IDs, validate **all** specs before any launch, preserve IDs and statuses in input order, and verify each exact unit is absent.

Deliberate mistake to reason about: a later job has `tasks_max: 0`, but the first job was already launched before validating it. Explain why malformed input should reject the batch before side effects, while a valid job returning 7 need not prevent later valid jobs. Use `validated` from this local source to review each spec without launching; it is separate from `main`.

Checkpoint for this faded practice: show ordered 0/7/0 results, observed per-job memory, exact unit absence, and a malformed later spec rejected before any worker runs. The capstone withholds a batch implementation and uses fresh profiles.

## Troubleshooting and replay

A missing result can mean validation, setup, timeout, or collection failure; read the specific launcher diagnostic. A valid result with status 7 means an ordinary workload failure was preserved. A remaining owner record is evidence to inspect, not permission to kill a name-matched process.

If cgroups fail, run `../../scripts/linux-preflight`. If a socket path is too long, keep the VM course path short and use a fresh prepared workspace. If static execution fails, verify the workload is beneath its allowed root. Keep SELinux enabled; do not add IP routes, host firewall changes, or public services.

Preview `../../lab-cleanup 10.03 --dry-run`, then run `../../lab-cleanup 10.03`. Save your notes, return with `cd ../..`, and use `./lab-reset 10.03` to discard this lesson's generated artifacts after verified cleanup.

## Source truth

[setpriv(1)](https://man7.org/linux/man-pages/man1/setpriv.1.html) explains privilege settings across execution; [proc_pid_status(5)](https://man7.org/linux/man-pages/man5/proc_pid_status.5.html) defines observed capability/policy fields. Use the installed `man systemd-run` and `man systemd.resource-control` for the VM's manager version. The [Landlock documentation](https://cdn.kernel.org/doc/html/latest/userspace-api/landlock.html) defines the ABI-specific limits that a passing local observation must not overstate.
<!-- /source -->

---

<!-- source: course/module-10-complete-runtime/lab/README.md format=markdown -->
# Module 10 independent lab - Composed contained runtime

## Assignment and readiness check

Build the single-job launcher practiced in 10.01-10.03. It must retain an approved operation while applying the outer controls and proving owned collection. Do not replace effective observations with input-configuration labels.

Before coding, explain the dependency order, the difference between inner guard and outer launcher, why systemd argv expansion needs explicit treatment, and why an absent exact unit is stronger evidence than requesting collection. Complete the small 0/7/0 worker exercise before progressing to the later batch capstone.

## Prepare and read the starter

From the course root:

```bash
./lab-start module-10
cd .student/10.lab
pwd
ls -l complete_runtime.py
cat complete_runtime.py
nano complete_runtime.py
```

Work only in this prepared copy. Ctrl+O then Enter saves in the default nano configuration; Ctrl+X exits.

```python
#!/usr/bin/env python3
"""Module 10 starter: functional execution without outer runtime controls."""

import json
from pathlib import Path
import subprocess
import sys


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    command = [spec["guard"], spec["allowed_root"], *spec["command"]]
    run = subprocess.run(command, text=True, capture_output=True, check=False, timeout=20)
    Path(sys.argv[2]).write_text(json.dumps({
        "schema": 1, "status": run.returncode, "unit": None,
        "stdout": run.stdout, "stderr": run.stderr, "attestation": None,
    }) + "\n", encoding="utf-8")
    return run.returncode != 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### Starter, line by line

- The imports provide JSON, paths, subprocess execution, and arguments.
- The guard requires a spec and result filename; the starter then parses JSON without the complete validation you must add.
- The command list preserves argv while invoking the supplied guard and workload directly.
- A timeout bounds this incomplete foreground execution, but no cgroup or namespace is created.
- The result records status/output and explicitly has no unit or parsed attestation.
- A nonzero child status makes the starter return nonzero. This is useful baseline behavior, not successful composition.

The starter may perform the guard's inner controls while failing the outer properties. Do not mistake that partial functionality for the assignment being complete.

## Interface and validation contract

The grader invokes:

```text
python3 complete_runtime.py SPEC.json RESULT.json
```

Require exactly `guard`, `allowed_root`, `command`, `memory_max`, `tasks_max`, and `cpu_percent`. Guard/root must be absolute paths of the expected regular-file/directory kind, without a symlink leaf. Treat the guard as trusted operator-provided TCB, not a workload-selectable convenience. Refuse the whole filesystem as an allowed root.

Require nonempty structured string argv without NUL characters, an absolute executable that resolves beneath the allowed root, and actual integer limits: memory 16 MiB through 1 GiB, tasks 4 through 256, CPU 10 through 100 percent. Reject Boolean limits. Invalid input must fail before a result, ownership record, or service is created. These setup paths are trusted for this exercise; do not claim race-free validation against concurrent same-account mutation.

## Launch and collection contract

Record exact unit ownership before launch. In prepared course workspaces, use the course registry with the matching target and workspace description. The isolated external grader copies your single source file into a separate directory; preserve a local ownership record under `.runtime` there, as practiced in 10.03. Use names with the ordinary UID, target, and fresh random suffix; the grader's standalone target is `10.lab`.

Create a transient **user** service with validated CPU/memory/task limits, zero swap, a 100 ms CPU period, a finite runtime backstop, control-group stop semantics, bounded stop time, synchronous waiting, and collection. Disable systemd's own argument environment expansion when promising literal argv.

Within that cgroup create fresh user/network namespaces; then reduce bounding/inheritable/ambient capability sets and set no-new-privileges. Give the final guard/workload a fixed environment without the fake credential. Invoke the trusted guard with the allowed root and separate workload argv. Do not use a shell to reinterpret those arguments.

On normal return, failure, and timeout, inspect the **exact** recorded unit. Before stopping a remaining unit, verify its description and cgroup are owned by the expected delegated user manager. Treat a manager inspection failure as unknown, not absent. Confirm actual unit/cgroup collection before publishing a completed result. Retain ownership evidence and refuse mutation if identity cannot be established.

Write one JSON result with schema 1, workload status, exact unit name, stdout, stderr, and the parsed final-line observation when present. A valid worker exit of 7 must remain 7 in the result and produce a nonzero launcher status. A missing final JSON line need not erase an ordinary worker's status/stderr.

## What the external checks observe

The grader compiles its own static guard and observer, rotates synthetic paths/tokens/credentials, and runs a separate local Unix-socket fixture. It checks:

- effective CPU, memory, swap, and task controller values;
- distinct user/network namespaces and denied AF_INET creation;
- empty capability sets and no-new-privileges;
- allowed/protected file behavior and seccomp mode;
- successful intended Unix-socket operation and fake-credential use by the fixture;
- absence of the known fake credential from observed workload environment/output;
- literal paths, including a systemd-style environment reference;
- ordinary failure status/stderr, invalid-spec refusal, and exact reported-unit/socket absence.

These are finite observations. They do not certify a general parser, a production broker, exclusive access to one Unix socket on ABI 7, durable credential replay state, private PID/mount views, all-channel non-disclosure, or independently bounded outer output capture.

## Map the work to practice

Validation and structured input: Module 04 and 10.03. Resource ownership and timeouts: Module 07 and 10.03. Namespace/privilege ordering: Modules 02-03 and 10.01. Native filesystem/syscall guard: Modules 05-06 and 10.02. Intended broker operation and its limits: Modules 08-09 and 10.03. Failure aggregation and status preservation: Module 04 and the 0/7/0 practice.

Write an explanation of each layer's evidence and one limitation it does not address. The lab does not include a complete launcher implementation.

## Validate, diagnose, and replay

```bash
python3 -m py_compile complete_runtime.py
../../lab-grade module-10
../../lab-grade module-10 --mode exam
```

Compilation checks syntax without creating a service. Practice mode reports failed properties with lesson references; exam mode reduces hints. A failed approved operation must not be “repaired” by removing confinement. Identify which setup/control dependency broke the intended task.

For manual runs, use only generated local fixtures and exact registered ownership. Preview `../../lab-cleanup module-10 --dry-run`, then run `../../lab-cleanup module-10`. Do not kill by prefix, modify host cgroups/firewalls, disable SELinux, or use real credentials.

Save your design notes, return with `cd ../..`, and use `./lab-reset module-10` to discard the working copy and synthetic fixtures after verified cleanup.
<!-- /source -->
