# North Echo field manual - Module 10

This chapter is self-contained for the complete-runtime composition lessons and independent lab. It repeats every guided command and complete source listing used by the module. All services, capabilities, credentials, paths, and data are synthetic and local to the disposable Linux VM.

The central security rule is conjunctive: the runtime is acceptable only when every layer is effective at the same time and the owned process tree is collected afterward. Configuration intent is not evidence; the lessons inspect state from inside the final workload and separately inspect teardown from outside it.

<!-- PAGEBREAK -->

## Module overview

<!-- source: course/module-10-complete-runtime/README.md format=markdown -->
# Module 10 - Compose a complete agent runtime

Assemble the controls from Modules 01-09 in dependency order, then ask the running workload and kernel for evidence that the composition is effective. The final runtime has bounded resources, fresh user and network namespaces, empty capability sets, `no_new_privs`, Landlock filesystem policy, a default-deny seccomp filter, capability-mediated Unix-socket access, a clean credential environment, structured telemetry, and synchronous process-tree collection.

Play in order: `10.01`, `10.02`, `10.03`, then `module-10`.

Outcomes:

- distinguish launch dependencies from an arbitrary checklist order;
- apply pathname policy before a syscall filter can remove the setup syscalls;
- keep the broker outside the restricted network namespace while exposing only its Unix socket;
- place the launcher and every descendant under cgroup limits before workload creation;
- attest effective namespaces, capabilities, Landlock effects, seccomp mode, cgroup values, credential absence, and broker success;
- propagate workload failure and synchronously collect the exact transient unit.

All data, credentials, capabilities, services, paths, and requests are synthetic and local. The module creates no veth pair, route, firewall rule, public request, real credential, or production target. Prerequisites are Modules 01-09 and the Linux features reported by `./scripts/linux-preflight`.
<!-- /source -->

<!-- PAGEBREAK -->

## Lesson 10.01

<!-- source: course/module-10-complete-runtime/lesson-01/README.md format=markdown -->
# 10.01 - Order the complete runtime by dependency

## Goal

Turn the earlier controls into a launch dependency graph, trigger an invalid order, and prove the repaired plan satisfies every dependency.

## Exercise 1 - Read the plan validator

```bash
sed -n '1,240p' check_order.py
python3 -m json.tool broken-plan.json
python3 -m json.tool repaired-plan.json
```

### Source, block by block

- `REQUIRED` names every phase that changes the security result. A plan cannot silently omit teardown or broker readiness.
- `BEFORE` contains dependency edges, not a preferred cosmetic order. The cgroup precedes descendants; namespace creation precedes capability removal; Landlock setup precedes a filter that does not allow Landlock syscalls; every restriction precedes workload `exec`; collection follows workload exit.
- `main` accepts only a JSON string array, rejects duplicate, missing, and unknown steps, maps each step to its position, and reports every reversed edge.
- The exit status is nonzero whenever an effective dependency is violated, so the check can gate a launcher build.

## Exercise 2 - Trigger the ordering failure

```bash
python3 check_order.py broken-plan.json; test "$?" -eq 1
```

Expected output includes `apply_landlock must precede apply_seccomp`. The deliberate mistake installs seccomp first. A useful workload policy may deny the Landlock setup syscalls; applying that filter first can make the filesystem control impossible to install. A list containing both controls is not proof of composition.

## Exercise 3 - Repair and challenge the graph

```bash
python3 check_order.py repaired-plan.json
cp repaired-plan.json challenge-plan.json
python3 - <<'PY'
import json
from pathlib import Path
p = Path("challenge-plan.json")
steps = json.loads(p.read_text())
steps.remove("enter_cgroup")
steps.insert(3, "enter_cgroup")
p.write_text(json.dumps(steps) + "\n")
PY
python3 check_order.py challenge-plan.json; test "$?" -eq 1
rm challenge-plan.json
```

### Line by line

- The repaired plan moves Landlock before seccomp and returns `ok: true`.
- The small Python edit deliberately moves cgroup entry after namespace creation. The validator rejects it because processes created during namespace setup would otherwise exist before accounting is attached.
- Removing the temporary challenge leaves only shipped lesson files.

