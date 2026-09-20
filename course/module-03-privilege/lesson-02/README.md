# 03.02 - Drop capability sets deliberately

## Goals

- Decode all five capability sets rather than reading only `CapEff`.
- Use `setpriv` to establish a capability-empty child.
- Observe why clearing only one set is an incomplete fix.
- Verify the resulting process rather than trusting requested flags.

## Exercise 1 - Decode every set

Complete 03.01 first. "Drop privilege" is a desired outcome, not an operation with one universal meaning. In this lesson you will remove capability channels, then inspect what the child actually received. This does not remove your ordinary account's access to its own files.

From the course root:

```bash
./lab-start 03.02
cd .student/03.02
pwd
ls -l
```

The commands prepare and locate your editable workspace. Start with the shell observations; a small C bridge later connects these observations to the independent launcher lab.

```bash
for field in CapInh CapPrm CapEff CapBnd CapAmb; do
  value=$(awk -v key="$field:" '$1==key{print $2}' /proc/self/status)
  printf '%-7s %s -> ' "$field" "$value"
  capsh --decode="$value"
done
```

## What each line does

- The loop assigns each procfs field name to `field`.
- `awk -v key="$field:"` passes the current field plus its colon into `awk`.
- `$1==key` performs exact first-field equality; `{print $2}` emits the mask.
- Command substitution stores the mask in `value`.
- `printf` aligns the name, prints the raw mask, and deliberately omits a newline.
- `capsh --decode` prints capability names and completes the record.
- `done` closes the loop.

Do not collapse the five results into one adjective. Ask which set controls present checks and which sets constrain or enable future exec transitions.

## Exercise 2 - Launch with empty sets

```bash
unshare --user --map-root-user setpriv \
  --bounding-set=-all \
  --inh-caps=-all \
  --ambient-caps=-all \
  sh -c 'grep -E "^(Groups|Cap(Inh|Prm|Eff|Bnd|Amb)):" /proc/self/status'
```

## What each line does

- The mapped user namespace supplies a safe environment for practicing privilege transitions.
- A trailing backslash tells the shell the same command continues on the next physical line.
- `setpriv` changes process privilege attributes before executing the final command.
- `--bounding-set=-all` subtracts every named capability from the bounding set.
- `--inh-caps=-all` clears the inheritable set.
- `--ambient-caps=-all` clears the ambient set.
- The final shell runs the procfs observation after the transitions and reports supplementary groups separately from capability state.

Expected:

```text
CapInh: 0000000000000000
CapPrm: 0000000000000000
CapEff: 0000000000000000
CapBnd: 0000000000000000
CapAmb: 0000000000000000
```

`setpriv` and the kernel perform linked capability calculations during execution, which is why the resulting permitted and effective sets are also observed rather than assumed.

The `Groups` line need not be empty. For the unprivileged single-ID mapping used here, `setgroups(2)` must be disabled before the GID map can be written. Adding `setpriv --clear-groups` after that transition therefore fails with `Operation not permitted` on the course baselines. Group reduction is a separate launcher responsibility that must happen at a boundary where the caller has authority to change its supplementary groups; this exercise isolates capability-set behavior instead of pretending the two controls are interchangeable.

## Exercise 3 - Make the partial fix

```bash
unshare --user --map-root-user setpriv --inh-caps=-all sh -c 'grep -E "^Cap(Inh|Prm|Eff|Bnd|Amb):" /proc/self/status'
```

- This changes only the inheritable set request.
- The final `grep` deliberately prints all sets.
- Expected: `CapInh` is zero, while other sets need not be empty.

The phrase “drop capabilities” is underspecified. Name every relevant set, state the intended postcondition, and verify the kernel-reported result.

## Exercise 4 - Clear current sets in C

The shell utility is useful for experiments, but the independent lab asks for a C launcher. Read this smaller fixed-purpose program before adapting the mechanism. It clears current capability sets and reports them; it does not implement the lab's arbitrary-command interface or `no_new_privs` control.

```bash
ls -l clear-current.c
cat clear-current.c
```

The first command confirms the file exists in `.student/03.02`; the second displays its complete contents. Open it with `nano clear-current.c` if you want to annotate your student copy.

