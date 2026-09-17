# 01.02 - Environment inheritance is authority

Goal: observe a child receiving data it never requested, then launch it with an explicit environment.

## Exercise 1 - Observe the leak

The workspace `FIXTURE.txt` contains a randomized synthetic user. Export a fake token derived from it:

```bash
export DEMO_AGENT_TOKEN="fake-$(awk -F= '/fixture_id/{print $2}' FIXTURE.txt)"
python3 show-env.py
```

### Line by line

- `export` creates or replaces a shell variable and marks it for inheritance by later child processes.
- `DEMO_AGENT_TOKEN=...` names the deliberately fake variable used in this lesson.
- `$(...)` is command substitution: the shell runs the nested `awk` command and inserts its output into the surrounding string.
- `awk -F=` treats `=` as the field separator; the pattern `/fixture_id/` selects the matching line and `{print $2}` emits its value.
- `python3 show-env.py` starts a child process. Without an explicit environment, it inherits every exported variable from the shell.

Expected pattern:

```text
DEMO_AGENT_TOKEN=fake-...
```

The child did not open a credential store. The parent handed the value across `execve` in `envp`.

Confirm at the syscall boundary:

```bash
strace -f -e trace=execve python3 show-env.py 2>&1 | head -20
```

### Line by line

- `-f` follows any child processes Python creates; `-e trace=execve` keeps only program-execution transitions.
- `python3 show-env.py` is the command being traced, not an argument interpreted by `strace` itself.
- `2>&1` makes the syscall trace available to the pipeline.
- `head -20` limits display to the first 20 lines. It does not change the traced execution.

Expected pattern: `execve` reports an environment count. `strace -v -s 200` can show more; do not use that option around real secrets.

## Exercise 2 - Make the intentional mistake

Run the starter launcher:

```bash
sed -n '1,160p' launch-insecure.py
python3 launch-insecure.py
```

### Line by line

- `sed` lets you inspect the launcher before trusting or executing it.
- `python3 launch-insecure.py` runs the parent launcher, which then creates the child shown in the source.

Expected: the token is still printed. Passing `env=os.environ.copy()` feels explicit but preserves every inherited variable.

### Launcher source, line by line

- `#!/usr/bin/env python3` lets an executable script locate Python through `PATH`; invoking `python3 file.py` does not depend on this line.
- `import os` exposes the current process environment; `import subprocess` exposes child-process creation.
- `os.environ.copy()` materializes every inherited environment key/value pair in a new dictionary. The copy prevents Python dictionary aliasing, not authority inheritance.
- `subprocess.run([...], env=child_env, check=True)` executes an argument vector without a shell, supplies that full dictionary as the child's environment, and raises an exception if the child exits nonzero.
- The list form `['python3', 'show-env.py']` keeps program and argument boundaries explicit.

### Observer source, line by line

- `os.environ.get("DEMO_AGENT_TOKEN", "<absent>")` reads one variable and substitutes the literal marker only when the key is missing.
- String `+` joins the label and observed value before `print` writes it.
- The second `print` performs the same check for `PATH`, which remains present in the allowlisted version.

Fix the launcher by replacing the copied environment with only:

```python
child_env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
```

### Line by line

- `child_env =` binds a new Python dictionary; it does not mutate the parent process's environment.
- `PATH` permits only the two named command-search directories.
- `LANG` gives child tools a predictable locale without copying unrelated parent variables.

Run it again. Expected: `DEMO_AGENT_TOKEN=<absent>`.

## Exercise 3 - Verify, do not assume

```bash
python3 launch-insecure.py | grep -F 'DEMO_AGENT_TOKEN=<absent>'
```

### Line by line

- The launcher writes its child's output to stdout.
- `|` passes that output to `grep`.
- `grep -F` performs a fixed-string match, so angle brackets and punctuation are treated literally rather than as a regular expression.
- A matching line gives `grep` exit status 0; no match gives a nonzero status.

Expected: one matching line and exit status 0. The control is an allowlisted environment constructed at the authority-transfer point, not a promise that children will ignore secrets.
