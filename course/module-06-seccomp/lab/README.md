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

<!-- source: course/module-06-seccomp/lab/seccomp_guard.c format=code -->
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
<!-- /source -->

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
