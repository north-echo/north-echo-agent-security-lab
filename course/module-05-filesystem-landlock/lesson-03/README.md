# 05.03 - Restrict a child with Landlock

## Goal

Apply an unprivileged Landlock ruleset before `exec`, then prove both its protection and its pre-opened-descriptor limit. Compose Landlock with descriptor hygiene rather than mistaking either control for the other.

## Concepts and preparation

Complete 05.02 and recall `no_new_privs` from 03.03. A cooperative broker can use a safe open operation, but an arbitrary child can issue its own file operations. **Landlock** adds kernel-enforced restrictions to the calling thread and its future descendants. An unprivileged program can reduce its access; it cannot use a Landlock rule to override existing permissions.

A **ruleset** declares the categories of access it handles. A **rule** grants selected handled accesses beneath a directory. A handled access with no applicable grant is denied; an unhandled category is generally outside that policy. The **ABI version** is the kernel interface generation, not the distribution version. New headers do not make an older running kernel support new rights.

We intentionally use a static, tiny child so its program and runtime code fit in one allowed tree. This keeps dynamic-loader permissions out of the first example. It does not mean static linking itself is a sandbox. Predict whether a file already opened before the restriction will lose its read authority.

From the course root in the disposable VM:

```bash
./lab-start 05.03
cd .student/05.03
pwd
ls -l fd_probe.c landlock_launch.c pass_fd.py
cat fd_probe.c
cat landlock_launch.c
cat pass_fd.py
```

`lab-start` prepares the student copy. The next commands enter and inspect it; each `cat` reads a supplied source before execution. Missing files usually mean the wrong working directory or lesson number. Edit only these student copies with `nano FILENAME`, save with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. Recompile after every C edit. An old binary does not automatically track a changed source.

## Exercise 1 - Build a static observation probe

`fd_probe.c` opens a named path or reads an existing descriptor. Its complete source is:

<!-- source: course/module-05-filesystem-landlock/lesson-03/fd_probe.c format=code -->
```c
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s path PATH | fd NUMBER\n", argv[0]);
        return 2;
    }
    int fd = strcmp(argv[1], "path") == 0 ? open(argv[2], O_RDONLY) : atoi(argv[2]);
    char buffer[256];
    ssize_t count = read(fd, buffer, sizeof(buffer));
    if (count < 0) {
        fprintf(stderr, "DENIED: %s\n", strerror(errno));
        return 1;
    }
    return write(STDOUT_FILENO, buffer, (size_t)count) == count ? 0 : 1;
}
```
<!-- /source -->

### Source, line by line

- The probe accepts exactly a mode and operand.
- `path` performs a new `open`; `fd` reuses an integer descriptor inherited across `exec`.
- `read` is the common observation. On failure the probe reports `DENIED` and returns nonzero.
- The final `write` makes successful access independently visible.

Compile it statically inside the future allowed tree so its executable and runtime code need no outside filesystem access:

```bash
rm -rf demo
mkdir -p demo/allowed demo/protected
printf 'allowed\n' > demo/allowed/note.txt
printf 'synthetic-secret\n' > demo/protected/secret.txt
cc -std=c11 -Wall -Wextra -Werror -O2 -static fd_probe.c -o demo/allowed/fd-probe
```

### Line by line

- The files are synthetic and local to the lesson.
- `-static` puts the probe's required runtime code in its binary. This keeps the policy example focused on one allowed tree rather than adding read/execute rules for dynamic-loader paths.
- A static build failure usually means the VM lacks its distribution C development files; install the documented build toolchain rather than broadening the policy.

## Exercise 2 - Apply a version-aware Landlock policy

Complete source of `landlock_launch.c`:

