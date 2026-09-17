# Module 03 independent lab - Privilege floor

Implement `secure-launch.c`, a launcher that establishes a non-gainable, capability-empty privilege state before executing an arbitrary command.

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
