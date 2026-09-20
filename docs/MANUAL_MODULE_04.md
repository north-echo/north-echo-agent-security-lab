<!-- source: course/module-04-minimal-agent/README.md format=markdown -->
# Module 04 - Build a minimal tool-using agent

Build a small deterministic agent loop with `read_file`, `write_file`, and argv-based command execution over synthetic tasks. Begin deliberately over-authorized, inventory inherited authority, then define and verify a narrow tool contract.

No AI service, network call, or API credential is used. A checked-in JSON task acts as the local scripted policy so every decision is reproducible and inspectable.

Play in order: `04.01`, `04.02`, `04.03`, then `module-04`.

Outcomes:

- execute a deterministic sequence of named tools and emit one complete JSON record per action;
- preserve argv boundaries without shell reparsing and record nonzero tool results;
- inventory the launcher's environment, descriptors, and working directory without logging secret values;
- remove synthetic ambient environment authority before launching a child;
- distinguish an action request, an execution result, and evidence that the result actually occurred.

## Learning route and limits

Prerequisites: B0/B1 and Modules 01-03. Continue as your ordinary account inside the disposable Linux VM. The guided lessons introduce their new syntax and interfaces before the independent lab combines them.

04.01 connects each requested action to a result and an independently observed effect, including aggregate failure status. 04.02 preserves argument boundaries and distinguishes child status from runner status. 04.03 applies environment hygiene at the child boundary.

A JSON request, a runner's trace, and an independently observed effect are three different forms of evidence. JSON syntax does not authorize an action. This module is not a production schema validator, path sandbox, resource manager, durable audit store, or model safety policy.

Before moving on, demonstrate both useful allowed work and the intended restriction, and explain the difference in your own words. A failed compiler command or missing input is not a security success. Use the independent lab's practice feedback to revisit a specific lesson; passing checks does not replace understanding or make the combined program production-ready.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-04-minimal-agent/lesson-01/README.md format=markdown -->
# 04.01 - Run a deterministic tool loop and record every action

## Goal

Turn a local JSON task into explicit tool actions and a complete JSON-lines trace. The JSON task is a deterministic stand-in for a model: it makes the control flow reproducible and requires no network or credential.

## Concepts and preparation

Complete B0/B1 and Modules 01-03 first. Here an **agent loop** means a program that receives a requested action, chooses a named tool, executes it, and records a result. We use a fixed task instead of a model so every decision is visible. This teaches the execution boundary, not model reasoning or prompt resistance.

A JSON **object** contains named fields in braces; an **array** contains ordered values in brackets. In Python these become a dictionary and a list. `task["actions"]` retrieves the list; `for action in ...` processes each dictionary in order. A **dispatcher** chooses a function based on the tool name. None of these data structures grants permission: the process still has its ordinary Linux authority.

The trace uses JSON Lines: one complete object per physical line. A task JSON document and a JSONL trace are different formats. Parsing the entire multi-record trace as one ordinary JSON object would be a format error.

From the course root:

```bash
./lab-start 04.01
cd .student/04.01
pwd
ls -l agent_loop.py task.json input.txt
cat agent_loop.py
cat task.json
cat input.txt
```

The first command prepares your student copy. `cd` enters it; `pwd` and `ls -l` verify location and filenames; the `cat` commands read the supplied files before you run them. If a file is absent, check the lesson number and working directory rather than creating a substitute with guessed contents. To edit a source below, use `nano FILENAME` with the actual filename, save with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. Python runs the saved file directly; there is no compile step.

## Exercise 1 - Inspect the request before execution

```bash
sed -n '1,200p' task.json
python3 -m json.tool task.json
```

### Line by line

- `sed -n` prints the complete small fixture without modifying it.
- `python3 -m json.tool` parses the file and pretty-prints valid JSON; a nonzero exit means the request is malformed.
- Each action has a stable `id`, a named `tool`, and tool-specific arguments. The action is a request, not proof that the effect occurred.

Expected: two actions appear in order: `read_file` for `input.txt`, then `write_file` for `output.txt`.

## Exercise 2 - Run the loop and inspect effects

Complete source:

```python
#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def perform(action: dict) -> dict:
    tool = action["tool"]
    if tool == "read_file":
        content = Path(action["path"]).read_text(encoding="utf-8")
        return {"content": content}
    if tool == "write_file":
        Path(action["path"]).write_text(action["content"], encoding="utf-8")
        return {"bytes_written": len(action["content"].encode())}
    raise ValueError(f"unknown tool: {tool}")


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} TASK.json TRACE.jsonl", file=sys.stderr)
        return 2
    task = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    trace_path = Path(sys.argv[2])
    with trace_path.open("w", encoding="utf-8") as trace:
        for action in task["actions"]:
            record = {"id": action["id"], "tool": action["tool"]}
            try:
                record.update({"ok": True, "result": perform(action)})
            except Exception as error:
                record.update({"ok": False, "error": str(error)})
            trace.write(json.dumps(record, sort_keys=True) + "\n")
            trace.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### Source, line by line

- `json` parses requests and serializes trace records; `sys` supplies argv and exit handling; `Path` performs explicit file operations.
- `perform` dispatches on the exact tool name. Unknown names fail closed through `ValueError`.
- `read_file` returns observed content. `write_file` reports the encoded byte count after the write call returns.
- `main` requires exactly a task path and trace path, then parses the task before acting.
- Opening the trace with `"w"` creates one trace for this run. Each action begins with its stable ID and tool name.
- The `try` block converts success or failure into data. It does not silently claim success.
- JSON Lines uses one complete JSON object per line. `sort_keys=True` makes the local fixture deterministic; `flush` makes completed records immediately observable.
- `raise SystemExit(main())` turns the function result into the process exit status.

Run it:

```bash
rm -f output.txt trace.jsonl
python3 agent_loop.py task.json trace.jsonl
cat output.txt
python3 -c 'import json; [print(json.loads(line)) for line in open("trace.jsonl")]'
```

### Line by line

- `rm -f` removes only the two lesson-generated files so an old result cannot masquerade as new evidence.
- The agent receives request and trace paths as separate arguments.
- `cat` verifies the filesystem effect independently of the trace.
- The Python one-liner parses every trace line; merely printing unvalidated text would not prove valid JSON.

Expected: `output.txt` contains `synthetic result`. The trace contains exactly two parseable records in request order, including the read content and write byte count.

## Exercise 3 - Create and repair an evidence gap

Temporarily comment out the `trace.write(...)` line, remove old outputs, and rerun:

```bash
rm -f output.txt trace.jsonl
python3 agent_loop.py task.json trace.jsonl
wc -l trace.jsonl
test -f output.txt
```

### Line by line

- The action still changes `output.txt`, but `wc -l` reports zero trace records.
- `test -f` returns success without printing; it proves the effect exists but says nothing about which request caused it.
- Restore `trace.write(...)`, rerun, and require `test "$(wc -l < trace.jsonl)" -eq 2`.

The intentional mistake is not a missing log decoration. It removes the evidence needed to connect requested actions to observed results.

### Follow one action through the program

For the first action, read `tool`, enter the `read_file` branch, and retrieve the named path's text. The returned dictionary becomes the record's `result`. For the second, `write_text` creates or replaces the requested output before the function returns a byte count. The supplied content ends with a newline; that byte is part of the result.

`def` defines a function but does not run its body. The annotations `: dict` and `-> dict` describe intended types; Python does not enforce a schema merely because they are present. The indentation determines which statements belong to each branch. `return` leaves the function, so a successful known tool does not reach the final `raise`.

`record.update(...)` adds fields to a dictionary. Python evaluates `perform(action)` before performing that update, so an exception does not first install a false success result. `except Exception` handles ordinary action errors, not every possible interruption or output-write failure. `with` closes the trace when the block exits. `flush` pushes Python's buffered output onward; it is not a promise of durable storage or a tamper-proof audit log.

This first example deliberately returns 0 after recording action failures. It separates "the loop completed" from "every action succeeded." The independent lab requires the stronger aggregate-status rule. Practice that small change below before combining tools.

## Exercise 4 - Make action failure affect the process result

Before changing the program, create a tiny task containing an unknown tool:

```bash
printf '%s\n' '{"actions":[{"id":"unknown-1","tool":"not_a_tool"}]}' > failure-task.json
python3 agent_loop.py failure-task.json failure-trace.jsonl
STATUS=$?
cat failure-trace.jsonl
printf 'loop status=%s\n' "$STATUS"
```

`printf` writes only a synthetic task in this workspace. The loop records `ok: false` and an unknown-tool error, but the status is initially 0. Saving `$?` immediately prevents the later `cat` from replacing that observation.

Open `nano agent_loop.py` and make these three small edits:

- Before opening the trace, initialize `failed = False` at the same indentation as `trace_path = ...`.
- After the `try`/`except` block, inside the action loop and before `trace.write`, add `failed = failed or not record["ok"]`.
- Replace `main`'s final `return 0` with `return 1 if failed else 0`.

The Boolean starts false. `not record["ok"]` becomes true for a failed action. `or` retains any earlier failure, so a later success cannot erase it. The final return summarizes the whole run without discarding individual records. Save, inspect with `cat agent_loop.py`, and repeat both the failure task and the original task. Expect one failed record with status 1 for the former, and two successful records with status 0 for the latter.

This is aggregation, not rollback. If one action writes a file and a later action fails, the earlier file still exists. Do not claim all-or-nothing behavior that the code does not implement.

## Checkpoint and troubleshooting

```bash
test "$(wc -l < trace.jsonl)" -eq 2
test "$(cat output.txt)" = "synthetic result"
```

- If JSON parsing fails, inspect the exact line; JSON Lines requires one complete object per line.
- If the trace says success but the file is absent, the record was emitted before the effect or without checking it.
- If an old output survives, repeat the scoped `rm -f` command; never delete outside this lesson workspace.
- Checkpoint: explain why the request, trace record, and filesystem observation are three distinct facts.

## Replay and source truth

From this workspace, `cd ../..` returns to the course root. `./lab-reset 04.01` discards only this lesson's student workspace and generated fixtures after confirmation. Save any notes elsewhere in the disposable VM first. Do not edit canonical `course/` files to repair your attempt.

Python's [JSON documentation](https://docs.python.org/3.14/library/json.html) defines parsing and serialization, and [pathlib](https://docs.python.org/3.14/library/pathlib.html) defines the text-file operations. The course adds the one-object-per-line framing; ordinary JSON is not itself a multi-record framing protocol.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-04-minimal-agent/lesson-02/README.md format=markdown -->
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

### Source, line by line

- The imports provide JSON, process launch, argv handling, and path reads.
- The task must contain `argv` as a JSON array. Each element becomes exactly one child argument.
- `child_env` is constructed from constants; it does not copy unknown parent authority.
- `subprocess.run(task["argv"], shell=False, ...)` launches the vector directly. No shell interprets spaces, dollar signs, parentheses, semicolons, or redirections.
- Text capture keeps stdout and stderr separate. `check=False` preserves a nonzero result for the trace instead of raising before it can be recorded.
- The JSON result records the requested argv, exit status, stdout, and stderr. The runner itself exits nonzero when the tool did.

The observer is deliberately tiny:

```python
#!/usr/bin/env python3
import json
import sys

