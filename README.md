# North Echo Agent Security Lab

A hands-on, replayable Linux course on **runtime containment for agent workloads**: the kernel and userspace controls that bound what a tool-using process can touch, no matter what a model tells it to do. Twelve modules and a cold capstone cover process authority, namespaces, capabilities, Landlock, seccomp, cgroups, network and credential brokering, composed runtimes, and break/fix research.

**Scope.** This course teaches the *runtime* side of agent security - the boundary between an agent process and the host. It deliberately does not cover model-side attack surface such as prompt injection, tool-schema policy, or output handling. No LLM is required or invoked during the exercises. The "agent" in Modules 04 and 09-12 is a deterministic local action loop, so every observation is reproducible.

**How it was built.** Course content and platform code were authored with AI coding agents - primarily OpenAI Codex, with a v1.0.1 review by Anthropic Claude/Fable - under Christopher Lusk's direction, then kernel-validated on disposable Ubuntu 24.04 systems. Validation records under `validation/` are from those runs.

This is an independent educational project. It contains no employer-internal material, production credentials, external targets, or instructions to test systems you do not own. Run it only in a disposable Linux VM with synthetic data. The published course has Ubuntu 24.04 validation on x86-64 and arm64. Unreleased changes and their exact validation coverage are tracked in [the audit implementation record](docs/dev/AUDIT_IMPLEMENTATION.md); do not apply an older release's evidence to newer code.

## Start doing the work

On a macOS host with Lima 2.2 or newer, create the pinned disposable appliance without sharing any host directory:

```bash
git clone https://github.com/north-echo/north-echo-agent-security-lab.git
cd north-echo-agent-security-lab
limactl start --name north-echo deploy/north-echo.yaml
limactl shell north-echo
cd ~/north-echo
./lab-start 01.01
cd .student/01.01
less README.md
```

The appliance pins its Ubuntu 24.04 cloud image and course release by checksum, installs the same package manifest used by CI, validates the course before declaring itself ready, and preserves student work across ordinary VM restarts. To return to a known-clean baseline, delete and recreate the VM. See [Disposable Linux VM setup](docs/VM_SETUP.md) for the complete lifecycle and evidence-export commands.

On a supported Linux VM:

```bash
sudo apt-get update
sudo apt-get install -y git ca-certificates
git clone https://github.com/north-echo/north-echo-agent-security-lab.git
cd north-echo-agent-security-lab
xargs sudo apt-get install -y < deploy/ubuntu-packages.txt
./scripts/linux-preflight
./scripts/attest-course
./lab-start 01.01
cd .student/01.01
less README.md
```

Ubuntu 24.04 on x86-64 and arm64 is the validated baseline. Debian 12 is a candidate baseline awaiting acceptance testing. Use an ordinary, non-root user. If preflight fails, follow the narrowly scoped disposable-VM setup in [docs/VM_SETUP.md](docs/VM_SETUP.md) before starting a lesson.

## Daily CLI

Begin with the [entry diagnostic and learning path](docs/LEARNING_PATH.md). It
includes preparation, faded exercises, cumulative checkpoints after Modules 03,
06, and 09, and a separate reasoning rubric for capstone graduation.

```bash
./lab-start 01.01                    # create or resume one guided lesson
./lab-start module-01                # create or resume Module 01 independent lab
./lab-start 02.01 --mode exam        # workspace whose later grading defaults to exam mode
./lab-grade module-01                # fresh property-based evaluation fixture
./lab-grade module-01 --mode exam    # reduced diagnostic detail
./lab-status
./lab-reset 01.01 --yes              # remove one lesson workspace and fixtures
./lab-reset module-01 --yes          # reset all Module 01 workspaces
./lab-reset --all --yes              # reset all disposable work
./lab-reset 01.01 --dry-run          # show cleanup without changing anything
./lab-start capstone --cold           # fresh unlabeled graduation workspace
```

`module-01` is shorthand for the independent target `01.lab`. Guided lessons are not graded; their job is to make you touch and observe the primitives. Each end-of-module lab uses only interfaces practiced earlier and does not disclose a complete solution.

### How command blocks are taught

Guided lessons do not leave a command block unexplained. Immediately after a meaningful block, a **Line by line** section explains each command, important argument, shell operator, variable expansion, and expected state change. Guided source files also contain comments at the security-sensitive lines. Independent module labs still withhold complete solutions, but their interface and test commands are explained without revealing the implementation.

## What replay means here