The broker starts before the isolated child because the child has no inherited IP network and must find a ready filesystem socket. The user namespace is entered before dropping capabilities because mapping root in a new user namespace creates namespace-scoped capabilities that must then be removed. Collection is last because `--collect` is a lifecycle guarantee, not a workload restriction.

## Checkpoint and troubleshooting

```bash
test "$(python3 check_order.py repaired-plan.json)" = '{"ok": true, "violations": []}'
```

- If JSON parsing fails, restore an array of quoted step names; ordering is evaluated only after shape validation.
- If a step appears harmless to move, identify what it creates, what syscalls it needs, and which later phase removes that authority.
- Checkpoint: explain why `apply_landlock` before `apply_seccomp` and `enter_namespaces` before `drop_privilege` are dependencies rather than style choices.
<!-- /source -->

<!-- PAGEBREAK -->

## Complete source: `check_order.py`

Canonical path: `course/module-10-complete-runtime/lesson-01/check_order.py`

<!-- source: course/module-10-complete-runtime/lesson-01/check_order.py format=code -->
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
<!-- /source -->

<!-- PAGEBREAK -->

## Complete source: `broken-plan.json`

Canonical path: `course/module-10-complete-runtime/lesson-01/broken-plan.json`

<!-- source: course/module-10-complete-runtime/lesson-01/broken-plan.json format=code -->
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
<!-- /source -->

<!-- PAGEBREAK -->

## Complete source: `repaired-plan.json`

Canonical path: `course/module-10-complete-runtime/lesson-01/repaired-plan.json`

<!-- source: course/module-10-complete-runtime/lesson-01/repaired-plan.json format=code -->
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
<!-- /source -->

<!-- PAGEBREAK -->

## Lesson 10.02

<!-- source: course/module-10-complete-runtime/lesson-02/README.md format=markdown -->
# 10.02 - Seal filesystem and syscall policy before exec

## Goal

Observe an unrestricted native probe, then place the same static executable behind one guard that applies Landlock before a native-architecture, default-deny seccomp filter.

## Exercise 1 - Read and compile the complete programs

```bash
sed -n '1,360p' runtime_guard.c
sed -n '1,240p' guard_probe.c
gcc -O2 -Wall -Wextra -static runtime_guard.c -o runtime_guard -lseccomp
gcc -O2 -Wall -Wextra -static guard_probe.c -o guard_probe
```

### Line by line

- Both `sed` commands display the complete local sources before execution.
- `-O2` makes an ordinary optimized binary; `-Wall -Wextra` keep diagnostics visible; `-static` removes post-policy dynamic-loader dependencies.
- Only the guard links libseccomp because the probe merely observes the installed filter.

### `runtime_guard.c`, block by block

- The syscall wrappers query the running Landlock ABI. `supported_rights` handles filesystem rights explicitly named by this source and available in its build headers, gated by their runtime ABI. Like Module 05, it includes `REFER`, `TRUNCATE`, and conditionally `IOCTL_DEV` and `RESOLVE_UNIX`. Newer unnamed rights are not automatically denied.
- `install_landlock` grants the workload root execute/read access and, with ABI 9 headers and kernel support, pathname Unix-socket resolution. It grants `/proc` and `/sys/fs/cgroup` read access for observations, but no Unix-socket resolution there. These are explicit observability exceptions: this is not a private PID or mount view. Unmentioned paths receive no handled access. Device IOCTL is handled but never granted; seccomp also omits `ioctl`.
- The ABI message identifies runtime support, not build-header completeness. On the Ubuntu baseline, newer rights that the headers cannot name remain a reviewed source property rather than a demonstrated kernel guarantee.
- `PR_SET_NO_NEW_PRIVS` precedes `landlock_restrict_self`; a regular user cannot otherwise enforce the ruleset on itself.
- `install_seccomp` starts from `EPERM`, adds a small static-program syscall surface, and allows `socket` only when argument zero is `AF_UNIX`. `AF_INET` and alternate socket domains therefore remain denied by the default.
- The guard loads the filter only after Landlock setup is complete and calls `execv` with the original argv boundaries.

### `guard_probe.c`, block by block

- `readable` performs a real `open` and `read`; it does not infer access from path text or mode bits.
- `status_number` reads the probe's own `NoNewPrivs` and `Seccomp` fields from `/proc/self/status`.
- `main` reads one allowed and one protected file, attempts an IPv4 socket, and prints observed return values and kernel state.

