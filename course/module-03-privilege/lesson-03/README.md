# 03.03 - Make privilege non-gainable

## Goals

- Set the one-way `no_new_privs` bit before exec.
- Observe that bit in the executed child and a grandchild.
- Understand why ordering around exec is a security property.
- Distinguish non-gainability from removal of existing authority.

## Exercise 1 - Build the launcher

Complete 03.01 and 03.02 first. A program can begin with little privilege but execute a file whose attributes would normally grant more. `no_new_privs` is a one-way promise enforced by the kernel: an exec transition must not grant privilege that was unavailable before that transition. It does not remove authority the process already has. Here we will observe the bit itself, not install a setuid program to demonstrate privilege gain.

From the course root:

```bash
./lab-start 03.03
cd .student/03.03
pwd
ls -l nnp-launch.c
cat nnp-launch.c
grep '^NoNewPrivs:' /proc/self/status
```

The first four commands prepare and locate the editable C source. `cat` opens its contents for reading without editing. The final command records your inherited baseline. If it already reports 1, the deliberate ordering error later cannot make it 0: the bit is sticky. Do not weaken the VM or try to unset it to force an expected screenshot.

Complete source:

<!-- source: course/module-03-privilege/lesson-03/nnp-launch.c format=code -->
```c
#define _GNU_SOURCE
#include <stdio.h>
#include <sys/prctl.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s COMMAND [ARG ...]\n", argv[0]);
        return 2;
    }
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
        perror("prctl(PR_SET_NO_NEW_PRIVS)");
        return 1;
    }
    execvp(argv[1], &argv[1]);
    perror("execvp");
    return 1;
}
```
<!-- /source -->

## Source, line by line

- `_GNU_SOURCE` requests GNU/Linux declarations before headers are included.
- `<stdio.h>` declares diagnostics; `<sys/prctl.h>` declares `prctl` and its operation constants; `<unistd.h>` declares `execvp`.
- `argc < 2` rejects a missing child command.
- The usage message describes the preserved `COMMAND [ARG ...]` interface.
- `prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)` asks the kernel to set the calling thread's one-way bit. The remaining zero arguments are unused for this operation.
- A nonzero return indicates failure, which must stop execution of untrusted code.
- `execvp(argv[1], &argv[1])` searches `PATH`, uses the requested command, and passes the command plus all remaining arguments as the new `argv`.
- `&argv[1]` points into the original pointer array instead of rebuilding it.
- The final diagnostic runs only when exec fails.

Build and observe:

```bash
sed -n '1,220p' nnp-launch.c
cc -std=c11 -Wall -Wextra -O2 nnp-launch.c -o nnp-launch
./nnp-launch sh -c 'grep -E "^(NoNewPrivs|CapEff):" /proc/self/status'
```

## What each line does

- `sed` displays the full small launcher before execution.
- The compile line selects C11, warnings, normal optimization, and the output name.
- Every token after `./nnp-launch` becomes the child command and arguments.
- `sh -c` executes the quoted observation after the launcher sets policy.
- The anchored expression selects only `NoNewPrivs` and `CapEff`.

Expected:

```text
NoNewPrivs:  1
CapEff:      0000000000000000
```

`NoNewPrivs: 1` is the required property. A zero effective set is an additional observation, not proof that every authority channel is empty.

## Exercise 2 - Make the ordering mistake

Open `nano nnp-launch.c`. Move the **entire** `if (prctl(...) != 0) { ... }` block to immediately after the `execvp` call, keeping its failure handling together. Save with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. Run `cat nnp-launch.c` to inspect the saved order, then repeat the compile and observation commands from Exercise 1.

- A successful exec replaces the launcher, so code after it is unreachable on the success path.
- The executed child therefore observes the old `NoNewPrivs` value, normally 0.
- Restore the complete block before exec, save, recompile, and rerun. The repaired child must report 1.

Security controls governing a transition must be established before that transition. Source presence is not enough; control-flow ordering is part of the property.

## Exercise 3 - Verify inheritance in a descendant

```bash
./nnp-launch sh -c 'sh -c "grep ^NoNewPrivs: /proc/self/status"'
```

## What each part does

- The launcher sets the bit and executes the first shell.
- The outer single quotes protect the inner command from the invoking shell.
- The first child shell launches another shell.
- The inner shell reads its own procfs status.
- Seeing 1 proves inheritance across more than one exec transition.

`no_new_privs` cannot be unset and is inherited across fork and exec. It prevents privilege gain from exec mechanisms such as set-user-ID and file capabilities. It does not close descriptors, scrub the environment, empty current capability sets, isolate files, restrict the network, or filter syscalls.

## Troubleshooting and checkpoint

- If `prctl` is undeclared, verify Linux headers and `_GNU_SOURCE` placement.
- If the child reports 0, inspect control-flow ordering before changing the probe.
- If the command does not launch, distinguish `prctl` failure from `execvp` failure using stderr.
- You should be able to explain both what `no_new_privs` guarantees and what it deliberately does not guarantee.

For the checkpoint, compare the repaired child and grandchild, then name two inherited authority channels this bit does not remove. If your initial baseline was already 1, say explicitly that the negative case was masked by an inherited restriction; do not claim you observed a 0-to-1 transition.

Reset only your lesson workspace from the course root: `cd ../..` then `./lab-reset 03.03`. The child set its own bit; the parent shell was not changed.

## Source truth

The kernel's [no_new_privs documentation](https://docs.kernel.org/userspace-api/no_new_privs.html) describes inheritance, irreversibility, and limits. [execve(2)](https://man7.org/linux/man-pages/man2/execve.2.html) explains why successful execution does not return to the old program.
