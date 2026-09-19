# Cold capstone - Process an ordered batch of contained jobs

Build `cold_runtime.py`. A local batch service must complete useful work under
different resource budgets, retain each job's identity, and continue after an
ordinary workload failure. Each job gets an independently collected runtime.

Interface: `python3 cold_runtime.py BATCH.json RESULT.json`.

The batch has exactly `schema: 2` and `jobs`, a list of one through eight objects.
Each job has exactly a unique nonempty string `id` and a `runtime` object containing
`guard`, `allowed_root`, `command`, `memory_max`, `tasks_max`, and `cpu_percent`.
Those fields have the same meanings and bounds as the previously practiced
single-job runtime. Validate the whole batch before launching any job. Reject
duplicate IDs, empty batches, extra fields, and invalid runtime specifications
without creating a result or a unit.

Return `{"schema":2,"jobs":[{"id":"...","result":{...}}]}` in input order.
Each result has schema 1, workload status, a distinct exact owned unit name,
stdout, stderr, and the parsed final-line attestation (or null for a worker
without one). Do not assume every worker emits attestation JSON. Continue after
an ordinary nonzero workload exit; return nonzero overall if any job failed.
All jobs must have CPU/memory/swap/task limits, fresh user/network namespaces,
the privilege floor, filesystem/syscall policy, clean credential environment,
literal argv, and exact teardown. Use the `north-echo-UID-10-lab-RANDOM.service`
unit convention so the evaluator can inspect collection. Never stop unrelated units.

The evaluator varies resource profiles, checks all kernel properties, and then
uses a three-job success/failure/success batch to assess transfer. It also checks
invalid batch rejection and empty runtime state. No guided solution is copied.

```bash
python3 -m py_compile cold_runtime.py
../../lab-grade capstone
../../lab-grade capstone --mode exam
```

Graduation also requires a short `RATIONALE.md` reviewed by a human: identify
the authority each control removes, explain why useful work still succeeds,
map each claim to an observation, and state the limits of that observation.
Discuss job failure versus invalid input and why a fresh unit matters per job.
The automated result is a runtime assessment, not a substitute for this reasoning
rubric. Use the rubric in `docs/LEARNING_PATH.md`; no real credential or external
target belongs in the rationale or runtime.