Static linking keeps the execution policy small: the post-Landlock `exec` does not need dynamic-loader reads from host library directories.

## Exercise 2 - Observe the incomplete launch

```bash
DEMO=$(mktemp -d /tmp/north-echo-10.02.XXXXXX)
mkdir "$DEMO/allowed"
cp guard_probe "$DEMO/allowed/guard_probe"
printf 'allowed\n' > "$DEMO/allowed/input.txt"
printf 'synthetic-protected\n' > "$DEMO/protected.txt"
"$DEMO/allowed/guard_probe" "$DEMO/allowed/input.txt" "$DEMO/protected.txt"
```

Expected patterns are `allowed=1 protected=1`, a nonnegative `inet_fd`, and the host process's seccomp/no-new-privileges values. The intentional mistake is launching the probe merely because its binary is trusted. Nothing prevents it from opening the protected file or creating an IP socket.

## Exercise 3 - Repair with ordered kernel policy

```bash
./runtime_guard "$DEMO/allowed" "$DEMO/allowed/guard_probe" \
  "$DEMO/allowed/input.txt" "$DEMO/protected.txt"
```

Expected patterns are:

```text
allowed=1 protected=0 protected_errno=Permission denied inet_fd=-1 inet_errno=Operation not permitted nnp=1 seccomp=2
```

- The allowed read proves the policy did not simply break all file access.
- `Permission denied` is an effective Landlock observation against a file whose Unix mode still permits the user.
- `AF_INET` returns `EPERM`, while Lesson 10.03 will prove the explicitly allowed `AF_UNIX` broker path still works.
- `NoNewPrivs: 1` and `Seccomp: 2` are kernel-reported state after `exec`, not claims made by the launcher.

Clean only the exact lesson objects:

```bash
rm "$DEMO/allowed/guard_probe" "$DEMO/allowed/input.txt" "$DEMO/protected.txt"
rmdir "$DEMO/allowed" "$DEMO"
rm runtime_guard guard_probe
```

## Checkpoint and troubleshooting

```bash
test ! -e "$DEMO" || { echo "lesson temporary directory remains" >&2; false; }
```

- If static linking fails, install the packages named by `./scripts/linux-preflight`; do not weaken the Landlock policy to expose host libraries.
- If Landlock reports unsupported, use the disposable VM kernel required by Module 05.
- If `execv` returns `EPERM`, confirm the static workload executable is beneath the allowed root and Landlock was installed before seccomp.
- Checkpoint: explain why seccomp mode 2 does not prove pathname confinement, and why a protected-file denial does not prove IP denial.
<!-- /source -->

<!-- PAGEBREAK -->

## Complete source: `runtime_guard.c`

Canonical path: `course/module-10-complete-runtime/lesson-02/runtime_guard.c`