<!-- source: course/module-05-filesystem-landlock/lesson-03/landlock_launch.c format=code -->
```c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/close_range.h>
#include <linux/landlock.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <unistd.h>

static int create_ruleset(const struct landlock_ruleset_attr *attr, size_t size, __u32 flags) {
    return syscall(SYS_landlock_create_ruleset, attr, size, flags);
}

static int add_rule(int ruleset_fd, const struct landlock_path_beneath_attr *attr) {
    return syscall(SYS_landlock_add_rule, ruleset_fd, LANDLOCK_RULE_PATH_BENEATH, attr, 0);
}

static int restrict_self(int ruleset_fd) {
    return syscall(SYS_landlock_restrict_self, ruleset_fd, 0);
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

static int close_inherited(void) {
    /* Both course baselines support this operation. Do not weaken the
       descriptor guarantee with a fallback bounded by a mutable soft limit. */
    return syscall(SYS_close_range, 3U, ~0U, CLOSE_RANGE_CLOEXEC);
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: %s ALLOWED_ROOT COMMAND [ARG...]\n", argv[0]);
        return 2;
    }
    int abi = create_ruleset(NULL, 0, LANDLOCK_CREATE_RULESET_VERSION);
    if (abi < 1) {
        perror("Landlock ABI");
        return 1;
    }
    fprintf(stderr, "Landlock ABI %d\n", abi);
    __u64 rights = supported_rights(abi);
    struct landlock_ruleset_attr ruleset = {.handled_access_fs = rights};
    int ruleset_fd = create_ruleset(&ruleset, sizeof(ruleset), 0);
    int root_fd = open(argv[1], O_PATH | O_CLOEXEC);
    if (ruleset_fd == -1 || root_fd == -1) {
        perror("create policy");
        return 1;
    }
    struct landlock_path_beneath_attr rule = {
        .allowed_access = rights,
        .parent_fd = root_fd,
    };
    if (add_rule(ruleset_fd, &rule) == -1) {
        perror("landlock_add_rule");
        return 1;
    }
    close(root_fd);
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) == -1 || restrict_self(ruleset_fd) == -1) {
        perror("restrict self");
        return 1;
    }
    close(ruleset_fd);
    if (close_inherited() == -1) {
        perror("close inherited descriptors");
        return 1;
    }
    execv(argv[2], &argv[2]);
    perror("execv");
    return 1;
}
```
<!-- /source -->

### Source, line by line

- The three small syscall wrappers keep the argument ordering visible and return raw success or failure to the caller.
- `supported_rights` builds the ABI-1 set first, then adds rights introduced by ABI 2, 3, 5, and 9 only when both the build headers and the running kernel support them. The preprocessor guards keep the source buildable with older distribution headers.
- `close_inherited` requires the kernel's range operation. `CLOSE_RANGE_CLOEXEC` preserves descriptors until `exec` but prevents the new program from inheriting them.
- Failure stops the launch, including an unsupported operation. The course baselines support this flag (introduced in Linux 5.11); there is no weaker fallback bounded by a process's mutable descriptor soft limit.
- `main` queries and prints the ABI before it creates policy. It never treats an unavailable Landlock interface as permission to continue.
- The ruleset declares which operations Landlock will handle; the path-beneath rule grants that same set only under `root_fd`.
- `PR_SET_NO_NEW_PRIVS` and `restrict_self` are joined by `||`: if either fails, `execv` is unreachable.
- The policy and root descriptors are closed before inherited descriptors are marked. Standard input, output, and error remain available.
- `execv(argv[2], &argv[2])` preserves the caller's structured argv. Returning from `execv` is always an error and is reported.

### Unhandled means allowed

### Read the policy structures without guessing

The `__u64` type is an unsigned 64-bit value used for the access mask. A `|` combines right bits; `|=` adds bits to an existing mask. `#ifdef` is a compile-time test for a header definition, whereas `if (abi >= ...)` is a runtime test. Both must agree before this binary requests a newer right.

`create_ruleset(NULL, 0, LANDLOCK_CREATE_RULESET_VERSION)` is a query: no policy structure is supplied. The next call passes an initialized `landlock_ruleset_attr` and its size to create a policy descriptor. The `landlock_path_beneath_attr` holds the rights granted under the already-open root. `&rule` passes its address to the add-rule operation.

The lesson grants **all handled rights under the allowed tree**, not read-only access. Those grants only remove Landlock's denial for that tree; normal permissions and other security modules can still deny access. Restricting this process does not change global SELinux policy. On Fedora, keep SELinux enforcing throughout.

