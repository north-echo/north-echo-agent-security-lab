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

Graders are outside the student workspace. Each run generates a fresh evaluation canary or hostname, compiles or invokes the student's declared interface, and observes effects from an external probe. Results are security properties such as “pre-opened protected descriptor is not inherited,” not source-code prescriptions. Practice mode adds lesson references; exam mode suppresses them. Only pass state, counts, and timestamps persist.

## Reset and cleanup safety

Reset first processes `.runtime/TARGET/resources.json`, then deletes the corresponding student and fixture directories. Runtime resources are opt-in and scoped:

- a PID is signaled only when `/proc/PID/cmdline` contains the exact target workspace path;
- a mount is unmounted only when it is both registered and resolves under `.student`;
- a cgroup-bearing transient user service is stopped only when its unit name, exact workspace-bound description, and effective cgroup all prove ownership inside the invoking user's delegated systemd manager;
- direct cgroup-path registry entries fail closed; Module 07 registers the owning transient user unit so systemd removes its subtree;
- a temp path is removed only below that target's `.runtime` directory.

Any failed containment proof aborts cleanup. `--dry-run` executes the same validation and prints intended actions. Modules 01-06 do not leave background resources; the registry exists so later cgroup/network/runtime modules inherit a safe contract.

Module 07 uses transient services in the ordinary user's delegated systemd manager. Before launch, the internal `register-unit` transaction records a narrowly formatted unit name under the active target. Cleanup trusts neither that name nor the registry alone: the live unit must also have the exact workspace-bound description and an effective cgroup below `user-UID.slice/user@UID.service`, ending in that unit name. Direct cgroup-path entries are rejected so systemd, rather than recursive course code, owns subtree removal.

## Limits

This platform is not itself a security boundary against a malicious local user who owns the repository. A student can read graders, edit platform code, or delete state. The threat model is accidental contamination and pedagogical answer leakage across honest replays, not hostile anti-cheat. The actual containment exercises must run inside a disposable VM because kernel configuration and implementation mistakes can affect the running system.
