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

Expected: every displayed mask is `0000000000000000`.

## Exercise 3 - Make the intentional partial fix

Run only:

```bash
unshare --user --map-root-user setpriv --inh-caps=-all sh -c 'grep -E "^Cap(Inh|Prm|Eff|Bnd|Amb):" /proc/self/status'
```

Expected: `CapInh` is zero, but that command did not necessarily empty the bounding, permitted, effective, or ambient sets. “Drop capabilities” is incomplete unless you name and verify every relevant set.

Checkpoint: write down which set controls current checks and which set limits future exec transitions. Then verify your answer against the observations above.
