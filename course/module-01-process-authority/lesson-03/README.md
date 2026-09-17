# 01.03 - File descriptors cross exec

Goal: prove that a pathname restriction applied later cannot revoke an object already opened by the parent.

## Exercise 1 - Observe descriptor authority

Build and run the intentionally vulnerable launcher. Use the randomized protected fixture created for this attempt:

```bash
cc -std=c11 -Wall -Wextra -O2 fd-parent.c -o fd-parent
./fd-parent "$(python3 -c 'import json; print(json.load(open(".north-echo.json"))["fixture_manifest"])')"
```

Expected pattern: the child lists descriptors under `/proc/self/fd`; one descriptor points to `manifest.json`, and the child can read it without opening its pathname.

Inspect the source:

```bash
sed -n '1,220p' fd-parent.c
```

The intentional mistake is `open(..., O_RDONLY)` followed by `execvp` with no close and no close-on-exec flag.

## Exercise 2 - Fix at creation time

Change the open flags to:

```c
O_RDONLY | O_CLOEXEC
```

Rebuild and run the same command. Expected: the protected descriptor is absent after `execve`; the child may still have descriptors 0, 1, and 2.

## Exercise 3 - Verify the flag before exec

Add this immediately after `open` and before `execvp`:

```c
int flags = fcntl(fd, F_GETFD);
fprintf(stderr, "FD_CLOEXEC=%s\n", (flags & FD_CLOEXEC) ? "yes" : "no");
```

Rebuild. Expected: `FD_CLOEXEC=yes`, followed by no protected manifest in the child. `FD_CLOEXEC` affects the exec transition; it does not prevent the current process from using the descriptor.

Security conclusion: descriptors are capabilities to already-open kernel objects. Path checks and later filesystem policy do not retroactively erase them.
