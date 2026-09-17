# Linux validation and evidence matrix

Run this matrix only in a disposable Linux VM with synthetic data and no personal, employer, cloud, or production credentials. Use an ordinary non-root user unless a step explicitly says otherwise.

## Supported baseline

The first supported target is Ubuntu 24.04 or Debian 12 on x86-64 or arm64 with a recent distribution kernel. Record the exact environment:

```bash
mkdir -p validation
{
  date -u +%Y-%m-%dT%H:%M:%SZ
  uname -a
  test -r /etc/os-release && cat /etc/os-release
  python3 --version
  cc --version | head -n 1
  strace --version | head -n 1
  unshare --version | head -n 1
  capsh --version 2>&1 | head -n 1
  setpriv --version | head -n 1
} | tee validation/environment.txt
```

### Line by line

- `mkdir -p validation` creates a dedicated directory for synthetic validation records and succeeds if it already exists.
- `{ ...; }` groups the inventory commands so one pipe can capture all of them.
- `date -u` records the check time in UTC without depending on a local timezone label.
- `uname -a` records kernel and architecture; `/etc/os-release` records the distribution.
- The version commands identify the user-space tools that influence the lessons.
- `2>&1` joins standard error to standard output for tools that print their version there.
- `tee` shows the inventory and stores the same text. Inspect it before sharing and remove unexpected host-identifying details.

## Gate 0: non-destructive preflight

```bash
./scripts/linux-preflight | tee validation/preflight.txt
```

Expected: all v0.1 required checks report `PASS`. Future-module checks may report `INFO` or `MISSING` until their packages and VM configuration are added. Do not weaken the host to turn a missing feature into a pass.

## Gate 1: control plane and integrity

```bash
python3 -m unittest discover -s tests -v 2>&1 | tee validation/tests.txt
./scripts/attest-course | tee validation/attestation.txt
./lab-status | tee validation/status-before.txt
```

Expected: the test suite and attestation pass. Initial status should show zero or previously recorded metadata, but there should be no unexplained student workspace or fixture.

## Gate 2: Modules 01-03 guided paths

Run each target from a fresh workspace and follow its local README completely:

```bash
for target in 01.01 01.02 01.03 02.01 02.02 02.03 03.01 03.02 03.03; do
  ./lab-reset "$target" --yes
  ./lab-start "$target"
  printf '%s\n' "RUN MANUALLY: $target -> .student/$target/README.md"
done
```

The loop prepares each lesson but cannot substitute for doing the observations. For every target, record:

- commands and expected patterns observed;
- the intentional failure reproduced;
- the repair completed;
- the final checkpoint result;
- any difference caused by kernel, architecture, compiler, or package version.

Module-specific kernel facts to verify:

| Module | Required evidence |
| --- | --- |
| 01 | syscall trace is visible; environment authority crosses `exec`; non-`CLOEXEC` descriptor crosses `exec`; repairs remove the authority |
| 02 | user and UTS isolation work; PID view changes; fresh procfs shows namespace-local PIDs; host namespace state is unchanged |
| 03 | capability sets are observable; bounding/ambient/inheritable/effective/permitted state reaches the required floor; `NoNewPrivs` is set before `exec` |

## Gate 3: independent graders

Start each module lab, confirm the starter fails properties, complete it using only the guided material, then grade in both modes:

```bash
./lab-start module-01
./lab-grade module-01 --mode practice
./lab-grade module-01 --mode exam

./lab-start module-02
./lab-grade module-02 --mode practice
./lab-grade module-02 --mode exam

./lab-start module-03
./lab-grade module-03 --mode practice
./lab-grade module-03 --mode exam
```

Expected before completing the labs: each starter produces `RESULT: NOT PASSED`; practice includes useful lesson references and exam output omits them. Expected after completing the labs: functional and security properties pass using fresh evaluation details.

Do not commit the completed student implementations. The validation record should name outcomes, not contain the solution source.

## Gate 4: replay and metadata

Use one lesson to prove fresh replay and metadata-only persistence:

```bash
./lab-reset 01.01 --yes
./lab-start 01.01
cp .student/01.01/.north-echo.json validation/01.01-before.json
printf '%s\n' 'synthetic student work' > .student/01.01/reset-proof.txt
./lab-reset 01.01 --yes
test ! -e .student/01.01/reset-proof.txt
./lab-start 01.01
cp .student/01.01/.north-echo.json validation/01.01-after.json
python3 - <<'PY'
import json
from pathlib import Path

before = json.loads(Path("validation/01.01-before.json").read_text())
after = json.loads(Path("validation/01.01-after.json").read_text())
assert before["fixture_id"] != after["fixture_id"]
progress = Path(".state/progress.json").read_text()
assert "synthetic student work" not in progress
print("REPLAY AND METADATA: PASS")
PY
```

### Line by line

- The first reset/start pair creates a known-fresh run.
- `cp` preserves only the non-secret workspace metadata needed for comparison.
- `reset-proof.txt` stands in for disposable student work.
- `test ! -e` proves reset removed that work.
- The second start creates a new fixture.
- The short Python check proves the fixture ID rotated and the persistent progress file did not absorb the student content.

Delete the copied fixture metadata after recording the pass:

```bash
rm validation/01.01-before.json validation/01.01-after.json
```

## Gate 5: reset scopes and cleanup containment

```bash
./lab-start 01.01
./lab-start 01.02
./lab-reset module-01 --dry-run | tee validation/reset-dry-run.txt
test -d .student/01.01
test -d .student/01.02
./lab-reset module-01 --yes
test ! -e .student/01.01
test ! -e .student/01.02

./lab-start 02.01
./lab-start 03.01
./lab-reset --all --dry-run | tee validation/reset-all-dry-run.txt
./lab-reset --all --yes
test ! -e .student/02.01
test ! -e .student/03.01
```

Expected: dry-run changes nothing; module reset touches only the module; all reset removes every disposable workspace/fixture/runtime entry while `.state/progress.json` retains counts and pass state.

The automated suite contains hostile-path and unrelated-resource rejection tests. Later modules must add equivalent tests for their cgroups, services, network objects, and mounts before those resources are created by a lesson.

## Gate 6: final inspection

```bash
./scripts/attest-course
./lab-status | tee validation/status-after.txt
find .student .fixtures .runtime -mindepth 1 ! -name .gitkeep -print
```

Expected: attestation passes and the final `find` prints nothing after the all-scope reset. Inspect the validation directory for unexpected host identifiers or solution material before retaining it.

## Acceptance record

Create `validation/RESULTS.md` with:

- commit tested;
- environment inventory;
- every gate marked pass, fail, or skipped;
- exact reason and impact of each skip;
- defects fixed and regression tests added;
- residual risks;
- confirmation that only synthetic local fixtures were used;
- confirmation that completed student solutions were reset and not committed.

Gate A passes only when Modules 01-03 work end to end on Linux and cleanup leaves no lab-owned resource behind.
