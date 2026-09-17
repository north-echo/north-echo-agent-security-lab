# 03.02 - Drop capability sets deliberately

Goal: distinguish effective, permitted, inheritable, bounding, and ambient sets, then remove them for a child.

## Exercise 1 - Decode the five sets

```bash
for field in CapInh CapPrm CapEff CapBnd CapAmb; do
  value=$(awk -v key="$field:" '$1==key{print $2}' /proc/self/status)
  printf '%-7s %s -> ' "$field" "$value"
  capsh --decode="$value"
done
```

### Line by line

- `for field in ...; do` iterates across the five capability-set field names.
- `awk -v key="$field:"` passes the current name plus its colon into `awk` as variable `key`.
- `$1==key{print $2}` selects the exact field and emits its hexadecimal mask.
- `printf` displays the field and mask without ending the line; `%-7s` keeps the columns aligned.
- `capsh --decode` prints capability names and completes the line.
- `done` ends the loop.

Immediate interpretation:

- effective: checked for current privileged operations;
- permitted: ceiling for effective capabilities;
- inheritable: input to capability inheritance across exec;
- bounding: ceiling applied during exec transitions;
- ambient: capabilities preserved across exec of ordinary programs.

## Exercise 2 - Launch with empty sets

```bash
unshare --user --map-root-user setpriv \
  --bounding-set=-all \
  --inh-caps=-all \
  --ambient-caps=-all \
  --clear-groups \
  sh -c 'grep -E "^Cap(Inh|Prm|Eff|Bnd|Amb):" /proc/self/status'
```

### Line by line

- `unshare --user --map-root-user` creates a safe namespace where the mapped identity can practice capability transitions.
- A trailing `\` tells the shell that the command continues on the next physical line.
- `setpriv` changes process privilege attributes before executing the command that follows.
- `--bounding-set=-all` removes every capability from the bounding set; `-all` means subtract the named set `all`.
- `--inh-caps=-all` and `--ambient-caps=-all` clear the inheritable and ambient sets.
- `--clear-groups` removes supplementary groups.
- `sh -c 'grep ...'` executes the observation after the requested transitions.

Expected: every displayed mask is `0000000000000000`.

## Exercise 3 - Make the intentional partial fix

Run only:

```bash
unshare --user --map-root-user setpriv --inh-caps=-all sh -c 'grep -E "^Cap(Inh|Prm|Eff|Bnd|Amb):" /proc/self/status'
```

### Line by line

- The `unshare` prefix provides the same mapped practice environment.
- This `setpriv` invocation changes only `--inh-caps`.
- The final `grep` deliberately displays all five sets, making the unchanged channels visible instead of assuming one flag cleared everything.

Expected: `CapInh` is zero, but that command did not necessarily empty the bounding, permitted, effective, or ambient sets. “Drop capabilities” is incomplete unless you name and verify every relevant set.

Checkpoint: write down which set controls current checks and which set limits future exec transitions. Then verify your answer against the observations above.
