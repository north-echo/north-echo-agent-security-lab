<!-- source: course/module-06-seccomp/README.md format=markdown -->
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

## Learning route and limits

Prerequisites: Modules 01-05. Continue as your ordinary account inside the disposable Linux VM. The guided lessons introduce their new syntax and interfaces before the independent lab combines them.

06.01 establishes a functional baseline and the limits of one trace. 06.02 compares failure actions and an incomplete one-call rule. 06.03 constructs a native default-deny policy, then checks useful work and denied calls.

A small list is not automatically sound: it can omit required startup work or allow unnecessary operations. Explain why Seccomp: 2 proves less than a correct rule set. The independent lab deliberately uses a tiny static workload and errno-based denial; it does not promise arbitrary-program compatibility.

Before moving on, demonstrate both useful allowed work and the intended restriction, and explain the difference in your own words. A failed compiler command or missing input is not a security success. Use the independent lab's practice feedback to revisit a specific lesson; passing checks does not replace understanding or make the combined program production-ready.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-06-seccomp/lesson-01/README.md format=markdown -->
# 06.01 - Measure the workload before filtering

## Goal

Collect the syscalls of one explicit file-copy workload, separate startup activity from application intent, and demonstrate why a profile is evidence for policy design rather than a permanent universal allowlist.

## Concepts and preparation

Complete Modules 01-05 first. A syscall profile is a measurement of one program, input, build, and environment. It is not a list of everything that program could ever need. A dynamic executable also asks the kernel to load its runtime libraries before your `main` function begins; those startup calls are part of the observed process.

A **seccomp filter** will later decide which kernel calls may proceed. Before designing that policy, establish an ordinary successful workload and define what "still works" means. Here it means that the output file's bytes equal the input's bytes. Predict whether an empty input needs the same data-write calls as a nonempty input.

From the course root inside the Linux VM:

```bash
./lab-start 06.01
cd .student/06.01
pwd
ls -l workload.c
cat workload.c
```

The commands prepare and enter the student workspace, confirm filenames, and display every supplied source before execution. C sources are text, not executable programs yet. Use the compile commands below to create binaries. For an edit, run `nano FILENAME` with the actual source name, save with `Ctrl-O`, `Enter`, and leave with `Ctrl-X`; then rebuild. Keep all experiments in this disposable VM and leave SELinux enforcing on Fedora.

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

`O_RDONLY` requests reading. `O_WRONLY | O_CREAT | O_TRUNC` permits writing, creation, and replacement of old content; `0600` is an octal permission request for a new file. Do not use the same path for input and output: opening the output with truncation can erase the input before it is read. This lesson uses different synthetic names on purpose.

The `while` condition first assigns the result of `read` to `count`, then compares it with zero. A zero result means end of input, not an error. The following unbraced `if` is the loop body; adding another statement would require braces to keep it in that body. The example treats a short write as failure rather than retrying, which is sufficient for the supplied tiny regular files but not a complete production copier.

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
- If your installed `strace` omits PID prefixes or prints unfinished/resumed records, inspect `trace.txt` directly. This display pipeline is a convenience, not a parser suitable for generating a security policy automatically.
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

## Replay and source truth

From this workspace, `cd ../..` then `./lab-reset 06.01` discards this lesson's generated work after confirmation. A filter installed in a child does not modify your parent shell or global kernel policy; do not attempt a host-wide "seccomp reset."

