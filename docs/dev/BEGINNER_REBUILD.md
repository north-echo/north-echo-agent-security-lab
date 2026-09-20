# Beginner rebuild: bounded pilot

## Decision and evidence

The user reported that the existing exercises did not build understanding for
a newcomer, and identified RH124/RH134 9.3 student workbooks as courses that had
worked for them. Technical validation of our existing course does not refute
that feedback. Preserve the twelve-module reference track while testing a
different entry experience; do not scale another untested teaching template.

Read-only reference review covered the supplied workbooks' exercise-method
introduction, topic progression, concept presentations, guided exercises,
independent labs, feedback/reset instructions, and separate solutions. Useful
examples are RH124 printed pages xviii, 30-32, 40-46, 68-71 and RH134 printed
pages 2-8, 29-30 (PDF page indices differ). Two representative pages were also
rendered to inspect the separation of outcomes, preparation, and task steps.
These are teaching-design references, not course content to redistribute.
The PDFs, extracted text, imagery, exercise datasets, solutions, and wording
are not included in this repository. North Echo is independent, not affiliated
with or endorsed by Red Hat.

The useful distinction is not "commands are bad." Explicit worked examples
can teach when explanation precedes action, practice varies the circumstances,
and assessment withdraws support only after the required skills are practiced.

## Pilot design

- B0 is a test-out/refresher path: files and paths; program/process and status;
  one small Python change; independent report reader.
- B1 is the first security problem: observe unnecessary environment inheritance;
  compare full/empty/selected handoffs; repair a changed-key case; independently
  preserve useful work while withholding unneeded parent settings.
- Every guided lesson has outcomes, concepts before commands, a known starting
  location, purposeful tasks, source explanations, predictions, observed failure,
  repair verification, a checkpoint, troubleshooting, and scoped reset.
- The practical contracts do not disclose complete implementations. Practice
  grading maps failures to lessons; exam mode reduces hints. Source shape is not
  graded. Human explanations and delayed replay remain part of assessment.
- No new kernel controls or C are introduced in this slice. B0 is not a full
  Linux or Python course. No promise is made that this fixes pacing in Modules
  01-12. Decide the next slice only after the user's walkthrough.

## Functional acceptance

Required: synchronized canonical README/manual listings; canonical attestation;
starter failures; valid implementation passes; empty-environment, single-key,
hard-coded-style, output-only, and swallowed-status regressions rejected;
fresh grading inputs; resume preserves edits; replay rotates report identifiers;
lesson/module/all reset isolation; reduced exam hints; Linux run evidence.

Initial mechanical acceptance passed on Ubuntu arm64: 73 tests without skips
and all 33 preflight checks (`validation/beginner-pilot-20260919/RESULTS.md`).
The depth/source revision passes 76 tests without skips and the same 33 readiness
checks; exact snapshot and coverage are in
`validation/beginner-pilot-20260919/DEPTH_AND_SOURCES.md`. The claim-level source
map is `docs/dev/BEGINNER_SOURCE_REVIEW.md`. These are not human learning results.

The B1 grader runs an independent worker that records its received environment
under an owned temporary directory. Only synthetic settings are passed into
student code. This witness prevents accidental output-only passes; it is not
tamper-proof against a malicious same-user student. Student processes are
bounded and collected by the existing supervisor. No persistent services,
mounts, network objects, or new privileged cleanup are introduced.

## Human acceptance: pending

Have the learner start with only the manual and functioning VM. Record where
they pause, what they predict, and what assistance they use. Can they explain
the failure before the repair, handle a changed public setting/private key,
and distinguish environment hygiene from filesystem isolation? Can they repeat
the practical later without copying a previous implementation? Track setup
failures separately. No automated count or word count is a proxy for this gate.

## Trying an unreleased working copy

The default appliance installs pinned v1.0.2, not local source. Keep it pinned;
do not silently replace a student's work or add host directory mounts.

From the host repository root, make a transfer archive with no student data,
Git history, generated artifacts, or host credentials:

```bash
tar -czf /private/tmp/north-echo-beginner-source.tgz \
  --exclude=__pycache__ --exclude='*.pyc' --exclude=.DS_Store --exclude='dist-*' \
  README.md AGENTS.md VERSION lab-start lab-grade lab-status lab-reset lab-cleanup \
  scripts graders course deploy docs tests validation .github release \
  .north-echo-root .gitignore ARCHITECTURE.md COURSE_DESIGN.md ROADMAP.md SECURITY.md LICENSE
limactl copy /private/tmp/north-echo-beginner-source.tgz north-echo:/tmp/north-echo-beginner-source.tgz
limactl shell north-echo
```

The archive snapshots this working tree (including uncommitted pilot files).
The explicit safety marker must be present; lifecycle commands intentionally
refuse to operate if `.north-echo-root` is missing.
`limactl copy` transfers it by SSH rather than mounting the host directory.
The last command enters the guest. Substitute a dedicated disposable instance
name if desired. These commands do not replace its existing `~/north-echo`.

Inside the VM:

```bash
mkdir "$HOME/north-echo-beginner-preview"
cd "$HOME/north-echo-beginner-preview"
tar -xzf /tmp/north-echo-beginner-source.tgz
mkdir -p .student .fixtures .runtime .state
xargs sudo apt-get install -y < deploy/ubuntu-packages.txt
./scripts/attest-course
./scripts/linux-preflight
./lab-start b0.01
cd .student/b0.01
less README.md
```

`mkdir` intentionally fails if that preview directory already exists: **stop
there** rather than extracting over it. Use a new empty preview directory for
a later snapshot. The second `mkdir` restores empty managed directories omitted
from the archive. Package installation is guest-only and adds the shared
prerequisites, including nano; it may need `sudo apt-get update` first. The two
checks must pass before continuing. `less` reads the guide; press `q` to quit.
Keep this workflow manual until the learner pilot justifies a release.
