# 01.03 - File descriptors cross exec

## Outcomes and prerequisites

Observe an open descriptor surviving exec, prevent that inheritance, and
practice closing unknown extra descriptors. You need 01.01's C compile cycle
and 01.02's understanding that exec receives inherited state.

## Understand first

A pathname is a name to resolve. A descriptor is a small integer referring
to an already-open object. By convention, 0 is stdin, 1 is stdout, and 2 is
stderr. Other numbers are allocated as needed; descriptor 3 is common, not
a universal identifier for a protected file.

Opening performs pathname lookup and access checks. Later reads use the open
object without repeating that original lookup. A launcher can therefore hand
another program a reference that checking only future pathnames would miss.
We observe this channel using synthetic data, not an actual secret store.

## Prepare and read before executing

From the VM repository root:

```bash
./lab-start 01.03
cd .student/01.03
pwd
ls -l fd-parent.c fd-child.py close-extra.c .north-echo.json
cat fd-parent.c
cat fd-child.py
```

Confirm `.student/01.03`. The metadata file names this attempt's synthetic
fixture. The parent opens it; the observer tries existing descriptors.
Reading the files is not running them.

<!-- source: course/module-01-process-authority/lesson-03/fd-parent.c format=code -->
```c
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: %s PATH\n", argv[0]);
        return 2;
    }
    int fd = open(argv[1], O_RDONLY); /* Intentional mistake: no O_CLOEXEC. */
    if (fd < 0) {
        perror("open");
        return 1;
    }
    char *child[] = {"python3", "fd-child.py", NULL};
    execvp(child[0], child);
    perror("execvp");
    return 1;
}
```
<!-- /source -->

`open` returns a descriptor or -1 on failure. The argument check requires one
pathname. `char *child[]` is an array of string pointers ending in NULL, as in
01.02. `execvp` searches PATH and replaces the program. Follow the error branch
first: a failed open must not be treated as an open reference.

<!-- source: course/module-01-process-authority/lesson-03/fd-child.py format=code -->
```python
#!/usr/bin/env python3
import os

for fd in range(0, 32):
    try:
        target = os.readlink(f"/proc/self/fd/{fd}")
    except OSError:
        continue
    print(f"fd={fd} target={target}")
    if fd >= 3:
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            print(os.read(fd, 4096).decode(errors="replace"))
        except OSError:
            pass
```
<!-- /source -->

The observer tests descriptor numbers 0-31. `readlink` asks procfs what each
reference names; `continue` skips unopened numbers. For numbers above 2,
`lseek` attempts to rewind a seekable object and `read` requests up to 4096
bytes. Ignoring errors for non-seekable or unreadable objects does not prove
they are harmless. This bounded observer is not a complete inventory algorithm.

## Exercise 1 - Observe descriptor authority

Build and run the intentionally vulnerable launcher. Use the randomized protected fixture created for this attempt:

```bash
cc -std=c11 -Wall -Wextra -O2 fd-parent.c -o fd-parent
./fd-parent "$(python3 -c 'import json; print(json.load(open(".north-echo.json"))["fixture_manifest"])')"
```

### Line by line

- `cc ... fd-parent.c -o fd-parent` compiles the launcher with warnings enabled and writes the binary named `fd-parent`.
- `python3 -c '...'` executes the quoted Python expression without creating another file.
- `open(".north-echo.json")` opens non-secret workspace metadata; `json.load(...)` parses it; `["fixture_manifest"]` selects the generated manifest path; `print(...)` writes that path.
- `$(...)` substitutes the printed path into the outer command.
- The double quotes around `$(...)` keep the entire pathname as one argument even if a directory name contains spaces.

Expected pattern: the child lists descriptors under `/proc/self/fd`; one descriptor points to `manifest.json`, and the child can read it without opening its pathname.

Inspect the source:

```bash
sed -n '1,220p' fd-parent.c
```

### Line by line

- `sed -n` suppresses automatic printing.
- `'1,220p'` prints source lines 1 through 220, which covers this intentionally small program.
- Reading before running is part of the exercise: identify the `open` and `execvp` authority-transfer points.

The intentional mistake is `open(..., O_RDONLY)` followed by `execvp` with no close and no close-on-exec flag.

### Parent source, line by line

- `#define _GNU_SOURCE` exposes GNU/Linux extensions such as `O_CLOEXEC` from the included headers.
- The four `#include` lines declare file flags, diagnostics, general utilities, and POSIX process functions.
- `argc` counts arguments and `argv` holds them; requiring `argc == 2` ensures exactly one pathname was supplied.
- `open(argv[1], O_RDONLY)` asks the kernel to resolve and open that pathname. The returned integer is process-local descriptor authority.
- `if (fd < 0)` handles failure before attempting an exec transition.
- `char *child[] = {..., NULL}` builds the NUL-terminated argument vector required by `execvp`.
- `execvp(child[0], child)` searches `PATH` for Python and replaces the current process image while retaining non-close-on-exec descriptors.
- Code after a successful `execvp` never runs; `perror` and `return 1` handle only failure.

### Child source, line by line

- `for fd in range(0, 32)` tests a bounded set of possible descriptor numbers.
- `os.readlink(f"/proc/self/fd/{fd}")` asks procfs what object a descriptor references; an `OSError` means that number is not open or not inspectable.
- The first `print` reports descriptor number and target.
- For descriptors 3 and above, `os.lseek` rewinds seekable objects and `os.read` attempts to consume bytes without reopening a pathname.
- The second `except OSError` deliberately tolerates descriptors that cannot seek or read. It does not prove those descriptors lack other authority.

