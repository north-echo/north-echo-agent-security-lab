# North Echo Agent Security Lab v1.0.1 release specification

Status: accepted

Scope: repository framing, release hygiene, continuous architecture coverage, development-document organization, and one Landlock content correction

Target: `north-echo/north-echo-agent-security-lab` main, tagged `v1.0.1`

This specification incorporates the Claude/Fable review supplied on 2026-09-18 and the implementation review that followed it.

## 1. Summary

v1.0.0 is technically sound. v1.0.1 improves how its scope and evidence are communicated, removes a generated PDF from Git, makes releases version-aware, runs continuous validation on x86-64 and arm64, and corrects the Module 05 treatment of filesystem rights added after Landlock ABI 3.

The course teaches runtime containment for agent workloads. It does not claim to teach model-side security, require an LLM, or provide a hostile local-user boundary.

## 2. Work items

| ID | Item | Release | Course manifest |
| --- | --- | --- | --- |
| F1 | Reframe README scope and disclose AI-assisted authorship | v1.0.1 | no |
| F2 | Align platform and root-marker versions | v1.0.1 | no |
| F3 | Update repository metadata and publish PDF only as a release asset | v1.0.1 | no |
| F4 | Run Ubuntu 24.04 CI continuously on x86-64 and arm64 | v1.0.1 | no |
| F5 | Move development-process documents and replace the build-era roadmap | v1.0.1 | no |
| F6 | Handle build-time-known Landlock filesystem rights through ABI 9 | v1.0.1 | yes |
| F7 | Deepen Module 12 | post-v1.0.1 | yes |

## 3. Framing, release hygiene, and CI

The README first screen must state:

- the course is about runtime containment for agent workloads;
- model-side issues such as prompt injection and tool-schema policy are outside its scope;
- no LLM is invoked during exercises;
- AI coding agents assisted authorship under human direction;
- validation ran only in disposable Linux environments with synthetic data.

The clone command must use the public GitHub URL. The PDF link must reference the `v1.0.1` release asset. No `YOUR_COPY` placeholder may remain.

The public repository description is:

> Hands-on Linux containment course for agent runtimes: Landlock, seccomp, namespaces, cgroups, brokers

Repository topics are `linux-security`, `landlock`, `seccomp`, `namespaces`, `cgroups`, `sandboxing`, `agent-security`, and `course`.

`.north-echo-root` and `scripts/northecho/__init__.py` report v1.0.1. `docs/FIELD_MANUAL.md` remains tracked, while generated PDFs are ignored and published as release assets.

The release builder must:

1. require a clean tree whose `HEAD` is the requested tag;
2. verify the tracked field manual is synchronized with its module sources;
3. create the source archive and complete Git bundle;
4. build the PDF directly from the tagged Markdown source;
5. select release notes using the requested version;
6. emit SHA-256 checksums for every distributed file.

CI uses a non-fail-fast matrix with `ubuntu-24.04` and `ubuntu-24.04-arm`. Each leg records its kernel, distribution, and Debian architecture, then runs the existing tests, attestation, preflight, and empty-runtime check. GitHub's standard `ubuntu-24.04` runner is x86-64; the matrix makes the already mixed manual/CI evidence continuously reproducible on both architectures.

## 4. Development-document organization

Move these files under `docs/dev/`:

- `HANDOFF.md`;
- `CODEX_HANDOFF_PROMPT.md`;
- `MODULE_ACCEPTANCE_TEMPLATE.md`.

`AGENTS.md` stays at the repository root because coding agents discover it there. Its first line identifies it as development-process material rather than course content. Update path references in the moved documents, README, tests, validation records, and repository instructions.

The roadmap becomes a concise completed-release history plus a post-v1.0.1 list. The root should contain only learner-facing overview documents, `AGENTS.md`, directories, and CLI entry points.

## 5. Landlock filesystem-right coverage

### Problem

Landlock restricts filesystem actions listed in `handled_access_fs`. Apart from the historical `LANDLOCK_ACCESS_FS_REFER` exception, an omitted right remains allowed. The Module 05 launcher stopped at ABI 3, so it did not handle device IOCTL at ABI 5 when newer build headers and kernels exposed that right.

Runtime ABI detection cannot name a constant that was absent when the source was compiled. The correct guarantee is therefore not "every right the runtime ABI supports." It is "every filesystem right explicitly known to this source and build headers that the detected ABI supports."

### Code

`supported_rights()` retains ABI 1 rights and conditionally adds:

- `LANDLOCK_ACCESS_FS_REFER` for ABI 2+;
- `LANDLOCK_ACCESS_FS_TRUNCATE` for ABI 3+;
- `LANDLOCK_ACCESS_FS_IOCTL_DEV` for ABI 5+ when the header defines it;
- `LANDLOCK_ACCESS_FS_RESOLVE_UNIX` for ABI 9+ when the header defines it.

Preprocessor guards preserve compilation against older Ubuntu 24.04 headers. The launcher prints the detected ABI before policy creation so the learner can compare runtime support with the source's explicit gates.

### Teaching and grading

Lesson 05.03 and the Module 05 manual include an "Unhandled means allowed" section, the ABI diagnostic, a source-gate checkpoint, and the build-time-known limitation. The independent-lab contract uses the same precise guarantee.

The Ubuntu 24.04 external grader continues to observe path confinement, protected-open denial, execution, and inherited-descriptor hygiene. ABI 5 device IOCTL and ABI 9 pathname UNIX-socket handling are stated source properties unless a safe targeted fixture and matching baseline are present. The acceptance template requires such unobservable properties to be identified and justified rather than implied by a generic grader pass.

Acceptance requires:

- warning-free C11 compilation on the supported Ubuntu headers;
- synchronized canonical lesson, Module 05 manual, and complete field manual;
- an updated course manifest reviewed as a content change;
- full tests, attestation, preflight, and both architecture CI legs;
- a dated Module 05 validation addendum;
- a regenerated and visually inspected PDF.

## 6. Post-v1.0.1 Module 12 depth

Module 12 expansion remains outside v1.0.1:

- an attestation-driven probe-selection lesson using Module 10 evidence;
- a true-negative versus false-negative comparison using identical bounded budgets against hardened and seeded-weakness targets.

Each future lesson needs exact commands, complete small source, local line-by-line teaching, a deliberate failure and repair, expected observations, grader-visible packaging properties, and Linux evidence.

## 7. Release procedure

1. Merge framing, release hygiene, metadata, and the architecture matrix; require both CI legs green.
2. Merge document reorganization and Landlock content; regenerate the manifest and field manual; require both CI legs green.
3. Verify main, create annotated tag `v1.0.1`, and push it.
4. Run `./scripts/build-release v1.0.1` from the clean tagged commit.
5. Verify `SHA256SUMS`, the Git bundle, source-archive contents, and rendered PDF pages.
6. Publish the GitHub release and attach the archive, bundle, Markdown manual, PDF manual, release notes, and checksums.

## 8. Out of scope

- Adding an LLM or network dependency to the student path.
- Changing grader semantics for Modules 01-11.
- Claiming a hostile local-user boundary for the control plane.
- Module 12 expansion or a Debian 12 validation baseline.