print(json.dumps(sys.argv[1:]))
```

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
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-04-minimal-agent/lesson-03/README.md format=markdown -->
# 04.03 - Inventory and remove ambient launcher authority

## Goal

Inventory the process state inherited by a local agent without printing secret values, reproduce an ambient-environment leak, and repair the child launch with an allowlist.

## Concepts and preparation

Complete 04.01-04.02 and recall 01.02-01.03. **Ambient authority** is usable access arriving from the surrounding process environment instead of being explicitly selected for this task. Examples include inherited credentials, open files, and an unexpectedly sensitive working directory.

An inventory answers "what inputs and handles are present?" It is observation, not enforcement. Listing environment key names avoids deliberately copying their values, but names, directory paths, and other metadata can still be sensitive outside this synthetic VM. Do not publish raw inventories from your real workstation.

From the course root:

```bash
./lab-start 04.03
cd .student/04.03
pwd
ls -l authority_agent.py probe.py FIXTURE.txt
cat authority_agent.py
cat probe.py
cat FIXTURE.txt
```

The first command prepares your student copy. `cd` enters it; `pwd` and `ls -l` verify location and filenames; the `cat` commands read the supplied files before you run them. If a file is absent, check the lesson number and working directory rather than creating a substitute with guessed contents. To edit a source below, use `nano FILENAME` with the actual filename, save with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. Python runs the saved file directly; there is no compile step.

## Exercise 1 - Inventory names and handles, not values

Complete source:

```python
#!/usr/bin/env python3
import json
import os
import subprocess
import sys