## Exercise 2 - Fix at creation time

Open `nano fd-parent.c` in the workspace. Change the open flags to:

```c
O_RDONLY | O_CLOEXEC
```

### Line by line

- `O_RDONLY` requests a read-only descriptor.
- `|` is C's bitwise OR operator; it combines independent flag bits in one integer.
- `O_CLOEXEC` asks the kernel to set close-on-exec atomically when the descriptor is created, avoiding a window between `open` and a later `fcntl`.

Save with Ctrl+O, Enter, then Ctrl+X. Check with `cat fd-parent.c`, rebuild
with the same compiler command, and repeat the fixture invocation. Stop on
compiler errors. Expected: the manifest descriptor is absent after exec;
descriptors 0, 1, and 2 may remain. This flag does not prevent the parent
from using the descriptor before that exec transition.

## Exercise 3 - Verify the flag before exec

Add this immediately after `open` and before `execvp`:

```c
int flags = fcntl(fd, F_GETFD);
if (flags < 0) {
    perror("fcntl(F_GETFD)");
    return 1;
}
fprintf(stderr, "FD_CLOEXEC=%s\n", (flags & FD_CLOEXEC) ? "yes" : "no");
```

### Line by line

- `fcntl(fd, F_GETFD)` reads descriptor flags; the error branch stops before treating failure as a valid mask.
- `flags & FD_CLOEXEC` uses bitwise AND to test whether that specific bit is present.
- `condition ? "yes" : "no"` is C's conditional operator.
- `fprintf(stderr, ...)` sends the diagnostic to standard error, and `\n` terminates the line.

Rebuild. Expected: `FD_CLOEXEC=yes`, followed by no protected manifest in the child. `FD_CLOEXEC` affects the exec transition; it does not prevent the current process from using the descriptor.

Security conclusion: descriptors are capabilities to already-open kernel objects. Path checks and later filesystem policy do not retroactively erase them.

## Exercise 4 - Close descriptors already inherited

`O_CLOEXEC` helps when you control descriptor creation. A general launcher can
already have extra descriptors at startup. Closing only the number seen in
one run does not solve that case. Read the supplied bridge program:

```bash
ls -l close-extra.c
cat close-extra.c
```

<!-- source: course/module-01-process-authority/lesson-03/close-extra.c format=code -->
```c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>

int main(void) {
    int descriptor = open("/dev/null", O_RDONLY);
    if (descriptor < 0) {
        perror("open");
        return 1;
    }
    printf("Opened descriptor: %d\n", descriptor);
    if (close_range(3, ~0U, 0) != 0) {
        perror("close_range");
        return 1;
    }
    errno = 0;
    int flags = fcntl(descriptor, F_GETFD);
    if (flags != -1 || errno != EBADF) {
        fprintf(stderr, "Expected the descriptor to be closed\n");
        return 1;
    }
    puts("Extra descriptor closed; stdout still works.");
    return 0;
}
```
<!-- /source -->

### Source, line by line

`_GNU_SOURCE` exposes the installed libc's `close_range` declaration. The
headers declare errors, descriptor operations, diagnostics, and range closure.
The program opens only `/dev/null`, a harmless local device whose reads return
end-of-file, and stops if that open fails.

`close_range(3, ~0U, 0)` closes from descriptor 3 through the maximum unsigned
value. `U` makes zero unsigned; bitwise complement `~` sets all its bits. The
final zero requests immediate closure, not close-on-exec marking. Standard
streams 0-2 remain, and no specific extra descriptor number is assumed.

`errno = 0` clears the error indicator before the observation. `F_GETFD` should
then fail with `EBADF`, meaning that descriptor is not open. Checking both the
return and reason avoids treating any error as the expected one. The final
`puts` proves stdout still works.

```bash
cc -std=c11 -Wall -Wextra -O2 close-extra.c -o close-extra
./close-extra
echo $?
```

Expect an opened descriptor above 2, the closure confirmation, and status 0.
Using nano, temporarily remove only the `close_range` error-check block from
the workspace copy. Save, rebuild, and run: verification should now fail
because the descriptor remains open. Restore the block and confirm success.
Do not change the expected-error test to make an incomplete control pass.

The bridge closes descriptors but launches no arbitrary command and does not
alter the environment. The independent lab combines separate practiced skills.

## Checkpoint, troubleshooting, and reset

Explain preventing inheritance of a newly opened descriptor versus closing
extra descriptors already inherited. Why is a literal `close(3)` insufficient?

- Missing manifest: use this attempt's metadata, not a remembered old path.
- No initial leak: inspect flags and whether a resumed workspace was already
  repaired. Reset only if discarding those edits is intended.
- Different number: identify the target object, not just descriptor 3.
- `close_range` unavailable: check the supported VM kernel/libc; do not ignore
  the error and continue to launch a less-confined workload.

Return to the repository root for `./lab-reset 01.03 --dry-run`, then
`./lab-reset 01.03 --yes` when ready to discard the lesson's edits.

## Sources and scope

[open](https://man7.org/linux/man-pages/man2/open.2.html),
[execve](https://man7.org/linux/man-pages/man2/execve.2.html), and
[close_range](https://man7.org/linux/man-pages/man2/close_range.2.html) describe
creation, inheritance, and range closure. Range closure requires Linux 5.9+
and this wrapper requires glibc 2.34+; the Fedora/Ubuntu baselines supply them.
Removing a reference does not prove every other authority channel is closed
or prevent reopening a pathname the process can still access.
