<!-- source: course/module-05-filesystem-landlock/README.md format=markdown -->
# Module 05 - Confine filesystem access

Turn a directory name into an enforced filesystem boundary. First break lexical path checks with traversal and symlinks. Then anchor lookup to a directory descriptor with `openat2(2)` and add Landlock so an entire child process is restricted. Finally confront Landlock's important pre-opened-file-descriptor limit.

Play in order: `05.01`, `05.02`, `05.03`, then `module-05`.

Outcomes:

- distinguish a pathname string from the kernel object reached during lookup;
- reproduce traversal, prefix-collision, and symlink escapes against a naive broker;
- use `openat2` with `RESOLVE_BENEATH`, `RESOLVE_NO_MAGICLINKS`, and `RESOLVE_NO_SYMLINKS` for descriptor-relative lookup;
- query the Landlock ABI, select supported rights, add a path-beneath rule, set `no_new_privs`, and restrict a child before `exec`;
- demonstrate that Landlock does not revoke already-open descriptors and remove that inherited authority before launch.

Prerequisites: Modules 01-04, Linux, a C compiler, Linux UAPI headers containing `openat2.h` and `landlock.h`, and a kernel with `openat2` and Landlock. The lessons require no root privilege, mount, network access, or host policy change.

Cross-layer boundary: `openat2` protects individual brokered lookups. Landlock restricts future filesystem operations by the launched process. Neither one closes an already-open descriptor; descriptor hygiene from Module 01 remains necessary.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-05-filesystem-landlock/lesson-01/README.md format=markdown -->
# 05.01 - Break pathname string checks

## Goal

Observe that a pathname is a lookup request, not an object identity. Break a plausible string-prefix policy with a similarly named sibling and with a symlink, then repair those demonstrations with resolved-object containment while naming the remaining race.

## Exercise 1 - Build only synthetic local paths

```bash
rm -rf demo
mkdir -p demo/allowed demo/allowed-escape demo/protected
printf 'allowed\n' > demo/allowed/note.txt
printf 'prefix-secret\n' > demo/allowed-escape/secret.txt
printf 'symlink-secret\n' > demo/protected/secret.txt
ln -s ../protected/secret.txt demo/allowed/link.txt
python3 naive_open.py demo/allowed note.txt
```

### Line by line

- `rm -rf demo` removes only the lesson-owned directory in the disposable workspace, preventing stale evidence.
- `mkdir -p` creates an allowed tree, a sibling whose name shares the `allowed` prefix, and a protected sibling.
- Each `printf` creates synthetic text; none is a real credential or host file.
- `ln -s` places a pathname inside the allowed tree whose target object is outside it.
- The final command asks the naive broker for an ordinary allowed file. Expected: `allowed`.

## Exercise 2 - Exploit the lexical policy

Complete source of `naive_open.py`:

```python
#!/usr/bin/env python3
import os
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} ROOT REQUEST", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).absolute()
    candidate = Path(os.path.abspath(root / sys.argv[2]))
    if not str(candidate).startswith(str(root)):
        print("DENIED: lexical prefix mismatch", file=sys.stderr)
        return 1
    print(candidate.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### Source, line by line

- `os.path.abspath` normalizes `..` text but does not resolve symlink targets.
- `Path.absolute` produces a pathname; it does not establish a kernel-enforced root.
- `startswith` compares characters. It cannot distinguish `allowed` from `allowed-escape` and does not identify the object behind `link.txt`.
- `read_text` performs a new lookup after the check, leaving both semantic mismatch and a check/use window.
- The exit status distinguishes a policy denial from normal completion.

Run both bypasses:

```bash
python3 naive_open.py demo/allowed ../allowed-escape/secret.txt
python3 naive_open.py demo/allowed link.txt
```

### Line by line

- `..` reaches the sibling `allowed-escape`; its absolute string still begins with the characters ending in `allowed`.
- `link.txt` has an allowed lexical name, but normal lookup follows it to `demo/protected/secret.txt`.
- Expected: both synthetic secret strings print. This proves the check is not a confinement boundary; it does not imply access to any path beyond this lesson.

## Exercise 3 - Repair the demonstrations, identify the limit

`resolved_open.py` resolves both root and candidate, then uses `relative_to` as a path-component comparison:

```bash
python3 resolved_open.py demo/allowed note.txt
python3 resolved_open.py demo/allowed ../allowed-escape/secret.txt || echo 'traversal denied'
python3 resolved_open.py demo/allowed link.txt || echo 'symlink escape denied'
```

### Line by line

- The first lookup remains functional and prints `allowed`.
- `resolve(strict=True)` follows existing symlinks and rejects missing components.
- `relative_to(root)` compares path components, avoiding the prefix-collision error.
- `|| echo` runs only after the expected nonzero denial; it makes the result visible without hiding success as failure.
- Expected: the allowed read succeeds and both escapes print `DENIED` plus the matching shell message.

Intentional failure: replace `candidate.relative_to(root)` with the original `startswith` check and rerun the traversal. Restore the component-aware version before the checkpoint.

This repair is useful application validation, but it still separates checking from opening. Another process could exchange a checked component before `read_text` opens it. Lesson 05.02 asks the kernel to resolve and open in one operation.

## Checkpoint and troubleshooting

```bash
test "$(python3 resolved_open.py demo/allowed note.txt)" = allowed
! python3 resolved_open.py demo/allowed ../allowed-escape/secret.txt
! python3 resolved_open.py demo/allowed link.txt
```

- `!` succeeds only when the guarded command fails, so these are denial assertions.
- If `ln` says the link exists, rerun the scoped `rm -rf demo` setup.
- If `resolve(strict=True)` reports a missing file, verify the setup paths rather than weakening strict resolution.
- Checkpoint: explain why component-aware resolution repairs these examples but is not atomic authorization.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-05-filesystem-landlock/lesson-02/README.md format=markdown -->
# 05.02 - Make lookup descriptor-relative with `openat2`

## Goal

Replace check-then-open pathname logic with one kernel operation anchored to an already-open directory. Require resolution to remain beneath that descriptor and reject symlinks.

## Exercise 1 - Compile the brokered open

Complete source of `safe_open.c`:

```c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/openat2.h>
#include <stdio.h>
#include <string.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s ROOT RELATIVE_PATH\n", argv[0]);
        return 2;
    }
    int root_fd = open(argv[1], O_PATH | O_DIRECTORY | O_CLOEXEC);
    if (root_fd == -1) {
        perror("open root");
        return 1;
    }
    struct open_how how = {
        .flags = O_RDONLY | O_CLOEXEC,
        .resolve = RESOLVE_BENEATH | RESOLVE_NO_MAGICLINKS | RESOLVE_NO_SYMLINKS,
    };
    int fd = syscall(SYS_openat2, root_fd, argv[2], &how, sizeof(how));
    if (fd == -1) {
        fprintf(stderr, "DENIED: %s\n", strerror(errno));
        close(root_fd);
        return 1;
    }
    char buffer[4096];
    ssize_t count;
    while ((count = read(fd, buffer, sizeof(buffer))) > 0) {
        if (write(STDOUT_FILENO, buffer, (size_t)count) != count) {
            perror("write");
            close(fd);
            close(root_fd);
            return 1;
        }
    }
    if (count == -1)
        perror("read");
    close(fd);
    close(root_fd);
    return count == -1;
}
```

### Source, line by line

- `_GNU_SOURCE`, `linux/openat2.h`, and `sys/syscall.h` expose the Linux-specific syscall interface and `open_how` structure.
- The program accepts exactly a root and one relative request. A different shape fails with usage status 2.
- `open(..., O_PATH | O_DIRECTORY | O_CLOEXEC)` obtains a reference to the root directory without opening it for file data. `O_CLOEXEC` prevents accidental inheritance.
- `open_how.flags` requests a read-only result descriptor, also close-on-exec.
- `RESOLVE_BENEATH` rejects resolution that escapes above the supplied directory descriptor, including absolute paths.
- `RESOLVE_NO_MAGICLINKS` rejects procfs-style magic links; `RESOLVE_NO_SYMLINKS` rejects every symbolic link in the request.
- `syscall(SYS_openat2, root_fd, ...)` makes the resolution policy and open one atomic kernel request. The root descriptor, not the process working directory, is the anchor.
- A failure is printed as `DENIED` with the kernel reason and returns nonzero.
- The read/write loop copies observed bytes to standard output. It checks both input and output errors.
- Both descriptors are closed on every explicit completion path.

Build it:

```bash
cc -std=c11 -Wall -Wextra -Werror -O2 safe_open.c -o safe-open
```

### Line by line

- `-std=c11` selects the language baseline; the Linux interfaces remain explicitly requested by `_GNU_SOURCE`.
- `-Wall -Wextra -Werror` turns common warnings into build failures rather than accepting ambiguous code.
- `-O2` produces a normal optimized binary; it is not a security boundary.
- `-o safe-open` names only the lesson-local output.

## Exercise 2 - Verify allowed and denied lookups

```bash
rm -rf demo
mkdir -p demo/allowed demo/protected
printf 'allowed\n' > demo/allowed/note.txt
printf 'protected\n' > demo/protected/secret.txt
ln -s ../protected/secret.txt demo/allowed/link.txt
./safe-open demo/allowed note.txt
./safe-open demo/allowed ../protected/secret.txt || echo 'traversal denied'
./safe-open demo/allowed link.txt || echo 'symlink denied'
```

### Line by line

- The setup uses only synthetic paths in this workspace.
- The plain relative lookup prints `allowed`.
- The `..` request fails because `RESOLVE_BENEATH` will not cross above `root_fd`.
- The link request fails because `RESOLVE_NO_SYMLINKS` rejects it before following the target.
- Expected denial errors commonly report `Invalid cross-device link` for escape and `Too many levels of symbolic links` for a forbidden symlink. Match success/failure, not locale-dependent wording.

## Exercise 3 - Remove the boundary and repair it

Create a deliberately weakened copy that retains only magic-link denial:

```bash
sed 's/RESOLVE_BENEATH | RESOLVE_NO_MAGICLINKS | RESOLVE_NO_SYMLINKS/RESOLVE_NO_MAGICLINKS/' safe_open.c > unsafe_open.c
cc -std=c11 -Wall -Wextra -Werror -O2 unsafe_open.c -o unsafe-open
./unsafe-open demo/allowed ../protected/secret.txt
./unsafe-open demo/allowed link.txt
```

### Line by line

- `sed` writes a new lesson-local source; it does not alter the repaired canonical example.
- Without `RESOLVE_BENEATH`, `..` can leave the anchor. Without `RESOLVE_NO_SYMLINKS`, an ordinary symlink can be followed.
- Expected: both unsafe commands print `protected`.
- Delete `unsafe_open.c` and `unsafe-open`, then rerun the repaired denial commands. The repair is the policy in the `openat2` operation itself, not a prior string check.

`openat2` constrains only lookups made through this broker. A child can still call ordinary `open` itself. Lesson 05.03 adds process-wide future-access restrictions.

## Checkpoint and troubleshooting

```bash
test "$(./safe-open demo/allowed note.txt)" = allowed
! ./safe-open demo/allowed ../protected/secret.txt
! ./safe-open demo/allowed link.txt
```

- If `linux/openat2.h` is absent, install the distribution's normal Linux UAPI development headers; do not copy an untrusted header into the lesson.
- `ENOSYS` means the running kernel lacks `openat2`; record the exact kernel and use a supported disposable VM.
- If the safe link succeeds, confirm the repaired binary was rebuilt from `safe_open.c`.
- Checkpoint: point to the directory descriptor, the kernel resolution flags, and the single operation that joins authorization to use.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-05-filesystem-landlock/lesson-03/README.md format=markdown -->
# 05.03 - Restrict a child with Landlock

## Goal

Apply an unprivileged Landlock ruleset before `exec`, then prove both its protection and its pre-opened-descriptor limit. Compose Landlock with descriptor hygiene rather than mistaking either control for the other.

## Exercise 1 - Build a static observation probe

`fd_probe.c` opens a named path or reads an existing descriptor. Its complete source is:

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
    if (syscall(SYS_close_range, 3U, ~0U, CLOSE_RANGE_CLOEXEC) == 0)
        return 0;
    if (errno != ENOSYS)
        return -1;
    long maximum = sysconf(_SC_OPEN_MAX);
    for (int fd = 3; fd < maximum; fd++) {
        int flags = fcntl(fd, F_GETFD);
        if (flags != -1 && fcntl(fd, F_SETFD, flags | FD_CLOEXEC) == -1)
            return -1;
    }
    return 0;
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

### Source, line by line

- The three small syscall wrappers keep the argument ordering visible and return raw success or failure to the caller.
- `supported_rights` builds the ABI-1 set first, then adds rights introduced by ABI 2, 3, 5, and 9 only when both the build headers and the running kernel support them. The preprocessor guards keep the source buildable with older distribution headers.
- `close_inherited` prefers the kernel's range operation. `CLOSE_RANGE_CLOEXEC` preserves descriptors until `exec` but guarantees the new program cannot inherit them.
- The fallback queries the descriptor limit and adds `FD_CLOEXEC` only to descriptors that are actually open. Any mutation error fails the launch.
- `main` queries and prints the ABI before it creates policy. It never treats an unavailable Landlock interface as permission to continue.
- The ruleset declares which operations Landlock will handle; the path-beneath rule grants that same set only under `root_fd`.
- `PR_SET_NO_NEW_PRIVS` and `restrict_self` are joined by `||`: if either fails, `execv` is unreachable.
- The policy and root descriptors are closed before inherited descriptors are marked. Standard input, output, and error remain available.
- `execv(argv[2], &argv[2])` preserves the caller's structured argv. Returning from `execv` is always an error and is reported.

### Unhandled means allowed

Landlock restricts only the access rights listed in `handled_access_fs`. With the historical exception of `LANDLOCK_ACCESS_FS_REFER`, a filesystem right the running kernel supports but the ruleset does not handle stays allowed. A launcher that stops at ABI 3 therefore under-restricts on ABI 5, where `LANDLOCK_ACCESS_FS_IOCTL_DEV` can restrict device IOCTL operations, and on ABI 9, where `LANDLOCK_ACCESS_FS_RESOLVE_UNIX` can restrict pathname UNIX-socket resolution.

Version-aware code can handle only rights known to its source and build headers. The guarded ABI 5 and ABI 9 additions make this source enforce the complete filesystem-right set it knows when the headers expose those constants and the running kernel supports them. If newer headers introduce another filesystem right, this source and its stated guarantee must be reviewed again; runtime ABI detection cannot invent a constant absent at build time.

Checkpoint: print the ABI reported by the running kernel and compare it with the highest filesystem ABI explicitly handled by the source:

```bash
./landlock-launch demo/allowed /bin/true 2>&1 | head -1
grep -n 'abi >=' landlock_launch.c
```

- The first command relies on the launcher's diagnostic and may later deny `/bin/true` because that executable is outside the allowed tree; only its first line is the ABI observation.
- The second command lists the explicit ABI gates compiled into this source. A high runtime number is not by itself proof that every future right is handled.

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

### Source, line by line

- `open` creates authority to the protected object before Landlock is installed.
- `pass_fds` deliberately clears close-on-exec for that descriptor in the immediate child.
- The launcher receives the allowed root, exact probe path, `fd` mode, and descriptor number as distinct argv elements.
- The wrapper returns the observed child status.

The repaired launcher calls `close_inherited` after using its policy descriptors and before `execv`. `close_range(..., CLOSE_RANGE_CLOEXEC)` atomically marks every descriptor from 3 upward close-on-exec; an older-kernel fallback applies `FD_CLOEXEC` one descriptor at a time.

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
- Substitute `./unsafe-launch` for `./landlock-launch` in the wrapper command. The synthetic secret prints even though the path rule is active.
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
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-05-filesystem-landlock/lab/README.md format=markdown -->
# Module 05 independent lab - Filesystem guard

Implement `fs_guard.c`. The grader builds one executable and invokes these interfaces:

```text
fs-guard read ALLOWED_ROOT RELATIVE_PATH
fs-guard write ALLOWED_ROOT RELATIVE_PATH CONTENT
fs-guard run ALLOWED_ROOT COMMAND [ARG...]
```

Required security properties:

- `read` prints an allowed regular file and `write` creates or truncates an allowed regular file with exact content;
- both operations resolve from an opened `ALLOWED_ROOT` descriptor in one kernel operation;
- absolute paths, `..` traversal, magic links, and every symlink are denied rather than normalized and reopened;
- `run` queries the Landlock ABI, handles every filesystem right known to its source and build headers that the detected ABI supports - including device IOCTL at ABI 5 and pathname UNIX-socket resolution at ABI 9 when those constants are available - grants the child filesystem access beneath `ALLOWED_ROOT`, sets `no_new_privs`, and restricts before `exec`;
- an executable inside the allowed tree still runs, while that child cannot newly open a protected sibling;
- inherited descriptors numbered 3 and above are closed on `exec`, preventing a pre-opened protected file from bypassing the pathname policy;
- malformed or unknown modes fail closed with a nonzero status.

The external grader observes the common path, traversal, symlink, execution, protected-open, and inherited-descriptor properties. ABI 5 device IOCTL and ABI 9 pathname UNIX-socket handling are stated source properties rather than externally graded properties on the Ubuntu 24.04 baseline: observing them safely requires matching newer headers plus controlled device or socket fixtures. Review the guarded rights table and the lesson's ABI checkpoint instead of treating a baseline grader pass as evidence for unavailable kernel features.

The grader changes directory names, relative paths, contents, and synthetic canaries on every run. It compiles its observation child statically inside the allowed tree, creates a symlink to a protected sibling, passes a protected descriptor deliberately, and evaluates a read-only copy of your source.

The starter is useful but intentionally unsafe. It joins root and request as text, follows symlinks, permits traversal, launches a child without Landlock, and preserves inherited descriptors. Replace those behaviors using only the interfaces practiced in Lessons 05.01-05.03.

Build and exercise the harmless sample:

```bash
cc -std=c11 -Wall -Wextra -O2 fs_guard.c -o fs-guard
rm -rf sample-root
mkdir sample-root
printf 'sample\n' > sample-root/input.txt
./fs-guard read "$PWD/sample-root" input.txt
./fs-guard write "$PWD/sample-root" output.txt 'sample-output'
test "$(cat sample-root/output.txt)" = sample-output
../../lab-grade module-05
../../lab-grade module-05 --mode exam
```

### Test commands, line by line

- `cc` builds exactly the submitted source and enables useful warnings.
- The scoped `rm -rf` and `mkdir` create only a lab-local sample root.
- `printf` supplies non-sensitive input.
- `read` and `write` verify the functional interface before confinement is graded.
- `test` independently checks the write effect.
- Practice grading names failed properties and points back to the relevant lesson.
- Exam grading runs the same fresh bypasses but suppresses repair-oriented references.

The lab does not provide a completed implementation. Plan separate read/write and run paths, keep the root descriptor alive only as long as needed, make every setup failure stop the command, and preserve the required order: inspect ABI, create ruleset, add rule, set `no_new_privs`, restrict, close inherited authority, then `exec`.

This is an unprivileged local exercise. Do not add `sudo`, mounts, external paths, network access, or real secrets.
<!-- /source -->