<!-- source: course/module-10-complete-runtime/lesson-02/runtime_guard.c format=code -->
```c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/landlock.h>
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
        add_path_rule(ruleset_fd, "/proc", read_only) == -1 ||
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
        if (allow_name(context, allowed[index]) < 0) {
            seccomp_release(context);
            return -1;
        }
    }
    int socket_number = seccomp_syscall_resolve_name("socket");
    if (socket_number == __NR_SCMP_ERROR ||
        seccomp_rule_add(context, SCMP_ACT_ALLOW, socket_number, 1,
                         SCMP_A0(SCMP_CMP_EQ, AF_UNIX)) < 0 ||
        seccomp_load(context) < 0) {
        seccomp_release(context);
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

<!-- PAGEBREAK -->

## Complete source: `guard_probe.c`

Canonical path: `course/module-10-complete-runtime/lesson-02/guard_probe.c`

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

<!-- PAGEBREAK -->

## Lesson 10.03

<!-- source: course/module-10-complete-runtime/lesson-03/README.md format=markdown -->
# 10.03 - Launch, attest, and collect the complete runtime

## Goal

Compose the outer cgroup/namespace/privilege launcher with the native guard, make one capability-mediated synthetic operation, emit effective-state telemetry, and prove exact teardown.

## Exercise 1 - Read the complete composition

```bash
sed -n '1,340p' complete_runtime.py
sed -n '1,360p' runtime_probe.c
sed -n '1,220p' demo_broker.py
```

### Line by line

- The first file is the outer orchestrator and result writer.
- The second is the confined workload that obtains kernel-visible evidence from inside every layer.
- The third is a one-shot synthetic host-side broker; it owns the fake credential and exact socket lifecycle.

### `complete_runtime.py`, block by block

- `validated` accepts only a regular trusted guard, an absolute directory, an argv array whose executable resolves beneath that directory, and bounded CPU, memory, and task values. It rejects before creating a result or unit.
- The exact transient unit name contains the ordinary UID and random material. `systemd-run --wait --collect` creates the cgroup before descendants, applies CPU/memory/swap/PID limits, uses control-group kill semantics, and synchronously collects the unit.
- `unshare` creates user and network namespaces. `setpriv` then removes bounding, inheritable, and ambient capabilities and sets `no_new_privs` after user mapping has created namespace-scoped capabilities.
- The native guard receives the allowed root, installs Landlock and seccomp, and executes the structured workload argv. No shell interprets paths or arguments.
- The systemd client receives only its IPC variables plus a fixed locale/path; the transient service explicitly unsets the fake credential, and `/usr/bin/env -i` gives the guard only fixed locale/path values. Timeout handling stops only the exact generated unit.
- The result preserves status, stdout, stderr, unit identity, and the parsed final JSON attestation.

### Probe and broker, block by block

- `runtime_probe.c` performs real allowed/protected reads; compares its network-namespace inode with the host value; reads its own capability, `NoNewPrivs`, and `Seccomp` fields; and reads effective cgroup controller files.
- Its `AF_INET` call must fail, while its `AF_UNIX` call sends one prebuilt capability request to the broker. The response must be successful and must not contain the public fake-credential prefix marker; the full credential is never in workload argv.
- `demo_broker.py` holds the expected synthetic capability and fake credential outside the workload. On one exact request it uses the credential to derive an event proof but returns only a synthetic value. Its `finally` block unlinks the exact socket.

## Exercise 2 - Build a randomized local system

```bash
DEMO=$(mktemp -d /tmp/north-echo-10.03.XXXXXX)
mkdir "$DEMO/allowed"
gcc -O2 -Wall -Wextra -static \
  ../../course/module-10-complete-runtime/lesson-02/runtime_guard.c \
  -o "$DEMO/runtime_guard" -lseccomp
gcc -O2 -Wall -Wextra -static runtime_probe.c -o "$DEMO/allowed/runtime_probe"
python3 - "$DEMO" <<'PY'
import json, secrets, sys
from pathlib import Path
root = Path(sys.argv[1])
token = "CAP-" + secrets.token_hex(16)
credential = "FAKE-CREDENTIAL-" + secrets.token_hex(16)
(root / "allowed" / "allowed.txt").write_text("allowed\n")
(root / "protected.txt").write_text("synthetic-protected\n")
(root / "token.txt").write_text(token + "\n")
(root / "credential.txt").write_text(credential + "\n")
(root / "allowed" / "request.json").write_text(json.dumps({
    "operation": "read", "resource": "synthetic:record", "token": token,
}, sort_keys=True, separators=(",", ":")) + "\n")
PY
chmod 600 "$DEMO/token.txt" "$DEMO/credential.txt"
HOST_NET=$(stat -Lc '%i' /proc/self/ns/net)
HOST_USER=$(stat -Lc '%i' /proc/self/ns/user)
```

Every identifier is synthetic and fresh. The broker's secret files are outside the allowed root; the request file contains only a narrow bearer capability.

## Exercise 3 - Trigger the incomplete composition

Start the one-shot broker and invoke only the inner guard:

```bash
python3 demo_broker.py "$DEMO/allowed/broker.sock" "$DEMO/token.txt" \
  "$DEMO/credential.txt" "$DEMO/direct-event.json" & direct_broker=$!
for attempt in 1 2 3 4 5; do test -S "$DEMO/allowed/broker.sock" && break; sleep 0.1; done
NORTH_ECHO_FAKE_CREDENTIAL="$(sed -n '1p' "$DEMO/credential.txt")" \
  "$DEMO/runtime_guard" "$DEMO/allowed" "$DEMO/allowed/runtime_probe" \
  "$DEMO/allowed/allowed.txt" "$DEMO/protected.txt" "$DEMO/allowed/broker.sock" \
  "$DEMO/allowed/request.json" "$HOST_NET" "$HOST_USER" 'FAKE-CREDENTIAL-' || true
