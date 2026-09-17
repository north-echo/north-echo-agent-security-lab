# 03.03 - Make privilege non-gainable

Goal: set `no_new_privs` before exec and observe the sticky bit in the child.

## Exercise 1 - Build the one-way transition

```bash
sed -n '1,220p' nnp-launch.c
cc -std=c11 -Wall -Wextra -O2 nnp-launch.c -o nnp-launch
./nnp-launch sh -c 'grep -E "^(NoNewPrivs|CapEff):" /proc/self/status'
```

Expected:

```text
NoNewPrivs:  1
CapEff:      0000000000000000
```

`PR_SET_NO_NEW_PRIVS` is inherited across fork and exec and cannot be unset. It promises that exec will not grant privileges the process did not already have.

## Exercise 2 - Make the ordering mistake

Temporarily move the `prctl(PR_SET_NO_NEW_PRIVS, ...)` call after `execvp`. Rebuild.

Expected compiler behavior: code after a successful `execvp` is never reached; the child reports `NoNewPrivs: 0`. Restore the call before exec. Security controls that govern the transition must be established before the transition.

## Exercise 3 - Verify the descendant

```bash
./nnp-launch sh -c 'sh -c "grep ^NoNewPrivs: /proc/self/status"'
```

Expected: the grandchild also reports `1`.

Limit: `no_new_privs` does not remove current authority. It does not close descriptors, erase environment data, empty capabilities, isolate filesystems, or filter syscalls. It is one composable control.