def inventory() -> dict:
    descriptors = []
    for name in os.listdir("/proc/self/fd"):
        if name.isdigit():
            descriptors.append(int(name))
    return {"cwd": os.getcwd(), "environment_keys": sorted(os.environ), "descriptor_numbers": sorted(descriptors)}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"unsafe", "safe"}:
        print(f"usage: {sys.argv[0]} unsafe|safe", file=sys.stderr)
        return 2
    print("INVENTORY=" + json.dumps(inventory(), sort_keys=True))
    child_env = os.environ.copy() if sys.argv[1] == "unsafe" else {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
    run = subprocess.run(["python3", "probe.py"], env=child_env, text=True, capture_output=True, check=False)
    print(run.stdout, end="")
    return run.returncode


if __name__ == "__main__":
    raise SystemExit(main())
```

### Source, line by line

- `inventory` reads the current working directory, environment key names, and numeric descriptor entries.
- It deliberately does not read environment values or descriptor contents. An inventory should identify authority channels without copying secrets into logs.
- `/proc/self/fd` is a snapshot; the directory scan itself may temporarily use a descriptor.
- The mode must be the exact word `unsafe` or `safe`.
- Unsafe mode copies the entire parent environment. Safe mode constructs two known values.
- The child is launched as a structured argv list, and its output is captured for the observation.

The probe is:

```python
#!/usr/bin/env python3
import os

print("NE_AGENT_SECRET=" + os.environ.get("NE_AGENT_SECRET", "<absent>"))
```

- The probe reads one synthetic key and reports absence explicitly.
- Do not adapt this exercise to real credential names or values.

Run the metadata-only inventory:

```bash
export NE_AGENT_SECRET="synthetic-$(awk -F= '/fixture_id/{print $2}' FIXTURE.txt)"
python3 authority_agent.py safe
```

Expected: the inventory lists `NE_AGENT_SECRET` as a key but does not contain its value. The child reports `<absent>`.

`export` deliberately makes this fake value available to child processes. The `awk` command reads the generated fixture identifier, making the observation specific to this attempt. There is no output-redaction filter here: a filter could hide a leak and make a failed control appear successful. Predict which part of the output will change when the mode becomes `unsafe`.

## Exercise 2 - Reproduce ambient authority

```bash
python3 authority_agent.py unsafe | tee unsafe-output.txt
grep -F "$NE_AGENT_SECRET" unsafe-output.txt
```

### Line by line

- Unsafe mode uses `os.environ.copy()`, transferring every inherited value.
- `tee` retains only this synthetic lesson output.
- `grep -F` treats the synthetic value literally and succeeds when the child leaked it.

This reproduces the Module 01 environment lesson inside a tool-using agent. Adding tools did not erase the launcher's inherited authority.

## Exercise 3 - Repair and verify absence

```bash
python3 authority_agent.py safe > safe-output.txt
grep -F 'NE_AGENT_SECRET=<absent>' safe-output.txt
! grep -F "$NE_AGENT_SECRET" safe-output.txt
printf 'absence-check status=%s\n' "$?"
```

### Line by line

- Safe mode constructs a fixed environment at the child-exec boundary.
- The first `grep` requires the explicit absence observation.
- `!` reverses the literal-match command's success status: finding the value makes the assertion fail. Require status 0 **and** the explicit `<absent>` line from the first check. A missing or unreadable output file is an infrastructure error, not evidence of secure absence.
- This repair does not constrain paths, syscalls, CPU, memory, or network access. Later modules add those independent controls.

### Read the inventory and the mode switch

`os.listdir("/proc/self/fd")` returns entry names as strings. `name.isdigit()` selects numeric descriptor entries; `int(name)` turns them into numbers for sorting. The listing can include the transient descriptor used to enumerate the directory, so it is not a stable count of usable inherited files.

`os.getcwd()` reports the current working directory. Relative paths such as `probe.py` depend on that directory, even though the environment has been narrowed. The conditional expression chooses a full environment copy only for the literal mode `unsafe`; `safe` builds a new mapping.

`print(run.stdout, end="")` forwards captured child output without adding another newline. It does not forward captured stderr, so a missing probe can otherwise look like silent failure. Check the return status and the file's existence before calling an empty output "secure." The name `safe` means environment hygiene in this example, not a complete sandbox.

## Checkpoint and troubleshooting

- If the inventory prints values, reduce it to sorted key names before capturing evidence.
- If safe mode cannot locate Python, inspect the fixed VM path with `command -v python3`; do not copy the whole environment.
- If the unsafe grep fails, confirm the variable was exported in the same shell.
- Remove `unsafe-output.txt` after the observation; it contains only a synthetic value, but it is still disposable fixture data.
- Checkpoint: identify which authority is removed by the repair and name at least three channels it does not address.

## Replay and source truth

Run `unset NE_AGENT_SECRET` to remove the synthetic value from this parent shell. From this workspace, `cd ../..` returns to the course root. `./lab-reset 04.03` discards only this lesson's student workspace and generated fixtures after confirmation. Save any notes elsewhere in the disposable VM first. Do not edit canonical `course/` files to repair your attempt.

The [Python subprocess documentation](https://docs.python.org/3.14/library/subprocess.html) defines argv, environment replacement, captured streams, and return codes. These API guarantees are narrower than a containment policy.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-04-minimal-agent/lab/README.md format=markdown -->
# Module 04 independent lab - Auditable local tool runner

## Preparation and practiced skills

Complete 04.01-04.03 first. You practiced dispatch and trace framing in 04.01, including aggregate failure status; argv and child-result handling in 04.02; and environment allowlisting in 04.03. Combine these responsibilities without changing the external interface.

The starter parses a task, loops over its actions, and only handles one tool. It joins arguments into shell text, inherits the full environment, omits required result fields, and always returns success. Its imports and file-writing syntax are familiar from the guided examples. A runnable starter is not a secure reference implementation.

The grader accepts tool-result fields either inside a `result` object, as in 04.01, or at the record's top level. Use one consistent format. Required fields are `content` for reads, `bytes_written` for writes, and `status`, `stdout`, and `stderr` for command results. Unknown tools still need an action record with `ok: false`. File paths are relative to the evaluation working directory, which need not be the directory holding your Python source.

From the course root:

```bash
./lab-start module-04
cd .student/04.lab
pwd
ls -l agent.py
cat agent.py
nano agent.py
```

The commands prepare your editable lab, enter and inspect it, then open the starter for reading and editing. Save in nano with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. Python executes the saved file directly. Keep the canonical files and grader unchanged.

```python
#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} TASK.json TRACE.jsonl", file=sys.stderr)
        return 2
    task = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    trace = Path(sys.argv[2])
    records = []
    for action in task.get("actions", []):
        if action.get("tool") == "run_argv":
            command = " ".join(action["argv"])
            run = subprocess.run(command, shell=True, text=True, capture_output=True, env=os.environ.copy())
            records.append({"id": action.get("id"), "tool": "run_argv", "ok": run.returncode == 0, "status": run.returncode, "stdout": run.stdout})
    trace.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## Contract


Implement `agent.py`. The grader invokes:

```text
python3 agent.py TASK.json TRACE.jsonl
```

The task is local JSON with an ordered `actions` array. Every action contains a unique string `id`, a `tool`, and the fields required by that tool:

- `read_file`: relative `path`;
- `write_file`: relative `path` and string `content`;
- `run_argv`: nonempty string array `argv`.

Your runner must:

- execute all three tools in request order;
- preserve argv boundaries without a shell parser;
- launch commands with a constructed environment that does not inherit `NE_AGENT_SECRET`;
- write exactly one valid JSON object per action to the requested JSONL trace;
- include `id`, `tool`, and Boolean `ok` in every record;
- record read content, write byte count, or command status/stdout/stderr as appropriate;
- record unknown tools and command failures as failures rather than claiming success;
- return nonzero if any action failed, while retaining the completed trace.

The starter is intentionally unsafe: it supports only `run_argv`, joins the vector into shell text, copies the parent environment, and produces incomplete records. The grader changes paths, content, arguments, and a synthetic environment canary on every run. It also checks a shell-metacharacter bypass and a separate failure task.

Use only interfaces practiced in Lessons 04.01-04.03. Do not add network access, an AI API, or a real credential.

```bash
python3 agent.py sample-task.json trace.jsonl
../../lab-grade module-04
../../lab-grade module-04 --mode exam
```

### Test commands, line by line

- The first command exercises the required two-path interface with the included harmless `sample-task.json`.
- The grader creates fresh evaluation files outside the student workspace and supplies its own task and trace paths.
- Practice mode names failed properties and lesson references.
- Exam mode tests the same properties but suppresses repair-oriented references.

The lab intentionally does not provide a complete implementation. Plan the dispatcher, per-tool result fields, trace write point, failure aggregation, argv launch, and child environment before coding.

## Verify, explain, and replay

Run the starter and record its failed properties before editing. After repair, preserve both successful useful work and the expected denials/errors; a launcher that refuses everything does not pass. A compiler failure, missing executable, or missing fixture is not the desired security outcome.

For each passing property, explain which earlier lesson supplied the mechanism and what the observation does **not** establish. Keep an unresolved property unresolved rather than weakening its expected result. The lab intentionally withholds a combined implementation.

From this workspace, `cd ../..` returns to the course root. `./lab-reset module-04` removes this module's student work and generated fixtures after confirmation; preserve notes first. Start the module again for a fresh randomized attempt. Never substitute real credentials, personal directories, or external services for the synthetic fixtures.
<!-- /source -->
