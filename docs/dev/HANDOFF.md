# Codex hand-off: build the complete North Echo course

This file is the authoritative continuation brief for moving development into a Codex project attached to a disposable Linux VM.

## Outcome

Continue the existing repository from the v0.1 foundation through a complete twelve-module course and a cold-start capstone. Preserve the established platform contracts: hands-on first, complete line-by-line teaching, randomized replay, external property grading, safe teardown, no retained student solution after reset, and no real credentials or external targets.

The next task should work in this repository rather than regenerate it from a specification.

## Current checkpoint

**User-authorized v2.0.0-beta.1 learner-review release (2026-09-20).**
The full rewrite supersedes the historical B0/B1-only restriction below.
Fedora 44 ARM64 is the preferred new-install baseline; Ubuntu remains available.
The user's original learner VM has not been modified.

B0/B1, all 36 numbered guided lessons, module introductions, independent
practicals, capstone, setup, learning path, and assembled manual are reconciled.
The approved B0.02 source remains unchanged. Exact file access, local source
explanations, failure/repair/checkpoint, scope limits, and reset guide the rewrite.
See `docs/SOURCE_TRUTH.md` for version-qualified primary references and the
claim/mechanism/evidence map. This is not a formal audit or human-learning result.

New regressions replay documented guided commands, all 15 independent preparation
paths, and ownership/cleanup failures. The final candidate and artifact checks
are recorded in `validation/beta-20260920/RESULTS.md`; earlier per-module records
retain their own exact archive hashes and counts. Never transfer old counts to
new source. Both installers now pin the beta and accept strict beta version names.

The 271-page candidate PDF has a linked contents section, bookmarks, complete
sources, and version-pinned repository links. All pages were rendered for layout
inspection, representative pages reviewed at reading resolution, and automated
text/navigation/geometry checks passed. Recheck the final release-built PDF.

Publication gates still open at this checkpoint: final candidate results,
commit/push and dual-architecture CI, tagged artifact build/publication, then
clean installation of the actual published beta archive with preservation,
negative readiness, and plain-mode evidence export. The earlier Fedora v1.0.2
bootstrap passed those deployment checks but cannot certify the beta archive.
The current ledger is `docs/dev/V2_REWRITE.md`.

Stable v2.0.0 requires learner walkthrough, independent practice, feedback repair,
and delayed replay; no automated suite can establish those outcomes. Preserve
synthetic defensive scope and do not expand autonomous offensive workflows.

### Earlier pilot checkpoint (historical; scope restriction superseded above)

Beginner pilot mechanically accepted: `docs/dev/BEGINNER_REBUILD.md` describes a bounded
B0/B1 pilot based on the user's learning feedback and read-only review of their
successful course references. `docs/BEGINNER_FIELD_MANUAL.md` is the learner
entry. Preserve the numbered track. Do not extend the rebuild to all modules
until the learner has tried the first practical. Do not confuse Linux tests
with that human acceptance gate. The default appliance remains pinned to
v1.0.2; use a separate working-copy transfer for unreleased pilot work.
Initial evidence is `validation/beginner-pilot-20260919/RESULTS.md`. The subsequent
depth/source pass is in `validation/beginner-pilot-20260919/DEPTH_AND_SOURCES.md`:
Ubuntu 24.04.5 arm64, 76 tests passing without skips, attestation/manual
synchronization passing, and 33 preflight checks passing. Claim-level review:
`docs/dev/BEGINNER_SOURCE_REVIEW.md`. File access and read/edit/run distinctions
are explicit; text and exit-status claims have precise limits. Human acceptance
is still pending, and Modules 01-12 have not had this new claim-level review.

The user positively reviewed the revised B0.02 Desktop copy on 2026-09-19;
use that level of file-access guidance and explanation as the depth target.
This is prose feedback, not yet an independent-practical or delayed-replay pass.
The separate Fedora 44 ARM64 trial passed 76 strict tests and 33 preflight
checks with SELinux enforcing and no course-code changes. Record and remaining
gates: `validation/fedora-trial-20260919/RESULTS.md`. Experimental OS bootstrap:
`deploy/experimental/`. Ubuntu remains the default; do not infer authority to
migrate, publish, or extend support. Fedora `/tmp` is volatile: keep course work
in the guest home. The trial VM is stopped and its test lesson was reset.

