# B0 practical - Read the report you were given

## Outcome and preparation

Implement a small report reader without a step-by-step repair. This is an
independent assessment of B0.01-03, or a diagnostic if those skills are familiar.
Python source editing is required; no C, networking, or administrator privileges.

From the repository root in your disposable VM:

```bash
./lab-start module-b0
cd .student/b0.lab
```

The first command prepares/resumes the independent workspace. The second enters
it. Read and edit only its `read_report.py`; the initial implementation is
intentionally incomplete. The reports contain synthetic data.

The practical withholds the implementation, not how to access your files:

```bash
pwd
ls -l read_report.py
cat read_report.py
nano read_report.py
```

Confirm `.student/b0.lab`, locate the starter, read its current contents, then
open it for your own changes. Save with Ctrl+O and Enter, then exit with Ctrl+X.
Use `cat read_report.py` afterward to inspect what was saved. If you only want
to inspect the starter now, stop before the `nano` command. No completed source
is supplied here; revisit B0.03 if you need help choosing the implementation.

## Your task

The interface is `python3 read_report.py REPORT`, where REPORT is one path.

1. Read the report named by the caller, not a fixed filename. A filename may
   contain spaces; the caller will supply it as one argument.
2. On success, write exactly its UTF-8 text to standard output, with no extra
   heading or newline, no error output, and a zero exit status.
3. On a missing argument or a file that cannot be read (including a directory),
   write a diagnostic to standard error, no report to standard output, and exit
   nonzero. Exact error wording is not graded.
4. Test two reports with different content and at least one failed read.

The evaluation uses fresh filenames and contents, including a report with no
final newline. Reports are valid UTF-8 with Unix LF line endings; malformed
encodings, binary files, and preservation of other newline encodings are outside
this task. No new API or algorithm beyond B0.03 is needed. Do not inspect
the grader for a solution; judge the contract above.

## Evaluate and review

```bash
cd ../..
./lab-grade module-b0
```

`cd` returns to the repository root. `lab-grade` runs fresh cases and reports
properties, not a line-for-line source comparison. A first `NOT PASSED` with
the starter is expected. Use its lesson references, repair your working copy,
and repeat. `./lab-grade module-b0 --mode exam` checks the same properties with
fewer hints; it does not erase your work.

Automated checks are not the entire assessment. Explain without reading a
solution: What changes between a program and one running process? Why do we
check both text and exit status? What does quoting a filename accomplish?
If those explanations are unclear, revisit the relevant guided lesson even
if the tests pass.

## Finish

You may keep your work. To discard all B0 student work, preview with
`./lab-reset module-b0 --dry-run`, then use `./lab-reset module-b0 --yes`.
This removes B0's three guided workspaces, lab, and fixtures, not B1 or the
existing numbered course. The next start generates new report identifiers.
Attempt/pass metadata remains; your source does not. Ready? Continue with B1.01.

## Sources and scope

The interfaces are documented in [Python 3.12 sys](https://docs.python.org/3.12/library/sys.html#sys.argv),
[pathlib](https://docs.python.org/3.12/library/pathlib.html#pathlib.Path.read_text),
[print](https://docs.python.org/3.12/library/functions.html#print), and
[filesystem exceptions](https://docs.python.org/3.12/library/exceptions.html#os-exceptions).
The argument/output/error requirements are this lab's contract. The fresh
grader cases check that contract; they do not certify an arbitrary file reader.
The required skills were practiced in B0.01-03, including the directory-read
failure. These references are not extra prerequisite assignments.
