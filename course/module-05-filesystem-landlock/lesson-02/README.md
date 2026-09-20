# 05.02 - Make lookup descriptor-relative with `openat2`

## Goal

Replace check-then-open pathname logic with one kernel operation anchored to an already-open directory. Require resolution to remain beneath that descriptor and reject symlinks.

## Concepts and preparation

Complete 05.01 and recall descriptor authority from 01.03. The previous checker resolved a path, decided it was acceptable, and later opened it. Those are separate operations. Here the broker gives the kernel both the root descriptor and resolution constraints in the **same open request**. There is no separate approved pathname to reopen.

`openat2` is a Linux syscall, not a shell command. A C structure carries its options. Fields omitted from the designated initializer are zero-initialized; that matters because the kernel expects unused fields to be zero. This policy constrains lookup, not future edits to the contents of an allowed file, and not arbitrary opens made elsewhere in the process.

From the course root in the disposable VM:

```bash
./lab-start 05.02
cd .student/05.02
pwd
ls -l safe_open.c
cat safe_open.c
```

`lab-start` prepares the student copy. The next commands enter and inspect it; each `cat` reads a supplied source before execution. Missing files usually mean the wrong working directory or lesson number. Edit only these student copies with `nano FILENAME`, save with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. Recompile after every C edit. An old binary does not automatically track a changed source.

## Exercise 1 - Compile the brokered open

Complete source of `safe_open.c`:

<!-- source: course/module-05-filesystem-landlock/lesson-02/safe_open.c format=code -->
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
<!-- /source -->

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

The leading `&` passes a structure's address; `sizeof(how)` tells the kernel how many bytes of that structure are supplied. The `|` operators combine independent flag bits. `ssize_t` can represent a byte count or the negative error value; `size_t` is an unsigned size, so the code casts only after a positive read. The assignment in the `while` condition stores the count before testing it. This teaching copy loop fails on a short write rather than retrying it; it is not a complete general-purpose I/O library.

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

## Exercise 4 - Practice a descriptor-relative write

The independent lab needs both reads and writes. Practice the creation flags in a smaller fixed-content program, not a combined lab solution:

```bash
ls -l safe_write.c
cat safe_write.c
```

`ls` confirms the source in this workspace; `cat` displays it before compiling.

<!-- source: course/module-05-filesystem-landlock/lesson-02/safe_write.c format=code -->
```c
#define _GNU_SOURCE
#include <fcntl.h>
#include <linux/openat2.h>
#include <stdio.h>
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
        .flags = O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC,
        .mode = 0600,
        .resolve = RESOLVE_BENEATH | RESOLVE_NO_MAGICLINKS | RESOLVE_NO_SYMLINKS,
    };
    int fd = syscall(SYS_openat2, root_fd, argv[2], &how, sizeof(how));
    if (fd == -1) {
        perror("openat2");
        close(root_fd);
        return 1;
    }
    close(root_fd);
    const char content[] = "created through an anchored descriptor\n";
    int failed = write(fd, content, sizeof(content) - 1) != (ssize_t)(sizeof(content) - 1);
    if (failed)
        fprintf(stderr, "write did not complete\n");
    if (close(fd) == -1) {
        perror("close output");
        failed = 1;
    }
    return failed;
}
```
<!-- /source -->

### Source, line by line

- The headers and argument guard serve the same roles as in `safe_open.c`.
- The root is opened as a directory reference and marked close-on-exec. An error stops the operation.
- `O_WRONLY` requests writing; `O_CREAT` permits a new file; `O_TRUNC` replaces existing contents. These are different choices from append mode.
- `mode = 0600` requests owner read/write permissions for a newly created file, further restricted by the process umask. The leading zero denotes an octal permission constant. `mode` must be zero when no creation flag is used.
- The same resolution flags apply to creation, so a write does not get a weaker lookup rule than a read.
- The fixed payload includes a newline. `sizeof(content) - 1` excludes the C string's terminating zero byte.
- A short or failed write is reported as failure. The output descriptor is closed, and a close error also fails the operation; this still does not promise durable storage without an explicit synchronization policy.
- All successful setup paths close the root descriptor. Returning nonzero stops the caller from treating a failed write as a valid result.

```bash
cc -std=c11 -Wall -Wextra -Werror -O2 safe_write.c -o safe-write
./safe-write demo/allowed created.txt
cat demo/allowed/created.txt
printf 'old contents deliberately longer than the replacement payload to expose missing truncation\n' > demo/allowed/created.txt
./safe-write demo/allowed created.txt
test "$(cat demo/allowed/created.txt)" = 'created through an anchored descriptor'
```

The compile command builds the new program. The first write creates a file and the following `cat` observes it. The second run replaces longer old content; the final equality check catches a missing truncation flag that would leave trailing bytes. The payload and destination are local synthetic data. In the independent lab, adapt the mechanism to the specified content argument yourself.

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

## Replay and source truth

The demo contains only lesson-created synthetic files. Do not substitute personal directories or real credentials. From this workspace, `cd ../..` then `./lab-reset 05.02` discards this lesson's edits and fixtures after confirmation. No host mount, filesystem permission, or global security setting needs changing.

[openat2(2)](https://man7.org/linux/man-pages/man2/openat2.2.html) defines the structure, resolution flags, and error cases; it was introduced in Linux 5.6. The lesson uses flags available on both course baselines, not newer flags merely present in current online documentation.
