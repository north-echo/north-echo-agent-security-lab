# Module 01 independent lab - Hygienic launcher

Build a small launcher for an untrusted local tool. This is independent work: the exact implementation is intentionally not provided.

## Preparation and planning

Before attempting this lab, complete 01.01-01.03. Use 01.02's explicit C environment array and 01.03's descriptor-closure exercise as mechanisms, not as a ready-made combined launcher. You are deciding how to preserve the command interface while removing unintended inputs.

A denylist for only one known variable meets a narrower goal than an environment allowlist. The randomized grader checks its synthetic token; it does not prove your policy removes every possible sensitive variable. State the policy you actually implemented. Likewise, checking only descriptor 3 is not closing all unknown descriptors above 2.

From the course root:

```bash
./lab-start module-01
cd .student/01.lab
pwd
ls -l launcher.c
cat launcher.c
nano launcher.c
```

`lab-start` creates your editable lab copy. The next three commands enter it and confirm the source name; `cat` reads it, and `nano` opens it for editing. Save with `Ctrl-O`, `Enter`, then leave with `Ctrl-X`. Work only in this student copy. The canonical starter is deliberately incomplete:

<!-- source: course/module-01-process-authority/lab/launcher.c format=code -->
```c
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s COMMAND [ARG ...]\n", argv[0]);
        return 2;
    }

    /* Intentional starter flaw: authority is transferred without hygiene. */
    execvp(argv[1], &argv[1]);
    perror("execvp");
    return 1;
}
```
<!-- /source -->

The feature-test macro appears before headers. `stdio.h` supplies diagnostics; `unistd.h` supplies `execvp`. `argc` counts arguments, including the launcher name. The usage block rejects a missing child command. `argv[1]` names that command, while `&argv[1]` forwards its complete argument vector. Successful `execvp` never returns; `perror` and the final nonzero return handle failure. The starter preserves this interface but omits the stated security controls.

## Contract

Edit `launcher.c`. The grader will compile it with a C11 compiler, then invoke it as:

```text
./launcher COMMAND [ARG ...]
```

Your launcher must:

- execute the requested command and preserve its normal stdout/stderr;
- ensure the synthetic variable `NE_LAB_TOKEN` is absent in the executed program;
- ensure every inherited descriptor above 2 is closed before the executed program begins;
- return a nonzero status when it cannot launch the command;
- avoid printing environment values or protected data itself.

The grader changes the token, pathname, and inherited descriptor on every run. Hard-coded values cannot pass the security properties.

## Workflow

```bash
cc -std=c11 -Wall -Wextra -O2 launcher.c -o launcher
./launcher /usr/bin/printf 'child works\n'
../../lab-grade module-01
```

### Test commands, line by line

- `cc` compiles only your current `launcher.c`; the warning flags help catch interface mistakes before grading.
- `./launcher /usr/bin/printf ...` checks the required `COMMAND [ARG ...]` interface with an absolute, harmless command.
- `../../lab-grade module-01` moves no files: the relative path simply reaches the repository's grader from `.student/01.lab`.
- The starter's `execvp(argv[1], &argv[1])` preserves argument boundaries and demonstrates basic execution, but intentionally performs no authority hygiene. The guided lessons contain the required concepts; this lab does not state their complete implementation.

Run the final command from the repository root instead if your shell is not in this workspace:

```bash
./lab-grade module-01
```

Practice mode names failed properties and points back to practiced lessons. Exam mode reports only failed properties:

```bash
./lab-grade module-01 --mode exam
```

- `--mode exam` changes diagnostic detail only. It does not weaken or replace any property check.

## Interpret your result and replay

Run the starter once before editing and record which security properties fail. A compile error is not an observed security denial, and a missing child is not successful containment. After your repair, use both a harmless successful command and a deliberately nonexistent absolute command; the latter must produce a nonzero launcher status.

For the practice grader, read each failed property and revisit its lesson before changing code. Do not alter the grader, canonical files, or generated fixture to force a pass. Passing establishes only the tested contract, not a production-ready sandbox.

From this workspace, `cd ../..` returns to the course root. `./lab-reset module-01` discards this module's student work and generated fixtures after confirmation; copy any notes you want to retain first. Then `./lab-start module-01` creates a fresh randomized attempt. No saved implementation is supplied by this manual.