The `||` condition short-circuits: if setting `no_new_privs` fails, the second call is not attempted and the error path returns. If installing Landlock fails, execution also stops. Closing the ruleset descriptor afterward releases the userspace handle, not the installed restriction. Like the no-new-privileges bit, the resulting access reduction is not something this child can casually undo.

The tiny observation probe's conditional expression selects either a new path open or an already-supplied integer descriptor. Its fixed 256-byte read is enough for the supplied short fixtures, not a general file-copy contract. Use exactly the documented modes; the probe is not a production input parser.

### Compare handled rights with the running ABI

Landlock restricts only the access rights listed in `handled_access_fs`. With the historical exception of `LANDLOCK_ACCESS_FS_REFER`, a filesystem right the running kernel supports but the ruleset does not handle stays allowed. A launcher that stops at ABI 3 therefore under-restricts on ABI 5, where `LANDLOCK_ACCESS_FS_IOCTL_DEV` can restrict device IOCTL operations, and on ABI 9, where `LANDLOCK_ACCESS_FS_RESOLVE_UNIX` can restrict pathname UNIX-socket resolution.

Version-aware code can handle only rights known to its source and build headers. The guarded ABI 5 and ABI 9 additions make this source enforce the complete filesystem-right set it knows when the headers expose those constants and the running kernel supports them. If newer headers introduce another filesystem right, this source and its stated guarantee must be reviewed again; runtime ABI detection cannot invent a constant absent at build time.

Checkpoint: print the ABI reported by the running kernel and compare it with the highest filesystem ABI explicitly handled by the source:

```bash
cc -std=c11 -Wall -Wextra -Werror -O2 landlock_launch.c -o landlock-launch
./landlock-launch demo/allowed /bin/true 2>&1 | head -1
grep -n 'abi >=' landlock_launch.c
```

- Compile first: a freshly prepared lesson has source files, not a prebuilt launcher.
- The next command relies on the launcher's diagnostic and may later deny `/bin/true` because that executable is outside the allowed tree; only its first line is the ABI observation. The pipeline's status is not a launch-success assertion.
- `grep` lists the explicit ABI gates in the source. A high runtime number is not by itself proof that every future right is handled.

Build it:

```bash
cc -std=c11 -Wall -Wextra -Werror -O2 landlock_launch.c -o landlock-launch
./landlock-launch "$PWD/demo/allowed" "$PWD/demo/allowed/fd-probe" path "$PWD/demo/allowed/note.txt"
./landlock-launch "$PWD/demo/allowed" "$PWD/demo/allowed/fd-probe" path "$PWD/demo/protected/secret.txt" || echo 'outside path denied'
```

### Line by line

- The compiler flags reject warnings and create the lesson-local launcher.
- Each launch first reports `Landlock ABI N` on standard error, where `N` depends on the running kernel.
- The first launch grants filesystem rights beneath `demo/allowed`; the static probe executes and prints `allowed`.
- The second launches the same child under the same policy but asks it to open a protected sibling. Expected: `DENIED` and the shell message.

The source performs these security-sensitive steps in order:

- `landlock_create_ruleset(..., LANDLOCK_CREATE_RULESET_VERSION)` queries the running kernel ABI. Failure is reported; the launcher never silently runs unconfined.
- `supported_rights` begins with ABI-1 filesystem rights and conditionally adds `REFER` for ABI 2+, `TRUNCATE` for ABI 3+, device `IOCTL` for ABI 5+, and pathname UNIX-socket resolution for ABI 9+ when the build headers define those rights.
- A ruleset handles those rights. A path-beneath rule grants them only under the already-open allowed-root descriptor.
- The root descriptor is closed after the rule is added.
- `PR_SET_NO_NEW_PRIVS` is set before `landlock_restrict_self`; unprivileged callers need this promise that `exec` cannot grant new privilege.
- Restriction occurs before `execv`, so it is inherited by the child. Errors stop the launch.
- `execv` uses the exact argument vector and an explicit executable path; there is no shell parser or `PATH` search.

This proves future path access is constrained. It does not prove existing descriptors were revoked.