wait "$direct_broker"
```

The deliberate incomplete launch already has Landlock, seccomp, and broker access, but its attestation reports `private_net:false`, host cgroup values, and `credential_absent:false`. Composition is conjunctive: several successful layers do not compensate for missing outer controls.

## Exercise 4 - Repair, attest, and collect

Start a fresh one-shot broker, generate the structured spec without shell-built JSON, and run the complete launcher:

```bash
rm "$DEMO/direct-event.json"
python3 demo_broker.py "$DEMO/allowed/broker.sock" "$DEMO/token.txt" \
  "$DEMO/credential.txt" "$DEMO/event.json" & broker_pid=$!
trap 'kill "$broker_pid" 2>/dev/null || true; wait "$broker_pid" 2>/dev/null || true' EXIT
for attempt in 1 2 3 4 5; do test -S "$DEMO/allowed/broker.sock" && break; sleep 0.1; done
python3 - "$DEMO" "$HOST_NET" "$HOST_USER" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
spec = {
    "guard": str(root / "runtime_guard"),
    "allowed_root": str(root / "allowed"),
    "command": [str(root / "allowed" / "runtime_probe"),
                str(root / "allowed" / "allowed.txt"), str(root / "protected.txt"),
                str(root / "allowed" / "broker.sock"), str(root / "allowed" / "request.json"),
                sys.argv[2], sys.argv[3], "FAKE-CREDENTIAL-"],
    "memory_max": 50331648, "tasks_max": 16, "cpu_percent": 50,
}
(root / "spec.json").write_text(json.dumps(spec) + "\n")
PY
NORTH_ECHO_FAKE_CREDENTIAL="$(sed -n '1p' "$DEMO/credential.txt")" \
  python3 complete_runtime.py "$DEMO/spec.json" "$DEMO/result.json"
wait "$broker_pid"
trap - EXIT
python3 -m json.tool "$DEMO/result.json"
python3 -m json.tool "$DEMO/event.json"
```

The attestation must report allowed-read and protected-denial true, direct-IP denial and private user/network namespaces true, zero capability sets, `NoNewPrivs` 1, `Seccomp` 2, CPU `50000 100000`, memory `50331648`, swap `0`, PIDs `16`, broker success, and credential absence. The separate event proves the outside broker used its credential; neither result contains it.

Prove non-disclosure and teardown before removing exact paths:

```bash
! grep -F "$(sed -n '1p' "$DEMO/credential.txt")" "$DEMO/result.json"
test ! -e "$DEMO/allowed/broker.sock"
! systemctl --user list-units --all --plain --no-legend 'north-echo-*-10-lab-*.service' | grep .
rm "$DEMO/allowed/runtime_probe" "$DEMO/allowed/allowed.txt" "$DEMO/allowed/request.json"
rm "$DEMO/runtime_guard" "$DEMO/protected.txt" "$DEMO/token.txt" "$DEMO/credential.txt"
rm "$DEMO/spec.json" "$DEMO/result.json" "$DEMO/event.json"
rmdir "$DEMO/allowed" "$DEMO"
```

## Faded practice - From one job to a batch

Before the cold capstone, practice orchestration without changing the controls.
In this disposable lesson workspace, use the JSON-list validation and ordered
trace skills from Module 04 to plan three copies of an already validated runtime
spec. Give them distinct IDs and predict what should happen for workload exit
statuses 0, 7, and 0. Write the prediction in `batch-notes.md`.

Your independent exercise is to invoke the single-job interface sequentially,
preserve IDs and statuses in input order, and inspect exact unit collection after
each invocation. Use simple local static workers, not a broker that only accepts
one connection. Change one resource budget and verify its effective cgroup value
rather than merely inspecting the input JSON.

Deliberate mistake: validate and launch the first job before looking at the
second. Make the second job's task limit zero. Explain in `batch-notes.md` why
partial execution is inappropriate for malformed input. Repair the sequence by
validating all specs and unique identities before any launch. An ordinary worker
exit of 7 is different: its spec was valid, so later jobs should still run.

Checkpoint: show ordered 0/7/0 outcomes, no remaining owned units, and rejection
of a malformed later spec before any workload runs. No batch implementation is
provided; the capstone applies these practiced operations under fresh profiles.

## Checkpoint and troubleshooting

- If the broker socket is not ready, inspect only the owned broker PID and its exact synthetic paths; do not search for or kill name-matched host processes.
- If cgroup values differ, verify the delegated user manager and controllers with `./scripts/linux-preflight`.
- If the probe exits at `execv`, confirm the static workload executable resolves beneath `allowed_root`.
- If broker access fails while `AF_INET` is denied, confirm the socket path is below the allowed root and shorter than the Unix-socket path limit.
- Checkpoint: point to one attested field for each of privilege, filesystem, syscalls, resources, network, and credential mediation, then explain which separate evidence proves teardown.
<!-- /source -->

<!-- PAGEBREAK -->

## Complete source: `complete_runtime.py`

Canonical path: `course/module-10-complete-runtime/lesson-03/complete_runtime.py`

<!-- source: course/module-10-complete-runtime/lesson-03/complete_runtime.py format=code -->
```python
#!/usr/bin/env python3
"""Launch one workload through the complete North Echo containment stack."""