Use `man strace` in the VM for the installed tracing options and [write(2)](https://man7.org/linux/man-pages/man2/write.2.html) for byte-count/error behavior. Keep the compiler, libc, kernel, architecture, and test input alongside a profile.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-06-seccomp/lesson-02/README.md format=markdown -->
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
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-06-seccomp/lesson-03/README.md format=markdown -->
# 06.03 - Launch with a native default-deny filter

## Goal

Turn the measured workload into a native-architecture allowlist, prove filter state inside the child, and preserve file access while denying unlisted kernel interfaces.

## Concepts and preparation

Complete 06.01-06.02 first. This lesson switches to a default-deny policy for a stated small workload. Every allowed call needs a reason: startup, file observation, output, or orderly exit. A minimal-looking list that prevents the required workload from starting is not a successful design.

The **native architecture** matters because syscall numbers and available names differ between ABIs. The library resolves names for the current architecture and emits the associated architecture check. This lesson is not a multi-architecture compatibility launcher. Do not replace names with numbers copied from another machine.

A kernel report of `Seccomp: 2` shows filter mode, not the filter's exact rules or correctness. We need both that state observation and behavioral evidence: allowed work succeeds and selected unrelated calls receive the expected error.

From the course root inside the Linux VM:

```bash
./lab-start 06.03
cd .student/06.03
pwd
ls -l policy_probe.c allowlist.c
cat policy_probe.c
cat allowlist.c
```

The commands prepare and enter the student workspace, confirm filenames, and display every supplied source before execution. C sources are text, not executable programs yet. Use the compile commands below to create binaries. For an edit, run `nano FILENAME` with the actual source name, save with `Ctrl-O`, `Enter`, and leave with `Ctrl-X`; then rebuild. Keep all experiments in this disposable VM and leave SELinux enforcing on Fedora.

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
        if (!nnp || !seccomp) {
            fprintf(stderr, "required process-state fields are absent\n");
            return 1;
        }
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

The zero-initialized status buffer reserves its last byte for string termination. `strstr` locates the two field names; absent fields cause an explicit error rather than a fabricated report. The precision in the `dprintf` format prints only each short field/value segment. This is a focused observer for the course baseline, not a general procfs parser.

`report` prints a raw syscall result and `errno`; its caller returns 0 because the observation itself completed even when the requested syscall was denied. Therefore the denial checkpoint must inspect `result=-1 errno=1`, not merely the observer's exit status. This differs deliberately from 06.02's probe, which returned 1 for a denied call.

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
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0) {
        perror("set no_new_privs");
        seccomp_release(context);
        return 1;
    }
    int loaded = seccomp_load(context);
    if (loaded < 0) {
        fprintf(stderr, "install seccomp: %s\n", strerror(-loaded));
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

`allowed` is an array of pointers to constant strings. Dividing its total size by one element's size gives the number of entries, so the loop does not need a separately maintained count. `allow_name` resolves each entry and asks for an unconditional allow rule. Skipping a name absent from the native architecture does not allow an unknown syscall: the default remains denial. A typo can still break required functionality, which is why the functional tests matter.

The error paths distinguish APIs: `prctl` reports failure through `errno`, while `seccomp_load` returns a negative error number. The launcher prints `strerror(-loaded)` for the latter rather than using a stale `errno`. Releasing the library context afterward does not remove the installed kernel filter.

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

For the intentional policy-edit exercise, copy only this lesson's source with `cp allowlist.c extra_call.c`, open `nano extra_call.c`, and add `"getppid",` to its allowed-name array. Save and compile it as `extra-call` using the same library flags as above. Run `./extra-call ./policy-probe unexpected`. It returns a real parent PID, proving that default-deny still depends on a justified allowlist. Return to `./allowlist ./policy-probe unexpected` and require `result=-1 errno=1`; do not leave the expanded binary in the final checkpoint command.

The file test is also a boundary lesson: seccomp allowed `openat`, so it cannot distinguish `note.txt` from another pathname. Compose it with Module 05's `openat2`/Landlock layer for pathname policy. It likewise does not meter CPU/memory or authorize network destinations.

## Checkpoint and troubleshooting

```bash
./allowlist ./policy-probe status | grep -q 'Seccomp:[[:space:]]*2'
test "$(./allowlist ./policy-probe unexpected)" = 'result=-1 errno=1'
```

- If the static probe fails before output, compare its `strace` surface with the allowlist on this supported VM and add only justified startup calls.
- `EPERM` from `seccomp_load` usually means `no_new_privs` was not set or policy setup was reordered.
- If a newer libc needs a startup call not present here, record the exact failing call and build versions. Do not automatically grant every observed call or turn the default into allow; investigate whether the missing operation is required by the stated workload.
- Checkpoint: identify the functional syscalls, startup syscalls, deliberately denied syscalls, and the separate pathname assumption.

## Replay and source truth

From this workspace, `cd ../..` then `./lab-reset 06.03` discards this lesson's generated work after confirmation. A filter installed in a child does not modify your parent shell or global kernel policy; do not attempt a host-wide "seccomp reset."

The library's [seccomp_load manual](https://github.com/seccomp/libseccomp/blob/main/doc/man/man3/seccomp_load.3) and [architecture API manual](https://github.com/seccomp/libseccomp/blob/main/doc/man/man3/seccomp_arch_add.3) document the installation and architecture checks. Kernel [seccomp documentation](https://docs.kernel.org/userspace-api/seccomp_filter.html) explains why syscall filtering is only one containment layer.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-06-seccomp/lab/README.md format=markdown -->
# Module 06 independent lab - Default-deny syscall launcher

## Preparation and practiced skills

Complete 06.01-06.03 first. Use 06.01 to justify the workload and measurements, 06.02 to explain the required errno behavior, and 06.03 to plan native architecture, rule construction, loading, and post-exec evidence.

The starter checks that a command was supplied, then calls `execv` with the exact executable path and remaining arguments. Returning from exec prints an error and returns nonzero. The interface is functional, but no filter or privilege floor exists yet. Do not replace it with a shell command string.

A name genuinely absent from the native ABI can remain denied rather than receiving a rule, as practiced in 06.03. That is different from ignoring a failed rule-add operation for an available call. Keep the default deny behavior and stop on actual setup errors. The supplied static observation workload, not arbitrary programs, defines the functional contract.

From the course root:

```bash
./lab-start module-06
cd .student/06.lab
pwd
ls -l seccomp_guard.c
cat seccomp_guard.c
nano seccomp_guard.c
```

The commands prepare your editable lab, enter and inspect it, then open the starter for reading and editing. Save in nano with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. Rebuild after each C edit using the compiler command below. Keep the canonical files and grader unchanged.

```c
#include <stdio.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s COMMAND [ARG...]\n", argv[0]);
        return 2;
    }
    execv(argv[1], &argv[1]);
    perror("execv");
    return 1;
}
```

## Contract


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
- fail closed if context creation, architecture validation, rule installation for an available call, privilege-floor establishment, filter loading, or exec fails; a name unavailable on the native ABI remains denied rather than broadening the default action.

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

## Verify, explain, and replay

Run the starter and record its failed properties before editing. After repair, preserve both successful useful work and the expected denials/errors; a launcher that refuses everything does not pass. A compiler failure, missing executable, or missing fixture is not the desired security outcome.

For each passing property, explain which earlier lesson supplied the mechanism and what the observation does **not** establish. Keep an unresolved property unresolved rather than weakening its expected result. The lab intentionally withholds a combined implementation.

From this workspace, `cd ../..` returns to the course root. `./lab-reset module-06` removes this module's student work and generated fixtures after confirmation; preserve notes first. Start the module again for a fresh randomized attempt. Never substitute real credentials, personal directories, or external services for the synthetic fixtures.
<!-- /source -->
