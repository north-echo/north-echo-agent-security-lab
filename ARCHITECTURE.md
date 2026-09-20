# Architecture

## Trust and data layout

```text
course/                     canonical, attested teaching material
graders/                    external property checks and probes
scripts/                    control plane and safety checks
.student/TARGET/            disposable student copy; the only editing area
.fixtures/TARGET/           randomized synthetic secrets and evaluation context
.runtime/TARGET/            explicit registry of cleanup-owned resources
.state/progress.json        minimal persistent metadata; no solutions or canaries
```

The control plane discovers its root from its installed file location and requires `.north-echo-root`. It never accepts a root path from lesson input. Every managed deletion resolves its candidate and proves that it is a strict child of the expected managed directory.

## Start transaction

1. Normalize the target and reject unplayable scaffolds.
2. Verify every canonical course file against the checked-in SHA-256 manifest.
3. Refuse an orphan fixture directory or resume an existing workspace.
4. Increment the persistent start count.
5. Generate cryptographically random synthetic canary, ID, name, port, and hostname.
6. Copy the canonical target into `.student/TARGET` without following symlinks.
7. Write non-secret workspace metadata and atomically persist progress.

Fixtures are intentionally not deterministic byte-for-byte; replayability means deterministic lifecycle and learning objective with fresh randomized details.

## Grade transaction

Graders are outside the student workspace. Each run generates a fresh evaluation canary or hostname, compiles or invokes the student's declared interface, and observes effects from an external probe. Results are security properties such as “pre-opened protected descriptor is not inherited,” not source-code prescriptions. Practice mode adds lesson references; exam mode suppresses them. The shared supervisor bounds process time and captured output, collects its process group, and converts execution/JSON failures into failed checks. It is a reliability measure inside the VM, not an additional sandbox. Separately launched services still require their own exact-resource teardown.

All CLI lifecycle transactions hold the same advisory lock, preventing concurrent read-modify-write operations from losing progress or racing reset. Metadata records starts, resets, grading counts, latest result/mode/failed property names, and historical achievement; it contains neither solutions nor fixture payloads. A later failed grade does not erase an earlier achievement, and an earlier pass does not describe the current attempt as passing.

## Reset and cleanup safety

Reset validates every resource registry and deletion path across the entire requested scope before mutating anything. Execution rechecks resource identity and confirms teardown before deleting the corresponding student and fixture directories. Runtime resources are opt-in and scoped:

- a PID is signaled only when a command argument identifies the exact target workspace or a child path; Linux pidfds and process start time prevent PID reuse, and exit must be confirmed;
- a mount is unmounted only when it is both registered and resolves under that specific target's workspace;
- a cgroup-bearing transient user service is stopped only when its unit name, exact workspace-bound description, and effective cgroup all prove ownership inside the invoking user's delegated systemd manager;
- direct cgroup-path registry entries fail closed; Module 07 registers the owning transient user unit so systemd removes its subtree;
- a temp path is removed only below that target's `.runtime` directory.

Any failed containment proof aborts cleanup. A failed systemd query is not evidence that a unit is absent. A timeout retains the registry for recovery. `--dry-run` executes the same planning validation and prints intended actions. This is validation-before-mutation, not rollback: a later execution failure may follow earlier confirmed teardown. Modules 01-06 do not leave background resources; the registry exists so later cgroup/network/runtime modules inherit a safe contract.

Module 07 uses transient services in the ordinary user's delegated systemd manager. Before launch, the internal `register-unit` transaction records a narrowly formatted unit name under the active target. Cleanup trusts neither that name nor the registry alone: the live unit must also have the exact workspace-bound description and an effective cgroup below `user-UID.slice/user@UID.service`, ending in that unit name. Direct cgroup-path entries are rejected so systemd, rather than recursive course code, owns subtree removal.

Module 08 creates no persistent network object. Each `unshare --net` namespace exists only for its foreground client process; no veth, route, firewall rule, namespace pin, or DNS configuration is created. Guided synthetic services and brokers use registered, bounded user units with exact workspace descriptions. External grader fixtures have separately owned lifecycles. Unix sockets and readiness files use exact paths inside disposable workspaces or grader temporary directories, and the broker removes its socket on clean termination. No name-prefix cleanup is permitted.

Module 09 keeps every credential and shared HMAC key synthetic. The workload receives an authenticated bearer capability but neither secret through the intended interface; same-UID mode-0600 files do not isolate these roles against malicious code. The broker loads secrets at trusted startup and uses the fake upstream credential only after operation, resource, input, audience, run, time, policy, and nonce validation. Guided broker/upstream processes use registered bounded user units. Nonce state is process-local and is consumed before the upstream attempt; it is not durable exactly-once delivery. Files and sockets stay inside disposable workspaces or owned grader directories.

Modules 11-12 teach bounded evidence interpretation with fixed local models.
Their configuration choices and oracle labels are not kernel enforcement
observations. Module 12 inventory supplies the focused label; no independent
discovery or autonomous offensive workflow is implemented. Package integrity
checks execute no supplied code and do not establish authenticity.

## Limits

This platform is not itself a security boundary against a malicious local user who owns the repository. A student can read graders, edit platform code, or delete state. The threat model is accidental contamination and pedagogical answer leakage across honest replays, not hostile anti-cheat. The actual containment exercises must run inside a disposable VM because kernel configuration and implementation mistakes can affect the running system.