import json
import os
from pathlib import Path
import secrets
import subprocess
import sys


def integer(spec: dict, name: str, minimum: int, maximum: int) -> int:
    value = spec.get(name)
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer from {minimum} through {maximum}")
    return value


def validated(spec: dict) -> tuple[Path, Path, list[str], int, int, int]:
    if not isinstance(spec, dict):
        raise ValueError("spec must be an object")
    guard = Path(spec.get("guard", ""))
    root = Path(spec.get("allowed_root", ""))
    command = spec.get("command")
    if not guard.is_absolute() or not guard.is_file() or guard.is_symlink():
        raise ValueError("guard must be an absolute regular non-symlink path")
    if not root.is_absolute() or not root.is_dir() or root.is_symlink():
        raise ValueError("allowed_root must be an absolute directory without a symlink leaf")
    if not isinstance(command, list) or not command or any(not isinstance(item, str) or "\x00" in item for item in command):
        raise ValueError("command must be a nonempty argv string array")
    root = root.resolve(strict=True)
    executable = Path(command[0]).resolve(strict=True)
    if os.path.commonpath((root, executable)) != str(root) or not executable.is_file():
        raise ValueError("command executable must resolve beneath allowed_root")
    command = [str(executable), *command[1:]]
    return (
        guard.resolve(strict=True), root, command,
        integer(spec, "memory_max", 16 * 1024 * 1024, 1024 * 1024 * 1024),
        integer(spec, "tasks_max", 4, 256),
        integer(spec, "cpu_percent", 10, 100),
    )


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    result_path = Path(sys.argv[2])
    try:
        spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        guard, root, command, memory, tasks, cpu = validated(spec)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"runtime specification denied: {error}", file=sys.stderr)
        return 1

    unit = f"north-echo-{os.getuid()}-10-lab-{secrets.token_hex(6)}.service"
    argv = [
        "systemd-run", "--user", "--wait", "--pipe", "--collect", "--quiet",
        f"--unit={unit}", "--property=KillMode=control-group", "--property=TimeoutStopSec=5s",
        f"--property=CPUQuota={cpu}%", f"--property=MemoryMax={memory}",
        "--property=MemorySwapMax=0", f"--property=TasksMax={tasks}",
        "--property=UnsetEnvironment=NORTH_ECHO_FAKE_CREDENTIAL",
        "--setenv=PATH=/usr/bin:/bin", "--setenv=LANG=C.UTF-8", "--setenv=LC_ALL=C.UTF-8",
        "--", "unshare", "--user", "--map-root-user", "--net", "--",
        "setpriv", "--bounding-set=-all", "--inh-caps=-all", "--ambient-caps=-all",
        "--no-new-privs", "--", "/usr/bin/env", "-i", "PATH=/usr/bin:/bin",
        "LANG=C.UTF-8", "LC_ALL=C.UTF-8", str(guard), str(root), *command,
    ]
    client_env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
    for name in ("XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS"):
        if name in os.environ:
            client_env[name] = os.environ[name]
    try:
        run = subprocess.run(argv, text=True, capture_output=True, check=False,
                             timeout=20, env=client_env)
    except subprocess.TimeoutExpired:
        subprocess.run(["systemctl", "--user", "stop", unit], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=client_env)
        print("runtime timed out and its exact unit was stopped", file=sys.stderr)
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
    return run.returncode != 0


