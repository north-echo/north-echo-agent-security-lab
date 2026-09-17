# North Echo Agent Security Lab

## v0.1 field manual - Modules 01-03

This manual is the compact companion to the playable files under `course/`. The workspace `README.md` for each target remains the authoritative exercise. Run commands only in a disposable Linux VM as an ordinary user.

The rhythm is always: predict, run, observe, explain, break, fix, verify. Do not paste a complete lab solution from an AI. AI is optional as a tutor or debugger; the lab works without it.

Every guided workspace now follows meaningful command and code blocks with a **Line by line** explanation. This compact manual includes the same explanations for its representative blocks; the workspace lesson expands them further when a source file is involved.

## Platform quick start

```bash
./scripts/attest-course
./lab-start 01.01
cd .student/01.01
less README.md
```

Line by line:

- `./scripts/attest-course` verifies canonical lesson hashes before you create disposable work.
- `./lab-start 01.01` creates or resumes Module 01, Lesson 01.
- `cd .student/01.01` enters the generated editing area; canonical files remain under `course/`.
- `less README.md` opens the target's hands-on instructions. Press `q` to leave `less`.

Return to the repository root for lifecycle commands:

```bash
./lab-status
./lab-reset 01.01 --dry-run
./lab-reset 01.01 --yes
./lab-start 01.01
```

- `lab-status` reads persistent attempt/pass metadata without changing workspaces.
- `--dry-run` performs reset safety checks and prints intended actions without deleting anything.
- `--yes` confirms deletion non-interactively after the same containment checks pass.
- Starting again creates fresh randomized details while preserving only progress metadata.

After reset, the old student source and fixture disappear. A new start increments the persistent attempt count and creates a new synthetic ID, name, port, hostname, and canary.

# Module 01 - Processes, syscalls, and inherited authority

Outcome: trace a command to kernel-visible effects, then remove environment and descriptor authority before executing an untrusted tool.

## 01.01 - Processes are the boundary you actually launched

Establish the process facts:

```bash
printf 'shell pid=%s parent=%s\n' "$$" "$PPID"
ps -o pid,ppid,user,stat,comm,args -p $$ -p $PPID
readlink /proc/$$/exe
ls -l /proc/$$/ns
```

Line by line:

- `printf` formats the shell's PID (`$$`) and parent PID (`$PPID`).
- `ps -o ...` selects explicit process columns; the two `-p` arguments restrict the rows to those PIDs.
- `readlink /proc/$$/exe` reports the executable backing this shell.
- `ls -l /proc/$$/ns` reveals namespace symbolic-link targets; `-l` is necessary to display them.

Expected: the shell's `PPID` matches its parent row. Namespace handles look like `mnt:[402653....]`. A process carries identity, credentials, descriptors, memory, and namespace memberships; it is not merely command text.

Build and trace the starter:

```bash
cc -std=c11 -Wall -Wextra -O2 hello-syscall.c -o hello-syscall
./hello-syscall
strace -f -e trace=execve,write,exit_group ./hello-syscall 2>&1
```

- `cc` invokes the compiler; `-std=c11` selects C11, `-Wall -Wextra` enable warnings, `-O2` optimizes, and `-o` names the binary.
- `./hello-syscall` runs that exact local file rather than searching `PATH`.
- `strace -f` observes the process and any children.
- `-e trace=...` limits output to the three named syscalls.
- `2>&1` sends `strace`'s stderr to the same destination as stdout.

Expected: `execve(...) = 0`, one or more `write(...)` calls, then `exit_group(0)`. Change stdout buffering and observe why one source-level output call does not promise one syscall. Restore the starter before moving on.

## 01.02 - Environment inheritance is authority

Create an explicitly fake value and observe the child:

```bash
export DEMO_AGENT_TOKEN="fake-$(awk -F= '/fixture_id/{print $2}' FIXTURE.txt)"
python3 show-env.py
python3 launch-insecure.py
```

Line by line:

- `export` marks the fake token for child inheritance.
- `$(...)` runs the nested command and substitutes its output.
- `awk -F=` splits at `=`; the pattern selects `fixture_id` and `{print $2}` emits its value.
- The two Python commands demonstrate direct inheritance and inheritance through a launcher.

