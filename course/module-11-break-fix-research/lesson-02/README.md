# 11.02 - Identify invariants from an evidence matrix

## Outcomes and prerequisites

Complete 11.01. You will map supplied observations to intended invariants, avoid diagnosing every case from one dramatic symptom, and reject incomplete evidence instead of treating missing fields as negative observations.

## Concepts before commands

An **invariant** is a property the design intends to preserve across variants. “Arguments remain data” is an invariant; “this variant used the argv option” is a configuration fact. The latter does not automatically establish the former in arbitrary code.

**Overfitting** means tailoring your conclusion to the examples you noticed rather than the underlying property. A conspicuous shell marker can distract from a quieter inherited credential or cleanup over-selection.

These fixed JSON rows are teaching fixtures, not fresh measurements of your current VM. The classifier interprets their content; it does not run a workload or independently verify their provenance. Keep both the observation source and its limitations in your report.

## Prepare and read the classifier and cases

From the course root:

```bash
./lab-start 11.02
cd .student/11.02
pwd
ls -l classify_evidence.py overfit-evidence.json mixed-evidence.json
cat classify_evidence.py
cat overfit-evidence.json
cat mixed-evidence.json
```

Use `nano mixed-evidence.json` to navigate, but leave the shipped case intact. The deliberate missing-field case will use a separate copy.

### The classifier

<!-- source: course/module-11-break-fix-research/lesson-02/classify_evidence.py format=code -->
```python
#!/usr/bin/env python3
"""Map reproduced effects to invariant statements."""

import json
import sys
from pathlib import Path

INVARIANTS = {
    "shell_marker_created": "argv is data and is never shell syntax",
    "credential_visible": "the workload receives no ambient credential",
    "protected_read": "authorization follows resolved objects, not lexical paths",
    "inet_created": "the workload has no direct IP socket authority",
    "cleanup_decoy_selected": "cleanup selects only exact owned objects",
}

if len(sys.argv) != 2:
    raise SystemExit(f"usage: {sys.argv[0]} EVIDENCE.json")
evidence = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
required = {"schema", "variant_id", "allowed_operation", *INVARIANTS}
if (not isinstance(evidence, dict) or set(evidence) != required
        or type(evidence["schema"]) is not int or evidence["schema"] != 1
        or not isinstance(evidence["variant_id"], str)
        or any(type(evidence[name]) is not bool for name in ("allowed_operation", *INVARIANTS))):
    raise SystemExit("invalid or incomplete evidence; absence is not a negative observation")
failed = [{"signal": name, "invariant": statement}
          for name, statement in INVARIANTS.items() if evidence.get(name) is True]
print(json.dumps({"variant_id": evidence.get("variant_id"), "failed": failed}, indent=2, sort_keys=True))
raise SystemExit(0)
```
<!-- /source -->

### Source, line by line

- `INVARIANTS` maps each adverse signal to the positive property it calls into question.
- The argv guard requires one evidence filename; JSON is then parsed into Python data.
- The complete key-set check prevents an omitted signal from silently becoming `False`.
- Schema and Boolean type checks reject values such as the string `"false"` or integer 0 in place of observed Booleans.
- The list comprehension selects only signals whose supplied value is actually `True`.
- Each selected row carries both its signal name and explanatory invariant. Variant identity is retained as metadata, not used to choose the diagnosis.
- Printing the result and returning 0 means classification completed. An empty `failed` list is a data result, not a promise of universal safety.

### Two complete supplied cases

<!-- source: course/module-11-break-fix-research/lesson-02/overfit-evidence.json format=code -->
```json
{"schema":1,"variant_id":"lesson-overfit","allowed_operation":true,"shell_marker_created":true,"credential_visible":false,"protected_read":false,"inet_created":false,"cleanup_decoy_selected":false}
```
<!-- /source -->

This row contains one adverse shell-marker observation and successful allowed work.

