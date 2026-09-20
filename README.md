# North Echo Agent Security Lab

A hands-on Linux course on **runtime containment for agent workloads**: what a process inherits, what the kernel can restrict, and how to verify that useful work survives those restrictions.

The v2 curriculum begins with terminal/program basics and one small environment-handoff problem, then develops twelve technical modules and an independent batch-runtime capstone. Lessons provide file-access instructions, complete small sources, local explanations, predictions, deliberate failures, repairs, checkpoints, and scoped reset. Independent labs withhold complete implementations, not the interface or prerequisites.

**Release target: v2.0.0-beta.1, for learner review.** Automated validation is not evidence of beginner comprehension. Review pacing, missing connective steps, and delayed recall before calling this a stable teaching release.

No LLM, API key, external target, or production credential is required. This course covers the runtime boundary, not prompt injection or general model-side security. Later synthetic evidence models are explicitly distinguished from real kernel measurements.

## Start here

Use a disposable Linux VM, not your Mac's terminal for exercises. Fedora 44 ARM64 is the preferred new-install baseline on Apple Silicon; Ubuntu 24.04 remains a separate compatibility path. Fedora x86-64 is not claimed from ARM64 results.

On the **Mac host**, with Lima 2.2 or newer:

```bash
git clone --branch v2.0.0-beta.1 --depth 1 https://github.com/north-echo/north-echo-agent-security-lab.git north-echo-beta-source
cd north-echo-beta-source
limactl start --name north-echo-beta deploy/north-echo-fedora.yaml
limactl shell north-echo-beta
```

Use a new instance name. This does not migrate or overwrite an existing `north-echo` VM.

Inside the **Linux guest**:

```bash
cd ~/north-echo
./scripts/linux-preflight
./scripts/attest-course
./lab-start b0.01
cd .student/b0.01
less README.md
```

Press q to leave `less`. Begin with the [learning path](docs/LEARNING_PATH.md) and [beginner chapters](docs/BEGINNER_FIELD_MANUAL.md). Experienced shell users may try the B0 practical first.

The [complete setup guide](docs/VM_SETUP.md) covers manual Fedora/Ubuntu installation, host-versus-guest commands, restarts, private work export, evidence export, and destructive reset warnings. Images and course archives are pinned; package revisions can change and are recorded. Ordinary restarts preserve student work. No default host mount or SSH-agent forwarding is enabled.

## Course path

| Stage | What you learn to explain and verify |
| --- | --- |
| B0 | Locate, read, edit, and run a small program; distinguish output and exit status |
| B1 | Keep useful child behavior while withholding unnecessary parent settings |
| 01–03 | Syscalls, inherited environment/descriptors, namespace views, capability sets, no-new-privileges |
| 04–06 | Structured tool execution, complete traces, path resolution, Landlock, syscall filtering |
| 07–09 | Effective resource ceilings, owned lifecycle, local network mediation, scoped credential use |
| 10 | Compose the controls and preserve effective-state evidence across failure and collection |
| 11 | Repair fixed local model choices while preserving useful work; separate models from enforcement |
| 12 | Account for hinted synthetic dispatch, interpret incomplete evidence, verify and replay known packages |
| Capstone | Ordered independently bounded jobs, ordinary failure continuation, exact teardown, human-reviewed rationale |

The historical Module 12 directory name includes “adaptive adversary,” but its oracle supplies the answer. It is a bounded-dispatch teaching example, not independent vulnerability discovery or an autonomous offensive tool.

## Daily workflow

From the guest course root:

```bash
./lab-start 01.01
./lab-start module-01
./lab-grade module-01
./lab-grade module-01 --mode exam
./lab-status
./lab-reset 01.01 --dry-run
```

`module-01` is the CLI alias for `01.lab`; its workspace is `.student/01.lab`. Guided lessons use observation checkpoints; independent labs use fresh property checks. Practice mode gives lesson references, while exam mode reduces hints.

After saving anything you want to keep, `./lab-reset 01.01 --yes` removes that lesson's work. `./lab-reset module-01 --yes` removes all Module 01 work. `./lab-reset --all --yes` removes all prepared work. These are deletion commands, not harmless navigation. Preview first.

The capstone starts with `./lab-start capstone --cold`; cold start discards an existing capstone attempt. Its human reasoning rubric is separate from the automated result.

## Materials and source truth

The [complete Markdown field manual](docs/FIELD_MANUAL.md) assembles setup, source/version notes, learning path, B0/B1, Modules 01–12, and capstone. The beta release assets include the matching PDF, archive, history bundle, release notes, and checksums. Use artifacts from the same release; the v1.0.2 PDF does not describe v2.

[Source and version notes](docs/SOURCE_TRUTH.md) distinguish documented interfaces, course policy, and observations on a particular guest. Canonical source listings are synchronized into lesson READMEs and the manual. External documentation verifies claims; it does not replace the lesson's explanation.

[Course design](COURSE_DESIGN.md), [architecture](ARCHITECTURE.md), and the [learner-review protocol](docs/dev/LEARNER_PILOT.md) explain the teaching and safety contracts. Human review remains open; no course-duration or retention claim is made.

## Replay and safety

Canonical material lives under `course/` and is checked against its manifest before preparation. Edit only `.student/`. Fresh synthetic fixtures live under `.fixtures/`; owned runtime records under `.runtime/`; metadata-only progress under `.state/`. Reset removes solutions, notes, and fixtures while retaining allowed attempt/result metadata.

Integrity attestation is not immutability against the repository owner. The grader supports honest practice, not hostile anti-cheat. Run only in a disposable VM; keep SELinux/AppArmor enabled, use an ordinary account, and do not introduce real secrets, external targets, or host mounts. Cleanup requires exact ownership, not a name prefix.

## Development and evidence

```bash
python3 scripts/run_tests.py --require-no-skips
./scripts/attest-course
python3 scripts/build_field_manual.py --check
./scripts/linux-preflight
```

Run the strict suite in the supported Linux VM. macOS can check control-plane behavior but cannot validate Linux containment. Ubuntu CI and Fedora VM runs have distinct scopes. [Validation records](validation/) identify exact candidate archives and baselines; [the active beta ledger](docs/dev/V2_REWRITE.md) records outstanding release gates. Historical passes are not silently applied to new code.

This independent project was authored with AI coding assistance, primarily OpenAI Codex and review from Anthropic Claude/Fable, under Christopher Lusk's direction. It contains no employer-internal material. Its teaching quality must be judged through actual learner work, not the authorship method or test count.
