# Module 01 independent lab - Hygienic launcher

Build a small launcher for an untrusted local tool. This is independent work: the exact implementation is intentionally not provided.

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
