# 04.02 - Preserve argv boundaries and handle tool failure

## Goal

Execute a structured argument vector without passing it through a shell, then make nonzero status an explicit result instead of an exception that erases evidence.

## Concepts and preparation

Complete 04.01 first. An argument vector is a list of separate strings, not a command line waiting to be split. One argument can contain spaces or punctuation. With `shell=False`, Python supplies the vector directly to the selected program. That preserves boundaries; it does not establish that the requested program is authorized or harmless.

The contrast in this lesson is confined to the supplied synthetic marker inside your student workspace. Do not substitute real paths or external inputs. The later containment modules restrict what the launched process can do; avoiding an extra shell parser is only one part of that design.

From the course root:

```bash
./lab-start 04.02
cd .student/04.02
pwd
ls -l argv_runner.py show_argv.py task.json
cat argv_runner.py
cat show_argv.py
cat task.json
```

The first command prepares your student copy. `cd` enters it; `pwd` and `ls -l` verify location and filenames; the `cat` commands read the supplied files before you run them. If a file is absent, check the lesson number and working directory rather than creating a substitute with guessed contents. To edit a source below, use `nano FILENAME` with the actual filename, save with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. Python runs the saved file directly; there is no compile step.

## Exercise 1 - Observe safe argument preservation

Complete runner source:

<!-- source: course/module-04-minimal-agent/lesson-02/argv_runner.py format=code -->
```python
#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} TASK.json", file=sys.stderr)
        return 2
    task = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    child_env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
    run = subprocess.run(
        task["argv"],
        shell=False,
        env=child_env,
        text=True,
        capture_output=True,
        check=False,
    )
    print(json.dumps({"argv": task["argv"], "status": run.returncode, "stdout": run.stdout, "stderr": run.stderr}, sort_keys=True))
    return 0 if run.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
```
<!-- /source -->

### Source, line by line

- The imports provide JSON, process launch, argv handling, and path reads.
- The task must contain `argv` as a JSON array. Each element becomes exactly one child argument.
- `child_env` is constructed from constants; it does not copy unknown parent authority.
- `subprocess.run(task["argv"], shell=False, ...)` launches the vector directly. No shell interprets spaces, dollar signs, parentheses, semicolons, or redirections.
- Text capture keeps stdout and stderr separate. `check=False` preserves a nonzero result for the trace instead of raising before it can be recorded.
- The JSON result records the requested argv, exit status, stdout, and stderr. The runner itself exits nonzero when the tool did.

The observer is deliberately tiny:

<!-- source: course/module-04-minimal-agent/lesson-02/show_argv.py format=code -->
```python
#!/usr/bin/env python3
import json
import sys

print(json.dumps(sys.argv[1:]))
```
<!-- /source -->

- `sys.argv[1:]` excludes the program name and exposes the exact two arguments received.
- JSON output makes spaces and punctuation unambiguous.

Run and verify:

Before running, predict how many arguments the observer will receive and whether any shell will interpret the task's punctuation. A pipeline reports the last command's status by default; use the separate captured-status workflow in Exercise 3 when status itself is the observation.

```bash
rm -f SHELL_MARKER
python3 argv_runner.py task.json | python3 -m json.tool
test ! -e SHELL_MARKER
```

Expected: stdout contains `hello world` and the literal string `$(touch SHELL_MARKER)` as two array elements. The marker does not exist.

## Exercise 2 - Trigger the shell-reparsing failure

In your student copy, open `nano argv_runner.py` and temporarily replace only the `subprocess.run` call with this incomplete control. Keep the surrounding indentation, save, then inspect with `cat argv_runner.py`:

```python
run = subprocess.run(
    " ".join(task["argv"]),
    shell=True,
    env=child_env,
    text=True,
    capture_output=True,
    check=False,
)
```

### Line by line

- `" ".join(...)` destroys the original argument boundaries.
- `shell=True` asks `/bin/sh` to interpret the resulting string.
- The task's dollar-sign expression becomes command substitution, so `touch` runs and creates `SHELL_MARKER`.
- Capturing output does not make shell interpretation safe.

Rerun the three verification commands. Expected: the argument output changes and `test ! -e SHELL_MARKER` fails. Restore the argv-list call and confirm the marker remains absent.

## Exercise 3 - Record a nonzero tool result

Create a failure task and run it:

```bash
printf '%s\n' '{"argv":["sh","-c","printf failure-message >&2; exit 7"]}' > failure-task.json
python3 argv_runner.py failure-task.json > failure-result.json
STATUS=$?
cat failure-result.json | python3 -m json.tool
printf 'runner status=%s\n' "$STATUS"
```

### Line by line

- `printf` creates one synthetic local task; single quotes prevent the outer shell from interpreting its punctuation.
- Redirection writes only inside the lesson workspace.
- The runner captures the child's stderr and status before returning failure itself.
- `$?` is saved immediately, before another command can replace it.
- Expected JSON contains status 7 and `failure-message`; the runner status is 1.

### Separate child status from runner status

`CompletedProcess.returncode` belongs to the child; `return 0 if ... else 1` belongs to the runner. A child exit of 7 is retained as 7 in JSON even though the runner reports a generic failure status of 1. On POSIX, a negative Python return code indicates signal termination, not an ordinary negative exit status.

`capture_output=True` creates pipes and buffers captured output in memory. It does not set an output-size limit. This teaching runner has no deadline either. Use only the tiny supplied tasks; a production runner would require explicit time/output bounds and process-tree cleanup. `check=False` does not suppress every error: a nonexistent executable can still raise an exception before a child exists.

The final displayed JSON contains the child's stdout as a string. For the observer, that string is itself a JSON-encoded array. The outer result object and the inner observer array describe different layers; quoting in the display is not evidence that argument splitting occurred.

## Checkpoint and troubleshooting

- If `SHELL_MARKER` exists during the repaired run, remove it first and inspect whether any string command or `shell=True` remains.
- If `python3` is not found, verify the fixed `PATH` for this disposable VM rather than copying the parent environment.
- If failure JSON is empty, the runner probably raised instead of recording `returncode`, stdout, and stderr.
- Checkpoint: explain why an argv array is a security boundary only while every layer preserves the array.

## Replay and source truth

From this workspace, `cd ../..` returns to the course root. `./lab-reset 04.02` discards only this lesson's student workspace and generated fixtures after confirmation. Save any notes elsewhere in the disposable VM first. Do not edit canonical `course/` files to repair your attempt.

The [Python subprocess documentation](https://docs.python.org/3.14/library/subprocess.html) defines argv, environment replacement, captured streams, and return codes. These API guarantees are narrower than a containment policy.
