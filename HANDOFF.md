# Codex hand-off: build the complete North Echo course

This file is the authoritative continuation brief for moving development into a Codex project attached to a disposable Linux VM.

## Outcome

Continue the existing repository from the v0.1 foundation through a complete twelve-module course and a cold-start capstone. Preserve the established platform contracts: hands-on first, complete line-by-line teaching, randomized replay, external property grading, safe teardown, no retained student solution after reset, and no real credentials or external targets.

The next task should work in this repository rather than regenerate it from a specification.

## Current checkpoint

- Project: **North Echo Agent Security Lab**
- Source checkpoint: commit `8ba68bb` plus the hand-off commit that contains this file
- Modules 01-03: fully authored in v0.1, with nine guided lessons and three independent labs
- Modules 04-12: design scaffolds only; a scaffold is a reserved direction, not a playable module
- Platform lifecycle: start, status, grade, lesson/module/all reset, dry-run cleanup, randomized fixtures, practice/exam modes, and metadata-only progress are implemented
- Field manual: Modules 01-03 have a self-contained manual with complete guided source, line-by-line explanations, expected observations, troubleshooting, labs, integrated model, and glossary
- Existing automated control-plane result before hand-off: 12 tests passing and course attestation passing
- Remaining baseline work: run and record the actual namespace, capability, cleanup, and grader matrix on the target Linux VM

The current source was assembled and control-plane tested on macOS. That proves repository logic, not Linux kernel behavior. Linux validation is the first hand-off gate.

## First task in the Linux project

1. Read `AGENTS.md` and the documents it lists.
2. Run `./scripts/linux-preflight` as an ordinary non-root user.
3. Run `python3 -m unittest discover -s tests -v` and `./scripts/attest-course`.
4. Execute `docs/LINUX_VALIDATION.md` for Modules 01-03, including replay and cleanup checks.
5. Fix genuine portability or kernel-behavior defects without weakening safety checks.
6. Record the distribution, kernel, architecture, tool versions, results, and any unavailable feature.
7. Only after the v0.1 Linux gate passes, begin Module 04.

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

Implement `./lab-start capstone --cold` with a fresh unlabeled objective, randomized synthetic services and data, no guided solution material in the workspace, independent multi-layer grading, and complete reset. Every capstone variant must be solvable only with skills practiced in Modules 01-12.

## Per-module acceptance gate

A module is complete only when every item in `docs/MODULE_ACCEPTANCE_TEMPLATE.md` passes. In brief:

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
