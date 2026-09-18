# 11.03 - Repair and prove the hardened counterpart

## Goal

Repair all known weak controls in one pass, preserve the workload and variant identity, prove behavior with the same harness, and require idempotence.

## Exercise 1 - Read the complete repair tool

```bash
sed -n '1,300p' repair_variant.py
python3 -m json.tool vulnerable-plan.json
```

### Line by line

- `SECURE` expresses the five positive control choices; `ALLOWED` bounds both secure and deliberately weak input values.
- `repair` requires the exact top-level, workload, and control shapes, validates types and known values, copies opaque workload/identity fields, and replaces only the controls.
- `main` parses completely before output, writes a sibling temporary file, and atomically replaces the result. Invalid input leaves no claimed repair.
- Applying the function to an already hardened plan produces the same JSON object: repair is idempotent.

## Exercise 2 - Observe the vulnerable counterpart

```bash
cp vulnerable-plan.json before.json
NORTH_ECHO_FAKE_CREDENTIAL=FAKE-LESSON-11.03 \
  python3 ../../course/module-11-break-fix-research/lesson-01/variant_harness.py \
  before.json before-evidence.json before-run
python3 -m json.tool before-evidence.json
```

All five adverse signals are true while `allowed_operation` is true. This is the intentional vulnerable counterpart, not an instruction to target another system.

## Exercise 3 - Repair and compare

```bash
python3 repair_variant.py before.json after.json
NORTH_ECHO_FAKE_CREDENTIAL=FAKE-LESSON-11.03 \
  python3 ../../course/module-11-break-fix-research/lesson-01/variant_harness.py \
  after.json after-evidence.json after-run
python3 -m json.tool after-evidence.json
python3 repair_variant.py after.json second.json
cmp after.json second.json
```

Expected: the allowed operation stays true and every adverse signal is false. `cmp` proves a second repair does not mutate an already hardened plan.

Clean the exact generated objects:

```bash
rm before-run/allowed/data.txt before-run/allowed/link.txt before-run/protected.txt before-run/shell-marker
rmdir before-run/allowed before-run
rm after-run/allowed/data.txt after-run/allowed/link.txt after-run/protected.txt
rmdir after-run/allowed after-run
rm before.json after.json second.json before-evidence.json after-evidence.json
```

## Checkpoint and troubleshooting

- If the hardened evidence still contains a true adverse field, compare that field with the corresponding invariant before editing another layer.
- If cleanup says a marker is absent, remove it conditionally; only the vulnerable execution mode creates it.
- If relative canonical paths fail, confirm the command is run from `.student/11.03`.
- Checkpoint: explain why preserving workload bytes and allowed behavior matters as much as making adverse signals false.
