# Module 05 independent lab - Filesystem guard

## Preparation and practiced skills

Complete 05.01-05.03 first. Map read lookup and creation/truncation to 05.02's two small C programs; map child restriction and inherited-descriptor handling to 05.03. 05.01 explains why replacing a character-prefix test with another string manipulation is not the whole answer.

The starter branches on `argv[1]`. Its `run` branch executes without policy. Its other branches concatenate root and request into a string, then use ordinary stream operations. `fread` and `fwrite` operate on streams; `snprintf` formats text and does not validate a resolved object. The starter's single read also has a fixed buffer limit. Preserve the interface, not these shortcuts.

The contract describes mechanisms as well as outcomes. A black-box pass cannot prove that a read used one descriptor-relative kernel operation, or that every future ABI right was handled. Review the source against that stated design as well as checking the grader's observed outcomes.

From the course root:

```bash
./lab-start module-05
cd .student/05.lab
pwd
ls -l fs_guard.c
cat fs_guard.c
nano fs_guard.c
```

The commands prepare your editable lab, enter and inspect it, then open the starter for reading and editing. Save in nano with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. Rebuild after each C edit using the compiler command below. Keep the canonical files and grader unchanged.

<!-- source: course/module-05-filesystem-landlock/lab/fs_guard.c format=code -->
```c
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 4) {
        fprintf(stderr, "usage: %s read ROOT PATH | write ROOT PATH CONTENT | run ROOT COMMAND [ARG...]\n", argv[0]);
        return 2;
    }
    if (strcmp(argv[1], "run") == 0) {
        execv(argv[3], &argv[3]);
        perror("execv");
        return 1;
    }
    char path[4096];
    snprintf(path, sizeof(path), "%s/%s", argv[2], argv[3]);
    if (strcmp(argv[1], "read") == 0) {
        FILE *stream = fopen(path, "r");
        if (!stream) {
            perror("fopen");
            return 1;
        }
        char buffer[4096];
        size_t count = fread(buffer, 1, sizeof(buffer), stream);
        fwrite(buffer, 1, count, stdout);
        return ferror(stream) != 0;
    }
    if (strcmp(argv[1], "write") == 0 && argc == 5) {
        FILE *stream = fopen(path, "w");
        if (!stream) {
            perror("fopen");
            return 1;
        }
        fputs(argv[4], stream);
        return fclose(stream) == EOF;
    }
    fprintf(stderr, "unknown mode\n");
    return 2;
}
```
<!-- /source -->

## Contract


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

The external grader observes the common path, traversal, symlink, execution, protected-open, and inherited-descriptor properties. ABI 5 device IOCTL and ABI 9 pathname UNIX-socket handling are stated source properties rather than externally graded properties: observing them requires matching runtime support plus controlled device or socket fixtures. The Fedora trial reports runtime ABI 7, so ABI 9 enforcement is not demonstrated there even when newer headers define the constant. Review the guarded rights table and the lesson's ABI checkpoint instead of treating a grader pass as evidence for untested kernel features.

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

## Verify, explain, and replay

Run the starter and record its failed properties before editing. After repair, preserve both successful useful work and the expected denials/errors; a launcher that refuses everything does not pass. A compiler failure, missing executable, or missing fixture is not the desired security outcome.

For each passing property, explain which earlier lesson supplied the mechanism and what the observation does **not** establish. Keep an unresolved property unresolved rather than weakening its expected result. The lab intentionally withholds a combined implementation.

From this workspace, `cd ../..` returns to the course root. `./lab-reset module-05` removes this module's student work and generated fixtures after confirmation; preserve notes first. Start the module again for a fresh randomized attempt. Never substitute real credentials, personal directories, or external services for the synthetic fixtures.
