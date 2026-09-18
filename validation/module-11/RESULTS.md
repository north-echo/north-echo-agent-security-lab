# Module 11 acceptance record

Status: **PASS** on Ubuntu 24.04.4 LTS arm64 with Linux 6.8.0-134-generic.

Source under test: Module 11 feature branch based on `2b2e0c5`; the final commit hash will be the commit containing this record. Date: 2026-09-17.

## Acceptance checklist

- [x] Three guided lessons provide exact commands, complete sources/fixtures, local explanations, expected observations, failure/repair, checkpoints, and troubleshooting.
- [x] Independent lab states the plan transformation and behavioral properties without shipping the completed repair.
- [x] Seeded generator weakens two through four controls reproducibly; external grading varies one through five weaknesses with fresh identities, resources, literals, and canaries.
- [x] Non-agent harness safely reproduces shell interpretation, ambient credential visibility, symlink escape, unconnected IPv4 socket authority, and cleanup decoy selection.
- [x] Regression test proves the deliberately vulnerable symlink mode actually reaches the protected synthetic file.
- [x] Evidence classifier maps effects to implementation-independent invariants and demonstrates why one-symptom repair overfits mixed variants.
- [x] Completed repair preserves input, opaque identity, workload, and allowed operation; repairs every layer; rejects malformed plans; and is idempotent.
- [x] Starter fails multi-weakness variants; completed implementation passes all 11 grader properties in practice and exam modes.
- [x] Lesson, module reset, replay rotation, dry-run cleanup, and final empty-state checks pass.
- [x] Harness creates no persistent resource and never deletes cleanup candidates, connects a socket, uses a real credential, or targets an external system.
- [x] Synchronized field-manual chapter contains complete guided commands, sources, fixtures, interpretation limits, and lab contract.
- [x] Full automated suite passes 38/38 on Linux; course attestation and 28-check Linux preflight pass.

## Evidence

- `environment.txt`: supported VM and safety boundary.
- `tests.txt`: automated, attestation, preflight, and vulnerable-probe regression results.
- `lessons.txt`: guided observations and repair comparison.
- `grading.txt`: starter failure plus practice/exam success.
- `lifecycle.txt`: starts, reset, rotation, cleanup, and final state.

## Safety and residual risk

All effects used generated local files, an explicitly fake environment value, an unconnected IPv4 socket, and candidate-name comparison without deletion. No external target, network connection, real credential, host service, firewall, cgroup, mount, or production path was used. No feature was skipped.

The plan format is an educational research abstraction, not a production runtime policy language. A false harness signal means only that the bounded probe did not reproduce that effect; it is not universal proof of safety. The grader checks honest transformations and is not a hostile multi-user anti-cheat boundary.
