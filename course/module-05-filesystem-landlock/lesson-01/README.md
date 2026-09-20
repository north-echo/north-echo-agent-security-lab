# 05.01 - Break pathname string checks

## Goal

Observe that a pathname is a lookup request, not an object identity. Break a plausible string-prefix policy with a similarly named sibling and with a symlink, then repair those demonstrations with resolved-object containment while naming the remaining race.

## Concepts and preparation

Complete Module 04 first. A **pathname** is instructions for lookup: start here, walk these directory components, and possibly follow links. A **file descriptor** is a reference obtained after an object has been opened. Comparing the spelling of a request is not the same as authorizing the object eventually reached.

A symbolic link stores another pathname; lookup can follow it out of the apparent directory. The component `..` means the parent directory, while a shared character prefix says nothing about directory ancestry. This lesson uses only tiny synthetic sibling directories inside your workspace. Predict which requests a character-prefix test might mistake for children of the allowed tree.

From the course root in the disposable VM:

```bash
./lab-start 05.01
cd .student/05.01
pwd
ls -l naive_open.py resolved_open.py
cat naive_open.py
cat resolved_open.py
```

`lab-start` prepares the student copy. The next commands enter and inspect it; each `cat` reads a supplied source before execution. Missing files usually mean the wrong working directory or lesson number. Edit only these student copies with `nano FILENAME`, save with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. Recompile after every C edit. An old binary does not automatically track a changed source.

## Exercise 1 - Build only synthetic local paths

```bash
rm -rf demo
mkdir -p demo/allowed demo/allowed-escape demo/protected
printf 'allowed\n' > demo/allowed/note.txt
printf 'prefix-secret\n' > demo/allowed-escape/secret.txt
printf 'symlink-secret\n' > demo/protected/secret.txt
ln -s ../protected/secret.txt demo/allowed/link.txt
python3 naive_open.py demo/allowed note.txt
```

### Line by line

- `rm -rf demo` removes only the lesson-owned directory in the disposable workspace, preventing stale evidence.
- `mkdir -p` creates an allowed tree, a sibling whose name shares the `allowed` prefix, and a protected sibling.
- Each `printf` creates synthetic text; none is a real credential or host file.
- `ln -s` places a pathname inside the allowed tree whose target object is outside it.
- The final command asks the naive broker for an ordinary allowed file. Expected: `allowed`.

## Exercise 2 - Test the lexical policy against known synthetic cases

Complete source of `naive_open.py`:

<!-- source: course/module-05-filesystem-landlock/lesson-01/naive_open.py format=code -->
```python
#!/usr/bin/env python3
import os
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} ROOT REQUEST", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).absolute()
    candidate = Path(os.path.abspath(root / sys.argv[2]))
    if not str(candidate).startswith(str(root)):
        print("DENIED: lexical prefix mismatch", file=sys.stderr)
        return 1
    print(candidate.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
<!-- /source -->

### Source, line by line

- `os.path.abspath` normalizes `..` text but does not resolve symlink targets.
- `Path.absolute` produces a pathname; it does not establish a kernel-enforced root.
- `startswith` compares characters. It cannot distinguish `allowed` from `allowed-escape` and does not identify the object behind `link.txt`.
- `read_text` performs a new lookup after the check, leaving both semantic mismatch and a check/use window.
- The exit status distinguishes a policy denial from normal completion.

Run both bypasses:

```bash
python3 naive_open.py demo/allowed ../allowed-escape/secret.txt
python3 naive_open.py demo/allowed link.txt
```

### Line by line

- `..` reaches the sibling `allowed-escape`; its absolute string still begins with the characters ending in `allowed`.
- `link.txt` has an allowed lexical name, but normal lookup follows it to `demo/protected/secret.txt`.
- Expected: both synthetic secret strings print. This proves the check is not a confinement boundary; it does not imply access to any path beyond this lesson.

## Exercise 3 - Repair the demonstrations, identify the limit

`resolved_open.py` resolves both root and candidate, then uses `relative_to` as a path-component comparison:

<!-- source: course/module-05-filesystem-landlock/lesson-01/resolved_open.py format=code -->
```python
#!/usr/bin/env python3
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} ROOT REQUEST", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve(strict=True)
    candidate = (root / sys.argv[2]).resolve(strict=True)
    try:
        candidate.relative_to(root)
    except ValueError:
        print("DENIED: resolved object is outside root", file=sys.stderr)
        return 1
    print(candidate.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
<!-- /source -->

### Source, line by line

- The imports provide argv and path operations; the usage guard requires a root and one request.
- `resolve(strict=True)` follows existing links and requires the referenced components to exist. Missing paths raise an exception rather than becoming a policy grant.
- The `/` operator on `Path` joins path components. It is not numeric division here. An absolute right-hand path can replace the left-hand prefix, so joining alone is not containment.
- `candidate.relative_to(root)` asks whether the resolved candidate can be expressed beneath the resolved root. A sibling with a similar name is not a child component.
- `except ValueError` handles that failed relationship check, prints a denial on stderr, and returns 1.
- `read_text` still performs its own later lookup. The successful relationship check did not hand it an already-authorized open descriptor.
- `end=""` preserves the supplied text's newline; `SystemExit` carries the function's result to the shell.

Run the supplied repaired comparison:

```bash
python3 resolved_open.py demo/allowed note.txt
python3 resolved_open.py demo/allowed ../allowed-escape/secret.txt || echo 'traversal denied'
python3 resolved_open.py demo/allowed link.txt || echo 'symlink escape denied'
```

### Line by line

- The first lookup remains functional and prints `allowed`.
- `resolve(strict=True)` follows existing symlinks and rejects missing components.
- `relative_to(root)` compares path components, avoiding the prefix-collision error.
- `|| echo` runs only after the expected nonzero denial; it makes the result visible without hiding success as failure.
- Expected: the allowed read succeeds and both escapes print `DENIED` plus the matching shell message.

The earlier naive implementation is the intentional incomplete control. Compare its results with this repaired component check; do not splice an expression into the `try` block and assume it has the same failure behavior as a raised exception. A false Boolean that nobody checks is not a denial.

This repair is useful application validation, but it still separates checking from opening. Another process could exchange a checked component before `read_text` opens it. Lesson 05.02 asks the kernel to resolve and open in one operation.

## Checkpoint and troubleshooting

```bash
test "$(python3 resolved_open.py demo/allowed note.txt)" = allowed
! python3 resolved_open.py demo/allowed ../allowed-escape/secret.txt
! python3 resolved_open.py demo/allowed link.txt
```

- `!` succeeds only when the guarded command fails, so these are denial assertions.
- If `ln` says the link exists, rerun the scoped `rm -rf demo` setup.
- If `resolve(strict=True)` reports a missing file, verify the setup paths rather than weakening strict resolution.
- Checkpoint: explain why component-aware resolution repairs these examples but is not atomic authorization.

## Replay and source truth

The demo contains only lesson-created synthetic files. Do not substitute personal directories or real credentials. From this workspace, `cd ../..` then `./lab-reset 05.01` discards this lesson's edits and fixtures after confirmation. No host mount, filesystem permission, or global security setting needs changing.

[Python pathlib](https://docs.python.org/3.14/library/pathlib.html) documents lexical and resolved path operations. Component validation is useful, but this lesson's check-then-open sequence is not an atomic kernel authorization boundary.
