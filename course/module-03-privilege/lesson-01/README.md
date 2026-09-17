# 03.01 - UIDs are not the whole privilege story

Goal: read real/effective/saved IDs and Linux capability sets from `/proc`, then decode them.

## Exercise 1 - Inspect credentials

```bash
id
grep -E '^(Uid|Gid|Groups|Cap(Inh|Prm|Eff|Bnd|Amb)|NoNewPrivs):' /proc/self/status
```

Expected pattern for an ordinary VM user: matching real/effective UIDs, `CapEff` usually all zero, a nonzero or zero bounding set depending on the environment, and `NoNewPrivs: 0`.

Decode the effective mask:

```bash
CAP_EFF=$(awk '/^CapEff:/{print $2}' /proc/self/status)
capsh --decode="$CAP_EFF"
```

Expected: `0x...=` followed by capability names, or an empty set for zero.

## Exercise 2 - Compare a namespaced root process

```bash
unshare --user --map-root-user sh -c '
  id;
  grep -E "^(Uid|Cap(Inh|Prm|Eff|Bnd|Amb)):" /proc/self/status;
  capsh --decode=$(awk "/^CapEff:/{print \\$2}" /proc/self/status)
'
```

Expected: UID 0 and capabilities meaningful inside the new user namespace. They do not grant corresponding authority over parent-namespace objects.

## Exercise 3 - Correct the intentional simplification

Mistaken claim: “If effective UID is not zero, there is no privilege.” Run:

```bash
getcap -r /usr/bin 2>/dev/null | head
```

Expected on many distributions: one or more executables with file capabilities. UID is one input to authority, not the complete answer. A security review records UIDs, groups, all capability sets, namespace mappings, and pre-opened resources.
