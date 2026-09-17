# North Echo Agent Security Lab

North Echo is a hands-on, replayable Linux containment course for learning agent security by building, observing, breaking, fixing, and verifying. v0.1 fully implements Modules 01-03 and scaffolds Modules 04-12.

This is an independent educational project. It contains no employer-internal material, production credentials, external targets, or instructions to test systems you do not own. Run it only in a disposable Linux VM with synthetic data.

## Start doing the work

On a supported Linux VM:

```bash
sudo apt-get update
sudo apt-get install -y build-essential python3 strace util-linux libcap2-bin procps
git clone YOUR_COPY_OF_THIS_REPOSITORY north-echo-agent-security-lab
cd north-echo-agent-security-lab
./scripts/attest-course
./lab-start 01.01
cd .student/01.01
less README.md
```

Ubuntu 24.04 or Debian 12 with a recent kernel is the recommended baseline. Use an ordinary, non-root user. Unprivileged user namespaces must be enabled for Module 02 and parts of Module 03. Do not disable host security policy to make an exercise work; use the disposable VM described in [docs/VM_SETUP.md](docs/VM_SETUP.md).

## Daily CLI

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
./lab-start capstone --cold           # concept exists; capstone is not implemented in v0.1
```

`module-01` is shorthand for the independent target `01.lab`. Guided lessons are not graded; their job is to make you touch and observe the primitives. Each end-of-module lab uses only interfaces practiced earlier and does not disclose a complete solution.

## What replay means here

Canonical material lives under `course/` and is checked against `course/.course-manifest.json` before a workspace is created. Student work lives only under `.student/`; randomized manifests and canaries live under `.fixtures/`. A reset deletes both, then the next start generates new IDs, names, ports, hostnames, and canaries. `.state/progress.json` retains only starts, resets, grade attempts, mode, pass state, and timestamps - never student source or generated secrets.

The repository deliberately does not claim that chmod makes course content immutable to its owner. It uses separation plus integrity attestation: if canonical content changes, `lab-start` stops and names the changed file. Reinstall or restore from version control rather than blessing accidental edits.

## v0.1 curriculum

| Module | Status | Outcome |
| --- | --- | --- |
| 01 Processes/syscalls/inherited authority | Playable | Trace exec/syscalls; remove environment and FD authority |
| 02 Namespaces | Playable | Compose and verify user/UTS/PID/mount namespaces and procfs |
| 03 Privilege/capabilities/no_new_privs | Playable | Inspect capability state; establish an empty, non-gainable privilege floor |
| 04 Minimal tool-using agent | Scaffold | Local deterministic agent and tool contract |
| 05 Filesystem/Landlock | Scaffold | Path resolution, descriptor-relative access, Landlock |
| 06 seccomp | Scaffold | Measured syscall containment |
| 07 cgroups | Scaffold | Resource controls and safe teardown |
| 08 Network isolation | Scaffold | Mediated egress and redirect reauthorization |
| 09 Credential brokering | Scaffold | Operation-scoped, fake capabilities |
| 10 Complete runtime | Scaffold | Correctly ordered composed controls |
| 11 Break/fix research | Scaffold | Seeded variants and hardened counterparts |
| 12 Adaptive adversary | Scaffold | Calibrated agent studies and Boundary Atlas graduation |

The complete v0.1 course manual is [docs/MANUAL_MODULES_01_03.md](docs/MANUAL_MODULES_01_03.md). Architecture and pedagogy are documented in [ARCHITECTURE.md](ARCHITECTURE.md) and [COURSE_DESIGN.md](COURSE_DESIGN.md).

## Development and verification

```bash
python3 -m unittest discover -s tests -v
./scripts/attest-course
```

Platform tests exercise start/resume, randomized replay, reset scopes, dry-run, integrity rejection, path safety, state retention, and grader failure behavior. Kernel exercises and Module 02/03 graders require Linux; a non-Linux host can test the control plane but cannot validate namespace or capability behavior.