## Exercise 3 - Reproduce and repair the pre-opened-FD bypass

`pass_fd.py` deliberately opens the protected file before launching:

<!-- source: course/module-05-filesystem-landlock/lesson-03/pass_fd.py format=code -->
```python
#!/usr/bin/env python3
import os
import subprocess
import sys


with open(sys.argv[1], "rb") as stream:
    run = subprocess.run(
        ["./landlock-launch", sys.argv[2], sys.argv[3], "fd", str(stream.fileno())],
        pass_fds=(stream.fileno(),),
        check=False,
    )
raise SystemExit(run.returncode)
```
<!-- /source -->

### Source, line by line

- `open` creates authority to the protected object before Landlock is installed.
- `pass_fds` deliberately clears close-on-exec for that descriptor in the immediate child.
- The launcher receives the allowed root, exact probe path, `fd` mode, and descriptor number as distinct argv elements.
- The wrapper returns the observed child status.

The repaired launcher calls `close_inherited` after using its policy descriptors and before `execv`. `close_range(..., CLOSE_RANGE_CLOEXEC)` marks every descriptor from 3 upward close-on-exec. This single-threaded launcher creates no later descriptors before exec; it does not claim to solve concurrent descriptor creation in a multithreaded launcher.

Run the repaired result:

```bash
python3 pass_fd.py "$PWD/demo/protected/secret.txt" "$PWD/demo/allowed" "$PWD/demo/allowed/fd-probe" || echo 'inherited descriptor denied'
```

Expected: the probe reports a bad descriptor and the shell prints `inherited descriptor denied`.

Intentional failure: make a temporary copy without the `close_inherited()` call and its error block, then compile it while suppressing only the expected unused-helper warning:

```bash
sed '/if (close_inherited() == -1)/,+3d' landlock_launch.c > unsafe_launch.c
cc -std=c11 -Wall -Wextra -Wno-unused-function -O2 unsafe_launch.c -o unsafe-launch
```

- The addressed `sed` range removes the four-line call/error block from the temporary source only.
- `-Wno-unused-function` permits the deliberately orphaned helper; it does not suppress other warning classes.
- The executable name is inside `pass_fd.py`, not an argument to its command. Open your student copy with `nano pass_fd.py`, change only that executable string for the supplied synthetic comparison, save, and repeat the same Python invocation. Restore the original string immediately afterward. The protected fixture is not a real credential.
- Delete the temporary files, return to the shipped launcher, and confirm denial.

Landlock mediates new filesystem operations by path; reading an already-open file description is not a new path lookup.

## Checkpoint and troubleshooting

```bash
test "$(./landlock-launch "$PWD/demo/allowed" "$PWD/demo/allowed/fd-probe" path "$PWD/demo/allowed/note.txt")" = allowed
! ./landlock-launch "$PWD/demo/allowed" "$PWD/demo/allowed/fd-probe" path "$PWD/demo/protected/secret.txt"
! python3 pass_fd.py "$PWD/demo/protected/secret.txt" "$PWD/demo/allowed" "$PWD/demo/allowed/fd-probe"
```

- `Landlock ABI: Function not implemented` means the kernel lacks Landlock. Use the supported VM and record the skip; do not run the child unconfined.
- `Permission denied` on the allowed executable usually means the probe is outside the allowed tree or was not compiled successfully.
- A visible synthetic secret in the final command means inherited descriptors were not marked close-on-exec.
- Checkpoint: identify which assertion tests Landlock and which tests the independent descriptor-hygiene layer.

## Replay and source truth

The demo contains only lesson-created synthetic files. Do not substitute personal directories or real credentials. From this workspace, `cd ../..` then `./lab-reset 05.03` discards this lesson's edits and fixtures after confirmation. No host mount, filesystem permission, or global security setting needs changing.

The kernel's [Landlock userspace guide](https://cdn.kernel.org/doc/html/latest/userspace-api/landlock.html) documents handled rights, ABI additions, and inherited restrictions. [close_range(2)](https://man7.org/linux/man-pages/man2/close_range.2.html) documents the separate descriptor control. Record build headers and the running ABI; neither alone proves which rights this binary enforces.