if __name__ == "__main__":
    raise SystemExit(main())
```
<!-- /source -->

<!-- PAGEBREAK -->

## Complete source: `runtime_probe.c`

Canonical path: `course/module-10-complete-runtime/lesson-03/runtime_probe.c`

<!-- source: course/module-10-complete-runtime/lesson-03/runtime_probe.c format=code -->
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
    ssize_t count = read(fd, response, size - 1);
    close(fd);
    if (count <= 0)
        return 0;
    response[count] = '\0';
    return strstr(response, "\"ok\":true") != NULL && strstr(response, forbidden_marker) == NULL;
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

    unsigned long long cap_eff = 1, cap_bnd = 1, cap_amb = 1;
    int no_new_privs = 0, seccomp = 0;
    int status_ok = read_text("/proc/self/status", status, sizeof(status)) == 0 &&
                    status_value(status, "CapEff:\t", &cap_eff) == 0 &&
                    status_value(status, "CapBnd:\t", &cap_bnd) == 0 &&
                    status_value(status, "CapAmb:\t", &cap_amb) == 0 &&
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
           status_ok && cap_eff == 0 && cap_bnd == 0 && cap_amb == 0 ? "true" : "false",
           no_new_privs, seccomp, cpu, memory, swap, pids,
           broker_ok ? "true" : "false", credential_absent ? "true" : "false");
    return !(allowed_read && protected_denied && inet_denied && private_net && private_user &&
             status_ok && cap_eff == 0 && cap_bnd == 0 && cap_amb == 0 &&
             no_new_privs == 1 && seccomp == 2 && broker_ok && credential_absent);
}
```
<!-- /source -->

<!-- PAGEBREAK -->

## Complete source: `demo_broker.py`

Canonical path: `course/module-10-complete-runtime/lesson-03/demo_broker.py`