Unreleased audit implementation is tracked in `docs/dev/AUDIT_IMPLEMENTATION.md`.
It hardens cleanup and grading, introduces behavioral preflight and strict tests,
replaces the copied single-job capstone with ordered-batch transfer assessment,
adds offline evidence interpretation and portable replay, synchronizes manual
listings from canonical sources, and adds a diagnostic/checkpoint/pilot pathway.
The historical results below belong to the published release; they are not
validation claims for the changed working tree. Follow the audit record for its
new evidence and remaining release/human-study gates.

- Project: **North Echo Agent Security Lab**
- Source checkpoint: published v1.0.2 release at tagged commit `036c8e6376102a7dd5b0066ed77fe903429cea06`, with the pinned Lima appliance and completed deployment validation
- Modules 01-12: fully authored and Linux-validated, with thirty-six guided lessons and twelve independent labs
- Platform lifecycle: start, status, grade, lesson/module/all reset, dry-run cleanup, randomized fixtures, practice/exam modes, and metadata-only progress are implemented
- Field manual: Modules 01-12 have synchronized, self-contained chapters with complete guided source, local explanations, expected observations, troubleshooting, labs, and security models
- Published v1.0.2 automated result: 44 tests passing, course attestation passing, and continuous Ubuntu 24.04 CI passing on x86-64 and arm64
- Gate A record: `validation/RESULTS.md`; no required Gate A step was skipped
- Module 04 record: `validation/module-04/RESULTS.md`; all module acceptance items passed
- Module 05 record: `validation/module-05/RESULTS.md`; all module acceptance items passed
- Module 06 record: `validation/module-06/RESULTS.md`; all module acceptance items passed
- Module 07 record: `validation/module-07/RESULTS.md`; all module acceptance items passed
- Module 08 record: `validation/module-08/RESULTS.md`; all module acceptance items passed
- Module 09 record: `validation/module-09/RESULTS.md`; all module acceptance items passed
- Module 10 record: `validation/module-10/RESULTS.md`; all module acceptance items passed
- Module 11 record: `validation/module-11/RESULTS.md`; all module acceptance items passed
- Module 12 record: `validation/module-12/RESULTS.md`; all module acceptance items passed
- Tranche 3 / v0.4 record: `validation/tranche-03/RESULTS.md`; Modules 10-12 replay and teardown passed
- Tranche 1 / v0.2 record: `validation/tranche-01/RESULTS.md`; end-to-end replay and teardown passed
- Tranche 2 / v0.3 record: `validation/tranche-02/RESULTS.md`; Modules 07-09 replay and teardown passed
- Gate D / v1.0 record: `validation/gate-d/RESULTS.md`; cold capstone replay, external grading, reset, manuals, and release workflow passed

The current source was assembled on macOS and kernel-validated in a disposable Ubuntu 24.04.4 LTS arm64 Lima VM. macOS results prove only control-plane behavior; the retained Module 08 record distinguishes Linux evidence.

## Completed Linux baseline

Gate A passed on Ubuntu 24.04.4 LTS arm64. The run covered the non-destructive preflight, automated tests, attestation, all nine guided lessons, all three independent labs in practice and exam modes, randomized replay, every reset scope, cleanup containment, and final empty-state inspection. Focused fixes corrected Lesson 03.02's post-mapping `setgroups(2)` assumption and Module 02's namespace-local `NSpid` grading assumption.

Gate D is complete: the cold capstone, complete Markdown/PDF manuals, release notes, and reproducible release-artifact workflow are implemented and Linux-validated. Future work is maintenance, additional architecture baselines, or post-v1 course expansion rather than an unfinished core deliverable.

The v1.0.1 maintenance release clarifies the runtime-containment scope, moves development-process material under `docs/dev/`, makes PDF delivery a reproducible release-only artifact, adds continuous x86-64 and arm64 validation, and extends the Module 05 lesson through build-time-known Landlock filesystem rights at ABI 9. The exact scope and deferred Module 12 work are in `docs/dev/SPEC_v1.0.1.md`.

The v1.0.2 maintenance release adds a pinned Ubuntu 24.04 Lima appliance for macOS, plain-mode isolation from host mounts and agent forwarding, idempotent checksum-verified course installation, correct-user systemd lingering, a shared CI/package manifest, readiness probing, and SSH-based evidence export. Its acceptance plan and retained pre-release evidence are under `validation/deployment-v1.0.2/`.

Do not start by rewriting the platform. Preserve working behavior and add focused tests for every corrected defect.

## Delivery plan

### Gate A: Linux baseline for Modules 01-03

