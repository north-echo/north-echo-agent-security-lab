# Module 11 independent lab - Repair randomized runtime variants

Implement `repair_variant.py`. The grader invokes:

```text
python3 repair_variant.py INPUT.json OUTPUT.json
```

Input is a schema-1 object with opaque `variant_id`, an exact workload object (`operation`, `resource`, `literal`), and five controls: execution, environment, filesystem, network, and cleanup. Each control contains either the hardened value practiced in Lesson 11.03 or its deliberately weak counterpart. One through five weaknesses may coexist.

Validate the complete shape and known values before writing output. Preserve the input file, variant identity, and workload exactly. Repair every control, not only the first observed weakness. Write a valid plan atomically. A malformed or unknown plan must return nonzero without output. Applying the repair to its own output must be idempotent.

The external grader uses fresh identities, resources, literals, canaries, and six weakness combinations. It evaluates each output with the canonical non-agent harness. The allowed operation must still work; literal argv must not create a marker; the fake credential must be absent; the protected symlink target must not be read; direct IPv4 socket authority must be absent; and cleanup must exclude an unowned prefix-matching decoy. The harness never connects, deletes a candidate, or touches an external target.

The starter repairs only execution mode, so it is functional but fails mixed variants. The lab withholds the full repair implementation.

```bash
python3 -m py_compile repair_variant.py
../../lab-grade module-11
../../lab-grade module-11 --mode exam
```

- Syntax checking creates no research object.
- Practice mode reports failed properties with lesson references.
- Exam mode repeats fresh variants while withholding repair hints.

Use only generated synthetic plans. Do not turn the evidence harness into an external scanner or destructive cleanup tool.
