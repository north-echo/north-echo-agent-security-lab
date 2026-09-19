# Module 12 independent lab - Bounded adaptive runner

Implement `adaptive_runner.py`; the grader calls `python3 adaptive_runner.py SPEC.json RESULT.json`. The spec contains exact `oracle_command` argv, integer action `budget`, and opaque `run_id`.

Validate before acting. Invoke only `inventory`, `argv`, `credential`, `filesystem`, `network`, or `cleanup`, using exact argv without a shell and with bounded execution. Record sequential action numbers and complete parsed observations. Never exceed budget. Preserve run identity. For an observed focused effect, return its trace row as the finding. If no effect is observed, use `not_observed` and explicitly say security is not established.

The grader rotates five synthetic weakness classes plus a no-weakness case. Its oracle independently records actual calls and observations; the reported count and complete trace must match that record. This is an introductory bounded-dispatch assessment: the inventory names the focused synthetic probe. It is not evidence of independent vulnerability discovery. Lesson 12.02's separate offline evidence matrix assesses interpretation when observations are incomplete. The starter inventories only and therefore misses every weakness.

```bash
python3 -m py_compile adaptive_runner.py
../../lab-grade module-12
../../lab-grade module-12 --mode exam
```

Do not inspect, modify, or target anything outside the supplied local oracle command.