<!-- source: course/module-03-privilege/lesson-02/clear-current.c format=code -->
```c
#define _GNU_SOURCE
#include <linux/capability.h>
#include <stdio.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(void) {
    struct __user_cap_header_struct header = {
        .version = _LINUX_CAPABILITY_VERSION_3,
        .pid = 0
    };
    struct __user_cap_data_struct data[2] = {0};

    if (prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_CLEAR_ALL, 0, 0, 0) != 0) {
        perror("clear ambient capabilities");
        return 1;
    }
    if (syscall(SYS_capset, &header, data) != 0) {
        perror("capset");
        return 1;
    }
    if (syscall(SYS_capget, &header, data) != 0) {
        perror("capget");
        return 1;
    }
    printf("effective=%08x%08x\n", data[1].effective, data[0].effective);
    printf("permitted=%08x%08x\n", data[1].permitted, data[0].permitted);
    printf("inheritable=%08x%08x\n", data[1].inheritable, data[0].inheritable);
    return 0;
}
```
<!-- /source -->

### Read the program

- `_GNU_SOURCE` and the headers expose Linux's syscall numbers, capability structures, `prctl`, and diagnostics. This is Linux-specific C, not a portable POSIX capability API.
- The header's `version` selects the kernel's version-3 capability layout; `pid = 0` means the calling thread. The two data elements each represent 32 bits, covering the 64-bit interface.
- `= {0}` initializes every data field to zero, including effective, permitted, and inheritable masks. Uninitialized structures would not express an empty policy.
- `PR_CAP_AMBIENT_CLEAR_ALL` clears the separate ambient set. Any error stops the program. Ignoring an unsupported operation would silently weaken the intended postcondition.
- `syscall(SYS_capset, ...)` asks the kernel to replace the calling thread's current sets. glibc does not expose a normal `capset` wrapper; this small course example calls the kernel interface directly. Larger software should evaluate the higher-level libcap API.
- `SYS_capget` reads the actual state back into the same array. The program does not treat the requested zero-filled input as evidence that the transition worked.
- Each `printf` prints the high 32-bit half followed by the low half, with eight hexadecimal digits per half. The result is a comparable 16-digit mask, not two unrelated capabilities.
- A successful return here means the calls completed. Inspect the masks as well: effective, permitted, and inheritable must all be zero. The ambient-clear operation is separately checked for success.

Build and compare two starting contexts:

```bash
cc -std=c11 -Wall -Wextra -O2 clear-current.c -o clear-current
./clear-current
unshare --user --map-root-user ./clear-current
```

`cc` builds your current source. The direct invocation begins with the ordinary user's usually empty current sets. The second starts with namespace-local capabilities, then clears them inside the same process. Both should report three zero masks and return 0. No parent-shell capabilities are modified.

For an intentional failure, open `nano clear-current.c`, temporarily remove the entire `SYS_capset` error-check block, save with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. Recompile and repeat the **namespace** invocation. The masks are now nonzero even though the program may return 0. Restore the block, recompile, and verify zero again. This is why testing only an already-unprivileged input can miss a control that does nothing.

This program does not execute another file. Exec can recalculate capabilities, especially for UID 0; a current-state observation is not automatically a post-exec guarantee. Lesson 03.03 adds the restriction on privilege gain across exec. The independent lab preserves the ordinary invoking UID rather than manufacturing root.

## Capability caveats

- Clearing current sets does not close descriptors opened while capabilities were present.
- Dropping the bounding set is a one-way restriction for the process tree, but executable attributes and namespace context still need analysis.
- Supplementary groups are a separate authority channel.
- A zero capability mask does not restrict ordinary permissions granted by UID, GID, ACLs, or open resources.

## Troubleshooting and checkpoint

- If `setpriv` is missing, install util-linux in the disposable VM.
- If an option spelling differs, check the VM's util-linux version rather than silently omitting the property.
- If a transition fails, capture stderr and current sets before changing the exercise.
- You should be able to state which set is used for current checks and which set caps future acquisition across exec.

Repeat the complete Exercise 2 after the partial Exercise 3 and compare every field. Then verify the C bridge's repaired namespace case. These are separate checkpoints for the utility-based transition and the in-process C operation.

To discard student edits, return with `cd ../..` and run `./lab-reset 03.02`. A new child process gets its own starting credentials; do not try to restore a dropped bounding set within the same process.

## Source truth

See [capabilities(7)](https://man7.org/linux/man-pages/man7/capabilities.7.html), [capget/capset(2)](https://man7.org/linux/man-pages/man2/capget.2.html), and [PR_CAP_AMBIENT_CLEAR_ALL(2)](https://man7.org/linux/man-pages/man2/PR_CAP_AMBIENT_CLEAR_ALL.2const.html). `man setpriv` documents the installed utility's flags. Current-state reduction, exec-time restrictions, and supplementary-group changes are different mechanisms.
