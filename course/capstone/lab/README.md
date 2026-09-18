# Cold capstone - Contain a useful local worker

Build `cold_runtime.py`. The external evaluator supplies a trusted native guard, an allowed root, a useful static worker, structured argv, and bounded CPU/memory/task values. Launch the worker so it can read its allowed input and spend one local operation capability, while it cannot read the protected sibling, create a direct IP socket, inherit the fake credential, retain capabilities, escape its user/network namespaces, or leave its process tree behind.

Interface:

```text
python3 cold_runtime.py SPEC.json RESULT.json
```

Return schema 1, workload status, owned unit identity, stdout, stderr, and the worker's parsed final-line attestation. Preserve literal argv and failure status. Reject unsafe paths or unbounded values before creating a result. On timeout, stop only the exact owned unit.

No lesson reference or solution is copied into this workspace. Everything needed to solve the objective was practiced in Modules 01-12. Evaluation uses fresh synthetic paths, capabilities, fake credentials, canaries, broker state, and unit names. It contacts no external target.

```bash
python3 -m py_compile cold_runtime.py
../../lab-grade capstone
../../lab-grade capstone --mode exam
```
