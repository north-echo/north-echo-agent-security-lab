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

<!-- source: course/module-04-minimal-agent/lesson-01/agent_loop.py format=code -->
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
<!-- /source -->

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
