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

<!-- source: course/module-06-seccomp/lesson-01/workload.c format=code -->
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
<!-- /source -->

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
