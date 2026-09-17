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

Run the final command from the repository root instead if your shell is not in this workspace:

```bash
./lab-grade module-01
```

Practice mode names failed properties and points back to practiced lessons. Exam mode reports only failed properties:

```bash
./lab-grade module-01 --mode exam
```