Expected: both programs print the fake token. The launcher uses `os.environ.copy()`, which looks explicit while preserving every ambient variable.

Replace the copied environment with an allowlist:

```python
child_env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
```

- This Python dictionary is a new allowlisted environment, not a copy of the parent.
- `PATH` allows command lookup only in the named system directories.
- `LANG` supplies predictable locale behavior without carrying unrelated variables.

Verify:

```bash
python3 launch-insecure.py | grep -F 'DEMO_AGENT_TOKEN=<absent>'
```

The child cannot choose to ignore a value it never receives. Place the control at the authority-transfer point.

## 01.03 - File descriptors cross exec

Compile the intentionally vulnerable parent and give it the generated fixture manifest:

```bash
cc -std=c11 -Wall -Wextra -O2 fd-parent.c -o fd-parent
MANIFEST=$(python3 -c \
  'import json; print(json.load(open(".north-echo.json"))["fixture_manifest"])')
./fd-parent "$MANIFEST"
```

Line by line:

- The compiler flags have the same roles as in Lesson 01.
- `python3 -c` runs the quoted expression; it parses `.north-echo.json` and prints `fixture_manifest`.
- A trailing `\` continues one shell command on the next physical line.
- `MANIFEST=$(...)` captures the printed path.
- `"$MANIFEST"` keeps that pathname as one argument.

Expected: the child lists a descriptor above 2 and reads the already-open manifest. It did not resolve the protected pathname.

Change the parent's open flags from `O_RDONLY` to:

```c
O_RDONLY | O_CLOEXEC
```

- `O_RDONLY` requests read-only access.
- C's bitwise OR operator combines independent flag bits.
- `O_CLOEXEC` asks the kernel to mark the new descriptor close-on-exec atomically.

Rebuild and verify the protected descriptor disappears across exec. Add a pre-exec check with `fcntl(fd, F_GETFD)` and confirm `FD_CLOEXEC` is set.

Key fact: a file descriptor is authority to an already-open kernel object. Later pathname restrictions do not revoke it.

## Module 01 independent practical

```bash
./lab-start module-01
cd .student/01.lab
less README.md
```

Implement the C11 `launcher.c` contract. The randomized grader requires the child command to work while withholding `NE_LAB_TOKEN` and all inherited descriptors above 2. It checks external effects, not a preferred implementation.

```bash
cd ../..
./lab-grade module-01
./lab-grade module-01 --mode exam
```

- `lab-start module-01` creates the independent target `01.lab`.
- `less` opens its contract without changing it.
- `cd ../..` returns from `.student/01.lab` to the repository root.
- `lab-grade` creates fresh evaluation details and observes the student's declared interface.
- `--mode exam` reduces hints; it does not change the tested properties.

Practice mode cites relevant lessons. Exam mode names only failed security properties.

# Module 02 - Linux namespaces

Outcome: compose user, UTS, PID, and mount namespaces and verify effective state. Namespaces are scoped changes to resource views, not a complete sandbox.

## 02.01 - Read namespace identity

Capture baseline handles:

```bash
for ns in user uts pid mnt net ipc cgroup; do
  printf '%-8s %s\n' "$ns" "$(readlink /proc/self/ns/$ns)"
done
```

Line by line:

- `for ns in ...; do` assigns each namespace name to `ns` in turn.
- `readlink /proc/self/ns/$ns` returns the current process's handle for that type.
- `$(...)` substitutes the handle into `printf`.
- Quoting `"$ns"` and the command substitution preserves one argument per value.
- `done` closes the loop.

Create a mapped user namespace:

```bash
unshare --user --map-root-user sh -c '
  echo "inside uid=$(id -u)";
  readlink /proc/self/ns/user;
  cat /proc/self/uid_map
