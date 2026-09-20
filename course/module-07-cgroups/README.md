# Module 07 - Bound CPU, memory, and process creation

Use cgroup v2 through the ordinary user's delegated systemd manager. Observe effective controller files from inside workloads, trigger bounded pressure, and prove that transient service collection removes the complete process tree.

Play in order: `07.01`, `07.02`, `07.03`, then `module-07`.

Outcomes:

- connect a systemd user unit to its effective cgroup v2 path;
- interpret `cpu.max`, `cpu.stat`, `memory.max`, `memory.events`, `pids.max`, and `pids.events`;
- distinguish throttling, allocation failure/OOM, and PID exhaustion;
- apply limits to a process tree rather than a single PID;
- use bounded transient units whose cleanup is synchronous and ownership-verifiable.

Prerequisites: Modules 01-06, unified cgroup v2, a running delegated systemd user manager, and the `cpu`, `memory`, and `pids` controllers. No root access is used by the exercises.

## Learning route and limits

Earlier controls answered whether an operation may happen. Resource controls answer how much resource the permitted process tree may consume. A file read can be authorized while a computation still exhausts memory or creates too many tasks. These are different failure modes and need different evidence.

07.01 introduces service identity, registered ownership, the delegated user manager, and CPU quota/period observations. 07.02 reads actual memory/swap ceilings before a capped allocator runs and requires specific OOM evidence. 07.03 checks task-controller rejection events, then uses a harmless sleep to practice client timeout versus service cleanup. The independent lab combines resource properties, validation, literal argv, result handling, and exact ownership.

The helpers enforce small input caps even when a property is deliberately omitted. Never replace them with an unbounded stress loop. Do not change host controllers, swap, overcommit, or security-module policy to force a lesson outcome. If the expected runtime prerequisite fails, return to VM preflight.

Before moving on, distinguish throttling, allocation failure/OOM, and task-creation refusal. Explain why a nonzero command status or an absent wildcard listing is insufficient by itself. A timed-out client may leave a separately managed service; retain ownership evidence until collection or verified cleanup is established.