Prove all existing lessons and graders on the disposable VM. Exercise lesson, module, and all reset scopes. Confirm fresh canaries after reset, progress retention without source retention, exam hint reduction, canonical-content rejection, and cleanup containment.

### Tranche 1: Modules 04-06

- **04 Minimal tool-using agent:** deterministic local policy/model fixture; structured argv tools; complete action trace; deliberate ambient-authority failure; no API key.
- **05 Filesystem confinement:** traversal and symlink failures; descriptor-relative access; `openat2`; Landlock ABI detection and rights selection; pre-opened-FD limitation.
- **06 seccomp:** measured syscall surface; errno and kill actions; architecture check; default-deny filter; alternate-syscall test; explicit explanation that seccomp is not pathname authorization.

Gate the tranche with replay tests, property graders, safe cleanup, and full manual chapters before beginning Module 07.

### Tranche 2: Modules 07-09

- **07 cgroups v2:** delegated subtree; CPU, memory, and PID controls; pressure/OOM observations; process-tree and subtree teardown.
- **08 network isolation:** synthetic local services; network namespace; direct-egress denial; brokered egress; DNS and redirect reauthorization; run binding.
- **09 credential brokering:** fake ambient credential failure; operation-scoped capability; audience, run, expiry, and replay binding; confused-deputy repair.

Extend the runtime registry before lessons can leave any PID, mount, cgroup, namespace helper, veth/nftables object, or service behind. Teardown must never mutate unrelated host resources.

### Tranche 3: Modules 10-12

- **10 complete runtime:** compose controls in a security-correct launch order; prove effective state; deterministic teardown; explain cross-layer dependencies.
- **11 break/fix research:** randomized seeded weakness; non-agent reproducer; invariant identification; repair; hardened counterpart; evidence over exploit theatrics.
- **12 adaptive adversary:** bounded local adversary; scripted baseline; calibrated interpretation of non-discovery; package a candidate experiment for Boundary Atlas without making that methodology a prerequisite.

### Gate D: cold capstone and v1.0

**Complete.** `./lab-start capstone --cold` creates a fresh unlabeled objective with randomized synthetic services and data, no guided solution material in the workspace, independent multi-layer grading, and complete reset. Every capstone variant is solvable with skills practiced in Modules 01-12.

## Per-module acceptance gate

A module is complete only when every item in `docs/dev/MODULE_ACCEPTANCE_TEMPLATE.md` passes. In brief:

- at least three substantive guided lessons;
- exact commands and complete small code listings;
- local line-by-line explanations and expected observations;
- at least one intentional failure and verified repair per lesson;
- one independent lab that does not reveal a solution;
- randomized start and fresh evaluation fixtures;
- practice and exam grading against security properties;
- lesson, module, and all reset coverage;
- fail-closed registered cleanup for every owned runtime resource;
- automated platform and grader tests;
- Linux execution evidence;
- a full field-manual chapter synchronized with the shipped files.

No word-count target substitutes for pedagogical completeness. The manual is a first-class product surface.

## Security boundaries

- Use only a disposable Linux VM and an ordinary non-root account except for narrowly documented setup steps.
- Use only loopback or isolated synthetic services created by the lab.
- Use fake credentials generated per run.
- Do not target the host, LAN, cloud metadata service, employer systems, or public services.
- Do not disable host security controls to force an exercise to pass.
- Treat cleanup and reset code as safety-critical. Validate ownership before mutation and test hostile registry entries.
- Keep the lab's anti-cheat claim modest: it teaches and checks honest work; it is not a hostile multi-user boundary.

## Evidence required at every gate

Produce a short validation record containing:

- commit tested;
- distribution, kernel, architecture, and relevant package versions;
- automated-test and attestation results;
- lesson/lab/grader targets exercised;
- reset and cleanup results;
- feature skips with exact reasons;
- known defects or residual risks;
- confirmation that no real credential, external target, or retained student solution was used.

If evidence is missing, label the result unvalidated rather than inferred.

## Final deliverables

- complete repository with Modules 01-12 and cold capstone;
- source and grader tests;
- Linux validation records for supported baselines;
- Markdown field manual for the full course;
- rendered and visually checked PDF manual;
- concise setup, architecture, safety, course-design, and troubleshooting documentation;
- reproducible release archive, Git history bundle, checksums, and release notes.

The final student experience should remain simple:

```bash
./lab-start 04.01
./lab-grade module-04
./lab-reset module-04 --yes
./lab-start capstone --cold
```

The implementation may become sophisticated. The learner-facing workflow should not.
