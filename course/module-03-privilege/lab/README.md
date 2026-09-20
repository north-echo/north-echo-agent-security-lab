# Module 03 independent lab - Privilege floor

Implement `secure-launch.c`, a launcher that establishes a non-gainable, capability-empty privilege state before executing an arbitrary command.

## Preparation and planning

Complete 03.01-03.03 first. Map the contract to the earlier practice: read identity and all sets in 03.01, clear current sets in C in 03.02, and establish the pre-exec one-way bit in 03.03. The lab combines those pieces without giving you their final arrangement.

The ordinary-user grader typically begins with empty current capability sets. A pass on that input alone is not evidence that a missing clearing operation would handle a more privileged input. Use the namespace-local contrast practiced in 03.02 to understand that limitation; do not change the lab to run as VM root. The contract preserves the invoking account and does not require an empty bounding set or altered supplementary groups.

From the course root:

```bash
./lab-start module-03
cd .student/03.lab
pwd
ls -l secure-launch.c
cat secure-launch.c
nano secure-launch.c
```

`lab-start` creates your editable lab copy. The next three commands enter it and confirm the source name; `cat` reads it, and `nano` opens it for editing. Save with `Ctrl-O`, `Enter`, then leave with `Ctrl-X`. Work only in this student copy. The canonical starter is deliberately incomplete:

<!-- source: course/module-03-privilege/lab/secure-launch.c format=code -->
```c
#define _GNU_SOURCE
#include <stdio.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s COMMAND [ARG ...]\n", argv[0]);
        return 2;
    }

    /* Intentional starter flaw: no privilege floor is established. */
    execvp(argv[1], &argv[1]);
    perror("execvp");
    return 1;
}
```
<!-- /source -->

The feature-test macro appears before headers. `stdio.h` supplies diagnostics; `unistd.h` supplies `execvp`. `argc` counts arguments, including the launcher name. The usage block rejects a missing child command. `argv[1]` names that command, while `&argv[1]` forwards its complete argument vector. Successful `execvp` never returns; `perror` and the final nonzero return handle failure. The starter preserves this interface but omits the stated security controls.

## Contract

The grader compiles the file with C11 and invokes:

```text
./secure-launch COMMAND [ARG ...]
```

The executed command must observe:

- `NoNewPrivs: 1`;
- empty effective, permitted, inheritable, and ambient capability sets;
- the same real and effective UID as the ordinary user who invoked the launcher;
- normal command arguments, stdout/stderr, and exit behavior.

The lab must be run as an ordinary user in the disposable VM. Do not add setuid bits or file capabilities. Do not call an external shell to transform the command string.

All required interfaces were practiced in this module. The grader deliberately avoids line-level advice.

```bash
cc -std=c11 -Wall -Wextra -O2 secure-launch.c -o secure-launch
./secure-launch sh -c 'grep -E "^(Uid|CapInh|CapPrm|CapEff|CapAmb|NoNewPrivs):" /proc/self/status'
../../lab-grade module-03
```

### Test commands, line by line

- `cc` builds your C11 launcher with warnings and normal optimization.
- `./secure-launch sh -c 'grep ...'` uses the required arbitrary-command interface and observes the executed child's real state from procfs.
- The anchored regular expression selects only identity, capability, and no-new-privileges fields.
- `../../lab-grade module-03` compiles a fresh evaluation binary and runs a separate probe.
- The starter's `execvp(argv[1], &argv[1])` correctly forwards the command and arguments but intentionally establishes no privilege floor. The exact repair remains independent work.

## Interpret your result and replay

Run the starter once before editing and record which security properties fail. A compile error is not an observed security denial, and a missing child is not successful containment. After your repair, use both a harmless successful command and a deliberately nonexistent absolute command; the latter must produce a nonzero launcher status.

For the practice grader, read each failed property and revisit its lesson before changing code. Do not alter the grader, canonical files, or generated fixture to force a pass. Passing establishes only the tested contract, not a production-ready sandbox.

From this workspace, `cd ../..` returns to the course root. `./lab-reset module-03` discards this module's student work and generated fixtures after confirmation; copy any notes you want to retain first. Then `./lab-start module-03` creates a fresh randomized attempt. No saved implementation is supplied by this manual.