'
```

- `unshare --user` requests a new user namespace.
- `--map-root-user` maps your ordinary host identity to namespace UID/GID 0.
- `sh -c '...'` runs the quoted multi-line program inside it.
- `id -u`, `readlink`, and `cat uid_map` observe inside identity, namespace identity, and the mapping respectively.

Expected: namespace UID 0, a different user-namespace handle, and a map back to your ordinary host UID. Try writing host `/root`; it should fail. Namespace root is not host root.

## 02.02 - Isolate UTS state

```bash
HOST_BEFORE=$(hostname)
unshare --user --map-root-user --uts sh -c '
  hostname north-echo-lab;
  echo "inside=$(hostname)";
  readlink /proc/self/ns/uts
'
echo "host before=$HOST_BEFORE host after=$(hostname)"
```

- The first command substitution captures the parent hostname before isolation.
- `--uts` adds an isolated hostname view; the mapped user namespace supplies capability inside the new namespace.
- The inner `hostname` changes only that UTS namespace.
- The final host-side command substitution proves the parent value is unchanged.

Expected: the child changes to `north-echo-lab`, while the host value is unchanged.

Intentional incomplete attempt:

```bash
unshare --uts hostname broken-attempt
```

As an ordinary user this normally fails with `Operation not permitted`. The mapped user namespace supplies capability in the new namespace; the UTS namespace alone does not.

## 02.03 - PID namespace and procfs

First make the common mistake:

```bash
unshare --user --map-root-user --pid --fork sh -c '
  echo "shell says pid=$$";
  ps -o pid,ppid,comm | head
'
```

- `--pid --fork` creates a PID namespace for a newly forked child.
- `--mount` isolates mount-table changes.
- `--mount-proc` mounts procfs associated with the new PID namespace.
- `$$` reports the shell's namespace-local PID; `ps` should now agree with it.
- The two `readlink` calls record the actual PID and mount namespace handles.

The shell says PID 1, but the inherited `/proc` mount may show the host view.

Correct the composition:

```bash
unshare --user --map-root-user --pid --fork --mount --mount-proc sh -c '
  echo "shell says pid=$$";
  ps -o pid,ppid,comm;
  readlink /proc/self/ns/pid;
  readlink /proc/self/ns/mnt
'
```

Expected: namespace PID 1, a small process list, and new PID/mount handles. A production runtime also needs an init/reaper strategy for PID 1.

<!-- PAGEBREAK -->

## Module 02 independent practical

Implement `sandbox.sh` so an arbitrary command receives fresh user, UTS, PID, and mount namespaces, a procfs matching the new PID namespace, and the randomized `NE_EXPECTED_HOSTNAME`. The command must be namespace PID 1 and retain normal arguments/output/exit behavior.

```bash
./lab-start module-02
cd .student/02.lab
chmod +x sandbox.sh
./sandbox.sh sh -c 'echo "pid=$$ host=$(hostname)"; ps -o pid,ppid,comm'
cd ../..
./lab-grade module-02
```

- `chmod +x` makes the script directly executable.
- Single quotes keep `$$` and `$(hostname)` from expanding in the outer shell; they run inside the sandboxed command.
- The relative `../../lab-grade` path reaches the repository root without copying or exposing a solution.

The grader compares namespace inode identities with its own process. Merely including the word `unshare` cannot satisfy it.

# Module 03 - Privilege, capabilities, and no_new_privs

Outcome: inspect complete process privilege state, empty capability channels, and establish a one-way no-new-privileges transition before exec.

## 03.01 - UIDs are not the whole story

```bash
id
grep -E '^(Uid|Gid|Groups|Cap(Inh|Prm|Eff|Bnd|Amb)|NoNewPrivs):' /proc/self/status
CAP_EFF=$(awk '/^CapEff:/{print $2}' /proc/self/status)
capsh --decode="$CAP_EFF"
```

Line by line:

- `id` reports user and group identity.
- `grep -E` uses the anchored alternation to select only privilege-related procfs fields.
- `awk` extracts the second field from `CapEff`, the hexadecimal mask.
- `CAP_EFF=$(...)` stores it; `capsh --decode` translates set bits to names.

Expected for an ordinary user: matching real/effective UIDs and usually an empty effective capability set. Compare with mapped namespace root:

```bash
unshare --user --map-root-user sh -c '
  id;
  grep -E "^(Uid|Cap(Inh|Prm|Eff|Bnd|Amb)):" /proc/self/status