<!-- source: course/module-10-complete-runtime/lesson-03/demo_broker.py format=code -->
```python
#!/usr/bin/env python3
"""One-shot synthetic operation broker for the composition lesson."""

import hashlib
import json
import os
from pathlib import Path
import socket
import sys


def main() -> int:
    if len(sys.argv) != 5:
        return 2
    socket_path, token_path, credential_path, event_path = map(Path, sys.argv[1:])
    token = token_path.read_text(encoding="utf-8").strip()
    credential = credential_path.read_text(encoding="utf-8").strip()
    if socket_path.exists() or socket_path.is_symlink():
        raise SystemExit("broker socket path already exists")
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        listener.bind(str(socket_path))
        os.chmod(socket_path, 0o600)
        listener.listen(1)
        peer, _ = listener.accept()
        with peer:
            request = json.loads(peer.makefile("rb").readline(16384))
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
<!-- /source -->

<!-- PAGEBREAK -->

## Module 10 independent lab

<!-- source: course/module-10-complete-runtime/lab/README.md format=markdown -->
# Module 10 independent lab - Composed contained runtime

Implement `complete_runtime.py`. The grader invokes:

```text
python3 complete_runtime.py SPEC.json RESULT.json
```

The JSON spec contains an absolute trusted `guard` executable, an absolute `allowed_root`, structured workload `command` argv, and integer `memory_max`, `tasks_max`, and `cpu_percent` limits. The workload executable must resolve beneath the allowed root. Treat the guard as trusted runtime TCB and every command argument as literal data.

Create a uniquely named transient systemd user service with the validated CPU quota, memory limit, zero swap, PID limit, control-group kill behavior, bounded stop time, synchronous waiting, and collection. Inside that cgroup, create fresh user and network namespaces, then empty bounding/inheritable/ambient capability sets and set `no_new_privs`. Remove `NORTH_ECHO_FAKE_CREDENTIAL` from the workload environment. Invoke the guard with the allowed root and exact workload argv; do not use a shell.

Write one result object containing schema 1, workload status, exact unit name, stdout, stderr, and the parsed final-line attestation. Propagate nonzero workload status through a nonzero launcher status. Invalid roots, commands, limits, or shapes must fail before a result or unit exists. On timeout, stop only the exact unit created by this invocation. Successful and failed runs must leave no transient unit.

The external grader compiles its own static guard and workload probe, rotates synthetic paths, capabilities, fake credentials, canaries, and unit names, and runs a separate host-side Unix-socket broker. It verifies:

- exact CPU, memory, swap, and PID controller values;
- different user and network namespaces plus `AF_INET` denial;
- empty effective/bounding/ambient capability sets and `no_new_privs`;
- effective Landlock allowed/protected reads and seccomp filter mode;
- successful `AF_UNIX` capability mediation and broker-side fake-credential use;
- credential absence from the workload and all returned output;
- literal path handling without shell evaluation;
- failure status/stderr propagation, invalid-spec rejection, and exact cleanup.

The starter runs the guard and workload directly, so useful inner controls execute but outer composition properties fail. The lab withholds a complete implementation; use the launch dependency and interface practiced in Lessons 10.01-10.03.

```bash
python3 -m py_compile complete_runtime.py
../../lab-grade module-10
../../lab-grade module-10 --mode exam
```

- `py_compile` checks syntax without creating a unit.
- Practice mode names the lesson associated with each failed property.
- Exam mode repeats fresh external checks but withholds lesson references.

Use only the grader's generated local objects. Never substitute a real credential, external service, host firewall change, privileged cgroup, or production path.
<!-- /source -->

<!-- PAGEBREAK -->

## Integrated security model

The outer-to-inner execution chain is:

```text
host-side synthetic broker
  -> transient delegated cgroup
    -> user and network namespaces
      -> empty capability sets plus no_new_privs
        -> empty fixed workload environment
          -> Landlock filesystem rules
            -> native default-deny seccomp filter
              -> static workload and effective-state attestation
  -> synchronous unit collection
```

The ordering is policy. Entering the cgroup first accounts for every descendant. Entering the user namespace before capability removal ensures UID-mapping capabilities are removed. Applying Landlock before seccomp preserves setup syscalls while keeping them unavailable to the workload. Starting the broker before removing IP connectivity makes the Unix-socket capability usable without giving the workload a route. Collection after exit covers success and failure.

No field subsumes another. `Seccomp: 2` says a filter exists, not that it is useful. A protected-path denial says nothing about inherited descriptors or sockets. Fresh namespaces say nothing about Unix-socket authorization. Empty capabilities do not bound memory. Broker success does not prove credential absence. The grader checks each property independently and requires all of them.

## Failure interpretation

- A missing result means validation, setup, or timeout handling failed before a trustworthy record existed.
- A nonzero recorded status with stderr is a workload failure the launcher must preserve.
- Correct cgroup values with `private_net:false` identify a namespace-layer failure.
- `Seccomp:2` with a successful IPv4 socket identifies a policy-content failure.
- Broker success with `credential_absent:false` identifies ambient authority.
- A passing attestation followed by a remaining unit identifies a lifecycle failure.

## Cleanup and replay

The guided broker is a foreground, one-shot process retained by exact PID and unlinks its exact socket in `finally`. The launcher uses a random exact unit name, waits synchronously, and requests collection. Timeout stops only that unit. No veth pair, firewall object, host cgroup, background daemon, or public service is created, so the runtime registry needs no new persistent resource type.

Lesson, module, and all-scope reset remove student work and randomized fixtures while preserving only progress metadata. A later start rotates fixture details; every grade creates a separate fresh fixture.

## Optional primary references

Required teaching is above. Optional depth: `landlock(7)`, `seccomp(2)`, `proc_pid_status(5)`, `user_namespaces(7)`, `network_namespaces(7)`, `unshare(1)`, `setpriv(1)`, `systemd-run(1)`, `systemd.resource-control(5)`, the cgroup v2 kernel documentation, and `unix(7)`.

## Completion checkpoint

A complete run has three evidence classes: workload attestation for effective controls, a broker event proving fake-credential use outside the workload, and post-run unit/socket checks proving teardown. Passing only one or two is not a passing composition.
