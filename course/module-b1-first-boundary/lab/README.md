# B1 practical - A useful reader with a smaller handoff

## Outcome and preparation

Repair an independent launcher using only ideas practiced in B1.01-03. You
will be evaluated on actual child behavior, not specific source text.

From the repository root inside the disposable VM:

```bash
./lab-start module-b1
cd .student/b1.lab
```

The first command prepares/resumes the practical. The second enters its
workspace. Edit `launch.py` there, not canonical course material.

Inspect the actual starter before changing it:

```bash
pwd
ls -l launch.py
cat launch.py
nano launch.py
```

Confirm `.student/b1.lab`, locate the supplied file, display its source, then
open it to implement your chosen repair. Save with Ctrl+O and Enter; exit with
Ctrl+X. Run `cat launch.py` to verify the saved file. Stop before `nano` if
you are only inspecting. Access instructions do not supply the repair itself.

## Task and interface

Invoke the program as `python3 launch.py WORKER REPORT`. WORKER is a supplied
trusted local Python program; REPORT is a path passed as its one argument.
The grader supplies both using fresh names, including paths with spaces.

1. Actually run the selected worker with the selected report argument.
2. Pass the parent's `NE_REPORT_STYLE` value unchanged. It will be `plain` or
   `upper` and is guaranteed to exist for this assessment.
3. Do not copy other parent settings into the child. The parent contains fake
   private values and unrelated settings; their names are not a fixed list.
4. Preserve the worker's standard output, standard error, and ordinary exit code
   (0-255). Signal forwarding is outside this assessment.
   A failed report read must remain a failure. Do not print extra launcher
   messages or any private value.

You are not required to implement a sandbox, support arbitrary executables,
handle malformed argument counts, or defend against a malicious worker. This
lab tests explicit environment inheritance and a reliable subprocess handoff.
Python may introduce an interpreter locale setting of its own; that is not a
copied parent secret. No environment-wide dump is needed to solve this lab.

For local experiments you may reuse the observer from your B1.03 workspace by
supplying its path. The independent grader does not use your edited observer
and does not accept reassuring launcher messages as proof the child ran.

If that workspace still exists, this is a concrete invocation from `.student/b1.lab`:

```bash
ls -l ../b1.03/inspect_reader.py
NE_REPORT_STYLE=plain NE_PRIVATE_TOKEN=pretend-red python3 launch.py ../b1.03/inspect_reader.py report.txt
echo $?
```

`..` reaches `.student`; the rest of the relative path selects the earlier
observer. Check the listing succeeds before running it. If you reset B1.03,
prepare it again from the repository root first; don't invent another worker
to match your launcher. The prefixes and arguments have the meanings practiced
in B1.03. Use the report and presence observations to assess your repair, then
design a changed case yourself. Grading supplies its own worker regardless of
whether you retain this earlier workspace.

## Evaluate

```bash
cd ../..
./lab-grade module-b1
```

`cd` returns to the root. The grader launches fresh cases and reports failed
properties with references in practice mode. Expect the starter to fail the
unapproved-setting checks. Repair the implementation and rerun. Use
`./lab-grade module-b1 --mode exam` for the same checks with reduced hints.

An entirely empty environment must fail the useful-work check. A one-name
deletion must fail changed-key checks. A launcher that fabricates report output
without running the worker must fail the independent execution observation.
The grader is feedback for honest learners, not a hostile multi-user barrier.

## Explain and finish

Before calling this complete, explain in your own words:

- What crossed from parent to child before and after your repair?
- Which observation proves the report job still works?
- Which observation supports the claim that unnecessary settings did not cross?
- What could the child still access? Name a resource this repair does not restrict.
- If the worker fails, why should its caller see that failure too?

These are human review questions, not keyword-graded prose. Record predictions,
actual observations, and where you needed help in your own notes. A green grade
does not by itself establish understanding or containment of hostile code.

Optional `./lab-reset module-b1 --dry-run` previews removal of all B1 student
work. `./lab-reset module-b1 --yes` discards its lessons, lab, and fixtures while
keeping attempt/pass metadata. Reset and retry on a later day to test recall.

Pause here for a learner review. Continue to Module 01 when you can predict and
explain the handoff and its limits, not merely when you obtain a green grade.

## Sources and scope

- [Python 3.12 subprocess](https://docs.python.org/3.12/library/subprocess.html#subprocess.run)
  supports the explicit environment and structured invocation. Its
  [returncode contract](https://docs.python.org/3.12/library/subprocess.html#subprocess.CompletedProcess.returncode)
  distinguishes normal exits from signal termination; our lab covers the former.
- [Python startup locale handling](https://docs.python.org/3.12/using/cmdline.html#envvar-PYTHONCOERCECLOCALE)
  documents that the interpreter can introduce `LC_CTYPE`. "No copied parent
  settings except the public style" is therefore not a promise of an environment
  containing exactly one key after Python starts.

The grader's fresh worker checks selected inherited settings and useful work.
That is not a confidentiality guarantee against malicious same-user code or
evidence of filesystem/network confinement. Our policy and tested cases are
explicit lab choices, not universal requirements imposed by Python.
