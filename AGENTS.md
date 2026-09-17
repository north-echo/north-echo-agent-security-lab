# North Echo repository instructions

These instructions apply to every Codex task working in this repository.

## Mission

Build North Echo Agent Security Lab into a complete, hands-on Linux containment course. The course is independent educational work. It must never require employer-internal material, personal or production credentials, or access to an external target.

The learner should spend most of their time typing commands, compiling small programs, observing kernel-visible state, triggering a deliberate failure, repairing it, and verifying the repair. AI is an optional tutor or debugger; it is never part of the required student workflow.

## Read before changing the course

Read these files in order:

1. `HANDOFF.md`
2. `README.md`
3. `COURSE_DESIGN.md`
4. `ARCHITECTURE.md`
5. `ROADMAP.md`
6. `docs/MODULE_ACCEPTANCE_TEMPLATE.md`
7. `docs/LINUX_VALIDATION.md`

For work on Modules 01-03, also read `docs/MANUAL_MODULES_01_03.md`. For a later module, read every earlier module that supplies a skill the new module assumes.

## Non-negotiable teaching contract

Never cut corners on the field manual. A playable module is incomplete until its manual chapter is complete and synchronized with the actual lesson files, starter code, interface, fixtures, grader behavior, and expected observations.

Every guided lesson must include:

- exact commands and complete small source listings;
- a local line-by-line explanation immediately after each meaningful block;
- expected output patterns and an explanation of what the observation proves;
- an intentional mistake or incomplete control, followed by a repair;
- a checkpoint that verifies effective state rather than trusting command intent;
- troubleshooting that stays inside the disposable-VM threat model.

An independent module lab may explain the interface, inputs, commands, and security properties, but it must not reveal a complete implementation. Practice grading reports failed properties with useful lesson references. Exam grading reports the failed properties with reduced hints.

Primary references and man pages may be linked as optional depth. They must not replace the local explanation needed to complete a lesson.

## Replay and safety contract

- Canonical content stays under `course/` and is covered by `course/.course-manifest.json`.
- Student edits stay under `.student/`; randomized material stays under `.fixtures/`; owned runtime resources stay under `.runtime/`; metadata-only progress stays under `.state/`.
- Reset must remove student work and generated fixtures at lesson, module, and all scopes while retaining only allowed attempt/pass metadata.
- Every replay rotates synthetic identifiers, names, ports, paths, and canaries without changing the learning objective.
- Cleanup is fail-closed. Every PID, mount, cgroup, network object, service, and temporary path must be registered and proven to belong to the lab before it can be changed or removed.
- Do not add broad recursive deletion, wildcard teardown, host firewall mutation, host cgroup mutation, or cleanup based only on a name prefix.
- Exercises run only in a disposable Linux VM using synthetic local services and fake credentials.

## Definition of done

Use `docs/MODULE_ACCEPTANCE_TEMPLATE.md` for every module. A module is not playable merely because lesson prose or starter files exist. It needs guided lessons, an independent lab, randomized fixtures, practice and exam grading, safe reset/cleanup, automated tests, a complete manual chapter, and Linux evidence.

Work in the roadmap tranches. Finish and validate the tranche acceptance gate before beginning the next one. Modules 01-03 must receive a real Linux baseline run before the course is described as Linux-validated.

## Required checks

From the repository root:

```bash
python3 -m unittest discover -s tests -v
./scripts/attest-course
./scripts/linux-preflight
```

On Linux, also run the matrix in `docs/LINUX_VALIDATION.md` and retain only synthetic test logs under a dedicated validation directory. Never commit generated canaries, student solutions, real credentials, or host-identifying data.

After changing canonical course material, run `./scripts/update-course-manifest`, inspect the manifest diff, then rerun all checks. Do not update the manifest merely to silence an unexplained integrity failure.

## Claims and hand-off discipline

State exactly which checks ran, on which distribution and kernel, and which checks could not run. Do not convert a macOS control-plane test into a Linux-kernel validation claim. Do not call Modules 04-12 complete until each module meets its acceptance checklist. Keep `HANDOFF.md` and `ROADMAP.md` current at every tranche boundary.
