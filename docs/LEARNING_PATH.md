# Learning path and assessment

This course teaches runtime containment for local agent workloads. A passing
command is the beginning of an explanation: identify the authority, the control,
the observed effect, and the limits of that evidence. No AI service is required.

## Entry diagnostic

Use the validated disposable VM. Start `./lab-start 01.01` and enter
`.student/01.01`; all scratch files below stay in that resettable workspace.
Try the following without consulting the expected observations, then compare.

```bash
printf '%s\n' 'two words' 'one'
python3 -c 'import sys; sys.exit(7)'
printf 'previous status=%s\n' "$?"
python3 -c 'import json; print(json.loads("{\"count\": 2}")["count"])'
cc -std=c11 -Wall -Wextra hello-syscall.c -o diagnostic-program
./diagnostic-program
ps -o pid,ppid,comm -p "$$"
rm diagnostic-program
```

### Line by line

- Single quotes keep `two words` as one argument; the format emits one line per
  remaining argument. Predict two output lines.
- The Python child exits with status 7. Read `$?` immediately: another command
  would replace it. Expected `previous status=7`.
- `json.loads` parses an object; indexing `count` returns integer 2, not the
  original JSON string.
- The compiler turns the supplied C source into a local executable and reports
  syntax/type errors before execution. Expect the lesson's two output messages.
- `ps` shows the current shell and its parent ID. Explain which process `$$`
  denotes before comparing the row.
- Remove only the exact diagnostic executable. The canonical source is untouched.

Record one point each for explaining quoting, exit status, parsed JSON, the
compile/execute distinction, and PID/PPID. This is a self-check, not an exam.
For missed shell items, read “Reading command and code blocks” in the foundation
manual. For C, follow Lesson 01.01's source explanation and deliberately introduce
then repair a missing semicolon in the student copy. For JSON, change `count` to
a quoted string and explain the changed type. Repeat the missed task until you
can predict and explain it. No systems-programming background is assumed.

## Worked, faded, independent

For each module, complete the worked lessons, attempt the corresponding faded
task below with the manual closed, then take the independent lab. A faded task
changes one requirement while retaining familiar interfaces. Reopen a specific
explanation if needed and record which hint helped; do not mistake copied output
for an explanation.

| Module | Faded task before the independent lab |
| --- | --- |
| 01 | Predict which environment and descriptor state survives a launch; justify each observation. |
| 02 | Given two namespace/procfs observations, identify which establishes the child's PID view. |
| 03 | Explain a nonzero bounding set alongside empty effective capabilities; state what no_new_privs adds. |
| 04 | Add a harmless argv task with a space in one argument and a nonzero child status; predict its trace. |
| 05 | Draw a descriptor's lifetime across policy installation and exec; identify where it must be closed. |
| 06 | Explain why an allowed read must still succeed under a syscall policy; distinguish it from pathname authorization. |
| 07 | Change a bounded CPU quota and predict cpu.max; compare configured values with observed values. |
| 08 | Explain which authority the local broker retains and which authority the isolated client lacks. |
| 09 | Given a capability's audience, expiry and run identity, identify the evidence needed to accept an operation. |
| 10 | Plan two independent jobs before launch; predict ordered success/failure records and exact collection. |
| 11 | Classify a mixed synthetic evidence row without looking at its variant label; preserve useful-work requirements. |
| 12 | Classify incomplete observations without the oracle's next_probe hint; state the smallest missing observation. |

## Cumulative checkpoint after Module 03

From the repository root, grade `module-01`, `module-02`, and `module-03` in exam
mode. In `.student/03.lab/checkpoint.md`, make a table of environment, descriptors,
namespace membership, capability state, and no_new_privs. For each, name one
observation and one fact it cannot establish. Explain why a namespace change alone
does not remove inherited authority. Pass this checkpoint only when the practicals
pass and you can explain every row without reading a solution.

## Cumulative checkpoint after Module 06

Grade `module-04`, `module-05`, and `module-06` in exam mode. Record evidence in
`.student/06.lab/checkpoint.md`: literal argument preservation, allowed file access,
intended file denial, inherited descriptor hygiene, and effective syscall policy.
For each denial, include a corresponding useful operation that still works.
Explain why `Seccomp: 2` alone cannot establish a particular denial and why
filesystem denial does not establish resource limits. Revisit only the failed
property's lesson, then repeat with fresh evaluation fixtures.

## Cumulative checkpoint after Module 09

Grade `module-07`, `module-08`, and `module-09` in exam mode. In
`.student/09.lab/checkpoint.md`, map resource limits, direct network isolation,
broker authorization, credential absence, and replay handling to distinct
observations. Explain which component retains each authority and how it is
collected. A functional broker response alone does not establish all these facts.

## Graduation rubric

The capstone's automated batch-runtime assessment must pass. Separately review
`RATIONALE.md` using this rubric; the program does not grade prose by keywords.
Score each dimension 0 (absent/incorrect), 1 (correct but unsupported), or 2
(correct, tied to observed evidence, and appropriately limited).

| Dimension | Evidence needed for 2 points |
| --- | --- |
| Authority model | Names workload versus broker authority and the boundary each control enforces. |
| Composition | Explains launch order using dependencies, including privilege removal after namespace entry. |
| Functional preservation | Connects useful work and intended denial observations, rather than reporting only failures. |
| Lifecycle | Distinguishes invalid batch input, ordinary job failure, timeout, and exact resource collection. |
| Interpretation | States what each observation proves, what remains untested, and how a fresh run differs. |

Graduation requires an automated pass and 2 points in every reasoning dimension.
An instructor or peer should score the rationale; a solo learner may self-review
but should label that result self-assessed. Keep notes and solutions private when
exporting them. `lab-reset` intentionally deletes these workspace notes too.

## Pace and evidence

There is no validated course-duration estimate yet. Work one conceptual layer at
a time and record active time, hints used, and failed checkpoints. Stop at a
checkpoint until the missing prerequisite is understood. Time spent diagnosing
the VM is setup friction and should be measured separately from learning time.