'
```

- `unshare` creates mapped namespace root for comparison without granting host root.
- The inner `id` and `grep` observe namespace-relative IDs and capability masks.
- Their meaning must be interpreted with the user-namespace mapping, not in isolation.

The capability masks are meaningful relative to namespace ownership. Also inspect `getcap -r /usr/bin`: a nonzero UID does not by itself prove there is no privilege.

## 03.02 - Drop all relevant capability sets

Decode each set, then create a namespace where you can safely practice dropping them:

```bash
for field in CapInh CapPrm CapEff CapBnd CapAmb; do
  value=$(awk -v key="$field:" '$1==key{print $2}' /proc/self/status)
  printf '%-7s %s -> ' "$field" "$value"
  capsh --decode="$value"
done

unshare --user --map-root-user setpriv \
  --bounding-set=-all \
  --inh-caps=-all \
  --ambient-caps=-all \
  --clear-groups \
  sh -c 'grep -E "^Cap(Inh|Prm|Eff|Bnd|Amb):" /proc/self/status'
```

- Each trailing `\` continues the same shell command.
- `setpriv` changes privilege attributes before exec.
- `--bounding-set=-all`, `--inh-caps=-all`, and `--ambient-caps=-all` subtract all capabilities from the named channels.
- `--clear-groups` removes supplementary groups.
- The final shell prints all five capability masks after the transition.

Expected: zero masks. Then drop only the inheritable set and observe that naming one set is not equivalent to clearing every capability channel.

## 03.03 - Make privilege non-gainable

Build the launcher and inspect the child state:

```bash
cc -std=c11 -Wall -Wextra -O2 nnp-launch.c -o nnp-launch
./nnp-launch sh -c 'grep -E "^(NoNewPrivs|CapEff):" /proc/self/status'
```

- `cc` builds the launcher with warnings.
- `./nnp-launch` receives every remaining token as the child command and arguments.
- `sh -c` runs the quoted observation after the launcher sets its policy.
- The anchored expression selects the sticky bit and effective capability mask from the executed child.

Expected: `NoNewPrivs: 1`. Move the `prctl` after `execvp` as an intentional mistake: successful exec never reaches that code, so the child reports 0. Restore it before exec and verify a grandchild also sees 1.

`no_new_privs` is sticky but narrow. It does not empty current capabilities, close descriptors, scrub environment, isolate files, or filter syscalls.

<!-- PAGEBREAK -->

## Module 03 independent practical

Implement `secure-launch.c`. The executed command must see `NoNewPrivs: 1`, empty effective/permitted/inheritable/ambient capability sets, and the invoking ordinary UID while retaining its command interface.

```bash
./lab-start module-03
cd .student/03.lab
cc -std=c11 -Wall -Wextra -O2 secure-launch.c -o secure-launch
./secure-launch sh -c \
  'grep -E "^(Uid|CapInh|CapPrm|CapEff|CapAmb|NoNewPrivs):" /proc/self/status'
cd ../..
./lab-grade module-03
```

- The compile command checks the same interface the grader will use.
- The local probe reads the child's kernel-reported state rather than trusting source intent.
- `cd ../..` returns to the repository root and `lab-grade` runs the randomized external probe.

# Completion and replay

After passing all three module labs:

```bash
./lab-status
./lab-reset --all --dry-run
./lab-reset --all --yes
./lab-start 01.01
```

- `lab-status` records the end state before destruction.
- The dry run validates every reset target and resource without mutation.
- The confirmed all-scope reset removes student work and fixtures but retains metadata.
- Starting `01.01` proves the course can begin again without the previous solution.

The new run contains no prior solution. If the commands feel familiar but the answer is not sitting in front of you, replayability is doing its job.

Modules 04-12 continue from process hygiene into an actual local agent, filesystem and syscall policy, resources, network, credentials, composed runtime, break/fix research, and finally an adaptive cold capstone. See `ROADMAP.md`.
