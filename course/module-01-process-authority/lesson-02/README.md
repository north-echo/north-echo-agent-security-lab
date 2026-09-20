# 01.02 - Environment inheritance is authority

## Outcomes and prerequisites

Observe a child receiving data it never requested, replace its inherited
environment, and apply the same idea through C's explicit `envp` interface.
Complete B1's environment handoff and 01.01's compile/run/trace sequence first.

## Understand first

A new executable is not a clean slate. Its launcher supplies arguments and
environment entries during exec. Environment strings can affect configuration,
locale, command lookup, and application behavior. A program need not open a
file to receive a value the parent already copied into its environment.

B1 selected a Python mapping. Here we connect that mapping to the lower-level
array of `KEY=VALUE` strings received at exec, then practice the C interface
needed by the independent lab. A dictionary copy protects neither secrecy nor
authority: different containers can hold exactly the same values.

## Prepare and read the files

From the VM repository root:

```bash
./lab-start 01.02
cd .student/01.02
pwd
ls -l show-env.py launch-insecure.py clean-env.c FIXTURE.txt
cat show-env.py
cat launch-insecure.py
```

The preparation creates an editable copy and synthetic fixtures. Confirm
`.student/01.02` before continuing. The list locates each supplied file;
the two `cat` commands read Python source without executing it.

<!-- source: course/module-01-process-authority/lesson-02/show-env.py format=code -->
```python
#!/usr/bin/env python3
import os

print("DEMO_AGENT_TOKEN=" + os.environ.get("DEMO_AGENT_TOKEN", "<absent>"))
print("PATH=" + os.environ.get("PATH", "<absent>"))
```
<!-- /source -->

`import os` provides access to the process environment. `get` returns the
named value or the chosen `<absent>` marker. String `+` joins the label and
value; `print` writes the result. This observer prints only our selected fake
setting and PATH, not every environment value. Never substitute a real secret.

<!-- source: course/module-01-process-authority/lesson-02/launch-insecure.py format=code -->
```python
#!/usr/bin/env python3
import os
import subprocess

# Intentional mistake: copying the full parent environment copies its authority.
child_env = os.environ.copy()
subprocess.run(["python3", "show-env.py"], env=child_env, check=True)
```
<!-- /source -->

`subprocess.run` launches the named interpreter and observer as separate argv
elements. `env` selects the child's environment and `check=True` raises an
exception if that child fails. Neither option validates the contents of the
copied mapping. Predict the observer's output before running either program.

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
- `head -20` limits display. A consumer that closes a pipe early can affect its writer; this short trace should fit within the limit, but use the unpiped command when investigating missing output.

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

Open `nano launch-insecure.py` in this workspace. Replace the copied environment
assignment with only:

```python
child_env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
```

### Line by line

- `child_env =` binds a new Python dictionary; it does not mutate the parent process's environment.
- `PATH` permits only the two named command-search directories.
- `LANG` gives child tools a predictable locale without copying unrelated parent variables.

Save with Ctrl+O, Enter, then exit with Ctrl+X. Run `cat launch-insecure.py`
to check the saved assignment, then `python3 launch-insecure.py`. Expected:
`DEMO_AGENT_TOKEN=<absent>`. Saving the editor buffer is separate from proving
the child received the intended mapping.

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

## Exercise 4 - Express the handoff in C

Read the supplied bridge program before compiling it:

```bash
ls -l clean-env.c
cat clean-env.c
```

<!-- source: course/module-01-process-authority/lesson-02/clean-env.c format=code -->
```c
#include <stdio.h>
#include <unistd.h>

int main(void) {
    char *arguments[] = {"env", NULL};
    char *environment[] = {"PATH=/usr/bin:/bin", "LANG=C.UTF-8", NULL};
    execve("/usr/bin/env", arguments, environment);
    perror("execve");
    return 1;
}
```
<!-- /source -->

### Source, line by line

The headers declare diagnostics and `execve`. `char *arguments[]` is an array
of pointers to strings: each element points at the first character of one
argument. `NULL` ends the array; it is not the text `"NULL"`. The environment
array uses the same shape but contains `KEY=VALUE` strings. `execve` receives
an absolute executable path, the argument array, and this environment array.
Unlike `execvp`, it does not search PATH for the executable. A successful exec
never returns, so `perror` and `return 1` are reached only on failure.

```bash
cc -std=c11 -Wall -Wextra -O2 clean-env.c -o clean-env
DEMO_AGENT_TOKEN=synthetic-only ./clean-env
echo $?
```

The compile command creates the local executable. The shell prefix supplies
the fake token to the launcher. `/usr/bin/env` displays only `PATH=/usr/bin:/bin`
and `LANG=C.UTF-8`, with status 0; the launcher selected those strings instead
of inheriting its own environment. Output order is not the policy.

Changed-case practice: add another fake prefixed setting, such as
`NE_EXTRA_PRIVATE=also-fake`, to the same invocation. Predict and confirm its
absence without changing the program. Explain how an allowlist handles an
unknown parent name. This program deliberately launches one fixed observer;
the independent lab must preserve its general command/argument interface.

## Checkpoint, cleanup, and troubleshooting

Explain where Python's mapping becomes a child environment and how the C array
expresses the same choice. A successful command is not sufficient: check both
useful output and absence of the unwanted value.

- Missing interpreter: inspect `command -v python3`; do not restore the entire
  parent environment just to make command lookup work.
- Token still present: read the saved assignment and ensure you ran the edited
  launcher, not the direct observer.
- No observer output: run without grep and inspect stderr/status. An absent
  observation is not proof of a denied handoff.
- C compile failure: check quotes, commas, semicolons, and the NULL terminator.

Run `unset DEMO_AGENT_TOKEN` to remove the deliberately exported setting from
this shell. Return to the repository root for `./lab-reset 01.02 --dry-run`
and, when ready to discard your edits, `./lab-reset 01.02 --yes`.

## Sources and scope

[Python subprocess](https://docs.python.org/3.14/library/subprocess.html#subprocess.run)
documents replacement environments and child status;
[execve](https://man7.org/linux/man-pages/man2/execve.2.html) defines argv/envp
and image replacement. The guest's `man bash` ENVIRONMENT section describes
export and command-prefix assignments. Environment selection alone does not
close descriptors, restrict file access, or prevent the child from obtaining
data through other channels. The paths and two selected entries are course
policy on the Fedora/Ubuntu baselines, not a universal minimal environment.
