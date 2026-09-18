# Module 10 independent lab - Composed contained runtime

Implement `complete_runtime.py`. The grader invokes:

```text
python3 complete_runtime.py SPEC.json RESULT.json
```

The JSON spec contains an absolute trusted `guard` executable, an absolute `allowed_root`, structured workload `command` argv, and integer `memory_max`, `tasks_max`, and `cpu_percent` limits. The workload executable must resolve beneath the allowed root. Treat the guard as trusted runtime TCB and every command argument as literal data.

Create a uniquely named transient systemd user service with the validated CPU quota, memory limit, zero swap, PID limit, control-group kill behavior, bounded stop time, synchronous waiting, and collection. Inside that cgroup, create fresh user and network namespaces, then empty bounding/inheritable/ambient capability sets and set `no_new_privs`. Remove `NORTH_ECHO_FAKE_CREDENTIAL` from the workload environment. Invoke the guard with the allowed root and exact workload argv; do not use a shell.

Write one result object containing schema 1, workload status, exact unit name, stdout, stderr, and the parsed final-line attestation. Propagate nonzero workload status through a nonzero launcher status. Invalid roots, commands, limits, or shapes must fail before a result or unit exists. On timeout, stop only the exact unit created by this invocation. Successful and failed runs must leave no transient unit.

The external grader compiles its own static guard and workload probe, rotates synthetic paths, capabilities, fake credentials, canaries, and unit names, and runs a separate host-side Unix-socket broker. It verifies:

- exact CPU, memory, swap, and PID controller values;
- different user and network namespaces plus `AF_INET` denial;
- empty effective/bounding/ambient capability sets and `no_new_privs`;
- effective Landlock allowed/protected reads and seccomp filter mode;
- successful `AF_UNIX` capability mediation and broker-side fake-credential use;
- credential absence from the workload and all returned output;
- literal path handling without shell evaluation;
- failure status/stderr propagation, invalid-spec rejection, and exact cleanup.

The starter runs the guard and workload directly, so useful inner controls execute but outer composition properties fail. The lab withholds a complete implementation; use the launch dependency and interface practiced in Lessons 10.01-10.03.

```bash
python3 -m py_compile complete_runtime.py
../../lab-grade module-10
../../lab-grade module-10 --mode exam
```

- `py_compile` checks syntax without creating a unit.
- Practice mode names the lesson associated with each failed property.
- Exam mode repeats fresh external checks but withholds lesson references.

Use only the grader's generated local objects. Never substitute a real credential, external service, host firewall change, privileged cgroup, or production path.