Canonical material lives under `course/` and is checked against `course/.course-manifest.json` before a workspace is created. Student work lives only under `.student/`; randomized manifests and canaries live under `.fixtures/`. A reset deletes both, then the next start generates new IDs, names, ports, hostnames, and canaries. `.state/progress.json` retains only attempt counts, modes, timestamps, the latest result, failed property names, and historical achievement - never student source or generated secrets. Status distinguishes the current attempt, the last grade, and whether the target has ever passed. Lifecycle commands serialize state changes so parallel terminals do not lose updates.

The repository deliberately does not claim that chmod makes course content immutable to its owner. It uses separation plus integrity attestation: if canonical content changes, `lab-start` stops and names the changed file. Reinstall or restore from version control rather than blessing accidental edits.

## Curriculum status

| Module | Status | Outcome |
| --- | --- | --- |
| 01 Processes/syscalls/inherited authority | Playable | Trace exec/syscalls; remove environment and FD authority |
| 02 Namespaces | Playable | Compose and verify user/UTS/PID/mount namespaces and procfs |
| 03 Privilege/capabilities/no_new_privs | Playable | Inspect capability state; establish an empty, non-gainable privilege floor |
| 04 Minimal tool-using agent | Playable | Deterministic local agent, structured argv tools, complete action trace, and ambient-authority repair |
| 05 Filesystem/Landlock | Playable | Path resolution, descriptor-relative access, Landlock, and inherited-FD hygiene |
| 06 seccomp | Playable | Measured syscall surface, failure actions, native default-deny filtering |
| 07 cgroups | Playable | CPU, memory/OOM, PID controls, and safe transient-unit teardown |
| 08 Network isolation | Playable | Empty network namespace, Unix-socket mediation, run binding, and redirect reauthorization |
| 09 Credential brokering | Playable | Fake ambient-credential repair, operation capabilities, lifetime, replay, and deputy binding |
| 10 Complete runtime | Playable | Ordered cgroup, namespace, privilege, Landlock, seccomp, broker, attestation, and teardown composition |
| 11 Break/fix research | Playable | Seeded variants, bounded evidence, invariant diagnosis, and hardened counterparts |
| 12 Adaptive adversary | Playable | Scripted baseline, bounded adaptation, calibrated interpretation, and experiment packaging |

The current field-manual source is [Markdown](docs/FIELD_MANUAL.md). The [published v1.0.2 PDF](https://github.com/north-echo/north-echo-agent-security-lab/releases/download/v1.0.2/FIELD_MANUAL.pdf) belongs to that release and does not contain unreleased changes. Source chapters begin with [Modules 01-03](docs/MANUAL_MODULES_01_03.md) and continue through the individual Module 04-12 manuals. They are self-contained: commands, complete guided source listings, line-by-line explanations, expected observations, troubleshooting, checkpoints, lab contracts, and reference material are included rather than delegated to external reading. Canonical-source includes and CI detect stale listings. Architecture and pedagogy are documented in [ARCHITECTURE.md](ARCHITECTURE.md) and [COURSE_DESIGN.md](COURSE_DESIGN.md).

The revised cold capstone assesses ordered batches with independent resource budgets,
continuation after ordinary job failure, and exact teardown. It uses a different
interface from Module 10 and adds a separately reviewed reasoning rubric.

Gate A Linux validation is recorded in [validation/RESULTS.md](validation/RESULTS.md); module records are under `validation/module-NN/`, tranche records cover v0.2 through v0.4, and [Gate D](validation/gate-d/RESULTS.md) records the cold capstone and v1.0 acceptance run. Development acceptance criteria live in [docs/dev/MODULE_ACCEPTANCE_TEMPLATE.md](docs/dev/MODULE_ACCEPTANCE_TEMPLATE.md). `AGENTS.md` keeps the safety, replay, and field-manual standards persistent for future tasks.

## Development and verification

```bash
python3 scripts/run_tests.py
./scripts/attest-course
python3 scripts/build_field_manual.py --check
./scripts/linux-preflight
```

Platform tests exercise start/resume, randomized replay, reset scopes, dry-run, integrity rejection, path safety, state retention, and grader failure behavior. Kernel exercises and Module 02/03 graders require Linux; a non-Linux host can test the control plane but cannot validate namespace or capability behavior.

On a supported Linux validation VM, use `python3 scripts/run_tests.py --require-no-skips`.
Skipped kernel tests are not a successful full-course validation.
