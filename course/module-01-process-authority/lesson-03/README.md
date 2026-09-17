# 01.03 - File descriptors cross exec

Goal: prove that a pathname restriction applied later cannot revoke an object already opened by the parent.

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

Change the open flags to:

```c
O_RDONLY | O_CLOEXEC
```

### Line by line

- `O_RDONLY` requests a read-only descriptor.
- `|` is C's bitwise OR operator; it combines independent flag bits in one integer.
- `O_CLOEXEC` asks the kernel to set close-on-exec atomically when the descriptor is created, avoiding a window between `open` and a later `fcntl`.

Rebuild and run the same command. Expected: the protected descriptor is absent after `execve`; the child may still have descriptors 0, 1, and 2.

## Exercise 3 - Verify the flag before exec

Add this immediately after `open` and before `execvp`:

```c
int flags = fcntl(fd, F_GETFD);
fprintf(stderr, "FD_CLOEXEC=%s\n", (flags & FD_CLOEXEC) ? "yes" : "no");
```

### Line by line

- `fcntl(fd, F_GETFD)` reads descriptor flags for `fd`; a negative result would indicate an error.
- `flags & FD_CLOEXEC` uses bitwise AND to test whether that specific bit is present.
- `condition ? "yes" : "no"` is C's conditional operator.
- `fprintf(stderr, ...)` sends the diagnostic to standard error, and `\n` terminates the line.

Rebuild. Expected: `FD_CLOEXEC=yes`, followed by no protected manifest in the child. `FD_CLOEXEC` affects the exec transition; it does not prevent the current process from using the descriptor.

Security conclusion: descriptors are capabilities to already-open kernel objects. Path checks and later filesystem policy do not retroactively erase them.
