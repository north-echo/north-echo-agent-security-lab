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

<!-- source: course/module-04-minimal-agent/lab/agent.py format=code -->
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
<!-- /source -->

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
