# 11.02 - Identify invariants from an evidence matrix

## Goal

Map observable failure signals to stable invariants, then show why repairing only the most visible symptom does not harden a mixed variant.

## Exercise 1 - Read the classifier and evidence

```bash
sed -n '1,220p' classify_evidence.py
python3 -m json.tool overfit-evidence.json
python3 -m json.tool mixed-evidence.json
```

### Line by line

- `INVARIANTS` maps each bad effect to a positive statement that must remain true across implementations.
- The classifier selects only signals explicitly observed as true. It does not guess at missing fields or inspect a variant's control labels.
- `overfit-evidence.json` has one dramatic shell marker. `mixed-evidence.json` has no marker but shows ambient credential, protected read, and cleanup over-selection.

## Exercise 2 - Make and expose an overfit diagnosis

```bash
python3 classify_evidence.py overfit-evidence.json
python3 classify_evidence.py mixed-evidence.json
```

The first output names the argv invariant. The intentional mistake is to generalize that single diagnosis to all variants. The second output names three different invariants and contains no shell failure. A repair chosen from exploit theatrics rather than a property matrix would miss them.

## Exercise 3 - Build the research matrix

```bash
python3 - <<'PY'
import json
for name in ("overfit-evidence.json", "mixed-evidence.json"):
    value = json.load(open(name))
    bad = sorted(key for key, state in value.items() if key not in {"schema", "variant_id", "allowed_operation"} and state)
    print(name, "allowed=", value["allowed_operation"], "bad=", ",".join(bad) or "none")
PY
```

### Line by line

- The loop reads both fixed evidence rows rather than relying on memory of one run.
- Metadata and the positive functional signal are separated from adverse booleans.
- Sorting makes comparison stable. The matrix preserves the fact that useful work succeeds even when containment fails.

## Checkpoint and troubleshooting

```bash
test "$(python3 classify_evidence.py mixed-evidence.json | grep -c 'invariant')" -ge 3
```

- If the count differs, inspect the complete JSON rather than changing the classifier to match a desired answer.
- An absence of one signal proves only that probe did not observe that effect; it is not universal proof of safety.
- Checkpoint: state the filesystem invariant without naming `lexical`, `resolved`, or a particular exploit path.
