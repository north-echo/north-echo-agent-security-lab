# 03.01 - UIDs are not the whole privilege story

Goal: read real/effective/saved IDs and Linux capability sets from `/proc`, then decode them.

## Exercise 1 - Inspect credentials

```bash
id
grep -E '^(Uid|Gid|Groups|Cap(Inh|Prm|Eff|Bnd|Amb)|NoNewPrivs):' /proc/self/status
```

### Line by line

- `id` summarizes the current process's user ID, primary group, and supplementary groups.
- `grep -E` enables extended regular expressions.
- `^` anchors the pattern at the start of each line; `(A|B|C)` means any listed alternative.
- `Cap(Inh|Prm|Eff|Bnd|Amb)` compactly matches the five capability fields.
- `/proc/self/status` is kernel-generated status for the process running `grep`; inherited credentials make it representative of the shell that launched it.

Expected pattern for an ordinary VM user: matching real/effective UIDs, `CapEff` usually all zero, a nonzero or zero bounding set depending on the environment, and `NoNewPrivs: 0`.

Decode the effective mask:

```bash
CAP_EFF=$(awk '/^CapEff:/{print $2}' /proc/self/status)
capsh --decode="$CAP_EFF"
```

### Line by line

- `awk '/^CapEff:/{print $2}' ...` finds the line beginning `CapEff:` and emits its second whitespace-separated field, the hexadecimal mask.
- `CAP_EFF=$(...)` stores that emitted mask in a shell variable.
- `capsh --decode="$CAP_EFF"` translates set bits in the mask into human-readable capability names.
- Quoting the variable keeps even an empty or unusual expansion as one argument.

Expected: `0x...=` followed by capability names, or an empty set for zero.

## Exercise 2 - Compare a namespaced root process

```bash
unshare --user --map-root-user sh -c '
  id;
  grep -E "^(Uid|Cap(Inh|Prm|Eff|Bnd|Amb)):" /proc/self/status;
  capsh --decode=$(awk "/^CapEff:/{print \\$2}" /proc/self/status)
'
```

### Line by line

- `unshare --user --map-root-user` creates namespace-local root mapped to your ordinary host identity.
- `id` displays that inside identity.
- `grep -E ...` prints UID and capability fields from the child process's procfs status.
- The nested `awk` extracts `CapEff`; `capsh --decode=...` interprets it in names.
- The backslash before `$2` prevents the outer shell from expanding it before the inner shell runs `awk`.

Expected: UID 0 and capabilities meaningful inside the new user namespace. They do not grant corresponding authority over parent-namespace objects.

## Exercise 3 - Correct the intentional simplification

Mistaken claim: “If effective UID is not zero, there is no privilege.” Run:

```bash
getcap -r /usr/bin 2>/dev/null | head
```

### Line by line

- `getcap` reads file capability extended attributes.
- `-r /usr/bin` walks that directory recursively.
- `2>/dev/null` discards expected permission or unsupported-file diagnostics from stderr; do not use it when diagnosing a real failure.
- `| head` shows only the first few findings so the observation remains readable.

Expected on many distributions: one or more executables with file capabilities. UID is one input to authority, not the complete answer. A security review records UIDs, groups, all capability sets, namespace mappings, and pre-opened resources.
