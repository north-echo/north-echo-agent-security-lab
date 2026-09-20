# Module 11 independent lab - Repair randomized model variants

## Assignment and readiness check

Build a strict, deterministic repairer for the small model from 11.01-11.03. Preserve useful work and identity while correcting **every** known control choice. You are not implementing a new Linux sandbox.

Before coding, explain why a missing observation is not false, why a network branch that skips a socket is not kernel denial, and why repairing only the most conspicuous symptom leaves mixed variants incomplete.

## Prepare and read the starter

From the course root:

```bash
./lab-start module-11
cd .student/11.lab
pwd
ls -l repair_variant.py
cat repair_variant.py
nano repair_variant.py
```

Edit only this prepared copy. In the default nano configuration, Ctrl+O then Enter saves; Ctrl+X exits.

<!-- source: course/module-11-break-fix-research/lab/repair_variant.py format=code -->
```python
#!/usr/bin/env python3
"""Module 11 starter: repairs only one visible weakness."""

import json
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit(2)
plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
plan["controls"]["execution"] = "argv"
Path(sys.argv[2]).write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
```
<!-- /source -->

### Starter, line by line

- The imports provide JSON parsing, paths, and command arguments.
- The argument-count guard expects an input and an output filename.
- Parsing JSON alone does not validate the model's schema or known values.
- The single assignment repairs execution only. Other weak choices survive.
- Direct writing publishes a file without the complete validation and atomic publication required here.

The starter can produce useful-looking output while still failing most mixed variants. Your job includes failure handling, not just adding four assignments.

## Input and output contract

The grader invokes:

```text
python3 repair_variant.py INPUT.json OUTPUT.json
```

Require exactly the top-level keys `schema`, `variant_id`, `workload`, and `controls`. Schema must be integer 1, not Boolean true. Identity must be a nonempty string. Workload has exactly `operation`, `resource`, and `literal`, all strings. Treat those values as opaque data, never shell commands.

The controls must have exactly these known choices:

| Control | Intended model choice | Deliberately weak choice |
| --- | --- | --- |
| execution | argv | shell |
| environment | minimal | inherit |
| filesystem | resolved | lexical |
| network | broker_only | direct |
| cleanup | owned | prefix |

Validate the complete plan before creating output. Unknown fields, missing fields, wrong types, and unknown choices must fail nonzero. A rejected plan must not create a new output or modify an existing output. Refuse an output that aliases the input or is a symlink.

Preserve the input bytes, variant identity, and workload values. Correct all five control choices. Publish complete JSON through an exclusive temporary file in the destination directory and atomic replacement; clean only that exact owned temporary path on failure. This is atomic visibility, not a crash-durability guarantee. Setup paths belong to the exercise operator; this is not a race-free defense against a concurrent same-account mutator.

Repairing the result again must produce the same data. Use deterministic formatting so you can also compare bytes during your own tests. Return 0 only after successful publication.

## What the external checks observe

The grader rotates identities, resources, literals, fake canaries, and six combinations containing one through five weak choices. It compares preserved input/workload, complete controls, idempotence, malformed-input refusal, and fixed local harness results.

Allowed synthetic work must remain successful. The constant shell marker fixture must not run; the explicitly fake ambient variable must be absent; the generated protected sibling must not be read; the broker-only model branch must skip socket creation; and the cleanup selection must exclude the unowned string decoy.

These are finite model observations. The check does not prove kernel network denial, race-free filesystem confinement, actual cleanup ownership, or complete coverage of every malformed plan. Test your validation/publication edge cases yourself. No candidate is deleted and no socket connects.

## Map the work to practice

Plan shape and data preservation: 11.01 and 11.03. Evidence completeness and calibrated claims: 11.02. Exclusive temporary output, atomic publication, and idempotence: 11.03. Structured input and error status: Module 04.

Write `design-notes.md` describing one partial repair, the remaining observations, and how your complete repair preserves useful work. The independent lab intentionally withholds a complete implementation.

## Validate and replay

```bash
python3 -m py_compile repair_variant.py
../../lab-grade module-11
../../lab-grade module-11 --mode exam
```

Syntax checking does not execute a plan. Practice grading reports failed properties with lesson references; exam grading reduces hints and uses fresh fixtures.

If the allowed operation fails, inspect preserved workload data before changing the harness. If malformed input leaves output, inspect validation order and publication. Never replace missing observations with invented negative values.

Save notes, return with `cd ../..`, and use `./lab-reset module-11` to remove this prepared workspace and generated fixtures. There is no background service to kill. Do not extend the harness into an external scanner, arbitrary command runner, or destructive cleanup tool.