<!-- source: course/module-11-break-fix-research/lesson-02/mixed-evidence.json format=code -->
```json
{"schema":1,"variant_id":"lesson-mixed","allowed_operation":true,"shell_marker_created":false,"credential_visible":true,"protected_read":true,"inet_created":false,"cleanup_decoy_selected":true}
```
<!-- /source -->

This row has no shell marker but three other adverse observations. Neither the variant label nor the absence of one familiar symptom should override those fields.

## Exercise 1 - Diagnose both rows before execution

Predict the failed invariants, then run:

```bash
python3 classify_evidence.py overfit-evidence.json > overfit-result.json
python3 classify_evidence.py mixed-evidence.json > mixed-result.json
python3 -m json.tool overfit-result.json
python3 -m json.tool mixed-result.json
```

The first result should contain only `shell_marker_created`. The second should contain `credential_visible`, `protected_read`, and `cleanup_decoy_selected`.

The intentional diagnostic mistake is applying the first case's repair to every case. Repair the explanation by mapping **each** true signal to its invariant. Preserve the positive allowed-operation observation; disabling all useful work would not be a successful repair.

## Exercise 2 - Build a comparison matrix

```bash
python3 - <<'PY'
import json
from pathlib import Path

signals = ("shell_marker_created", "credential_visible", "protected_read",
           "inet_created", "cleanup_decoy_selected")
for name in ("overfit-evidence.json", "mixed-evidence.json"):
    value = json.loads(Path(name).read_text())
    adverse = [signal for signal in signals if value[signal] is True]
    print(name, "allowed=", value["allowed_operation"], "adverse=", ",".join(adverse) or "none")
PY
```

The program names the exact expected signal columns. It does not treat arbitrary metadata values as truthy failures. A consistent row structure makes differences visible without turning labels into evidence.

Remember 11.01's scope table: the network and cleanup branches model decisions, and pathname resolution is not a race-free kernel policy. State that distinction when using the matrix.

## Exercise 3 - Deliberately omit an observation

```bash
python3 - <<'PY'
import json
from pathlib import Path

value = json.loads(Path("mixed-evidence.json").read_text())
del value["protected_read"]
Path("incomplete.json").write_text(json.dumps(value) + "\n")
PY
NE_INCOMPLETE_STATUS=0
python3 classify_evidence.py incomplete.json > incomplete-result.json 2> incomplete.err || NE_INCOMPLETE_STATUS=$?
cat incomplete.err
test "$NE_INCOMPLETE_STATUS" -ne 0
test ! -s incomplete-result.json
python3 classify_evidence.py mixed-evidence.json > repaired-result.json
```

The omitted field is unknown, not false. The classifier refuses the incomplete row instead of silently reducing the failure count. Repair the analysis by returning to the complete supplied evidence, not by inventing a replacement observation.

## Checkpoint and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

def signals(name):
    return {row["signal"] for row in json.loads(Path(name).read_text())["failed"]}

assert signals("overfit-result.json") == {"shell_marker_created"}
assert signals("mixed-result.json") == {
    "credential_visible", "protected_read", "cleanup_decoy_selected"
}
assert signals("repaired-result.json") == signals("mixed-result.json")
assert "incomplete evidence" in Path("incomplete.err").read_text()
print("INVARIANT MATRIX AND MISSING-EVIDENCE REFUSAL: PASS")
PY
```

In `nano matrix-notes.md`, explain an invariant without naming the implementation option that supposedly enforces it. Then identify one additional observation needed before claiming kernel enforcement rather than model selection.

If a count differs, inspect all input fields and their types. Do not modify the classifier to produce a preferred answer. Save notes, return with `cd ../..`, and use `./lab-reset 11.02` to remove this prepared workspace. No service was launched.

## Source truth

Python's [JSON documentation](https://docs.python.org/3.14/library/json.html) defines parsing and serialization, not the truth of a record's claims. The invariant mapping and fixture limitations are course-defined. Modules 05, 08, and 10 show the separate behavioral observations needed to support enforcement conclusions.
