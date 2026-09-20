# North Echo Agent Security Lab - Complete Field Manual v2.0.0-beta.2

Learner-review beta: setup, source/version notes, beginner entry chapters, learning path, twelve rewritten technical modules, and an independent capstone. Use only a disposable Linux VM with synthetic data. Complete source listings and local explanations support guided practice; independent labs withhold implementations. Automated validation does not establish beginner comprehension or production security. See the release's validation records for exact scope.

<!-- PAGEBREAK -->

# Disposable Linux VM setup

## Choose the baseline

For this learner-review beta, **Fedora 44 ARM64 on Apple Silicon** is the preferred new-install path. The image is pinned, SELinux remains enforcing, and the course runs as an ordinary user. Fedora x86-64 is not covered by this template or inferred from ARM64 results.

Ubuntu 24.04 remains a compatibility path with a separate pinned template and x86-64/ARM64 CI. Read the release's validation record for the exact revision tested; old release evidence does not validate new code. Debian and other distributions are not acceptance baselines.

Desktop versus Server is not the deciding feature. A real booted Linux kernel, user systemd manager, delegated cgroup v2 controllers, user/network namespaces, working Landlock/seccomp, and the required toolchain are. A minimal cloud/server image avoids unnecessary desktop components. A container on macOS is not this guest environment.

Use 4 CPUs, 6 GiB memory, and 30 GiB disk. No real credentials, production data, shared host directory, SSH-agent forwarding, or public service is needed.

## Create a separate beta VM on your Mac

Install Lima 2.2 or newer using its official installation instructions, then check `limactl --version`. These are **Mac host** commands. Choose a new name; do not reuse or delete your existing `north-echo` learner VM.

```bash
git clone --branch v2.0.0-beta.2 --depth 1 \
  https://github.com/north-echo/north-echo-agent-security-lab.git \
  north-echo-beta2-source
cd north-echo-beta2-source
limactl start --name north-echo-beta2 deploy/north-echo-fedora.yaml
limactl shell north-echo-beta2
```

Beta.2 includes the corrected file-backed validation runner in the learner's user-manager context. Keep SELinux enforcing; no policy relaxation is needed. Use a new instance rather than restarting a failed beta.1 installation.

The tagged checkout contains the template and its companion package list. Run the start command from that checkout. Fedora installation downloads the pinned image and release; first boot takes longer than a restart. Successful readiness is required before beginning.

The last command opens the **Linux guest** shell. Now, inside it:

```bash
cd ~/north-echo
pwd
./scripts/linux-preflight
./scripts/attest-course
./lab-start b0.01
cd .student/b0.01
less README.md
```

The installer places the course under the guest user's home, not in a host mount. Preflight checks actual prerequisites; attestation checks canonical file integrity. `lab-start` prepares a student copy. `less` reads instructions; press q to exit. Do not type Linux exercise commands into your Mac shell.

If you already know the B0 material, return to the guest course root and try `./lab-start module-b0`; its directory is `.student/b0.lab`, not `.student/module-b0`.

## What is pinned and what can change

The Fedora image is `Fedora-Cloud-Base-Generic-44-1.7.aarch64.qcow2`, with SHA-256 `55c60a3b80d3616a08705afd0459e75fe9f03c54aba7a46e4002a41a72fa0d5b`. The template contains its full release URL. Ubuntu's template separately pins dated images for both supported architectures.

The course version is `v2.0.0-beta.2`. Provisioning downloads its archive and `SHA256SUMS`, checks the selected artifact, and validates the installed course before writing readiness. Checksums obtained from the same release detect mismatches, not compromise of the release publisher.

Package repositories still deliver current package revisions; an image digest does not freeze later package installation. Deployment evidence records exact installed versions. Fedora consumes `deploy/fedora-packages.txt`; Ubuntu and GitHub Actions consume `deploy/ubuntu-packages.txt`. They are distinct distro package names, not interchangeable lists. CI's Ubuntu jobs do not substitute for a booted Fedora validation run.

Both templates use Lima plain mode without host mounts, guest agent, dynamic port forwarding, built-in container runtime, Rosetta, or SSH-agent forwarding. Shell access, readiness probes, and file copy use SSH. Plain-mode copy and a deliberately failing readiness probe are part of appliance acceptance, not merely assumptions.

## Restart, export, and reset

Exit the guest shell with `exit`. These commands run on the **Mac host**:

```bash
limactl stop north-echo-beta2
limactl start north-echo-beta2
limactl shell north-echo-beta2
```

A readiness marker makes normal restarts idempotent: they do not reinstall over your source or re-extract over student work. Restarting an old release does not upgrade it. To review another version, use another instance or separately validated directory.

Export the synthetic first-install evidence from the **host**:

```bash
limactl copy north-echo-beta2:~/north-echo-deployment-evidence.tgz .
```

This is not a backup of your solutions. To save work, run inside the **guest course root**:

```bash
tar -czf ~/north-echo-student-work.tgz .student .state
```

Then copy it from the **host**:

```bash
limactl copy north-echo-beta2:~/north-echo-student-work.tgz .
```

Keep the work archive private: it contains solutions and notes. Verify it reached the host before deleting anything.

<!-- PAGEBREAK -->

Deleting/recreating is the factory reset, and destroys **all unexported work in that exact VM**. Only after export and only if you want a clean instance:

```bash
limactl delete -f north-echo-beta2
limactl start --name north-echo-beta2 deploy/north-echo-fedora.yaml
```

No deletion is needed for an ordinary restart or a single lesson reset.

## Ubuntu compatibility path

Use a different new instance name on the **host**:

```bash
limactl start --name north-echo-beta2-ubuntu deploy/north-echo.yaml
limactl shell north-echo-beta2-ubuntu
```

Then follow the same guest course-root and B0 steps. Do not use the Fedora package list with apt. The Ubuntu installer applies the narrow course AppArmor profile only if the ordinary user-namespace check requires it; it does not disable AppArmor globally.

## Manual provisioning inside a disposable Linux VM

First create an ordinary account and log in as that account. These are **guest** commands. For Fedora:

```bash
sudo dnf install -y git ca-certificates
git clone --branch v2.0.0-beta.2 --depth 1 \
  https://github.com/north-echo/north-echo-agent-security-lab.git \
  north-echo
cd north-echo
xargs sudo dnf install -y < deploy/fedora-packages.txt
test "$(getenforce)" = Enforcing
```

For Ubuntu, use this alternative, not both blocks:

```bash
sudo apt-get update
sudo apt-get install -y git ca-certificates
git clone --branch v2.0.0-beta.2 --depth 1 \
  https://github.com/north-echo/north-echo-agent-security-lab.git \
  north-echo
cd north-echo
xargs sudo apt-get install -y < deploy/ubuntu-packages.txt
if ! unshare --user --map-root-user true; then
  sudo install -m 0644 validation/apparmor-north-echo-unshare /etc/apparmor.d/north-echo-unshare
  sudo apparmor_parser -r /etc/apparmor.d/north-echo-unshare
fi
```

Then on either guest, enable the **actual ordinary user's** manager and validate:

```bash
test "$(id -u)" -ne 0
sudo loginctl enable-linger "$(id -un)"
./scripts/linux-preflight
./scripts/attest-course
python3 scripts/run_tests.py --require-no-skips
```

Do not run these from a root shell: `id -un` must identify the learner, not root. If the user manager is unavailable, log out and back into the guest as that account, then retry. Do not run lessons with sudo to bypass a failure.

## Troubleshooting without weakening the boundary

A failed readiness probe returns failure but does not necessarily power the guest off. Stop it explicitly from the host if required. Inspect the guest's `/var/log/cloud-init-output.log` and deployment evidence. Do not treat a booted login prompt as successful course validation.

If installation left `~/north-echo` but no readiness marker, the installer refuses to overwrite it. Export anything needed and recreate that disposable instance. Do not hand-create a readiness marker to suppress failures.

For a failing preflight, keep the exact failing check and environment versions. Static compilation, actual Landlock/seccomp enforcement, and effective user-manager limits are required—not just installed command names. Keep SELinux enforcing and AppArmor enabled. Never modify your Mac, employer host, LAN firewall, or shared server to force a lesson to pass.

The [source/version companion](SOURCE_TRUTH.md) explains baseline differences. The [Linux validation matrix](LINUX_VALIDATION.md) is the maintainer acceptance procedure, not extra required beginner homework. Lima's [official documentation](https://lima-vm.io/docs/) is optional setup reference.

# Source truth, versions, and limits

This beta separates three things: **documented behavior**, **North Echo's chosen
exercise policy**, and **observations on a recorded guest**. A source link is not
an experiment, a passing test is not a universal security guarantee, and neither
establishes learner comprehension.

Every guided lesson includes its own complete small sources and explanations.
The references below are verification and optional depth, not missing lesson
content that a beginner must reconstruct.

## Fedora companion to the beginner chapters

The B0/B1 lessons were first reviewed on Ubuntu 24.04 ARM64 with Bash 5.2.21,
coreutils 9.4, Python 3.12.3, and nano 7.2. Their explicit 3.12/Noble references
identify that review; they do not claim those are Fedora's installed versions.
The positively reviewed B0.02 teaching sequence is preserved.

The Fedora 44 ARM64 validation guest reports Bash **5.3.9**, coreutils **9.10**,
Python **3.14.3**, and nano **8.7.1**. B0/B1's documented-command and grader tests
run in the strict Fedora suite. Installed `man bash`, `help pwd`, `help cd`,
and `man nano` were consulted for the guest's actual interfaces. Python's
maintained 3.14 web documentation currently identifies 3.14.7, not the guest's
3.14.3; the reviewed examples use established interfaces exercised on that guest.

For the same beginner claims on Fedora, see Python 3.14's
[process/environment interfaces](https://docs.python.org/3.14/library/os.html),
[argument vector](https://docs.python.org/3.14/library/sys.html#sys.argv),
[text paths](https://docs.python.org/3.14/library/pathlib.html#pathlib.Path.read_text),
and [subprocess handoff](https://docs.python.org/3.14/library/subprocess.html).
Reading a file, editing it, and executing it remain different operations.
PID values legitimately vary; selected environment data is not a filesystem
sandbox; text preservation in these exercises is not arbitrary byte preservation.

Use the editor's displayed bindings. The default nano commands taught here are
Ctrl+O, Enter to save, and Ctrl+X to exit. Nano's optional modern-bindings mode
changes those keys; its installed manual documents that variant and Ctrl+G help
for the default mode. Do not infer key bindings from version number alone.

## Kernel and tool baseline

The pinned Fedora image booted kernel **6.19.10-300.fc44.aarch64** with SELinux
enforcing. The validation package set included GCC 16.2.1, systemd 259.5,
libseccomp 2.6.1, and kernel headers 7.2.4. Installed package versions can float
after image boot; each deployment exports its own inventory.

The running kernel reports **Landlock ABI 7**. Newer build headers or current
online documentation do not make later kernel features available. In particular,
pathname Unix-socket connection control added in ABI 9 is not demonstrated on
that ABI-7 guest. A successful intended broker operation is not evidence that
all other pathname Unix sockets are inaccessible.

SELinux enforcing is retained throughout. The Lima learner's unconfined SELinux
context is not a per-lesson SELinux sandbox. The course's observed boundaries
come from the explicitly installed controls; do not attribute every denial to
SELinux or disable it to diagnose a failure.

## Claim-to-mechanism review

The map names important reviewed claims and corrections, not a claim that every
possible implementation error has been excluded. Each lesson's source section
and its validation record provide the narrower context.

| Material | Primary interface and reviewed claim | Required observation or limitation |
| --- | --- | --- |
| 01 | [execve](https://man7.org/linux/man-pages/man2/execve.2.html), [close_range](https://man7.org/linux/man-pages/man2/close_range.2.html): program replacement is not a clean authority slate | Inspect child environment and descriptors; compare with intentionally omitted cleanup, not merely an already-clean parent |
| 02 | [namespaces](https://man7.org/linux/man-pages/man7/namespaces.7.html), [pid_namespaces](https://man7.org/linux/man-pages/man7/pid_namespaces.7.html): membership and resource view are distinct | Namespace-local procfs and child PID matter; a failed unshare is setup failure, not a successful denial |
| 03 | [capabilities](https://man7.org/linux/man-pages/man7/capabilities.7.html), [no-new-privileges](https://docs.kernel.org/userspace-api/no_new_privs.html): sets and exec restrictions are different mechanisms | Show current capability reduction from nonempty input; no-new-privileges alone does not remove current authority |
| 04 | [subprocess](https://docs.python.org/3.14/library/subprocess.html): argv, environment, output, and status have separate roles | Observe actual work and preserve an earlier failed action even when a later one succeeds; ordinary exits are not general signal forwarding |
| 05 | [openat2](https://man7.org/linux/man-pages/man2/openat2.2.html), [Landlock](https://cdn.kernel.org/doc/html/latest/userspace-api/landlock.html): anchored lookup and task policy solve different problems | A separate resolve/read check has a race; pre-opened descriptors require hygiene; unhandled rights remain allowed; headers and runtime ABI must both be considered |
| 06 | [seccomp filter](https://docs.kernel.org/userspace-api/seccomp_filter.html), libseccomp's installed/API man pages | Actual allowed/denied syscalls matter; mode 2 alone does not identify a policy; syscall filtering does not inspect pathname strings as a filesystem policy |
| 07 | [cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html), installed `man systemd-run` and `man systemd.resource-control` | Read effective limits, require specific OOM/PID-limit evidence, distinguish client timeout from service collection, disable manager argv expansion for literal arguments |
| 08 | [network namespaces](https://man7.org/linux/man-pages/man7/network_namespaces.7.html), [Unix sockets](https://man7.org/linux/man-pages/man7/unix.7.html), Python socket/HTTP interfaces | Compare actual namespace and connection outcomes; loopback is per-network-namespace; pathname Unix sockets still use the shared filesystem; reauthorize each redirect and reload policy explicitly |
| 09 | [HMAC](https://docs.python.org/3.14/library/hmac.html), [base64](https://docs.python.org/3.14/library/base64.html), subprocess/socket interfaces | HMAC is shared-key authentication, not asymmetric signing; encoded claims are readable; mode 0600 does not separate same-UID roles; nonce state is process-local and consumed before upstream use |
| 10 | [setpriv](https://man7.org/linux/man-pages/man1/setpriv.1.html), [proc status](https://man7.org/linux/man-pages/man5/proc_pid_status.5.html), the earlier kernel interfaces | Observe all five capability sets, limits, denials, intended broker work, and exact collection; no private PID/mount view, durable broker, or remote cryptographic attestation is claimed |
| 11 | [random](https://docs.python.org/3.14/library/random.html), [tempfile](https://docs.python.org/3.14/library/tempfile.html), [os.replace](https://docs.python.org/3.14/library/os.html#os.replace) | Fixed local effects and model choices are different; missing fields are unknown; atomic publication is not durable policy correctness; no arbitrary plan text executes |
| 12 | JSON/subprocess mechanics and [hashlib](https://docs.python.org/3.14/library/hashlib.html) | Inventory supplies the answer; offline rows are supplied data; complete favorable observations are still limited; hashes do not authenticate a package or authorize unfamiliar code |
| Capstone | Course-defined batch interface composed from the practiced mechanisms | Preserve ordered 0/7/0 results and independent limits; reject a malformed later job before guard entry; exact unit absence and human reasoning are separate requirements |

The systemd web pages were unavailable during review, so the installed upstream
manuals in the actual Fedora guest were used. Local documentation is often the
best version-specific source; do not quietly substitute current web behavior for
the installed tool. Python URL parsing is likewise not an authorization policy:
the broker's explicit checks remain course code that needs tests.

## Evidence and learner review

Tranche records under `validation/*-rewrite-20260919/` identify candidate archive
hashes, exact test counts, skips, preflight, corrections, and residual limits.
They include tests that replay actual guided command blocks, not only reference
implementations. The capstone record also documents a failed negative-test design
and its correction. Final release/installation evidence is a separate gate.

Repository-specific preparation, fresh fixtures, grading, registration, reset,
and progress semantics come from the platform code and its tests, not from Python
or Linux documentation. The platform is not a hostile multi-user security boundary.
No external target or real credential is needed to reproduce these observations.

The human questions remain: can a learner predict, explain, repair, and transfer
the skill after a delay? Record uncertainty and missing steps against an exact
lesson and release. Do not turn generated feedback, test counts, page counts,
or cited sources into fabricated learning evidence.

# North Echo - Beginner entry chapters

**Learner-review beta.** Begin with a short basics refresher and one complete
environment-handoff problem before the numbered technical track. Pause at
checkpoints and report missing explanations; a passing grade alone is not mastery.

## Before starting

Use a disposable Linux VM, synthetic data, and an ordinary non-root account.
The repository root is the directory containing `lab-start`, `lab-grade`, and
`course/`. All preparation commands below start there. Do not type exercise
commands on your Mac, and do not put real credentials into a lab.

The v2.0.0-beta.1 appliance and manual include these chapters. The older v1.0.2
appliance does not; merely restarting it will not upgrade the course, by design.
Use a separate new beta VM as described in [VM setup](VM_SETUP.md). Do not extract
over an existing student's directory or migrate their unfinished work silently.

Run `./scripts/attest-course` and `./scripts/linux-preflight` from that copy's
root before starting. Attestation checks canonical files; preflight checks
the supported Linux environment. Neither checks your understanding.

## How to use the instructions

Use the Bash shell inside the VM. Blocks labeled `bash` are commands to type
there, one line followed by Enter unless explicitly shown otherwise. Blocks
labeled `python` show source in the named file; do not paste them into Bash.
Blocks labeled `text` show data or expected output, not commands. A source
listing in this manual is not a substitute for locating that file in your VM;
each guided program now has explicit `pwd`, `ls -l`, and `cat` access steps.

Reading with `cat` displays a file and returns to the prompt. Opening it with
`nano` enters an editor. Running `python3 filename.py` executes its instructions.
Those are three different actions. Lessons say which one you need, when to
save a change, and how to check the saved file before running it again.

At the repository root, run `pwd` and keep its printed path in your notes.
If you lose your place, that is the directory to return to. Do not blindly
repeat `cd .student/...` while already inside a lesson: relative paths start
from your current location. A failed `cd` does not put you in the intended
directory. Stop, check `pwd`, and correct the location before editing a file.

## Choose your entry point

If shell commands, paths, exit status, or small Python edits are unfamiliar,
start with `./lab-start b0.01`. If these are familiar, try
`./lab-start module-b0` as a diagnostic. Passing the practical and explaining
its review questions lets you go directly to `./lab-start b1.01`.

This is not a timed course. Work in short sessions and stop when a prediction
does not match an observation. Read the explanation, predict, run, compare,
then explain in your own words. Exact commands belong in guided practice;
the independent lab removes them only after you have practiced the skills.

`lab-start` resumes an existing workspace without erasing it. `lab-grade` gives
feedback on independent labs; guided lessons use observation checkpoints.
`lab-reset TARGET --dry-run` previews removal; `--yes` confirms it and discards
that target's student work/fixtures. Do not reset work you want to retain.

## What to record for learner review

For each lesson, note your prediction, observed result, an explanation in your
own words, and the first place you needed help. Distinguish unclear teaching
from VM setup trouble. After B1's practical, explain the remaining authority
of the worker. Try it again later with fresh fixtures before calling it learned.
Do not post private terminal history or environment dumps with feedback.

## How the technical explanations are grounded

Each lesson and practical ends with **Sources and scope**: named primary
documentation, the claims it supports, and limits on the lesson's conclusions.
The lesson itself still contains the required teaching. External links are
for verification and optional detail, not homework needed to fill missing steps.

Three kinds of statement are kept separate: documented API/command behavior;
North Echo's chosen example or policy; and results actually observed on a
specific VM. Test results support the third, not a claim about every machine.
The initial review used Ubuntu 24.04.5 arm64, Bash 5.2.21, coreutils 9.4,
Python 3.12.3, and nano 7.2. The lesson links retain that explicit source context.
The [Fedora source companion](SOURCE_TRUTH.md) records the newer guest's actual
versions, corresponding primary interfaces, and repeated behavioral checks.
No Windows or macOS exercise equivalence is implied.

The [source-review record](dev/BEGINNER_SOURCE_REVIEW.md) maps the reviewed
claims and records corrections for the initial B0/B1 review. The complete beta's
source/version map is separate. Learning effectiveness still needs your walkthrough.

<!-- PAGEBREAK -->

<!-- source: course/module-b0-basics/README.md format=markdown -->
# B0 - Working at the terminal

This optional refresher prepares you to change and test a small Python program.
It is not a replacement for an introductory Linux administration course.

You will locate a file, distinguish a program from a process, interpret success
and failure, and change a reader so it uses the filename you supply.
No prior Python knowledge is assumed; shell basics are introduced as needed.

If you already use the shell comfortably, try the B0 independent lab first.
Passing its automated checks **and** explaining its review questions lets you
skip the guided refresher. If you need help, the failed properties point back
to specific lessons. A failed first attempt is diagnostic, not a penalty.

Work only inside a disposable Linux VM. Start commands run from the repository
root, the directory containing `lab-start`. Each lesson then names its working
directory. Do not edit `course/`. Your copies live under `.student/`.

Sequence: `b0.01`, `b0.02`, `b0.03`, then `module-b0`.
Allow several short sessions; no speed target is part of assessment.
<!-- /source -->

<!-- source: course/module-b0-basics/lesson-01/README.md format=markdown -->
# B0.01 - Locate and read a report

## Outcomes

Find your current directory, identify the file a relative path names, and read
a filename containing a space without accidentally supplying two filenames.

## Understand first

A terminal accepts text and displays results. The **shell** is the program
interpreting the commands you type. A command usually names a program followed
by arguments: information that tells that program what to do. Press Enter to
run one command. Our code blocks omit the shell prompt; type only the commands.

A **file** holds data; a **directory** groups names. The shell has a current
working directory. A relative path is interpreted from there. `..` means the
parent directory. An absolute path begins with `/` and does not depend on the
working directory. Spaces normally separate arguments, so quote a path that
contains a space. Quotes group the argument; they are not part of its name.

The scenario is ordinary on purpose: a delivery team has two reports. Before
we restrict a reader, we need to know which report we actually asked it to read.

## Before you begin

In the VM, return to your repository root. Then:

```bash
./lab-start b0.01
cd .student/b0.01
```

Line by line: `./lab-start` runs the course helper in the current directory and
creates a working copy plus synthetic reports. `cd` changes the shell's working
directory to that copy. Starting again resumes it; it does not erase your work.

The reports already exist: you do not need to create them or type their contents.
`report.txt` and `weekend report.txt` are data to inspect; `README.md` is this
guide. The directory `notes` contains a third text file. A leading `./` means
"in this directory"; `.student` is the course's student-work directory, not a
command. Its leading dot makes it normally hidden in a plain directory listing.

## Exercise 1 - Establish where you are

```bash
pwd
ls
cat report.txt
cat "weekend report.txt"
```

Line by line: `pwd` prints the current directory; its ending should be
`.student/b0.01`. `ls` lists names there. The first `cat` displays the daily
report. The second supplies one quoted filename to display the weekend report.
Expect a generated delivery identifier and parcel counts. Identifiers differ
between attempts; do not compare them against a screenshot or memorize them.

`cat` returns you to the shell after displaying the file. It does not start an
editor, so there is nothing to save or quit. Reading a file is different from
executing instructions in it. Here, parcel-count sentences are just text.
For the daily report, expect this shape (do not type this output):

```text
Delivery report for <generated identifier>
Three parcels arrived.
```

The angle-bracketed phrase represents a changing identifier, not literal file
content. The first line identifies this attempt; the second is the report data.

## Exercise 2 - Make and diagnose a path mistake

Predict which of these commands will fail before running them:

```bash
cd notes
cat location.txt
cat report.txt
cat ../report.txt
cd ..
```

Line by line: `cd notes` enters the child directory. `cat location.txt` reads its
orientation note. `cat report.txt` fails because that name is not in `notes`.
`cat ../report.txt` repairs the lookup by naming the parent's report. `cd ..`
returns to the lesson directory. The missing-file error does **not** show an
access-control denial: we simply asked for the wrong path.

The complete supplied note is:

```text
You are reading a file inside the notes directory.
The delivery reports are one directory above this one.
```

The first line describes location; the second tells you how the reports relate
to it. Neither line changes the filesystem: this is data, not a command.

## Checkpoint - Try without the command sequence

From the lesson directory, enter `notes`, read the weekend report without
leaving `notes`, and return. Explain why the quotes and `..` solve different
problems. If stuck, revisit Exercise 2 and then try again without looking.

Do not proceed until you can predict the result from your current directory.
There is no automatic grade for guided lessons.

## Troubleshooting and finish

If `./lab-start` is missing, you are not at the repository root. If `cd notes`
fails, check `pwd` and `ls`; do not create a replacement directory to hide the
mistake. Use `cd ..` only when you know which parent you intend to enter.

```bash
cd ../..
```

From the lesson directory this returns to the repository root. You may stop
here and resume later. To discard this lesson's files, run from that root:

```bash
./lab-reset b0.01 --dry-run
./lab-reset b0.01 --yes
```

The first command previews removal. The second removes this lesson's workspace
and fixtures, including your edits. It leaves other lessons alone. Reset is
optional, not a prerequisite for starting the next lesson.

## Sources and scope

- [Ubuntu 24.04 Bash manual](https://manpages.ubuntu.com/manpages/noble/man1/bash.1.html),
  QUOTING and SHELL BUILTIN COMMANDS (`cd`, `pwd`): command interpretation and
  navigation. The lab uses ordinary paths without symlink-navigation edge cases.
- [GNU ls manual shipped by Ubuntu](https://manpages.ubuntu.com/manpages/noble/man1/ls.1.html)
  and [GNU cat manual](https://manpages.ubuntu.com/manpages/noble/man1/cat.1.html):
  listing names and displaying file contents.

Report names and parcel counts are North Echo fixtures, not Linux guarantees.
The relative-path failure is an observed exercise result, not evidence of a
security restriction. References support the explanation; opening them is optional.
<!-- /source -->

<!-- source: course/module-b0-basics/lesson-02/README.md format=markdown -->
# B0.02 - A program is not its running process

## Outcomes

Identify a running program's process and parent, and check failure independently
of the text it printed. Prerequisite: B0.01 or equivalent shell experience.

## Understand first

A **program** is stored instructions. A **process** is one running instance of
those instructions. Running the same file twice normally creates two different
processes. A process ID (**PID**) identifies a process while it exists; it is
not a permanent identity. The parent is the process that launched it. Here,
your shell launches Python, which reads a program file.

The child can print text and then finish with an **exit status**. By convention,
zero means success and a nonzero number means failure. These are different
channels: a cheerful printed message is not proof of success. In the shell,
`$?` expands to the most recent command's status. Check it immediately, before
another command replaces it.

## Before you begin

From the VM repository root:

```bash
./lab-start b0.02
cd .student/b0.02
```

The first command prepares or resumes this lesson. The second enters its
working copy. You do not need to install Python packages or use `sudo`.

## Read the small program

`lab-start` supplied a file named `identify.py` in `.student/b0.02`. You do not
need to create or edit it. Stay in the directory entered above and inspect it:

```bash
pwd
ls -l identify.py
cat identify.py
```

Line by line: `pwd` should end in `.student/b0.02`. `ls -l identify.py` lists
details for that one file: file type/permissions, link count, owner, group,
size, modification time, and name. Those details can vary; the name should be
`identify.py`. We are locating the file, not changing its permissions.
`cat identify.py` prints its contents and returns to the shell. It does **not**
execute the Python statements. If the file is missing, stop and check the
working directory before proceeding; do not open an editor and create a blank
replacement with the same name.

Compare what `cat` prints with the complete source below. This is a listing of
an existing file, not commands to paste into the shell. No editor is needed
in B0.02; B0.03 will explicitly introduce opening, saving, and checking an edit.

```python
import os
import sys

print("This is one running copy of identify.py.")
print("Process ID:", os.getpid())
print("Parent process ID:", os.getppid())
if "fail" in sys.argv[1:]:
    print("I printed a message, but I am reporting failure.")
    raise SystemExit(7)
print("Finished successfully.")
```

Line by line: `import os` loads process-information functions. `import sys`
loads the argument interface. Each `print` writes a line to standard output,
the ordinary result stream. `os.getpid()` asks for this process's ID;
`os.getppid()` asks for its parent's ID. `sys.argv` is the argument list:
element zero names the script, and `[1:]` selects everything after it.
`if` conditionally runs its indented lines. When `fail` is present, the program
prints a message and `raise SystemExit(7)` ends it with status 7. Otherwise it
reaches the last print and ends normally with status zero. Indentation groups
Python statements; keep the supplied spaces when editing later.

### Follow the decision, not just the spelling

`import` makes a library available under a name. A library is reusable program
code: `os` and `sys` are included with Python, so these imports do not download
anything. In `os.getpid()`, the dot selects a function from `os` and the empty
parentheses call it with no arguments. `print` displays the value returned.

An **argument list** is an ordered sequence. Python numbers its positions from
zero. With `python3 identify.py fail`, `sys.argv` contains `identify.py` at
position zero and `fail` at position one. `[1:]` selects the entries starting
at position one. The `in` expression asks whether that selected sequence
contains the text `fail`; it produces a true/false decision.

Read the `if` as: "If that argument is present, do the indented actions."
`SystemExit(7)` supplies the exit condition and `raise` triggers it, so execution
does not continue to the final success print. Without `fail`, Python skips
that indented block and reaches the last line. The number 7 is our chosen
demonstration value, not a universal code for a particular operating-system error.

Before executing, point to the line that changes the exit status. This checks
your interpretation of the source before terminal output can suggest an answer.

## Exercise 1 - Observe two runs

Now run the file, using the same working directory:

```bash
python3 identify.py
echo $?
python3 identify.py
echo $?
```

Each `python3` starts a process running the same file. Each `echo` prints the
preceding status. Expect `Finished successfully.` and status `0` both times.
The process IDs normally differ; the parent ID should be the same shell.
This demonstrates new executions, not a security boundary. The processes end
quickly; you do not need to kill them or inspect a stale PID.

`python3` names the interpreter: the program that executes Python source.
`identify.py` tells it which file to read as instructions. There is no need to
make the `.py` file executable or run `chmod`; we are invoking the interpreter.
After each run, expect this output pattern followed by the status from `echo`:

```text
This is one running copy of identify.py.
Process ID: <number for this run>
Parent process ID: <number for the launching shell>
Finished successfully.
0
```

The placeholder numbers vary. The final `0` is printed by `echo`, not by
`identify.py`. `echo` is itself another command with its own status, which is
why you must check `$?` before running unrelated inspection commands.

## Exercise 2 - Text can accompany failure

Predict the next status, then run:

```bash
python3 identify.py fail
echo $?
```

`fail` is an argument to our script, not a Python option. The program prints its
failure message but exits with `7`. `echo` exposes that result. Repair this
deliberately failing invocation by running `python3 identify.py` with no `fail`
argument, then check `$?` again. Expected repaired status: `0`.

## Checkpoint

Without rerunning, explain whether the file, process, or both changed between
the two successful invocations. Then demonstrate a failed invocation and show
its status without accidentally reporting the status of `echo` instead.
Explain why looking only for a line of output would be a weak test.

## Troubleshooting and finish

An unexpected `0` often means another command ran before `echo $?`. Try the
two-line pair again. If Python cannot find the file, check `pwd` and `ls` as in
B0.01; do not change system Python settings.

```bash
cd ../..
```

This returns from the lesson directory to the repository root. Optional reset:
`./lab-reset b0.02 --dry-run` previews removal; `./lab-reset b0.02 --yes`
discards this lesson's workspace and fixtures. Nothing remains running.

## Sources and scope

- [Python 3.12 os](https://docs.python.org/3.12/library/os.html#os.getpid):
  `getpid()` and `getppid()` identify the current process and its parent.
- [Python 3.12 sys.argv](https://docs.python.org/3.12/library/sys.html#sys.argv),
  [if statements](https://docs.python.org/3.12/tutorial/controlflow.html#if-statements),
  and [SystemExit](https://docs.python.org/3.12/library/exceptions.html#SystemExit):
  script arguments, conditional execution, and the exit mechanism.
- [Python interpreter invocation](https://docs.python.org/3.12/using/cmdline.html#interface-options)
  and [print](https://docs.python.org/3.12/library/functions.html#print): running
  a source file versus displaying text.
- [Ubuntu 24.04 Bash manual](https://manpages.ubuntu.com/manpages/noble/man1/bash.1.html),
  EXIT STATUS: the shell's success convention and `$?`.
- [ls -l](https://manpages.ubuntu.com/manpages/noble/man1/ls.1.html) and
  [cat](https://manpages.ubuntu.com/manpages/noble/man1/cat.1.html): inspecting
  a file's details and contents without executing its Python source.

The displayed messages and choice of status 7 are our example's behavior.
The PID comparison assumes these foreground commands in the same interactive
shell; an ID is not permanent and may later be reused. This is a process
observation, not proof of isolation. Required teaching is above; references
are available for verification and optional depth.
<!-- /source -->

<!-- source: course/module-b0-basics/lesson-03/README.md format=markdown -->
# B0.03 - Change one behavior, then test it

## Outcomes

Make a small source edit, verify the reader uses a supplied path, and distinguish
ordinary output from error reporting. Prerequisites: B0.01-02 or their skills.

## Understand first

The useful job is to read the requested delivery report. Printing *a* report is
not enough: a program that always reads yesterday's file can look successful
while doing the wrong work. We will test two different inputs.

Python stores command-line arguments in `sys.argv`. With
`python3 read_report.py "weekend report.txt"`, element zero is `read_report.py`
and element one is `weekend report.txt`. Python itself is not element zero in
this script's list. Quotes keep the filename together in the shell.

Programs have separate **standard output** (results) and **standard error**
(diagnostics). Both normally appear in your terminal, but a caller can collect
them separately. A failed read should report failure, not pretend a blank
report was a successful result.

## Before you begin

From the VM repository root:

```bash
./lab-start b0.03
cd .student/b0.03
```

The helper makes a fresh copy if needed; `cd` enters it. Only edit that copy.

## Read the intentionally incomplete program

Locate the supplied reader before trying to edit it:

```bash
pwd
ls -l read_report.py
cat read_report.py
```

Line by line: confirm the path ends in `.student/b0.03`; list the existing
reader's details; then display its source. These commands neither run nor
change the reader. If the filename is absent, stop and check the preparation
steps instead of creating a replacement. The listing below is the supplied
file's contents; do not paste it at the shell prompt.

```python
import sys
from pathlib import Path

if len(sys.argv) != 2:
    print("usage: python3 read_report.py REPORT", file=sys.stderr)
    raise SystemExit(2)
try:
    text = Path("report.txt").read_text(encoding="utf-8")
except OSError:
    print("Could not read that report.", file=sys.stderr)
    raise SystemExit(1)
print(text, end="")
```

Line by line: `sys` supplies arguments and the error stream. `Path` represents
a filesystem path. `len(sys.argv) != 2` detects anything other than the script
name and one report argument. The indented `print(..., file=sys.stderr)` sends
usage help to the error stream; `SystemExit(2)` stops with nonzero status.
The `try` block attempts the read. `read_text(encoding="utf-8")` turns the file's
bytes into text. `except OSError` handles filesystem failures, prints a short
diagnostic, and exits with status 1. The last `print(text, end="")` emits the
text without adding another newline. A `#` begins a comment, not an operation.

The deliberate defect is `Path("report.txt")`: that literal filename ignores
the argument. All other behavior is supplied so we can focus on one change.

### Keep the inputs and decisions straight

For `python3 read_report.py "weekend report.txt"`, the values inside this script
are:

| Expression | Value | Why it matters |
| --- | --- | --- |
| `sys.argv[0]` | `read_report.py` | The script name occupies position zero. |
| `sys.argv[1]` | `weekend report.txt` | One quoted argument names the desired report. |
| `len(sys.argv)` | `2` | Count includes the script name and the report argument. |

`!=` means "not equal"; `=` assigns a value to a name. They are different
operations. The argument-count check happens before the read so the program
does not try to use a missing position. The `try` block then performs an
operation that can fail. An `OSError` transfers control to the matching
`except` block; the nonzero exit there prevents a success-looking blank report.
On a successful read, that error block is skipped and the final print runs.

`end=""` changes only the ending added by `print`. A file's existing newline
is already part of `text`; printing another would create an extra blank line.
Our reports are valid UTF-8 text with Unix LF line endings, or no final newline.
This text reader is not a byte-for-byte copier for arbitrary file formats:
Python's text I/O can normalize other line endings. We will assess the report
format practiced here, not binary files or malformed encodings.

## Exercise 1 - Establish the failure before editing

```bash
cat "weekend report.txt"
python3 read_report.py "weekend report.txt"
echo $?
```

`cat` shows the requested report. The reader instead prints the daily report,
although `echo` reports `0`. The process succeeded at the wrong task. Comparing
content as well as status makes this defect visible.

## Exercise 2 - Repair the source

```bash
nano read_report.py
```

This opens the student file in a terminal editor. Move with the arrow keys.
Change only `Path("report.txt")` to `Path(sys.argv[1])`. Press Ctrl+O, Enter
to save, then Ctrl+X to exit. `^` in nano's help means the Ctrl key. Preserve
the spaces before the line. You can use another familiar editor instead.

Hold Ctrl while pressing the letter; do not type the characters `Ctrl+O` into
the file. Check that nano's save prompt names `read_report.py` before Enter.
When the shell prompt returns, inspect what was actually saved:

```bash
cat read_report.py
```

This prints the on-disk file. Confirm the read line contains `sys.argv[1]` and
the surrounding error handling is still present. Merely changing text on the
editor screen does not establish that it was saved. If you accidentally opened
an empty buffer or changed unrelated lines, exit without saving and recheck
the path; do not overwrite the supplied program with an empty file.

Now `Path` receives the caller's argument rather than a fixed name. The
complete repaired read line is:

```python
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
```

The four leading spaces keep the assignment inside `try`. The right side
reads the named file; `=` assigns the resulting text to `text` for the final
print. This is an input-handling repair, not filesystem confinement.

## Exercise 3 - Verify more than the happy path

```bash
python3 read_report.py "weekend report.txt"
echo $?
python3 read_report.py report.txt
echo $?
python3 read_report.py absent.txt
echo $?
python3 read_report.py
echo $?
```

The first pair should print the weekend report and `0`; the second the daily
report and `0`. The missing path should produce the read diagnostic and `1`.
Omitting the argument should produce usage help and `2`. Each `echo` must
immediately follow the invocation it checks. You have tested correct selection
and two failures; a single successful output would not establish all three.

The practical also asks you to handle a directory supplied where a report is
expected. Practice that case now:

```bash
python3 read_report.py .
echo $?
```

`.` names the current directory, which cannot be read as an ordinary report.
Expect the read diagnostic and status `1`, as for the missing-file test.
The two failures have different causes but both belong to the filesystem-error family
handled by `OSError`; neither proves that a security policy blocked access.

## Checkpoint

Explain what `sys.argv[1]` contains when a filename includes a space. Explain
why a missing file must not return success. Close this guide and sketch the
reader's three decisions in words: argument count, read result, output.
You will recreate these behaviors independently in the practical lab.

## Troubleshooting and finish

An `IndentationError` usually means a line moved out of its block; compare the
supplied indentation. A `SyntaxError` can mean a missing quote or bracket.
Read the named line and make one repair at a time. If nano is unavailable, use
an installed editor or have the VM's shared package prerequisites installed;
do not modify your Mac's Python to repair a VM exercise.

```bash
cd ../..
```

This returns to the root. Optional `./lab-reset b0.03 --dry-run` previews;
`./lab-reset b0.03 --yes` discards only this lesson's work and fixtures.

## Sources and scope

- [sys.argv and streams](https://docs.python.org/3.12/library/sys.html#sys.argv),
  [len and print](https://docs.python.org/3.12/library/functions.html#print),
  [Path.read_text](https://docs.python.org/3.12/library/pathlib.html#pathlib.Path.read_text),
  and [exception handling](https://docs.python.org/3.12/tutorial/errors.html#handling-exceptions)
  support the argument, output, read, and failure explanations.
- [TextIOWrapper newline behavior](https://docs.python.org/3.12/library/io.html#io.TextIOWrapper)
  explains why this is text preservation for our LF reports, not arbitrary byte
  preservation. [OSError subclasses](https://docs.python.org/3.12/library/exceptions.html#os-exceptions)
  include missing-file and directory-as-file errors.
- [GNU nano 7.2 manual](https://www.nano-editor.org/dist/v7/nano.html), Editor
  Basics and the Write-Out command, supports the editor workflow. The built-in
  Ctrl+G help identifies the active key bindings; customized editors may differ.

The particular diagnostics and statuses 1/2 are North Echo interface choices.
Checking them validates our reader, not every Python program. References are
optional; this lesson supplies the explanation needed for the practical.
<!-- /source -->

<!-- source: course/module-b0-basics/lab/README.md format=markdown -->
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
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-b1-first-boundary/README.md format=markdown -->
# B1 - Useful work with less inherited data

The delivery team wants a tool to read a report. The program that starts it
also holds a fake private setting the reader does not need. Your job is to
control that handoff while keeping the reader useful.

By the end, you should be able to predict which environment settings a child
receives, construct a small allowlist, test required and prohibited behavior,
and state what that repair does **not** isolate.

Prerequisites: locate and quote paths, edit a short Python file, distinguish
program/process, and interpret exit status. Use B0 if any are unfamiliar.
New ideas are introduced here: process environment, parent-to-child handoff,
allowlisting, and positive/negative tests. No namespaces, capabilities, C,
kernel tracing, network service, model, or API key is required.

Three guided lessons build toward one independent practical. The third gives
less help: use the earlier explanation on a changed case before asking for a
hint. The independent lab supplies requirements, not repair instructions.

**Scope:** this is environment hygiene, not a sandbox. The child still runs as
your VM user and can use that user's filesystem and other available resources.
We are not demonstrating that hostile code is contained. Use only the supplied
local workers and synthetic data inside the disposable VM.

Sequence: `b1.01`, `b1.02`, `b1.03`, then `module-b1`.
Pause after the practical to explain the boundary and record any missing steps.
If you can predict the changed case and explain the remaining authority, continue
to Module 01. This beta still needs learner review; a grade alone is not mastery.
<!-- /source -->

<!-- source: course/module-b1-first-boundary/lesson-01/README.md format=markdown -->
# B1.01 - What did the reader receive?

## Outcomes

Distinguish an argument from an environment setting, predict inheritance, and
observe a fake private setting's presence without printing its value.

## Understand first

Imagine a report reader launched by a larger application. It needs the report
path. It does not need every setting belonging to that application.

An **environment** is a collection of named text values supplied to a process.
It is separate from its argument list. Programs often use it for configuration.
When a parent starts a child without choosing a replacement environment, the
child generally receives the parent's settings. The child can inspect them
whether or not its intended job mentions them.

Here, the shell is the parent and Python runs our reader. A shell prefix such
as `NE_PRIVATE_TOKEN=pretend-red command` adds a setting for that one command;
it does not permanently export it in your shell. `pretend-red` is deliberately
fake. Never substitute a real token or dump your whole environment for a lab.

"Private" describes our intended policy, not a special kind of operating-system
variable. Naming a setting `NE_PRIVATE_TOKEN` does not protect it. We are using
an obviously fake value to see whether the handoff follows that policy.

## Before you begin

From the VM repository root:

```bash
./lab-start b1.01
cd .student/b1.01
```

`lab-start` prepares/resumes the copy and synthetic reports; `cd` enters it.
You need B0's path, argument, and process concepts before continuing.

## Read the supplied observer

This lesson has its own `read_report.py`, separate from B0's reader. Locate and
read the copy in the current lesson, without opening an editor:

```bash
pwd
ls -l read_report.py
cat read_report.py
```

Line by line: the path should end in `.student/b1.01`; the listing confirms the
named file is there; `cat` displays the Python source without running it. Do not
edit the observer in this lesson. Compare its contents with the listing below;
the executable command comes later under Exercise 1.

```python
import os
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
print(text, end="")
print("Private setting received:", "NE_PRIVATE_TOKEN" in os.environ)
```

Line by line: `os` provides access to the process environment; `sys` provides
arguments; `Path` reads a file. The read uses the caller's first argument, as in
B0.03. `print(text, end="")` preserves its report text. The final expression
tests whether a key is **in** `os.environ`. It prints `True` or `False`, not
the associated value. This observer intentionally reports an extra line so
we can see the handoff; production report output would normally omit it.

`os.environ` behaves as a mapping from setting names to values. The expression
`"NE_PRIVATE_TOKEN" in os.environ` tests for the name, not whether the value
looks secret. Even a present but empty value would make this check `True`.
The comma in `print` separates two things to display: the label and the boolean
(true/false) result. That is why you see an explanatory label rather than just
a bare `True` or `False`.

## Exercise 1 - Compare two handoffs

Before each invocation, predict the final line:

```bash
python3 read_report.py report.txt
NE_PRIVATE_TOKEN=pretend-red python3 read_report.py report.txt
```

The first starts the reader with the shell's usual environment. In a clean lab
shell it ends with `Private setting received: False`. The second adds our fake
setting for that invocation and ends with `Private setting received: True`.
Both print the same report. Supplying the setting did not change the argument.

Read the longer command in three parts: the assignment prefix supplies a
setting; `python3` runs the interpreter; `read_report.py report.txt` names the
script and its argument. There are no spaces around `=`. Type the entire line
before Enter. It is one invocation, not a request to edit the report or script.

The failure is not that the observer printed a real secret: it did not. The
failure is that the unnecessary setting reached the process at all. Telling a
program "read only the report" would not remove this data from its environment.

## Exercise 2 - Repair this one invocation

```bash
python3 read_report.py "weekend report.txt"
echo $?
```

The prefix is gone, so the setting is not added to this child. The reader should
print the weekend report, `False`, and status `0`. Quotes supply one path, as
before. This confirms the observation, but **omitting a prefix is not a general
repair** for an application that already has private settings. The next lesson
adds a launcher that chooses what to pass on.

## Checkpoint

Draw or describe: shell -> reader, argument path beside the arrow, environment
settings beside the same arrow. Which input changed between the first two runs?
If the reader never called `os.environ`, would the value still have been
available to it? State why measuring presence is enough for this experiment.

## Troubleshooting and finish

If the first run says `True`, your shell already has that named setting. In
this lab terminal, `unset NE_PRIVATE_TOKEN` removes only that setting; repeat
the comparison. Do not clear your entire environment. If you see a missing-file
error, check `pwd` and the report name rather than calling it a security denial.

```bash
cd ../..
```

This returns to the repository root. Optional reset:
`./lab-reset b1.01 --dry-run`, then `./lab-reset b1.01 --yes`. The preview does
not remove anything; confirmation discards this lesson's workspace/fixtures.

## Sources and scope

- [Ubuntu 24.04 Bash manual](https://manpages.ubuntu.com/manpages/noble/man1/bash.1.html),
  ENVIRONMENT: exported settings and assignments preceding an external command.
  This lesson's prefix example invokes Python, not a shell function or special builtin.
- [Python 3.12 os.environ](https://docs.python.org/3.12/library/os.html#os.environ)
  and [mapping membership](https://docs.python.org/3.12/library/stdtypes.html#mapping-types-dict):
  accessing process settings and testing whether a key is present.

The observer's boolean is evidence about that key in this supplied process
at the time of the check. It does not prove that no other data was inherited,
that an untrusted program would report honestly, or that the process cannot
access data through files or other channels. No filesystem or user-identity
boundary is changed here. These limits are part of the lesson, not optional
advanced reading.
<!-- /source -->

<!-- source: course/module-b1-first-boundary/lesson-02/README.md format=markdown -->
# B1.02 - Choose what crosses the handoff

## Outcomes

Launch a child with an explicit environment, preserve its needed public setting,
and test useful work as well as private-setting absence. Prerequisite: B1.01.

## Understand first

We now separate the **launcher** from the **worker**. The launcher starts another
program; the worker does the report reading. Python's `subprocess.run` starts
the child and waits for it to finish. Its `env` argument replaces the child's
environment with the mapping we choose. It does not change the parent's copy.

A Python **dictionary** maps keys to values. `dict(os.environ)` copies all
current environment settings. `{}` is an empty dictionary. An **allowlist**
starts with only the settings required for the job. Deleting known bad keys
from a complete copy instead leaves every unanticipated key in place.

Our reader has one legitimate setting, `NE_REPORT_STYLE`: `plain` prints the
report unchanged and `upper` converts it to uppercase. Thus there are two
obligations: retain the selected public style, and withhold private settings.
Removing everything satisfies neither the job nor the complete lesson outcome.

## Before you begin

From the VM repository root:

```bash
./lab-start b1.02
cd .student/b1.02
```

The helper prepares this lesson; `cd` enters its independent working copy.

## Read the launcher

Stay in `.student/b1.02`. First locate both supplied programs, then read the
launcher from disk:

```bash
pwd
ls -l launch.py read_report.py
cat launch.py
```

Line by line: confirm the lesson directory; list the two existing files;
display the launcher's source. `ls` accepts two filename arguments here.
Neither listing nor reading starts the worker. If either file is missing,
check the lesson preparation rather than creating an empty file in an editor.

```python
import os
import subprocess
import sys

child_environment = dict(os.environ)
result = subprocess.run(
    [sys.executable, "read_report.py", sys.argv[1]],
    env=child_environment,
)
raise SystemExit(result.returncode)
```

Line by line: the three imports provide environment access, process launch,
and arguments. `child_environment` is initially a copy of **every** setting.
The list in `subprocess.run` supplies the executable and each argument as
separate elements, preserving path boundaries without constructing a shell
command. `sys.executable` is the Python executable already running this
launcher, so the child does not need `PATH` to find it. `"read_report.py"` names
the supplied worker in the current directory. `sys.argv[1]` forwards the report
path. `env=child_environment` selects the child's settings. The returned object
contains `returncode`; `SystemExit` forwards the ordinary child exit codes used here.
With default stream handling, the child's output and errors reach our terminal.

Follow the two levels of launch:

```text
shell starts launch.py -> launcher starts read_report.py -> reader reads report.txt
```

The shell's prefixes first reach the launcher. The launcher chooses a new
mapping for the worker; it does not ask the worker to remove its own secrets
after startup. `env=child_environment` is a named function argument, selecting
the `env` parameter of `subprocess.run`. It is not a shell prefix.

The square brackets make a Python list of executable/argument strings; no
second shell parses those strings. The parentheses start the function call,
and the indented continuation lines are part of that same call. The assignment
stores its result in `result`. `result.returncode` reads one field of that
result after the worker finishes. The worker is a separate process, not a
function imported into the launcher.

## Read the worker

Still in the same directory:

```bash
cat read_report.py
```

This displays the second program. Leave it unchanged: its job is to perform
the report task and expose the effect of changes to `launch.py`. The complete
listing follows so you can compare the on-disk source with the explanation.

```python
import os
import sys
from pathlib import Path

style = os.environ.get("NE_REPORT_STYLE")
if style not in ("plain", "upper"):
    print("The reader needs NE_REPORT_STYLE=plain or upper.", file=sys.stderr)
    raise SystemExit(2)
try:
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
except OSError:
    print("Could not read that report.", file=sys.stderr)
    raise SystemExit(1)
if style == "upper":
    text = text.upper()
print(text, end="")
print("Private setting received:", "NE_PRIVATE_TOKEN" in os.environ)
```

Line by line: the imports have the same roles as B1.01. `os.environ.get` looks
up the public setting, returning `None` if absent. The membership test accepts
only `plain` or `upper`; otherwise the indented diagnostic and exit report a
configuration error. The `try`/`except OSError` block reads the report or
reports a file error as in B0.03. The `if` calls `text.upper()` only for the
uppercase style. The final prints emit report text and the private-key presence
check. The code checks a key's presence; it never prints the fake private value.

In `if style == "upper"`, `==` compares two values; it does not assign a new
style. `None` from a missing lookup means there is no value for that key, not
the literal text `"None"`. The earlier validation prevents that missing-value
case from silently choosing a default report style.

## Exercise 1 - Observe the incomplete control

```bash
NE_REPORT_STYLE=upper NE_PRIVATE_TOKEN=pretend-red python3 launch.py report.txt
echo $?
```

The two prefixes provide settings to the launcher for this run. Its full copy
passes both to the worker. Expect an uppercase report, private presence `True`,
and status `0`. The job works, but the unnecessary data crossed the handoff.

## Exercise 2 - See why removing everything is insufficient

Open the launcher you just inspected, not the worker:

```bash
nano launch.py
```

This edits the local student copy. Change the environment assignment to:

```python
child_environment = {}
```

This constructs an empty mapping. Save with Ctrl+O, Enter; exit with Ctrl+X.
Then inspect the saved file:

```bash
cat launch.py
```

Confirm the assignment is now empty and the child-run/exit lines remain.
Repeat the two commands in Exercise 1. Expect the worker's style diagnostic,
no report, and status `2`. A worker that cannot do its job is not a successful
security repair. Keep the test that exposed this regression.

## Exercise 3 - Make the narrow repair

Reopen the same student file with `nano launch.py`, replace that assignment
with the line below, save with Ctrl+O and Enter, and exit with Ctrl+X:

```python
child_environment = {"NE_REPORT_STYLE": os.environ["NE_REPORT_STYLE"]}
```

The dictionary contains one key. Its value comes from the launcher's current
public setting, not a hard-coded style. The brackets perform a required-key
lookup; this exercise always supplies the public setting. No private key is
copied. This controls inheritance; it does not delete anything from the parent.

Run `cat launch.py` once more to confirm the saved line before testing it.
If your editor still shows unsaved changes, the next Python invocation would
read the old file from disk, not what you see in the editor.

```bash
NE_REPORT_STYLE=upper NE_PRIVATE_TOKEN=pretend-red python3 launch.py report.txt
echo $?
NE_REPORT_STYLE=plain NE_PRIVATE_TOKEN=pretend-red python3 launch.py "weekend report.txt"
echo $?
```

The first should print uppercase content, `False`, and `0`. The second should
print ordinary-case weekend content, `False`, and `0`. Changing the style and
path checks that the repair still honors caller choices.

## Checkpoint

Explain the observed difference among a full copy, an empty dictionary, and
the one-key dictionary. Which observation checks useful work? Which checks
withheld data? Could the worker still read a different file accessible to your
VM user? Yes: we have imposed no filesystem restriction. Explain that limit
before continuing.

| Chosen handoff | Useful report | Observed private key |
| --- | --- | --- |
| All parent settings | Works | Present |
| No settings | Fails style validation | Not checked: worker exits before its observer line |
| Selected public setting | Works | Absent |

The middle row matters: no private-key line is **not** an observed `False`.
It is missing evidence because the worker stopped early. Always check that the
intended observer actually ran before interpreting its absence as a denial.

## Troubleshooting and finish

A `KeyError` for `NE_REPORT_STYLE` means the required public prefix is missing;
repeat the complete invocation. A `SyntaxError` often means an unmatched brace,
quote, or bracket in the edit. Do not repair a failed observation by removing
the observer's print. Check what reached the worker instead.

```bash
cd ../..
```

Return to the root. Optional `./lab-reset b1.02 --dry-run` previews cleanup;
`./lab-reset b1.02 --yes` removes this lesson's edits and generated fixtures.

## Sources and scope

- [Python 3.12 subprocess.run](https://docs.python.org/3.12/library/subprocess.html#subprocess.run):
  waiting for a child, explicit `env` replacing default inheritance, argument
  sequences, and default stream behavior. [sys.executable](https://docs.python.org/3.12/library/sys.html#sys.executable)
  identifies the running interpreter; it is usable on our tested installation.
- [Dictionary operations](https://docs.python.org/3.12/library/stdtypes.html#mapping-types-dict)
  and [os.environ](https://docs.python.org/3.12/library/os.html#os.environ): copying
  the environment versus constructing a selected mapping.
- [CompletedProcess.returncode](https://docs.python.org/3.12/library/subprocess.html#subprocess.CompletedProcess.returncode)
  distinguishes ordinary exits from negative signal results on POSIX. This
  example forwards the ordinary 0/1/2 exit codes only; it is not a general
  signal-forwarding supervisor.
- [GNU nano 7.2](https://www.nano-editor.org/dist/v7/nano.html): opening a named
  file and saving/exiting, as also shown by its built-in Ctrl+G help.

The allowlist is our policy choice for this worker, not a universal list for
every application. Clearing `env` does not change the child's user, filesystem
permissions, or network access. The supplied-worker checks are local evidence
of the handoff, not proof that hostile code is contained.
<!-- /source -->

<!-- source: course/module-b1-first-boundary/lesson-03/README.md format=markdown -->
# B1.03 - Does the repair survive a changed case?

## Outcomes

Apply the previous lesson without a replacement line to copy, handle a second
unnecessary setting, and preserve child failures. Prerequisite: B1.02.

## Understand first

A test can be too narrow. If you remove only the private key you happened to
see, a differently named setting still passes through. The intended rule is
not "remove one spelling"; it is "pass only what this job requires."

We also change the interface: the caller now supplies a worker path as well as
a report path. An argument list preserves these boundaries even when either
path contains a space. This is not permission to run arbitrary downloaded
workers. Use only the supplied local observer in this disposable VM.

## Before you begin

From the VM repository root:

```bash
./lab-start b1.03
cd .student/b1.03
```

The first creates/resumes a separate attempt. The second enters its directory.
Your previous lesson's repair does not automatically appear in this new copy.

## Read the partial repair

Locate both supplied files in this new workspace, then inspect the launcher:

```bash
pwd
ls -l launch.py inspect_reader.py
cat launch.py
```

Line by line: confirm `.student/b1.03`; confirm both files exist; display the
launcher's source without executing it. This is a different student copy from
B1.02. Compare it with the listing below before deciding what to change.

```python
import os
import subprocess
import sys

# A partial repair: it removes one known name, not other private settings.
child_environment = dict(os.environ)
child_environment.pop("NE_PRIVATE_TOKEN", None)
result = subprocess.run(
    [sys.executable, sys.argv[1], sys.argv[2]],
    env=child_environment,
)
raise SystemExit(result.returncode)
```

Line by line: the imports match B1.02. The dictionary assignment copies the
parent settings; `.pop("NE_PRIVATE_TOKEN", None)` removes that specific key
if present and does nothing if absent. The run list uses the current Python
executable, argument one as the worker path, and argument two as the report
path. `env` supplies the edited copy. The last line forwards the child's ordinary
exit code. This is a deliberately incomplete repair to investigate, not a model
solution.

## Read the observer

From the same workspace:

```bash
cat inspect_reader.py
```

This prints the observer's source. Read it, but do not edit it: we will change
the launcher and keep the measurement program unchanged.

```python
import os
import sys
from pathlib import Path

style = os.environ.get("NE_REPORT_STYLE")
if style not in ("plain", "upper"):
    print("Missing or invalid report style.", file=sys.stderr)
    raise SystemExit(2)
try:
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
except OSError:
    print("Could not read that report.", file=sys.stderr)
    raise SystemExit(1)
if style == "upper":
    text = text.upper()
print(text, end="")
print("Original private setting received:", "NE_PRIVATE_TOKEN" in os.environ)
print("New private setting received:", "NE_OTHER_PRIVATE" in os.environ)
```

Line by line: imports and public-style validation match B1.02. The read's
`try`/`except` preserves the missing-file error path; uppercase conversion is
conditional. The report print preserves content. The final two lines check
two distinct keys in the environment, without disclosing their values. A
`False` for one key says nothing about the second key unless we measure it too.

## Exercise 1 - Predict and observe the changed case

```bash
NE_REPORT_STYLE=upper NE_PRIVATE_TOKEN=pretend-red NE_OTHER_PRIVATE=pretend-blue python3 launch.py inspect_reader.py "weekend report.txt"
echo $?
```

The three prefixes supply one needed setting and two unnecessary ones. The
launcher receives the observer path and quoted report path as separate
arguments. Expect uppercase report text, the first private check `False`, the
second `True`, and status `0`. The earlier single-key check would miss this.

## Exercise 2 - Repair, with less help

Edit the launcher so it passes the selected public style and no other parent
setting. Do not edit the observer to make its output reassuring. Write down
the rule you intend to enforce before writing code. Use B1.02 if you need a
hint, then close it and apply the idea here.

Use `nano launch.py` to open the file, Ctrl+O and Enter to save, and Ctrl+X to
return to the shell. Run `cat launch.py` to check the saved contents. Those
editing steps are not the answer: you still need to choose what the handoff
should contain and implement that choice yourself.

Repeat Exercise 1. Expected: correct uppercase report, both private checks
`False`, status `0`. Repeat with `plain` and the daily report; it must preserve
that choice too. A constant `upper` value is not a complete repair.

## Exercise 3 - Keep failure honest

```bash
NE_REPORT_STYLE=plain python3 launch.py inspect_reader.py absent.txt
echo $?
```

The worker receives a missing report path and should emit its diagnostic and
exit `1`; the launcher must also exit `1`. This invocation intentionally tests
failure, not a second security mechanism. Repair the input by replacing
`absent.txt` with `report.txt` and confirm report output plus status `0`.

## Checkpoint

Without consulting earlier code, explain why the starting `.pop` was too narrow.
What if a third unrelated setting appeared tomorrow? Why would suppressing all
output or always returning zero make a poor test pass? Demonstrate both a useful
run and a withheld-data observation. Then attempt the independent practical.

## Troubleshooting and finish

If the worker path is accidentally treated as the report path, review positions
one and two in `sys.argv`. If the original fake key is absent but the second is
present, the behavior is still a single-name deletion, not selection by need.
If a failed child appears successful, inspect the launcher's final exit line.

```bash
cd ../..
```

This returns to the root. Optional `./lab-reset b1.03 --dry-run` previews
removal; `./lab-reset b1.03 --yes` discards this lesson's work and fixtures.

## Sources and scope

- [Python 3.12 dictionary pop and lookup](https://docs.python.org/3.12/library/stdtypes.html#mapping-types-dict):
  deleting a named key differs from selecting the keys to retain.
- [sys.argv](https://docs.python.org/3.12/library/sys.html#sys.argv) and
  [subprocess](https://docs.python.org/3.12/library/subprocess.html#subprocess.run):
  the two caller arguments, a structured child argument list, explicit
  environment, and an ordinary exit result.
- [OSError](https://docs.python.org/3.12/library/exceptions.html#OSError): the
  report-read failure family. Status 1 and the two observer labels are choices
  in our supplied worker, not standardized Python diagnostic text.

The test varies two key names and the public style; it is evidence for these
cases, not exhaustive proof about all programs. Reading the selected mapping
explains why a third unselected parent key would also be omitted. The program
still runs with the VM user's other authority. Signal termination, arbitrary
worker arguments, and hostile-worker containment remain outside this first-boundary exercise.
<!-- /source -->

<!-- source: course/module-b1-first-boundary/lab/README.md format=markdown -->
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
<!-- /source -->

# Learning path and assessment

This course teaches runtime containment for local agent workloads. A passing
command is the beginning of an explanation: identify the authority, the control,
the observed effect, and the limits of that evidence. No AI service is required.

## Entry diagnostic

New learners should start with the [beginner chapters](BEGINNER_FIELD_MANUAL.md):
B0 offers a basics/test-out path, and B1 develops one small environment boundary.
Then continue through Modules 01-12 and the capstone, pausing at each checkpoint.
This beta needs your walkthrough; expanded explanations and passing tests do not
by themselves establish good pacing. The diagnostic below prepares the transition
from B1 to the numbered technical track, not a test you must already pass to begin.

Use the validated disposable VM. Start `./lab-start 01.01` and enter
`.student/01.01`; all scratch files below stay in that resettable workspace.
Try the following without consulting the expected observations, then compare.

```bash
printf '%s\n' 'two words' 'one'
python3 -c 'import sys; sys.exit(7)'
printf 'previous status=%s\n' "$?"
python3 -c 'import json; print(json.loads("{\"count\": 2}")["count"])'
cc -std=c11 -Wall -Wextra hello-syscall.c -o diagnostic-program
./diagnostic-program
ps -o pid,ppid,comm -p "$$"
rm diagnostic-program
```

### Line by line

- Single quotes keep `two words` as one argument; the format emits one line per
  remaining argument. Predict two output lines.
- The Python child exits with status 7. Read `$?` immediately: another command
  would replace it. Expected `previous status=7`.
- `json.loads` parses an object; indexing `count` returns integer 2, not the
  original JSON string.
- The compiler turns the supplied C source into a local executable and reports
  syntax/type errors before execution. Expect the lesson's two output messages.
- `ps` shows the current shell and its parent ID. Explain which process `$$`
  denotes before comparing the row.
- Remove only the exact diagnostic executable. The canonical source is untouched.

Record one point each for explaining quoting, exit status, parsed JSON, the
compile/execute distinction, and PID/PPID. This is a self-check, not an exam.
For missed shell items, read “Reading command and code blocks” in the foundation
manual. For C, follow Lesson 01.01's source explanation and deliberately introduce
then repair a missing semicolon in the student copy. For JSON, change `count` to
a quoted string and explain the changed type. Repeat the missed task until you
can predict and explain it. No systems-programming background is assumed.

## Worked, faded, independent

For each module, complete the worked lessons, attempt the corresponding faded
task below with the manual closed, then take the independent lab. A faded task
changes one requirement while retaining familiar interfaces. Reopen a specific
explanation if needed and record which hint helped; do not mistake copied output
for an explanation.

| Module | Faded task before the independent lab |
| --- | --- |
| 01 | Predict which environment and descriptor state survives a launch; justify each observation. |
| 02 | Given two namespace/procfs observations, identify which establishes the child's PID view. |
| 03 | Explain a nonzero bounding set alongside empty effective capabilities; state what no_new_privs adds. |
| 04 | Add a harmless argv task with a space in one argument and a nonzero child status; predict its trace. |
| 05 | Draw a descriptor's lifetime across policy installation and exec; identify where it must be closed. |
| 06 | Explain why an allowed read must still succeed under a syscall policy; distinguish it from pathname authorization. |
| 07 | Change a bounded CPU quota and predict cpu.max; compare configured values with observed values. |
| 08 | Explain which authority the local broker retains and which authority the isolated client lacks. |
| 09 | Given a capability's audience, expiry and run identity, identify the evidence needed to accept an operation. |
| 10 | Complete the practiced 0/7/0 single-job sequence with different observed memory ceilings; design whole-batch validation before any launch. |
| 11 | Classify a mixed synthetic evidence row without looking at its variant label; preserve useful-work requirements. |
| 12 | Classify incomplete observations without the oracle's next_probe hint; state the smallest missing observation. |

## Cumulative checkpoint after Module 03

From the repository root, grade `module-01`, `module-02`, and `module-03` in exam
mode. In `.student/03.lab/checkpoint.md`, make a table of environment, descriptors,
namespace membership, capability state, and no_new_privs. For each, name one
observation and one fact it cannot establish. Explain why a namespace change alone
does not remove inherited authority. Pass this checkpoint only when the practicals
pass and you can explain every row without reading a solution.

## Cumulative checkpoint after Module 06

Grade `module-04`, `module-05`, and `module-06` in exam mode. Record evidence in
`.student/06.lab/checkpoint.md`: literal argument preservation, allowed file access,
intended file denial, inherited descriptor hygiene, and effective syscall policy.
For each denial, include a corresponding useful operation that still works.
Explain why `Seccomp: 2` alone cannot establish a particular denial and why
filesystem denial does not establish resource limits. Revisit only the failed
property's lesson, then repeat with fresh evaluation fixtures.

## Cumulative checkpoint after Module 09

Grade `module-07`, `module-08`, and `module-09` in exam mode. In
`.student/09.lab/checkpoint.md`, map resource limits, direct network isolation,
broker authorization, credential absence, and replay handling to distinct
observations. Explain which component retains each authority and how it is
collected. A functional broker response alone does not establish all these facts.

## Graduation rubric

The capstone's automated batch-runtime assessment must pass. Separately review
`RATIONALE.md` using this rubric; the program does not grade prose by keywords.
Score each dimension 0 (absent/incorrect), 1 (correct but unsupported), or 2
(correct, tied to observed evidence, and appropriately limited).

| Dimension | Evidence needed for 2 points |
| --- | --- |
| Authority model | Names workload versus broker authority and the boundary each control enforces. |
| Composition | Explains launch order using dependencies, including privilege removal after namespace entry. |
| Functional preservation | Connects useful work and intended denial observations, rather than reporting only failures. |
| Lifecycle | Distinguishes invalid batch input, ordinary job failure, timeout, and exact resource collection. |
| Interpretation | States what each observation proves, what remains untested, and how a fresh run differs. |

Graduation requires an automated pass and 2 points in every reasoning dimension.
An instructor or peer should score the rationale; a solo learner may self-review
but should label that result self-assessed. Keep notes and solutions private when
exporting them. `lab-reset` intentionally deletes these workspace notes too.

## Pace and evidence

There is no validated course-duration estimate yet. Work one conceptual layer at
a time and record active time, hints used, and failed checkpoints. Stop at a
checkpoint until the missing prerequisite is understood. Time spent diagnosing
the VM is setup friction and should be measured separately from learning time.

# North Echo Agent Security Lab

## Foundation field manual - Modules 01-03

This is the self-contained teaching manual for the first three playable modules. It assumes no prior systems-programming expertise. The goal is not to memorize commands. The goal is to build a reliable mental model of what authority a Linux process carries and to verify every containment claim from observable kernel state.

The learning rhythm is: predict, run, observe, explain, break, repair, and verify.

> **Safety boundary:** Use only a disposable Linux VM with synthetic fixtures. Do not load personal or employer credentials. Do not target external systems. Run as an ordinary user unless an exercise explicitly creates namespace-local root.

## What this manual contains

- A command-reading primer so punctuation such as `|`, `>`, `$()`, and quotes is never magic.
- Detailed mental models for processes, `execve`, environment inheritance, file descriptors, namespaces, credentials, capabilities, and `no_new_privs`.
- Every guided command for Modules 01-03 followed by a line-by-line explanation.
- Complete guided source listings with explanations of each meaningful C or Python line.
- Expected output patterns, including values that legitimately vary by machine.
- Intentional failures, why they fail, and how to verify the correction.
- Independent lab contracts and verification plans without complete solutions.
- Troubleshooting notes, a glossary, and a compact command reference.

## Starting, resetting, and replaying

From the repository root:

```bash
./scripts/attest-course
./lab-start 01.01
cd .student/01.01
less README.md
```

### What each line does

- `./scripts/attest-course` recomputes hashes for canonical course material. A pass means it matches the recorded manifest.
- `./lab-start 01.01` creates or resumes a disposable workspace for Module 01, Lesson 01.
- `cd .student/01.01` enters the generated editing area. Edit here, not under `course/`.
- `less README.md` opens the workspace instructions. Press `q` to leave.

Return to the repository root before lifecycle commands:

```bash
./lab-status
./lab-reset 01.01 --dry-run
./lab-reset 01.01 --yes
./lab-start 01.01
```

### What each line does

- `lab-status` reads attempt counts, workspace state, and pass state without changing anything.
- `--dry-run` checks reset boundaries and prints intended actions without deleting the workspace.
- `--yes` confirms the scoped reset after the same containment checks pass.
- Starting again produces new synthetic IDs, names, paths, ports, and canaries while retaining only progress metadata.

Reset is part of the pedagogy. After reset, the old solution is gone. A new attempt tests understanding instead of recognition.

# Reading command and code blocks

## Shell command anatomy

A shell expands text, constructs an argument vector, applies redirections, and launches programs. Small punctuation marks can change data flow and authority.

```bash
grep -E '^CapEff:' /proc/self/status
```

### What each token means

- `grep` is the program selected through `PATH`.
- `-E` enables extended regular expressions.
- `'^CapEff:'` is one quoted argument. The shell removes the quotes before launch.
- `^` anchors the expression at the beginning of a line.
- `/proc/self/status` is the input pathname. For the running `grep`, `/proc/self` identifies that process.

### Variables and command substitution

```bash
CURRENT_UID=$(id -u)
printf 'uid=%s\n' "$CURRENT_UID"
```

- `$(id -u)` launches `id`, captures stdout without its trailing newline, and substitutes the result.
- `CURRENT_UID=...` creates a shell variable. It is not inherited unless exported.
- `printf` receives a format string and a value as separate arguments.
- Double quotes permit expansion while preserving the result as one argument.
- `\n` tells `printf` to emit a newline.

### Quoting changes which shell performs expansion

```bash
sh -c 'echo "child pid=$$"'
sh -c "echo child pid=$$"
```

- Single quotes protect `$$` from the outer shell. The child shell expands it to the child's PID.
- Double quotes let the outer shell expand `$$` before `sh` starts. The child receives the parent's number as ordinary text.
- Both outputs can look plausible, so quoting must be reasoned about explicitly.

### Pipes and redirections

```bash
strace -e trace=write ./program 2>&1 | grep write
```

- `strace ... ./program` starts the observed process.
- `2>&1` makes descriptor 2 use the destination currently used by descriptor 1.
- `|` connects the left command's stdout to the right command's stdin.
- `grep write` filters display. It does not change the traced process.
- Pipeline stages are separate processes with separate descriptors and exit statuses.

### Exit status

```bash
command && echo passed
command || echo failed
```

- Processes return a small integer status. Zero conventionally means success.
- `&&` runs the right side only after status zero.
- `||` runs the right side only after nonzero status.
- `;` sequences commands regardless of status.

## C source anatomy

- `#include` supplies declarations from a header.
- `main` is the user-space entry point after the program image is initialized.
- `argc` counts argument pointers; `argv` is a NUL-terminated pointer array.
- Successful `exec` does not create a process and does not return. It replaces the current program image.
- Most syscall wrappers report failure as `-1` and set `errno`; `perror` formats that error.
- File descriptors are process-local integers referring to kernel-managed open objects.
- Bitwise OR (`|`) combines flag bits; bitwise AND (`&`) tests bits. They differ from logical `||` and `&&`.

> **Reading rule:** Identify the authority-transfer point in every launcher. Hygiene and policy that must govern the executed program must be established before `exec`.

<!-- source: course/module-01-process-authority/README.md format=markdown -->
# Module 01 - Processes, syscalls, and inherited authority

You will trace a command from process creation to kernel-visible effects, then remove two authorities that commonly cross `execve(2)` by accident: environment data and open file descriptors.

Play in order: `01.01`, `01.02`, `01.03`, then `module-01`.

## Learning route and limits

Prerequisites: B0 and B1. Continue as your ordinary account inside the disposable Linux VM. The guided lessons introduce their new syntax and interfaces before the independent lab combines them.

01.01 connects source, executable, process, and syscall. 01.02 traces an environment value and practices a constructed C environment. 01.03 traces an already-open reference and practices closing unknown extra descriptors.

Replacing program code does not automatically discard its environment or open descriptors. Explain the difference between a filename and a descriptor, and between fork and exec. Neither environment hygiene nor descriptor closure restricts every future file open.

Before moving on, demonstrate both useful allowed work and the intended restriction, and explain the difference in your own words. A failed compiler command or missing input is not a security success. Use the independent lab's practice feedback to revisit a specific lesson; passing checks does not replace understanding or make the combined program production-ready.
<!-- /source -->

## Module outcome and mental model

You will trace shell text into a process, an `execve` transition, and syscalls. Then you will remove two quiet authority channels: inherited environment values and open file descriptors.

```text
parent process
  -> optional fork or clone
  -> prepare arguments, environment, and descriptors
  -> execve(new program, argv, envp)
  -> new program continues with surviving process authority
```

`fork` creates a process by copying state. `execve` replaces a process image while preserving selected process attributes. A syscall crosses from user space into the kernel. The new executable is not automatically a clean slate.

<!-- PAGEBREAK -->

<!-- source: course/module-01-process-authority/lesson-01/README.md format=markdown -->
# 01.01 - Follow a program into the kernel

## Outcomes and prerequisites

Identify your shell and its parent, compile a supplied C program, and connect
its output to observed system calls. Use the B0 skills of locating files,
saving edits, and checking exit status. Complete B1 before this security track.
The C features needed here are introduced locally; you do not need to write
the program from a blank file.

## Understand first

Python reads source through an interpreter. A C compiler translates source
into an executable first. Saving a source edit does not change an executable
already built from it. Compile again before testing that edit.

A process normally executes instructions in user space. A system call is a
controlled entry into the kernel to request an operation such as writing bytes.
A library function can make several syscalls or postpone one. Its source name
does not tell you exactly what the kernel observed.

`strace` starts our small program and reports selected system calls. This is
observation, not confinement: tracing does not install a rule denying writes.
Module 06 will use this distinction when building a syscall policy.

## Prepare and locate the supplied file

From the repository root inside the disposable VM:

```bash
./lab-start 01.01
cd .student/01.01
pwd
ls -l hello-syscall.c
cat hello-syscall.c
```

`lab-start` creates or resumes the lesson. `cd` enters its editable copy.
`pwd` must end in `.student/01.01`; stop otherwise. `ls -l` shows metadata;
`cat` reads the text without compiling or executing it. Do not create a blank
replacement if the supplied file is missing.

## Read the small C program

```c
#include <stdio.h>
#include <unistd.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    puts("userspace: about to write");
    const char message[] = "kernel-visible write\n";
    if (write(STDOUT_FILENO, message, sizeof(message) - 1) < 0) {
        perror("write");
        return 1;
    }
    return 0;
}
```

`#include` supplies declarations so the compiler knows the named functions
and constants. `int main(void)` defines the entry function with no arguments
in this example and an integer exit result. Braces group statements;
semicolons terminate them. Unlike Python, indentation does not define blocks.

`stdout` is a C-library stream; a descriptor is a process-local reference to
an open object. The stream can buffer bytes before a syscall transfers them.
`const char message[]` is an array of characters; `const` prevents modification
through that declaration. The string contains a newline and a terminating
zero byte. The later source commentary connects these pieces to each call.

This is not a general-purpose write-all routine: `write` can successfully
transfer fewer bytes than requested. Production copying must handle partial
writes and interruptions. Our short message makes the observation manageable.

## Exercise 1 - Establish the process facts

Run:

```bash
pwd
printf 'shell pid=%s parent=%s\n' "$$" "$PPID"
ps -o pid,ppid,user,stat,comm,args -p $$ -p $PPID
```

### Line by line

- `pwd` prints the workspace directory so you can confirm where the exercise is running.
- `printf ... "$$" "$PPID"` formats two shell variables: `$$` is this shell's PID and `$PPID` is its parent's PID. Quoting keeps each expanded value as one argument.
- `ps -o ...` selects explicit columns instead of relying on a distribution's default view. The two `-p` arguments restrict output to the shell and its parent.
- In the format list, `pid` and `ppid` show the relationship, `user` shows the effective account, `stat` shows process state, `comm` shows the executable name, and `args` shows the full argument vector.

Expected pattern: two rows. Your shell's `PPID` identifies its parent. A process is not “the command text”; it is a kernel object with identity, credentials, memory, descriptors, and namespace memberships.

Now inspect the executable and namespace handles:

```bash
readlink /proc/$$/exe
ls -l /proc/$$/ns
```

### Line by line

- `readlink /proc/$$/exe` asks procfs which executable object backs the current shell process.
- `ls -l /proc/$$/ns` lists the shell's namespace handles. `-l` is needed because each entry is a symbolic link whose target contains the namespace type and identity.

Expected pattern: `exe` names your shell; namespace entries look like `mnt:[402653....]`. Those inode-like numbers let you compare namespace membership later.

## Exercise 2 - Compile a process that crosses into the kernel

Inspect and build the starter:

```bash
sed -n '1,200p' hello-syscall.c
cc -std=c11 -Wall -Wextra -O2 hello-syscall.c -o hello-syscall
./hello-syscall
```

### Line by line

- `sed -n '1,200p' ...` displays only lines 1 through 200. `-n` suppresses normal output and `p` explicitly prints the selected range.
- `cc` invokes the C compiler. `-std=c11` selects the language version, `-Wall -Wextra` enable useful warnings, `-O2` enables normal optimization, and `-o hello-syscall` names the output binary.
- `./hello-syscall` executes the file from the current directory; the `./` prevents the shell from searching `PATH` for a different program.

Expected output:

```text
userspace: about to write
kernel-visible write
```

### Source, line by line

- `#include <stdio.h>` declares `puts`, `setvbuf`, and `perror`; `#include <unistd.h>` declares `write` and `STDOUT_FILENO`.
- `int main(void)` defines the C entry function with no arguments in this example and an integer exit result.
- `setvbuf(stdout, NULL, _IONBF, 0)` disables userspace buffering for `stdout`, making the observation easier to reason about.
- `puts(...)` is a C library call; it eventually needs a kernel write to make bytes visible.
- `const char message[] = ...` creates immutable message bytes in process memory; `\n` is one newline byte.
- `write(STDOUT_FILENO, message, sizeof(message) - 1)` asks the kernel to write those bytes to descriptor 1. Subtracting 1 excludes C's terminating NUL byte.
- `< 0` tests the syscall wrapper's failure convention; `perror` explains the current `errno` value.
- `return 1` reports failure, while the final `return 0` reports success to the parent process.

Trace it:

```bash
strace -f -e trace=execve,write,exit_group ./hello-syscall 2>&1
```

### Line by line

- `strace` observes syscalls made by the command it launches.
- `-f` follows child processes if the program creates any.
- `-e trace=...` reduces the trace to `execve`, `write`, and `exit_group`, keeping the observation focused.
- `2>&1` redirects file descriptor 2 (stderr, where `strace` writes) to the same destination as file descriptor 1 (stdout).

Expected pattern: an `execve(...) = 0`, one or more `write(...)` calls, then `exit_group(0)`. Library functions are not themselves the security boundary; their eventual syscalls are what enter the kernel.

## Exercise 3 - Make and correct an intentional prediction error

Before running this, predict whether the first source output statement must
produce the first visible line. Run the unchanged program first:

```bash
strace -e trace=write ./hello-syscall 2>&1 | grep write
```

### Line by line

- `strace -e trace=write` records only `write` syscalls.
- `2>&1` combines trace output and program output into one stream.
- `|` connects that stream to the next command.
- `grep write` keeps lines containing the word `write`; it is a display filter, not part of the traced program.

Now open the supplied source:

```bash
nano hello-syscall.c
```

Change only `_IONBF` to `_IOFBF`, selecting full buffering. Save with Ctrl+O,
confirm the existing filename with Enter, and exit with Ctrl+X. These use
Control, not the Mac's Command key. Check the saved file, rebuild, and trace:

```bash
cat hello-syscall.c
cc -std=c11 -Wall -Wextra -O2 hello-syscall.c -o hello-syscall
strace -e trace=write ./hello-syscall
```

Stop on compilation errors: an older executable can otherwise conceal a bad
edit. The direct write can now appear before the earlier `puts` output,
because the C stream retains its bytes until a later flush. Compare actual
events with source order; do not memorize a libc-specific syscall count.
Restore `_IONBF`, save, rebuild, and trace again. Explain why saving without
rebuilding would not repair the executable.

## Checkpoint and troubleshooting

Identify the shell/parent relationship, distinguish source from executable,
and point to the syscall that produced output. Name one fact the trace proves
and one containment claim it does not.

- Missing source: check `pwd` and the prepared workspace; do not edit `course/`.
- Compiler error: inspect the first diagnostic and the edited punctuation;
  do not continue using a stale binary.
- Different write grouping: compare buffering and bytes, not fixed addresses
  or an exact syscall count.
- Tracing denied: rerun preflight in the disposable VM. Do not use sudo,
  disable SELinux, or trace unrelated processes to force progress.

To discard this lesson only, return to the repository root, preview
`./lab-reset 01.01 --dry-run`, then confirm with `./lab-reset 01.01 --yes`
if the listed work is disposable. Reset removes its edits and binaries.

## Sources and scope

The Linux man-pages project's [execve](https://man7.org/linux/man-pages/man2/execve.2.html)
documents image replacement; [write](https://man7.org/linux/man-pages/man2/write.2.html)
documents partial transfers; [setvbuf](https://man7.org/linux/man-pages/man3/setbuf.3.html)
documents buffering. Consult `man strace`, `man ps`, and `man proc` in the guest
for the installed tools. Exact PIDs, namespace numbers, paths, and write
grouping are baseline observations, not universal constants.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-01-process-authority/lesson-02/README.md format=markdown -->
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

```python
#!/usr/bin/env python3
import os

print("DEMO_AGENT_TOKEN=" + os.environ.get("DEMO_AGENT_TOKEN", "<absent>"))
print("PATH=" + os.environ.get("PATH", "<absent>"))
```

`import os` provides access to the process environment. `get` returns the
named value or the chosen `<absent>` marker. String `+` joins the label and
value; `print` writes the result. This observer prints only our selected fake
setting and PATH, not every environment value. Never substitute a real secret.

```python
#!/usr/bin/env python3
import os
import subprocess

# Intentional mistake: copying the full parent environment copies its authority.
child_env = os.environ.copy()
subprocess.run(["python3", "show-env.py"], env=child_env, check=True)
```

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
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-01-process-authority/lesson-03/README.md format=markdown -->
# 01.03 - File descriptors cross exec

## Outcomes and prerequisites

Observe an open descriptor surviving exec, prevent that inheritance, and
practice closing unknown extra descriptors. You need 01.01's C compile cycle
and 01.02's understanding that exec receives inherited state.

## Understand first

A pathname is a name to resolve. A descriptor is a small integer referring
to an already-open object. By convention, 0 is stdin, 1 is stdout, and 2 is
stderr. Other numbers are allocated as needed; descriptor 3 is common, not
a universal identifier for a protected file.

Opening performs pathname lookup and access checks. Later reads use the open
object without repeating that original lookup. A launcher can therefore hand
another program a reference that checking only future pathnames would miss.
We observe this channel using synthetic data, not an actual secret store.

## Prepare and read before executing

From the VM repository root:

```bash
./lab-start 01.03
cd .student/01.03
pwd
ls -l fd-parent.c fd-child.py close-extra.c .north-echo.json
cat fd-parent.c
cat fd-child.py
```

Confirm `.student/01.03`. The metadata file names this attempt's synthetic
fixture. The parent opens it; the observer tries existing descriptors.
Reading the files is not running them.

```c
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: %s PATH\n", argv[0]);
        return 2;
    }
    int fd = open(argv[1], O_RDONLY); /* Intentional mistake: no O_CLOEXEC. */
    if (fd < 0) {
        perror("open");
        return 1;
    }
    char *child[] = {"python3", "fd-child.py", NULL};
    execvp(child[0], child);
    perror("execvp");
    return 1;
}
```

`open` returns a descriptor or -1 on failure. The argument check requires one
pathname. `char *child[]` is an array of string pointers ending in NULL, as in
01.02. `execvp` searches PATH and replaces the program. Follow the error branch
first: a failed open must not be treated as an open reference.

```python
#!/usr/bin/env python3
import os

for fd in range(0, 32):
    try:
        target = os.readlink(f"/proc/self/fd/{fd}")
    except OSError:
        continue
    print(f"fd={fd} target={target}")
    if fd >= 3:
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            print(os.read(fd, 4096).decode(errors="replace"))
        except OSError:
            pass
```

The observer tests descriptor numbers 0-31. `readlink` asks procfs what each
reference names; `continue` skips unopened numbers. For numbers above 2,
`lseek` attempts to rewind a seekable object and `read` requests up to 4096
bytes. Ignoring errors for non-seekable or unreadable objects does not prove
they are harmless. This bounded observer is not a complete inventory algorithm.

## Exercise 1 - Observe descriptor authority

Build and run the intentionally vulnerable launcher. Use the randomized protected fixture created for this attempt:

```bash
cc -std=c11 -Wall -Wextra -O2 fd-parent.c -o fd-parent
./fd-parent "$(python3 -c 'import json; print(json.load(open(".north-echo.json"))["fixture_manifest"])')"
```

### Line by line

- `cc ... fd-parent.c -o fd-parent` compiles the launcher with warnings enabled and writes the binary named `fd-parent`.
- `python3 -c '...'` executes the quoted Python expression without creating another file.
- `open(".north-echo.json")` opens non-secret workspace metadata; `json.load(...)` parses it; `["fixture_manifest"]` selects the generated manifest path; `print(...)` writes that path.
- `$(...)` substitutes the printed path into the outer command.
- The double quotes around `$(...)` keep the entire pathname as one argument even if a directory name contains spaces.

Expected pattern: the child lists descriptors under `/proc/self/fd`; one descriptor points to `manifest.json`, and the child can read it without opening its pathname.

Inspect the source:

```bash
sed -n '1,220p' fd-parent.c
```

### Line by line

- `sed -n` suppresses automatic printing.
- `'1,220p'` prints source lines 1 through 220, which covers this intentionally small program.
- Reading before running is part of the exercise: identify the `open` and `execvp` authority-transfer points.

The intentional mistake is `open(..., O_RDONLY)` followed by `execvp` with no close and no close-on-exec flag.

### Parent source, line by line

- `#define _GNU_SOURCE` exposes GNU/Linux extensions such as `O_CLOEXEC` from the included headers.
- The four `#include` lines declare file flags, diagnostics, general utilities, and POSIX process functions.
- `argc` counts arguments and `argv` holds them; requiring `argc == 2` ensures exactly one pathname was supplied.
- `open(argv[1], O_RDONLY)` asks the kernel to resolve and open that pathname. The returned integer is process-local descriptor authority.
- `if (fd < 0)` handles failure before attempting an exec transition.
- `char *child[] = {..., NULL}` builds the NUL-terminated argument vector required by `execvp`.
- `execvp(child[0], child)` searches `PATH` for Python and replaces the current process image while retaining non-close-on-exec descriptors.
- Code after a successful `execvp` never runs; `perror` and `return 1` handle only failure.

### Child source, line by line

- `for fd in range(0, 32)` tests a bounded set of possible descriptor numbers.
- `os.readlink(f"/proc/self/fd/{fd}")` asks procfs what object a descriptor references; an `OSError` means that number is not open or not inspectable.
- The first `print` reports descriptor number and target.
- For descriptors 3 and above, `os.lseek` rewinds seekable objects and `os.read` attempts to consume bytes without reopening a pathname.
- The second `except OSError` deliberately tolerates descriptors that cannot seek or read. It does not prove those descriptors lack other authority.

## Exercise 2 - Fix at creation time

Open `nano fd-parent.c` in the workspace. Change the open flags to:

```c
O_RDONLY | O_CLOEXEC
```

### Line by line

- `O_RDONLY` requests a read-only descriptor.
- `|` is C's bitwise OR operator; it combines independent flag bits in one integer.
- `O_CLOEXEC` asks the kernel to set close-on-exec atomically when the descriptor is created, avoiding a window between `open` and a later `fcntl`.

Save with Ctrl+O, Enter, then Ctrl+X. Check with `cat fd-parent.c`, rebuild
with the same compiler command, and repeat the fixture invocation. Stop on
compiler errors. Expected: the manifest descriptor is absent after exec;
descriptors 0, 1, and 2 may remain. This flag does not prevent the parent
from using the descriptor before that exec transition.

## Exercise 3 - Verify the flag before exec

Add this immediately after `open` and before `execvp`:

```c
int flags = fcntl(fd, F_GETFD);
if (flags < 0) {
    perror("fcntl(F_GETFD)");
    return 1;
}
fprintf(stderr, "FD_CLOEXEC=%s\n", (flags & FD_CLOEXEC) ? "yes" : "no");
```

### Line by line

- `fcntl(fd, F_GETFD)` reads descriptor flags; the error branch stops before treating failure as a valid mask.
- `flags & FD_CLOEXEC` uses bitwise AND to test whether that specific bit is present.
- `condition ? "yes" : "no"` is C's conditional operator.
- `fprintf(stderr, ...)` sends the diagnostic to standard error, and `\n` terminates the line.

Rebuild. Expected: `FD_CLOEXEC=yes`, followed by no protected manifest in the child. `FD_CLOEXEC` affects the exec transition; it does not prevent the current process from using the descriptor.

Security conclusion: descriptors are capabilities to already-open kernel objects. Path checks and later filesystem policy do not retroactively erase them.

## Exercise 4 - Close descriptors already inherited

`O_CLOEXEC` helps when you control descriptor creation. A general launcher can
already have extra descriptors at startup. Closing only the number seen in
one run does not solve that case. Read the supplied bridge program:

```bash
ls -l close-extra.c
cat close-extra.c
```

```c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>

int main(void) {
    int descriptor = open("/dev/null", O_RDONLY);
    if (descriptor < 0) {
        perror("open");
        return 1;
    }
    printf("Opened descriptor: %d\n", descriptor);
    if (close_range(3, ~0U, 0) != 0) {
        perror("close_range");
        return 1;
    }
    errno = 0;
    int flags = fcntl(descriptor, F_GETFD);
    if (flags != -1 || errno != EBADF) {
        fprintf(stderr, "Expected the descriptor to be closed\n");
        return 1;
    }
    puts("Extra descriptor closed; stdout still works.");
    return 0;
}
```

### Source, line by line

`_GNU_SOURCE` exposes the installed libc's `close_range` declaration. The
headers declare errors, descriptor operations, diagnostics, and range closure.
The program opens only `/dev/null`, a harmless local device whose reads return
end-of-file, and stops if that open fails.

`close_range(3, ~0U, 0)` closes from descriptor 3 through the maximum unsigned
value. `U` makes zero unsigned; bitwise complement `~` sets all its bits. The
final zero requests immediate closure, not close-on-exec marking. Standard
streams 0-2 remain, and no specific extra descriptor number is assumed.

`errno = 0` clears the error indicator before the observation. `F_GETFD` should
then fail with `EBADF`, meaning that descriptor is not open. Checking both the
return and reason avoids treating any error as the expected one. The final
`puts` proves stdout still works.

```bash
cc -std=c11 -Wall -Wextra -O2 close-extra.c -o close-extra
./close-extra
echo $?
```

Expect an opened descriptor above 2, the closure confirmation, and status 0.
Using nano, temporarily remove only the `close_range` error-check block from
the workspace copy. Save, rebuild, and run: verification should now fail
because the descriptor remains open. Restore the block and confirm success.
Do not change the expected-error test to make an incomplete control pass.

The bridge closes descriptors but launches no arbitrary command and does not
alter the environment. The independent lab combines separate practiced skills.

## Checkpoint, troubleshooting, and reset

Explain preventing inheritance of a newly opened descriptor versus closing
extra descriptors already inherited. Why is a literal `close(3)` insufficient?

- Missing manifest: use this attempt's metadata, not a remembered old path.
- No initial leak: inspect flags and whether a resumed workspace was already
  repaired. Reset only if discarding those edits is intended.
- Different number: identify the target object, not just descriptor 3.
- `close_range` unavailable: check the supported VM kernel/libc; do not ignore
  the error and continue to launch a less-confined workload.

Return to the repository root for `./lab-reset 01.03 --dry-run`, then
`./lab-reset 01.03 --yes` when ready to discard the lesson's edits.

## Sources and scope

[open](https://man7.org/linux/man-pages/man2/open.2.html),
[execve](https://man7.org/linux/man-pages/man2/execve.2.html), and
[close_range](https://man7.org/linux/man-pages/man2/close_range.2.html) describe
creation, inheritance, and range closure. Range closure requires Linux 5.9+
and this wrapper requires glibc 2.34+; the Fedora/Ubuntu baselines supply them.
Removing a reference does not prove every other authority channel is closed
or prevent reopening a pathname the process can still access.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-01-process-authority/lab/README.md format=markdown -->
# Module 01 independent lab - Hygienic launcher

Build a small launcher for an untrusted local tool. This is independent work: the exact implementation is intentionally not provided.

## Preparation and planning

Before attempting this lab, complete 01.01-01.03. Use 01.02's explicit C environment array and 01.03's descriptor-closure exercise as mechanisms, not as a ready-made combined launcher. You are deciding how to preserve the command interface while removing unintended inputs.

A denylist for only one known variable meets a narrower goal than an environment allowlist. The randomized grader checks its synthetic token; it does not prove your policy removes every possible sensitive variable. State the policy you actually implemented. Likewise, checking only descriptor 3 is not closing all unknown descriptors above 2.

From the course root:

```bash
./lab-start module-01
cd .student/01.lab
pwd
ls -l launcher.c
cat launcher.c
nano launcher.c
```

`lab-start` creates your editable lab copy. The next three commands enter it and confirm the source name; `cat` reads it, and `nano` opens it for editing. Save with `Ctrl-O`, `Enter`, then leave with `Ctrl-X`. Work only in this student copy. The canonical starter is deliberately incomplete:

```c
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s COMMAND [ARG ...]\n", argv[0]);
        return 2;
    }

    /* Intentional starter flaw: authority is transferred without hygiene. */
    execvp(argv[1], &argv[1]);
    perror("execvp");
    return 1;
}
```

The feature-test macro appears before headers. `stdio.h` supplies diagnostics; `unistd.h` supplies `execvp`. `argc` counts arguments, including the launcher name. The usage block rejects a missing child command. `argv[1]` names that command, while `&argv[1]` forwards its complete argument vector. Successful `execvp` never returns; `perror` and the final nonzero return handle failure. The starter preserves this interface but omits the stated security controls.

## Contract

Edit `launcher.c`. The grader will compile it with a C11 compiler, then invoke it as:

```text
./launcher COMMAND [ARG ...]
```

Your launcher must:

- execute the requested command and preserve its normal stdout/stderr;
- ensure the synthetic variable `NE_LAB_TOKEN` is absent in the executed program;
- ensure every inherited descriptor above 2 is closed before the executed program begins;
- return a nonzero status when it cannot launch the command;
- avoid printing environment values or protected data itself.

The grader changes the token, pathname, and inherited descriptor on every run. Hard-coded values cannot pass the security properties.

## Workflow

```bash
cc -std=c11 -Wall -Wextra -O2 launcher.c -o launcher
./launcher /usr/bin/printf 'child works\n'
../../lab-grade module-01
```

### Test commands, line by line

- `cc` compiles only your current `launcher.c`; the warning flags help catch interface mistakes before grading.
- `./launcher /usr/bin/printf ...` checks the required `COMMAND [ARG ...]` interface with an absolute, harmless command.
- `../../lab-grade module-01` moves no files: the relative path simply reaches the repository's grader from `.student/01.lab`.
- The starter's `execvp(argv[1], &argv[1])` preserves argument boundaries and demonstrates basic execution, but intentionally performs no authority hygiene. The guided lessons contain the required concepts; this lab does not state their complete implementation.

Run the final command from the repository root instead if your shell is not in this workspace:

```bash
./lab-grade module-01
```

Practice mode names failed properties and points back to practiced lessons. Exam mode reports only failed properties:

```bash
./lab-grade module-01 --mode exam
```

- `--mode exam` changes diagnostic detail only. It does not weaken or replace any property check.

## Interpret your result and replay

Run the starter once before editing and record which security properties fail. A compile error is not an observed security denial, and a missing child is not successful containment. After your repair, use both a harmless successful command and a deliberately nonexistent absolute command; the latter must produce a nonzero launcher status.

For the practice grader, read each failed property and revisit its lesson before changing code. Do not alter the grader, canonical files, or generated fixture to force a pass. Passing establishes only the tested contract, not a production-ready sandbox.

From this workspace, `cd ../..` returns to the course root. `./lab-reset module-01` discards this module's student work and generated fixtures after confirmation; copy any notes you want to retain first. Then `./lab-start module-01` creates a fresh randomized attempt. No saved implementation is supplied by this manual.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-02-namespaces/README.md format=markdown -->
# Module 02 - Linux namespaces

Namespaces change which kernel objects a process sees. They do not automatically remove capabilities, filter syscalls, limit resources, or make a complete sandbox.

Play in order: `02.01`, `02.02`, `02.03`, then `module-02`.

## Learning route and limits

Prerequisites: Module 01. Continue as your ordinary account inside the disposable Linux VM. The guided lessons introduce their new syntax and interfaces before the independent lab combines them.

02.01 introduces namespace handles and identity maps. 02.02 changes a child hostname while preserving the parent's and practices argument forwarding through a shell. 02.03 shows why changing PID numbering without replacing procfs creates contradictory observations.

Ask which namespace of which type, not merely whether a process is in a container. Explain why inside UID 0 is not global root, why PID 1 is namespace-relative, and why a fresh PID namespace needs a matching procfs view. Here the parent environment is the VM, not the Mac.

Before moving on, demonstrate both useful allowed work and the intended restriction, and explain the difference in your own words. A failed compiler command or missing input is not a security success. Use the independent lab's practice feedback to revisit a specific lesson; passing checks does not replace understanding or make the combined program production-ready.
<!-- /source -->

## Module outcome and mental model

Namespaces change what a process sees when it uses particular kernel interfaces. They do not form one all-or-nothing container switch. Each namespace type isolates a resource view, and useful containment requires deliberate composition.

- A **user namespace** changes how user and group IDs and capabilities are interpreted.
- A **UTS namespace** isolates hostname and domain-name state.
- A **PID namespace** changes visible process IDs and the process tree.
- A **mount namespace** isolates mount-table changes.
- A **network namespace** isolates interfaces, routes, ports, and network stacks.
- An **IPC namespace** isolates selected System V IPC and POSIX message queues.
- A **cgroup namespace** changes the cgroup hierarchy view; it does not impose resource limits by itself.

Two verification questions apply to every namespace exercise:

- Did the target process receive a namespace handle different from the observer's handle?
- Does the resource view actually match the intended namespace?

The first question checks membership. The second catches stale mounts, incorrect ordering, and a command that mentions `unshare` without achieving the required state.

> **Safety boundary:** These exercises depend on unprivileged user namespaces. If the VM disables them, enable them in the disposable VM. Do not switch to a work host or run the course as host root to force progress.

<!-- PAGEBREAK -->

<!-- source: course/module-02-namespaces/lesson-01/README.md format=markdown -->
# 02.01 - Read namespace identity

## Goals

- Record baseline namespace handles.
- Create a mapped user namespace as an ordinary user.
- Interpret namespace-local UID 0 without confusing it with host root.
- Read the UID mapping that connects inside and outside identities.

## Before you start

Complete Module 01 first. Work as your ordinary user inside the disposable Linux VM. In this chapter, **parent** means the surrounding VM environment, not your Mac. None of these commands belong in the Mac terminal.

A namespace is a kernel object that gives member processes a particular view of one category of state. Joining a UTS namespace changes hostname state; joining a PID namespace changes process-number visibility. A user namespace also defines how user and group IDs map to the parent. Creating one kind does not create all the others.

`/proc` is a kernel-provided filesystem, not a collection of saved reports. `/proc/self` refers to the process accessing it. Thus the `readlink` child below inspects its own membership, inherited from your shell. A namespace handle such as `user:[4026531837]` identifies an object; it is not a user ID and its exact number is not a learning target.

From the course root:

```bash
./lab-start 02.01
cd .student/02.01
pwd
ls -l
```

`lab-start` prepares the editable workspace. `cd` enters it, `pwd` confirms where you are, and `ls -l` shows its contents. This lesson uses shell commands; there is no hidden program you need to find or compile.

## Exercise 1 - Capture the baseline

```bash
printf '%-8s %s\n' TYPE HANDLE
for ns in user uts pid mnt net ipc cgroup; do
  printf '%-8s %s\n' "$ns" "$(readlink /proc/self/ns/$ns)"
done
```

## What each line does

- The first `printf` emits headings. `%-8s` left-aligns a string in an eight-character field.
- `for ns in ...; do` begins a loop and assigns each listed namespace name to `ns` in turn.
- `readlink /proc/self/ns/$ns` asks procfs for this process's handle for the current type.
- `$(...)` substitutes that handle into `printf`.
- Quotes around both expansions preserve one argument per value.
- `done` ends the loop.

Expected shape:

```text
TYPE     HANDLE
user     user:[4026531837]
uts      uts:[4026531838]
pid      pid:[4026531836]
mnt      mnt:[4026531841]
net      net:[4026531992]
ipc      ipc:[4026531839]
cgroup   cgroup:[4026531835]
```

Exact numbers vary. Equal handles mean two processes refer to the same namespace object for that type; unequal handles mean different membership.

## Exercise 2 - Create a mapped user namespace

```bash
unshare --user --map-root-user sh -c '
  echo "inside uid=$(id -u)";
  readlink /proc/self/ns/user;
  cat /proc/self/uid_map
'
```

## What each line does

- `unshare` creates requested namespaces for the command that follows.
- `--user` requests a new user namespace.
- `--map-root-user` maps the invoking ordinary identity to UID and GID 0 inside it.
- `sh -c` starts a shell whose program is the following quoted string.
- Single quotes keep the outer shell from expanding `$(id -u)` or interpreting inner newlines.
- Inside, `id -u` prints the namespace-visible effective UID.
- `readlink` records the new user namespace handle.
- `uid_map` describes how ranges of inside UIDs translate to parent-namespace UIDs.

Typical mapping shape:

```text
inside uid=0
user:[4026532777]
         0       1000          1
```

The mapping line means one ID beginning at inside UID 0 maps to parent UID 1000. The parent value will match your ordinary VM account, not necessarily 1000.

## Exercise 3 - Disprove “UID 0 means global root”

```bash
unshare --user --map-root-user sh -c 'id; ls /root'
```

## What each part does

- The namespace flags reproduce the mapped identity.
- `;` runs the second inner command whether or not `id` succeeds.
- `id` reports namespace-relative UID 0.
- `ls /root` attempts a read-only directory listing through the existing VM filesystem.
- On the course image, `/root` is not readable by your ordinary account. The expected permission denial shows that namespace-local UID 0 did not grant that access. If an administrator made `/root` world-readable, this particular test would not demonstrate a denial; inspect permissions instead of changing them.

User namespaces can grant a process capabilities over resources owned by the new namespace. They do not grant corresponding power over parent-owned resources. A complete identity statement therefore includes the numeric IDs, the user namespace handle, and the ID mappings.

## Troubleshooting and checkpoint

- `Operation not permitted` usually means unprivileged user namespaces are disabled by VM policy.
- An empty or surprising map means the mapping helper failed; inspect stderr instead of assuming root was created.
- Never interpret `id -u` alone as a privilege proof.
- You should be able to compare two namespace handles and explain the three columns in `uid_map`.

Before continuing, predict whether creating only a user namespace also changes the UTS handle. Repeat the baseline loop inside the quoted child command to test your prediction. The repair to the mistaken "root everywhere" interpretation is to record the mapping and namespace, not to add `sudo`.

The child namespace is released when its last process/reference disappears. No global setting needs undoing. To discard lesson work, return to the course root with `cd ../..` and run `./lab-reset 02.01`; that reset deliberately removes this lesson's workspace.

## Source truth

The identity and mapping model is documented in [user_namespaces(7)](https://man7.org/linux/man-pages/man7/user_namespaces.7.html); the command flags are documented in [unshare(1)](https://man7.org/linux/man-pages/man1/unshare.1.html). These explain the mechanism, while the observations above establish what your VM actually allowed.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-02-namespaces/lesson-02/README.md format=markdown -->
# 02.02 - Change UTS state without changing the host

## Goals

- Isolate hostname state in a UTS namespace.
- Understand why namespace creation and authority to modify its state are separate concerns.
- Compare host and child state before and after the change.
- Inspect a live process from another terminal.

## Exercise 1 - Baseline, change, and proof

Complete 02.01 first. A UTS namespace stores a hostname and NIS domain name. It does not create a new network stack, DNS service, or machine. The hostname starts as a copy; changing the copy must leave the parent VM's hostname unchanged.

From the course root, prepare this shell-only lesson:

```bash
./lab-start 02.02
cd .student/02.02
pwd
ls -l
```

The first command creates the student workspace; the next three enter and inspect it. There is no source file to compile. Predict the two `host` lines before running the next block: they should be identical. Here "host" means the parent VM environment, not the Mac.

```bash
HOST_BEFORE=$(hostname)
echo "host before=$HOST_BEFORE"
unshare --user --map-root-user --uts sh -c '
  echo "inside before=$(hostname)";
  hostname north-echo-lab;
  echo "inside after=$(hostname)";
  readlink /proc/self/ns/uts
'
echo "host after=$(hostname)"
```

## What each line does

- The first command substitution captures the parent-visible hostname.
- The variable is local to this shell unless exported.
- `--user --map-root-user` creates namespace-local capability; `--uts` creates an isolated UTS view.
- Single quotes defer inner `hostname` substitutions until the child shell runs.
- The first inner line observes the initial copied hostname.
- `hostname north-echo-lab` changes only the new UTS namespace.
- The second inner observation proves the new value.
- `readlink` records the namespace identity associated with that state.
- The final line runs back in the parent after `unshare` exits and proves the host value is unchanged.

Expected relationship:

```text
host before=<vm hostname>
inside before=<vm hostname>
inside after=north-echo-lab
uts:[different handle]
host after=<same vm hostname>
```

The mapped user namespace gives the process the relevant capability inside the newly owned UTS namespace. It does not create host authority.

## Exercise 2 - Make the incomplete attempt

```bash
unshare --uts hostname broken-attempt
```

- `--uts` requests only a UTS namespace.
- `hostname broken-attempt` is the command to run inside it.
- An ordinary user generally lacks the capability needed for this setup without the mapped user namespace.
- Expected: `Operation not permitted` and no host change.

The failure is useful. Creating a namespace type does not automatically supply every credential needed to configure it.

## Exercise 3 - Inspect a live namespace

In terminal one:

```bash
unshare --user --map-root-user --uts sh -c 'hostname north-echo-hold; echo $$; sleep 60'
```

- The flags create the temporary user and UTS namespaces.
- `hostname` assigns a recognizable value.
- `echo $$` prints the shell's PID as seen from the parent namespace running the terminal.
- `sleep 60` keeps the process and namespace alive. `Ctrl-C` ends it early.

Open a second terminal and enter the **same VM**, using the same `limactl shell INSTANCE_NAME` command you used for terminal one. Do not run the following inspection on the Mac or in a different VM. For example, if the first command printed `12345`, replace `PRINTED_PID` below with `12345`; do not type the placeholder literally. In terminal two:

```bash
readlink /proc/PRINTED_PID/ns/uts
readlink /proc/self/ns/uts
```

- The first line observes the held process's UTS namespace.
- `/proc/self` in the second terminal refers to the inspecting process.
- Different handles prove different membership even if both hostnames happened to contain the same text.

Verification should inspect effective state, not merely search a script for the word `unshare`.

## Exercise 4 - Preserve an argument vector through a shell

The independent lab will accept a command and its arguments. A shell wrapper must preserve their boundaries, including arguments containing spaces. Practice that separately from namespace setup:

```bash
NE_PRACTICE_LABEL=example sh -c '
  printf "label=%s script-name=%s\n" "$NE_PRACTICE_LABEL" "$0"
  exec "$@"
' practice-wrapper /usr/bin/printf '<%s>\n' 'two words' final
```

- The leading assignment puts a synthetic label in this child's environment. Reading a supplied value differs from hard-coding a particular fixture value.
- `sh -c` consumes one argument as its program. The next, `practice-wrapper`, becomes `$0`, the shell's script name. It is **not** part of `$@`.
- The remaining arguments become `$1`, `$2`, and so forth. `"$@"` expands them as separate arguments, preserving the original boundaries.
- `exec` replaces the shell with that argument vector. It does not concatenate and reinterpret a command string.
- `/usr/bin/printf` receives its format followed by two data arguments. Expect `<two words>` on one line and `<final>` on another.

Deliberately change `exec "$@"` to `exec $@` in the command you type and repeat. The unquoted expansion splits `two words` into separate arguments: the output becomes three data lines. Restore the quotes and verify two lines again. This error can be invisible when every test argument is a single word.

For a script file, the corresponding concepts are `#!/bin/sh` on the first line, `$1` for its first supplied argument, and `exec "$@"` to replace it. The starter in the independent lab shows that minimal script. Combine this practiced argument handling with the namespace controls yourself; do not turn the supplied command into text for another shell to parse.

## Troubleshooting and checkpoint

- If the first terminal exits before inspection, rerun with a longer harmless sleep.
- If `/proc/PRINTED_PID` is absent, confirm you used the host-visible PID and that the process is still alive.
- If the handles match, inspect the exact flags and quoting rather than changing the expected result.
- You should be able to state why the parent hostname remains unchanged.

Finish with `hostname` in terminal one after the child exits and compare it with `echo "$HOST_BEFORE"`. That comparison plus the different namespace handles is the checkpoint: a successful command alone does not prove isolation. The deliberately incomplete attempt in Exercise 2 is repaired by the mapped user namespace in Exercise 1, never by running the lesson as global root.

After the child exits, its private hostname disappears with the namespace. If you reset the workspace, run `cd ../..` followed by `./lab-reset 02.02` in terminal one; do not try to "restore" the parent hostname with a privileged command.

## Source truth

See [uts_namespaces(7)](https://man7.org/linux/man-pages/man7/uts_namespaces.7.html) for isolated hostname state and [user_namespaces(7)](https://man7.org/linux/man-pages/man7/user_namespaces.7.html) for the ownership-based capability check.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-02-namespaces/lesson-03/README.md format=markdown -->
# 02.03 - PID namespaces and the procfs mistake

## Goals

- Start a shell as PID 1 inside a new PID namespace.
- Observe why an inherited procfs can show the wrong process view.
- Compose PID and mount namespaces with a matching procfs.
- Recognize the responsibilities assigned to namespace PID 1.

## Exercise 1 - Create the incomplete setup

Complete 02.01 and 02.02 first. A PID is a process identifier **within a PID namespace**. The same process can have one number inside a child namespace and another in its parent. PID 1 is the first process in the child namespace and has special lifecycle responsibilities. A mount namespace separately controls which filesystem mounts are visible. We need both concepts because `ps` obtains its information from a mounted filesystem, `/proc`.

From the course root:

```bash
./lab-start 02.03
cd .student/02.03
pwd
ls -l
```

These commands prepare, enter, and inspect this shell-only workspace. There is no source file to open. Predict whether changing process numbering alone will automatically replace an existing `/proc` mount. Exercise 1 deliberately leaves that second control out.

```bash
unshare --user --map-root-user --pid --fork sh -c '
  echo "shell says pid=$$";
  ps -o pid,ppid,comm | head
'
```

## What each line does

- The mapped user namespace provides safe namespace-local authority.
- `--pid` creates a PID namespace for children, not retroactively for the calling `unshare` process.
- `--fork` creates the child that can enter the new PID namespace.
- The quoted shell runs as the namespace's first process and expands its own `$$`.
- `ps` obtains process data through the currently mounted `/proc`.
- `head` limits display but cannot correct the underlying view.

Expected surprise: the shell reports PID 1 while `ps` may show many host processes or numbers that do not agree. The PID namespace changed, but the inherited procfs mount still represents the parent PID namespace.

## Exercise 2 - Mount a matching procfs

```bash
unshare --user --map-root-user --pid --fork --mount --mount-proc sh -c '
  echo "shell says pid=$$";
  ps -o pid,ppid,comm;
  echo "pid namespace=$(readlink /proc/self/ns/pid)";
  echo "mount namespace=$(readlink /proc/self/ns/mnt)"
'
```

## What each line does

- `--mount` isolates mount-table changes from the parent.
- `--mount-proc` mounts a fresh procfs associated with the new PID namespace.
- `--pid --fork` creates and enters the PID namespace in the required child.
- The shell sees itself as PID 1.
- `ps` now reads the fresh procfs, so its process list should agree with the namespace-local IDs.
- The two `readlink` calls record both namespace identities.

Expected: a small process list containing the shell and observation tools, plus new PID and mount handles. Process counts can vary because `ps`, shells, and pipelines briefly create processes.

## Exercise 3 - Wait for a known child

```bash
unshare --user --map-root-user --pid --fork --mount --mount-proc sh -c '
  (exit 7) &
  child=$!
  wait "$child"
  result=$?
  echo "waited for child=$child status=$result"
  ps -o pid,ppid,stat,comm
'
```

## What each line does

- Parentheses create a subshell; `exit 7` gives it a recognizable nonzero status.
- `&` runs that subshell asynchronously.
- `$!` gives the last background child's PID; save it immediately rather than guessing it from the process list.
- `wait "$child"` collects the status for that child. The shell may already have reaped it internally; `wait` still retrieves the saved result.
- Save `$?` before another command replaces it. The expected status is 7, not a namespace failure.
- The final `ps` shows the remaining processes. Do not expect the exited child to remain in the list.

This demonstrates waiting for a known direct child. It does **not** test orphan adoption, zombie accumulation, or a general-purpose init implementation. A shell may automatically reap children, so a snapshot with no `Z` rows is not proof that an arbitrary application is a suitable init.

Namespace PID 1 has special signal behavior and becomes the adopter for orphaned descendants. A production runtime normally supplies a small init/reaper instead of casually making an arbitrary workload PID 1.

## Why namespace composition matters

A PID namespace without a matching procfs produces contradictory observations. A UTS namespace without suitable namespace-local authority may not be configurable. A mount namespace does not automatically create a private filesystem tree. Namespaces isolate selected views; they are components, not a complete sandbox policy.

## Troubleshooting and checkpoint

- If `--mount-proc` fails, confirm the mapped user namespace was created and the util-linux `unshare` version supports it.
- If `ps` shows the host, compare the mount namespace handle and inspect the active `/proc` mount.
- Do not grade by exact process count; grade by namespace relationships and the procfs view.
- You should be able to explain why `$$` and `ps` disagreed in the incomplete setup.

For your checkpoint, describe the missing control in Exercise 1, run the repaired Exercise 2, and explain why a changed PID handle alone would be insufficient evidence. Never change the VM's real `/proc` mount to repair this lesson. The private mounts vanish with their namespace after the command ends.

To discard the workspace, return with `cd ../..` and run `./lab-reset 02.03`. This does not erase other lessons.

## Source truth

See [pid_namespaces(7)](https://man7.org/linux/man-pages/man7/pid_namespaces.7.html) for PID 1, visibility, and procfs relationships; [unshare(1)](https://man7.org/linux/man-pages/man1/unshare.1.html) for `--fork` and `--mount-proc`; and the VM's `help wait` for the shell builtin.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-02-namespaces/lab/README.md format=markdown -->
# Module 02 independent lab - Namespace launcher

Implement `sandbox.sh` so it launches an arbitrary command in fresh user, UTS, PID, and mount namespaces.

## Preparation and planning

Complete 02.01-02.03 first. This lab combines controls you have observed separately: identity mapping in 02.01, UTS state and argument forwarding in 02.02, and PID/mount/procfs relationships in 02.03. Your job is to order those controls and preserve the caller's interface.

The command must become PID 1, not a child of a shell that unnecessarily remains PID 1. Explain where process replacement is needed before implementing it. An unchanged hostname by itself does not prove shared membership, and a different hostname by itself does not prove separate membership; verify handles as well.

From the course root:

```bash
./lab-start module-02
cd .student/02.lab
pwd
ls -l sandbox.sh
cat sandbox.sh
nano sandbox.sh
```

`lab-start` creates your editable lab copy. The next three commands enter it and confirm the source name; `cat` reads it, and `nano` opens it for editing. Save with `Ctrl-O`, `Enter`, then leave with `Ctrl-X`. Work only in this student copy. The canonical starter is deliberately incomplete:

```bash
#!/bin/sh
set -eu

if [ "$#" -eq 0 ]; then
  echo "usage: $0 COMMAND [ARG ...]" >&2
  exit 2
fi

# Intentional starter flaw: this does not create any isolation.
exec "$@"
```

The interpreter line selects `sh`. `set -eu` enables exit-on-error behavior and errors for unset expansions; neither creates a sandbox. `$#` counts supplied arguments. The `if` block rejects an empty interface, writes usage to stderr with `>&2`, and exits 2. `exec "$@"` preserves arguments and replaces the script, but all namespace setup is missing. Read 02.02's argument-vector exercise before modifying this line.

## Contract

The grader invokes:

```text
NE_EXPECTED_HOSTNAME=randomized-value ./sandbox.sh COMMAND [ARG ...]
```

The launched command must observe:

- the randomized hostname from `NE_EXPECTED_HOSTNAME`;
- a UTS namespace distinct from the grader;
- a PID namespace distinct from the grader, with the command running as namespace PID 1;
- a mount namespace distinct from the grader;
- a procfs that reflects the new PID namespace;
- the command's stdout, stderr, arguments, and exit status.

Do not hard-code a hostname. Do not change the host hostname or mount table. This lab expects an ordinary user in the disposable VM with unprivileged user namespaces enabled.

Useful interfaces have all appeared in the guided lessons. The grader reports properties, not an implementation recipe.

```bash
chmod +x sandbox.sh
./sandbox.sh sh -c 'echo "pid=$$ host=$(hostname)"; ps -o pid,ppid,comm'
../../lab-grade module-02
```

### Test commands, line by line

- `chmod +x sandbox.sh` adds the executable permission needed for the kernel to launch the script directly.
- `./sandbox.sh sh -c '...'` supplies `sh` as the arbitrary command under test; the quoted program observes namespace-local PID, hostname, and procfs state.
- `$$` and `$(hostname)` are intentionally inside single quotes, so the outer shell does not expand them before the sandbox runs.
- `../../lab-grade module-02` invokes the external randomized property grader from the generated workspace.
- The starter's `exec "$@"` preserves the caller's argument vector but creates no namespaces. `$@` is quoted so each original argument stays separate.

## Interpret your result and replay

Run the starter once before editing and record which security properties fail. A compile error is not an observed security denial, and a missing child is not successful containment. After your repair, use both a harmless successful command and a deliberately nonexistent absolute command; the latter must produce a nonzero launcher status.

For the practice grader, read each failed property and revisit its lesson before changing code. Do not alter the grader, canonical files, or generated fixture to force a pass. Passing establishes only the tested contract, not a production-ready sandbox.

From this workspace, `cd ../..` returns to the course root. `./lab-reset module-02` discards this module's student work and generated fixtures after confirmation; copy any notes you want to retain first. Then `./lab-start module-02` creates a fresh randomized attempt. No saved implementation is supplied by this manual.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-03-privilege/README.md format=markdown -->
# Module 03 - Privilege, capabilities, and no_new_privs

You will inspect the actual privilege state carried by a process, remove capability channels, and set a one-way privilege floor before `execve`.

Play in order: `03.01`, `03.02`, `03.03`, then `module-03`.

## Learning route and limits

Prerequisites: Module 02. Continue as your ordinary account inside the disposable Linux VM. The guided lessons introduce their new syntax and interfaces before the independent lab combines them.

03.01 inventories identity and all five capability sets. 03.02 contrasts partial and complete changes, then practices current-set reduction in C. 03.03 installs and observes the inherited no_new_privs restriction.

Separate current authority from the possibility of gaining privilege when executing another file. Explain why a capability-empty process can still read its own files or use inherited descriptors. Do not make setuid binaries, install file capabilities, or run this lab as global root.

Before moving on, demonstrate both useful allowed work and the intended restriction, and explain the difference in your own words. A failed compiler command or missing input is not a security success. Use the independent lab's practice feedback to revisit a specific lesson; passing checks does not replace understanding or make the combined program production-ready.
<!-- /source -->

## Module outcome and mental model

Linux privilege is not a Boolean “root or not root” value. A process's authority can depend on:

- real, effective, saved, and filesystem user and group IDs;
- supplementary groups;
- the effective, permitted, inheritable, bounding, and ambient capability sets;
- the owning user namespace and its ID mappings;
- file capabilities and set-user-ID or set-group-ID transitions;
- the `no_new_privs` bit;
- open descriptors and other authority channels from earlier modules.

Capabilities split many traditional root powers into named bits. That improves precision, but it creates several interacting sets that must be observed separately.

- **Effective:** bits currently considered for capability checks.
- **Permitted:** capabilities the thread may make effective.
- **Inheritable:** input to capability calculations across exec when file capability rules participate.
- **Bounding:** a ceiling that limits capabilities obtained during exec.
- **Ambient:** selected capabilities that can survive exec of ordinary non-privileged programs.

`no_new_privs` adds a one-way rule: an exec transition may not grant privileges the process did not already possess. It does not remove current authority by itself.

<!-- PAGEBREAK -->

<!-- source: course/module-03-privilege/lesson-01/README.md format=markdown -->
# 03.01 - UIDs are not the whole privilege story

## Goals

- Read complete UID, GID, group, capability, and `no_new_privs` state from procfs.
- Decode a hexadecimal capability mask.
- Compare ordinary identity with namespace-local root.
- Find file capabilities that complicate simplistic UID reasoning.

## Exercise 1 - Inspect current credentials

Complete Module 02 first. A UID identifies an account within a user namespace; it is not a complete privilege inventory. Linux splits many traditional root powers into **capabilities**. Each named capability corresponds to a bit in several per-thread sets. Hexadecimal is simply a compact way of writing those bits; you do not need to memorize the numbers.

- **Effective:** capabilities currently considered for capability checks.
- **Permitted:** capabilities the thread may make effective.
- **Inheritable:** a set that participates in capability calculations across execution.
- **Bounding:** a ceiling that limits capability acquisition through file capabilities across execution; it is not the currently effective set.
- **Ambient:** capabilities preserved across execution of ordinary, non-privileged programs, subject to the kernel's rules.

The four `Uid` columns are real, effective, saved-set, and filesystem UID. The analogous `Gid` columns describe group IDs; `Groups` lists supplementary groups. Keep these concepts separate from capabilities and from `NoNewPrivs`, which Lesson 03.03 introduces as a restriction on future execution transitions.

From the course root:

```bash
./lab-start 03.01
cd .student/03.01
pwd
ls -l
```

This prepares and locates the shell-only lesson. No C program is needed yet. Before inspecting, predict whether an ordinary account can have a nonzero bounding set while its effective set is empty.

```bash
id
grep -E '^(Uid|Gid|Groups|Cap(Inh|Prm|Eff|Bnd|Amb)|NoNewPrivs):' /proc/self/status
```

## What each line does

- `id` summarizes the invoking process's user, primary group, and supplementary groups.
- `grep -E` enables extended regular-expression syntax.
- `^` requires a match at the start of a line.
- The outer alternatives select identity, groups, capabilities, or `NoNewPrivs`.
- `Cap(Inh|Prm|Eff|Bnd|Amb)` matches the five capability fields without repeating the prefix.
- `/proc/self/status` is generated by the kernel for the process opening it. The `grep` child inherits the shell's credentials for this observation.

Typical ordinary-user shape:

```text
Uid:    1000    1000    1000    1000
Gid:    1000    1000    1000    1000
Groups: 1000 ...
CapInh: 0000000000000000
CapPrm: 0000000000000000
CapEff: 0000000000000000
CapBnd: 000001ffffffffff
CapAmb: 0000000000000000
NoNewPrivs: 0
```

Values vary by VM and distribution. A nonzero bounding set does not mean those bits are currently effective; it records an upper bound for future transitions.

Decode the effective mask:

```bash
CAP_EFF=$(awk '/^CapEff:/{print $2}' /proc/self/status)
capsh --decode="$CAP_EFF"
```

## What each line does

- The `awk` pattern selects the line beginning `CapEff:`.
- `{print $2}` emits the second whitespace-delimited field, the hexadecimal mask.
- Command substitution stores it in `CAP_EFF`.
- `capsh --decode=` translates set bits into capability names.
- Quoting ensures even an empty or unusual expansion remains one argument.

For a zero mask, expect an empty decoded set. For nonzero masks, record each capability name instead of describing the process merely as “privileged.”

## Exercise 2 - Compare namespace-local root

```bash
unshare --user --map-root-user sh -c '
  id;
  grep -E "^(Uid|Cap(Inh|Prm|Eff|Bnd|Amb)):" /proc/self/status;
  capsh --print
'
```

## What each part does

- `unshare` creates a new user namespace and maps the ordinary caller to UID 0 inside it.
- The child `id` displays namespace-relative identity.
- The child `grep` prints UID and all capability fields.
- `capsh --print` provides a named description of capability and identity state in this child environment. The first exercise already taught decoding a single raw mask; using the built-in report here avoids a second layer of shell/awk quoting.
- Capability bits are meaningful relative to the user namespace that owns the target resource.

Expected: UID 0 and a set of capabilities inside the new user namespace, but no corresponding host-root authority.

## Exercise 3 - Disprove the nonzero-UID simplification

```bash
getcap -r /usr/bin 2>/dev/null | head
```

## What each part does

- `getcap` reads file capability extended attributes.
- `-r /usr/bin` walks that directory recursively.
- `2>/dev/null` discards expected permission or unsupported-file diagnostics. Do not suppress stderr while diagnosing an unexpected failure.
- `head` keeps the display short.

Some systems contain programs with file capabilities such as a narrowly scoped network capability; an empty result on your image is valid. Executing an appropriately attributed file can change capability state even when the caller's effective UID is not zero, unless restrictions such as `no_new_privs` prevent the gain. This command only reads attributes: do not add file capabilities to make a demonstration appear. A review must record IDs, groups, namespace mappings, capability sets, executable attributes, and inherited resources.

## Troubleshooting and checkpoint

- If `capsh` or `getcap` is missing, install the distribution's capability utilities package in the VM.
- Treat an all-zero `CapEff` as one observation, not proof that every authority channel is empty.
- Keep the namespace handle alongside the decoded bits when comparing processes.
- You should be able to explain why `CapBnd` may be nonzero while `CapEff` is zero.

The intentional mistake here is a conclusion: "nonzero UID means no privilege" or "zero effective capabilities means no authority." Repair that conclusion with the complete inventory and with Module 01's inherited-descriptor example. Your checkpoint is an explanation of why the inventory still does not answer which already-open resources are accessible.

No privilege attributes were changed in the parent shell. To discard lesson work, return with `cd ../..` and run `./lab-reset 03.01`.

## Source truth

The set definitions and execution rules come from [capabilities(7)](https://man7.org/linux/man-pages/man7/capabilities.7.html); namespace-relative scope comes from [user_namespaces(7)](https://man7.org/linux/man-pages/man7/user_namespaces.7.html). Use `man capsh` in the VM for its display format.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-03-privilege/lesson-02/README.md format=markdown -->
# 03.02 - Drop capability sets deliberately

## Goals

- Decode all five capability sets rather than reading only `CapEff`.
- Use `setpriv` to establish a capability-empty child.
- Observe why clearing only one set is an incomplete fix.
- Verify the resulting process rather than trusting requested flags.

## Exercise 1 - Decode every set

Complete 03.01 first. "Drop privilege" is a desired outcome, not an operation with one universal meaning. In this lesson you will remove capability channels, then inspect what the child actually received. This does not remove your ordinary account's access to its own files.

From the course root:

```bash
./lab-start 03.02
cd .student/03.02
pwd
ls -l
```

The commands prepare and locate your editable workspace. Start with the shell observations; a small C bridge later connects these observations to the independent launcher lab.

```bash
for field in CapInh CapPrm CapEff CapBnd CapAmb; do
  value=$(awk -v key="$field:" '$1==key{print $2}' /proc/self/status)
  printf '%-7s %s -> ' "$field" "$value"
  capsh --decode="$value"
done
```

## What each line does

- The loop assigns each procfs field name to `field`.
- `awk -v key="$field:"` passes the current field plus its colon into `awk`.
- `$1==key` performs exact first-field equality; `{print $2}` emits the mask.
- Command substitution stores the mask in `value`.
- `printf` aligns the name, prints the raw mask, and deliberately omits a newline.
- `capsh --decode` prints capability names and completes the record.
- `done` closes the loop.

Do not collapse the five results into one adjective. Ask which set controls present checks and which sets constrain or enable future exec transitions.

## Exercise 2 - Launch with empty sets

```bash
unshare --user --map-root-user setpriv \
  --bounding-set=-all \
  --inh-caps=-all \
  --ambient-caps=-all \
  sh -c 'grep -E "^(Groups|Cap(Inh|Prm|Eff|Bnd|Amb)):" /proc/self/status'
```

## What each line does

- The mapped user namespace supplies a safe environment for practicing privilege transitions.
- A trailing backslash tells the shell the same command continues on the next physical line.
- `setpriv` changes process privilege attributes before executing the final command.
- `--bounding-set=-all` subtracts every named capability from the bounding set.
- `--inh-caps=-all` clears the inheritable set.
- `--ambient-caps=-all` clears the ambient set.
- The final shell runs the procfs observation after the transitions and reports supplementary groups separately from capability state.

Expected:

```text
CapInh: 0000000000000000
CapPrm: 0000000000000000
CapEff: 0000000000000000
CapBnd: 0000000000000000
CapAmb: 0000000000000000
```

`setpriv` and the kernel perform linked capability calculations during execution, which is why the resulting permitted and effective sets are also observed rather than assumed.

The `Groups` line need not be empty. For the unprivileged single-ID mapping used here, `setgroups(2)` must be disabled before the GID map can be written. Adding `setpriv --clear-groups` after that transition therefore fails with `Operation not permitted` on the course baselines. Group reduction is a separate launcher responsibility that must happen at a boundary where the caller has authority to change its supplementary groups; this exercise isolates capability-set behavior instead of pretending the two controls are interchangeable.

## Exercise 3 - Make the partial fix

```bash
unshare --user --map-root-user setpriv --inh-caps=-all sh -c 'grep -E "^Cap(Inh|Prm|Eff|Bnd|Amb):" /proc/self/status'
```

- This changes only the inheritable set request.
- The final `grep` deliberately prints all sets.
- Expected: `CapInh` is zero, while other sets need not be empty.

The phrase “drop capabilities” is underspecified. Name every relevant set, state the intended postcondition, and verify the kernel-reported result.

## Exercise 4 - Clear current sets in C

The shell utility is useful for experiments, but the independent lab asks for a C launcher. Read this smaller fixed-purpose program before adapting the mechanism. It clears current capability sets and reports them; it does not implement the lab's arbitrary-command interface or `no_new_privs` control.

```bash
ls -l clear-current.c
cat clear-current.c
```

The first command confirms the file exists in `.student/03.02`; the second displays its complete contents. Open it with `nano clear-current.c` if you want to annotate your student copy.

```c
#define _GNU_SOURCE
#include <linux/capability.h>
#include <stdio.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(void) {
    struct __user_cap_header_struct header = {
        .version = _LINUX_CAPABILITY_VERSION_3,
        .pid = 0
    };
    struct __user_cap_data_struct data[2] = {0};

    if (prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_CLEAR_ALL, 0, 0, 0) != 0) {
        perror("clear ambient capabilities");
        return 1;
    }
    if (syscall(SYS_capset, &header, data) != 0) {
        perror("capset");
        return 1;
    }
    if (syscall(SYS_capget, &header, data) != 0) {
        perror("capget");
        return 1;
    }
    printf("effective=%08x%08x\n", data[1].effective, data[0].effective);
    printf("permitted=%08x%08x\n", data[1].permitted, data[0].permitted);
    printf("inheritable=%08x%08x\n", data[1].inheritable, data[0].inheritable);
    return 0;
}
```

### Read the program

- `_GNU_SOURCE` and the headers expose Linux's syscall numbers, capability structures, `prctl`, and diagnostics. This is Linux-specific C, not a portable POSIX capability API.
- The header's `version` selects the kernel's version-3 capability layout; `pid = 0` means the calling thread. The two data elements each represent 32 bits, covering the 64-bit interface.
- `= {0}` initializes every data field to zero, including effective, permitted, and inheritable masks. Uninitialized structures would not express an empty policy.
- `PR_CAP_AMBIENT_CLEAR_ALL` clears the separate ambient set. Any error stops the program. Ignoring an unsupported operation would silently weaken the intended postcondition.
- `syscall(SYS_capset, ...)` asks the kernel to replace the calling thread's current sets. glibc does not expose a normal `capset` wrapper; this small course example calls the kernel interface directly. Larger software should evaluate the higher-level libcap API.
- `SYS_capget` reads the actual state back into the same array. The program does not treat the requested zero-filled input as evidence that the transition worked.
- Each `printf` prints the high 32-bit half followed by the low half, with eight hexadecimal digits per half. The result is a comparable 16-digit mask, not two unrelated capabilities.
- A successful return here means the calls completed. Inspect the masks as well: effective, permitted, and inheritable must all be zero. The ambient-clear operation is separately checked for success.

Build and compare two starting contexts:

```bash
cc -std=c11 -Wall -Wextra -O2 clear-current.c -o clear-current
./clear-current
unshare --user --map-root-user ./clear-current
```

`cc` builds your current source. The direct invocation begins with the ordinary user's usually empty current sets. The second starts with namespace-local capabilities, then clears them inside the same process. Both should report three zero masks and return 0. No parent-shell capabilities are modified.

For an intentional failure, open `nano clear-current.c`, temporarily remove the entire `SYS_capset` error-check block, save with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. Recompile and repeat the **namespace** invocation. The masks are now nonzero even though the program may return 0. Restore the block, recompile, and verify zero again. This is why testing only an already-unprivileged input can miss a control that does nothing.

This program does not execute another file. Exec can recalculate capabilities, especially for UID 0; a current-state observation is not automatically a post-exec guarantee. Lesson 03.03 adds the restriction on privilege gain across exec. The independent lab preserves the ordinary invoking UID rather than manufacturing root.

## Capability caveats

- Clearing current sets does not close descriptors opened while capabilities were present.
- Dropping the bounding set is a one-way restriction for the process tree, but executable attributes and namespace context still need analysis.
- Supplementary groups are a separate authority channel.
- A zero capability mask does not restrict ordinary permissions granted by UID, GID, ACLs, or open resources.

## Troubleshooting and checkpoint

- If `setpriv` is missing, install util-linux in the disposable VM.
- If an option spelling differs, check the VM's util-linux version rather than silently omitting the property.
- If a transition fails, capture stderr and current sets before changing the exercise.
- You should be able to state which set is used for current checks and which set caps future acquisition across exec.

Repeat the complete Exercise 2 after the partial Exercise 3 and compare every field. Then verify the C bridge's repaired namespace case. These are separate checkpoints for the utility-based transition and the in-process C operation.

To discard student edits, return with `cd ../..` and run `./lab-reset 03.02`. A new child process gets its own starting credentials; do not try to restore a dropped bounding set within the same process.

## Source truth

See [capabilities(7)](https://man7.org/linux/man-pages/man7/capabilities.7.html), [capget/capset(2)](https://man7.org/linux/man-pages/man2/capget.2.html), and [PR_CAP_AMBIENT_CLEAR_ALL(2)](https://man7.org/linux/man-pages/man2/PR_CAP_AMBIENT_CLEAR_ALL.2const.html). `man setpriv` documents the installed utility's flags. Current-state reduction, exec-time restrictions, and supplementary-group changes are different mechanisms.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-03-privilege/lesson-03/README.md format=markdown -->
# 03.03 - Make privilege non-gainable

## Goals

- Set the one-way `no_new_privs` bit before exec.
- Observe that bit in the executed child and a grandchild.
- Understand why ordering around exec is a security property.
- Distinguish non-gainability from removal of existing authority.

## Exercise 1 - Build the launcher

Complete 03.01 and 03.02 first. A program can begin with little privilege but execute a file whose attributes would normally grant more. `no_new_privs` is a one-way promise enforced by the kernel: an exec transition must not grant privilege that was unavailable before that transition. It does not remove authority the process already has. Here we will observe the bit itself, not install a setuid program to demonstrate privilege gain.

From the course root:

```bash
./lab-start 03.03
cd .student/03.03
pwd
ls -l nnp-launch.c
cat nnp-launch.c
grep '^NoNewPrivs:' /proc/self/status
```

The first four commands prepare and locate the editable C source. `cat` opens its contents for reading without editing. The final command records your inherited baseline. If it already reports 1, the deliberate ordering error later cannot make it 0: the bit is sticky. Do not weaken the VM or try to unset it to force an expected screenshot.

Complete source:

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <sys/prctl.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s COMMAND [ARG ...]\n", argv[0]);
        return 2;
    }
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
        perror("prctl(PR_SET_NO_NEW_PRIVS)");
        return 1;
    }
    execvp(argv[1], &argv[1]);
    perror("execvp");
    return 1;
}
```

## Source, line by line

- `_GNU_SOURCE` requests GNU/Linux declarations before headers are included.
- `<stdio.h>` declares diagnostics; `<sys/prctl.h>` declares `prctl` and its operation constants; `<unistd.h>` declares `execvp`.
- `argc < 2` rejects a missing child command.
- The usage message describes the preserved `COMMAND [ARG ...]` interface.
- `prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)` asks the kernel to set the calling thread's one-way bit. The remaining zero arguments are unused for this operation.
- A nonzero return indicates failure, which must stop execution of untrusted code.
- `execvp(argv[1], &argv[1])` searches `PATH`, uses the requested command, and passes the command plus all remaining arguments as the new `argv`.
- `&argv[1]` points into the original pointer array instead of rebuilding it.
- The final diagnostic runs only when exec fails.

Build and observe:

```bash
sed -n '1,220p' nnp-launch.c
cc -std=c11 -Wall -Wextra -O2 nnp-launch.c -o nnp-launch
./nnp-launch sh -c 'grep -E "^(NoNewPrivs|CapEff):" /proc/self/status'
```

## What each line does

- `sed` displays the full small launcher before execution.
- The compile line selects C11, warnings, normal optimization, and the output name.
- Every token after `./nnp-launch` becomes the child command and arguments.
- `sh -c` executes the quoted observation after the launcher sets policy.
- The anchored expression selects only `NoNewPrivs` and `CapEff`.

Expected:

```text
NoNewPrivs:  1
CapEff:      0000000000000000
```

`NoNewPrivs: 1` is the required property. A zero effective set is an additional observation, not proof that every authority channel is empty.

## Exercise 2 - Make the ordering mistake

Open `nano nnp-launch.c`. Move the **entire** `if (prctl(...) != 0) { ... }` block to immediately after the `execvp` call, keeping its failure handling together. Save with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. Run `cat nnp-launch.c` to inspect the saved order, then repeat the compile and observation commands from Exercise 1.

- A successful exec replaces the launcher, so code after it is unreachable on the success path.
- The executed child therefore observes the old `NoNewPrivs` value, normally 0.
- Restore the complete block before exec, save, recompile, and rerun. The repaired child must report 1.

Security controls governing a transition must be established before that transition. Source presence is not enough; control-flow ordering is part of the property.

## Exercise 3 - Verify inheritance in a descendant

```bash
./nnp-launch sh -c 'sh -c "grep ^NoNewPrivs: /proc/self/status"'
```

## What each part does

- The launcher sets the bit and executes the first shell.
- The outer single quotes protect the inner command from the invoking shell.
- The first child shell launches another shell.
- The inner shell reads its own procfs status.
- Seeing 1 proves inheritance across more than one exec transition.

`no_new_privs` cannot be unset and is inherited across fork and exec. It prevents privilege gain from exec mechanisms such as set-user-ID and file capabilities. It does not close descriptors, scrub the environment, empty current capability sets, isolate files, restrict the network, or filter syscalls.

## Troubleshooting and checkpoint

- If `prctl` is undeclared, verify Linux headers and `_GNU_SOURCE` placement.
- If the child reports 0, inspect control-flow ordering before changing the probe.
- If the command does not launch, distinguish `prctl` failure from `execvp` failure using stderr.
- You should be able to explain both what `no_new_privs` guarantees and what it deliberately does not guarantee.

For the checkpoint, compare the repaired child and grandchild, then name two inherited authority channels this bit does not remove. If your initial baseline was already 1, say explicitly that the negative case was masked by an inherited restriction; do not claim you observed a 0-to-1 transition.

Reset only your lesson workspace from the course root: `cd ../..` then `./lab-reset 03.03`. The child set its own bit; the parent shell was not changed.

## Source truth

The kernel's [no_new_privs documentation](https://docs.kernel.org/userspace-api/no_new_privs.html) describes inheritance, irreversibility, and limits. [execve(2)](https://man7.org/linux/man-pages/man2/execve.2.html) explains why successful execution does not return to the old program.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-03-privilege/lab/README.md format=markdown -->
# Module 03 independent lab - Privilege floor

Implement `secure-launch.c`, a launcher that establishes a non-gainable, capability-empty privilege state before executing an arbitrary command.

## Preparation and planning

Complete 03.01-03.03 first. Map the contract to the earlier practice: read identity and all sets in 03.01, clear current sets in C in 03.02, and establish the pre-exec one-way bit in 03.03. The lab combines those pieces without giving you their final arrangement.

The ordinary-user grader typically begins with empty current capability sets. A pass on that input alone is not evidence that a missing clearing operation would handle a more privileged input. Use the namespace-local contrast practiced in 03.02 to understand that limitation; do not change the lab to run as VM root. The contract preserves the invoking account and does not require an empty bounding set or altered supplementary groups.

From the course root:

```bash
./lab-start module-03
cd .student/03.lab
pwd
ls -l secure-launch.c
cat secure-launch.c
nano secure-launch.c
```

`lab-start` creates your editable lab copy. The next three commands enter it and confirm the source name; `cat` reads it, and `nano` opens it for editing. Save with `Ctrl-O`, `Enter`, then leave with `Ctrl-X`. Work only in this student copy. The canonical starter is deliberately incomplete:

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s COMMAND [ARG ...]\n", argv[0]);
        return 2;
    }

    /* Intentional starter flaw: no privilege floor is established. */
    execvp(argv[1], &argv[1]);
    perror("execvp");
    return 1;
}
```

The feature-test macro appears before headers. `stdio.h` supplies diagnostics; `unistd.h` supplies `execvp`. `argc` counts arguments, including the launcher name. The usage block rejects a missing child command. `argv[1]` names that command, while `&argv[1]` forwards its complete argument vector. Successful `execvp` never returns; `perror` and the final nonzero return handle failure. The starter preserves this interface but omits the stated security controls.

## Contract

The grader compiles the file with C11 and invokes:

```text
./secure-launch COMMAND [ARG ...]
```

The executed command must observe:

- `NoNewPrivs: 1`;
- empty effective, permitted, inheritable, and ambient capability sets;
- the same real and effective UID as the ordinary user who invoked the launcher;
- normal command arguments, stdout/stderr, and exit behavior.

The lab must be run as an ordinary user in the disposable VM. Do not add setuid bits or file capabilities. Do not call an external shell to transform the command string.

All required interfaces were practiced in this module. The grader deliberately avoids line-level advice.

```bash
cc -std=c11 -Wall -Wextra -O2 secure-launch.c -o secure-launch
./secure-launch sh -c 'grep -E "^(Uid|CapInh|CapPrm|CapEff|CapAmb|NoNewPrivs):" /proc/self/status'
../../lab-grade module-03
```

### Test commands, line by line

- `cc` builds your C11 launcher with warnings and normal optimization.
- `./secure-launch sh -c 'grep ...'` uses the required arbitrary-command interface and observes the executed child's real state from procfs.
- The anchored regular expression selects only identity, capability, and no-new-privileges fields.
- `../../lab-grade module-03` compiles a fresh evaluation binary and runs a separate probe.
- The starter's `execvp(argv[1], &argv[1])` correctly forwards the command and arguments but intentionally establishes no privilege floor. The exact repair remains independent work.

## Interpret your result and replay

Run the starter once before editing and record which security properties fail. A compile error is not an observed security denial, and a missing child is not successful containment. After your repair, use both a harmless successful command and a deliberately nonexistent absolute command; the latter must produce a nonzero launcher status.

For the practice grader, read each failed property and revisit its lesson before changing code. Do not alter the grader, canonical files, or generated fixture to force a pass. Passing establishes only the tested contract, not a production-ready sandbox.

From this workspace, `cd ../..` returns to the course root. `./lab-reset module-03` discards this module's student work and generated fixtures after confirmation; copy any notes you want to retain first. Then `./lab-start module-03` creates a fresh randomized attempt. No saved implementation is supplied by this manual.
<!-- /source -->

<!-- PAGEBREAK -->

# Integrated understanding

## How the first three modules compose

A minimally disciplined local launcher now has several separate responsibilities:

```text
parent process
  -> select arguments without accidental shell parsing
  -> construct an allowlisted environment
  -> close or mark unwanted descriptors close-on-exec
  -> create and configure namespace views
  -> reduce groups and capability channels
  -> set no_new_privs
  -> exec the workload
  -> verify the workload's effective state externally
```

Ordering matters. A descriptor opened before confinement can bypass later path restrictions. A `prctl` after exec never runs on success. A PID namespace paired with the old procfs gives a contradictory view. A copied environment preserves unknown parent authority.

No single observation proves complete containment. Instead, define properties and collect evidence for each:

- **Execution:** the intended binary and arguments run.
- **Environment:** disallowed keys are absent and required keys remain.
- **Descriptors:** unintended open objects do not survive exec.
- **Namespaces:** handles differ where required and resource views agree.
- **Credentials:** IDs, groups, and all capability sets match the declared floor.
- **Privilege gain:** `NoNewPrivs` is 1 in descendants.
- **Host preservation:** parent hostname, mounts, and process view remain unchanged.

## A disciplined failure-reading loop

When a grader reports a failed property:

- Restate the property without guessing at a line-level fix.
- Reproduce it with the smallest harmless local probe.
- Observe the executed child, not just the launcher's source.
- Separate setup failure from workload failure using stderr and exit status.
- Change one authority channel at a time.
- Rerun the local probe, then the randomized grader.
- Reset and replay to ensure the fix was not tied to one fixture.

# Completion, replay, and reference

## Replay the completed sequence

```bash
./lab-status
./lab-reset --all --dry-run
./lab-reset --all --yes
./lab-start 01.01
```

### What each line does

- Status records the end state before reset.
- The dry run validates every reset target and resource without mutation.
- The confirmed all-scope reset removes disposable student work and generated fixtures while retaining attempt/pass metadata.
- Starting 01.01 creates a fresh attempt with no retained solution.

If the commands feel familiar but the answer is not sitting in front of you, replayability is working.

## Quick command reference

- `ps -o ... -p PID` selects explicit process columns for named PIDs.
- `readlink /proc/PID/ns/TYPE` records namespace membership.
- `grep -E` uses extended regular expressions; `grep -F` matches literal text.
- `strace -f -e trace=LIST` follows descendants and restricts syscall display.
- `unshare` creates specified namespaces for a command.
- `setpriv` changes privilege attributes before executing a command.
- `capsh --decode=MASK` translates a hexadecimal capability mask.
- `getcap -r PATH` finds file capability attributes recursively.
- `fcntl(fd, F_GETFD)` reads descriptor flags.
- `prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)` sets the one-way no-new-privileges bit.

## Glossary

- **Ambient authority:** authority available to a program without an explicit request for each use, such as inherited environment values or descriptors.
- **Argument vector (`argv`):** the ordered, NUL-terminated array of strings supplied to a new program.
- **Capability:** a named Linux privilege bit evaluated in a namespace context.
- **Close-on-exec:** a descriptor flag instructing the kernel to close that descriptor during successful exec.
- **Environment (`envp`):** an array of `KEY=VALUE` strings supplied to an executed program.
- **Exec:** a transition replacing the current process image while preserving defined process state.
- **File descriptor:** a process-local integer reference to an open kernel object.
- **Namespace:** a kernel mechanism giving processes a scoped view of one resource class.
- **Namespace handle:** a procfs link target such as `uts:[4026531838]` identifying a namespace object.
- **PID 1:** the first process in a PID namespace, with special signal and child-reaping responsibilities.
- **procfs:** the `/proc` virtual filesystem exposing kernel-generated process and system views.
- **Property-based grading:** checking externally observable security outcomes rather than matching one source implementation.
- **Syscall:** a controlled transition from user space into the kernel to request an operation.
- **`no_new_privs`:** a sticky process attribute preventing exec from granting new privilege.
- **User namespace mapping:** the translation between IDs visible inside a user namespace and IDs in its parent.

## What comes next

Modules 04-12 continue this course with guided examples, exact commands, line explanations, deliberate failures, randomized fixtures, independent labs, property-based graders, safe reset, and replay. Their chapters follow in the complete manual.

The path moves from a minimal tool-using agent through filesystem and syscall confinement, resource controls, network mediation, credential brokering, a composed runtime, break/fix analysis, bounded evidence interpretation, and a cold batch-runtime capstone. Use the cumulative checkpoints in `docs/LEARNING_PATH.md` before advancing.

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

<!-- source: course/module-05-filesystem-landlock/README.md format=markdown -->
# Module 05 - Confine filesystem access

Turn a directory name into an enforced filesystem boundary. First break lexical path checks with traversal and symlinks. Then anchor lookup to a directory descriptor with `openat2(2)` and add Landlock so an entire child process is restricted. Finally confront Landlock's important pre-opened-file-descriptor limit.

Play in order: `05.01`, `05.02`, `05.03`, then `module-05`.

Outcomes:

- distinguish a pathname string from the kernel object reached during lookup;
- reproduce traversal, prefix-collision, and symlink escapes against a naive broker;
- use `openat2` with `RESOLVE_BENEATH`, `RESOLVE_NO_MAGICLINKS`, and `RESOLVE_NO_SYMLINKS` for descriptor-relative lookup;
- query the Landlock ABI, select supported rights, add a path-beneath rule, set `no_new_privs`, and restrict a child before `exec`;
- demonstrate that Landlock does not revoke already-open descriptors and remove that inherited authority before launch.

Prerequisites: Modules 01-04, Linux, a C compiler, Linux UAPI headers containing `openat2.h` and `landlock.h`, and a kernel with `openat2` and Landlock. The lessons require no root privilege, mount, network access, or host policy change.

Cross-layer boundary: `openat2` protects individual brokered lookups. Landlock restricts future filesystem operations by the launched process. Neither one closes an already-open descriptor; descriptor hygiene from Module 01 remains necessary.

## Learning route and limits

Prerequisites: Modules 01-04. Continue as your ordinary account inside the disposable Linux VM. The guided lessons introduce their new syntax and interfaces before the independent lab combines them.

05.01 distinguishes path spelling, component ancestry, and lookup results. 05.02 practices descriptor-relative reads and writes. 05.03 restricts a launched child and revisits authority already held in descriptors.

Keep two questions separate: did the broker resolve this request safely, and is the entire child restricted when it opens files itself? The first is an openat2 question; the second is a Landlock question. Record the running ABI and build headers rather than relying on the distro name.

Before moving on, demonstrate both useful allowed work and the intended restriction, and explain the difference in your own words. A failed compiler command or missing input is not a security success. Use the independent lab's practice feedback to revisit a specific lesson; passing checks does not replace understanding or make the combined program production-ready.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-05-filesystem-landlock/lesson-01/README.md format=markdown -->
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
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-05-filesystem-landlock/lesson-02/README.md format=markdown -->
# 05.02 - Make lookup descriptor-relative with `openat2`

## Goal

Replace check-then-open pathname logic with one kernel operation anchored to an already-open directory. Require resolution to remain beneath that descriptor and reject symlinks.

## Concepts and preparation

Complete 05.01 and recall descriptor authority from 01.03. The previous checker resolved a path, decided it was acceptable, and later opened it. Those are separate operations. Here the broker gives the kernel both the root descriptor and resolution constraints in the **same open request**. There is no separate approved pathname to reopen.

`openat2` is a Linux syscall, not a shell command. A C structure carries its options. Fields omitted from the designated initializer are zero-initialized; that matters because the kernel expects unused fields to be zero. This policy constrains lookup, not future edits to the contents of an allowed file, and not arbitrary opens made elsewhere in the process.

From the course root in the disposable VM:

```bash
./lab-start 05.02
cd .student/05.02
pwd
ls -l safe_open.c
cat safe_open.c
```

`lab-start` prepares the student copy. The next commands enter and inspect it; each `cat` reads a supplied source before execution. Missing files usually mean the wrong working directory or lesson number. Edit only these student copies with `nano FILENAME`, save with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. Recompile after every C edit. An old binary does not automatically track a changed source.

## Exercise 1 - Compile the brokered open

Complete source of `safe_open.c`:

```c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/openat2.h>
#include <stdio.h>
#include <string.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s ROOT RELATIVE_PATH\n", argv[0]);
        return 2;
    }
    int root_fd = open(argv[1], O_PATH | O_DIRECTORY | O_CLOEXEC);
    if (root_fd == -1) {
        perror("open root");
        return 1;
    }
    struct open_how how = {
        .flags = O_RDONLY | O_CLOEXEC,
        .resolve = RESOLVE_BENEATH | RESOLVE_NO_MAGICLINKS | RESOLVE_NO_SYMLINKS,
    };
    int fd = syscall(SYS_openat2, root_fd, argv[2], &how, sizeof(how));
    if (fd == -1) {
        fprintf(stderr, "DENIED: %s\n", strerror(errno));
        close(root_fd);
        return 1;
    }
    char buffer[4096];
    ssize_t count;
    while ((count = read(fd, buffer, sizeof(buffer))) > 0) {
        if (write(STDOUT_FILENO, buffer, (size_t)count) != count) {
            perror("write");
            close(fd);
            close(root_fd);
            return 1;
        }
    }
    if (count == -1)
        perror("read");
    close(fd);
    close(root_fd);
    return count == -1;
}
```

### Source, line by line

- `_GNU_SOURCE`, `linux/openat2.h`, and `sys/syscall.h` expose the Linux-specific syscall interface and `open_how` structure.
- The program accepts exactly a root and one relative request. A different shape fails with usage status 2.
- `open(..., O_PATH | O_DIRECTORY | O_CLOEXEC)` obtains a reference to the root directory without opening it for file data. `O_CLOEXEC` prevents accidental inheritance.
- `open_how.flags` requests a read-only result descriptor, also close-on-exec.
- `RESOLVE_BENEATH` rejects resolution that escapes above the supplied directory descriptor, including absolute paths.
- `RESOLVE_NO_MAGICLINKS` rejects procfs-style magic links; `RESOLVE_NO_SYMLINKS` rejects every symbolic link in the request.
- `syscall(SYS_openat2, root_fd, ...)` makes the resolution policy and open one atomic kernel request. The root descriptor, not the process working directory, is the anchor.
- A failure is printed as `DENIED` with the kernel reason and returns nonzero.
- The read/write loop copies observed bytes to standard output. It checks both input and output errors.
- Both descriptors are closed on every explicit completion path.

The leading `&` passes a structure's address; `sizeof(how)` tells the kernel how many bytes of that structure are supplied. The `|` operators combine independent flag bits. `ssize_t` can represent a byte count or the negative error value; `size_t` is an unsigned size, so the code casts only after a positive read. The assignment in the `while` condition stores the count before testing it. This teaching copy loop fails on a short write rather than retrying it; it is not a complete general-purpose I/O library.

Build it:

```bash
cc -std=c11 -Wall -Wextra -Werror -O2 safe_open.c -o safe-open
```

### Line by line

- `-std=c11` selects the language baseline; the Linux interfaces remain explicitly requested by `_GNU_SOURCE`.
- `-Wall -Wextra -Werror` turns common warnings into build failures rather than accepting ambiguous code.
- `-O2` produces a normal optimized binary; it is not a security boundary.
- `-o safe-open` names only the lesson-local output.

## Exercise 2 - Verify allowed and denied lookups

```bash
rm -rf demo
mkdir -p demo/allowed demo/protected
printf 'allowed\n' > demo/allowed/note.txt
printf 'protected\n' > demo/protected/secret.txt
ln -s ../protected/secret.txt demo/allowed/link.txt
./safe-open demo/allowed note.txt
./safe-open demo/allowed ../protected/secret.txt || echo 'traversal denied'
./safe-open demo/allowed link.txt || echo 'symlink denied'
```

### Line by line

- The setup uses only synthetic paths in this workspace.
- The plain relative lookup prints `allowed`.
- The `..` request fails because `RESOLVE_BENEATH` will not cross above `root_fd`.
- The link request fails because `RESOLVE_NO_SYMLINKS` rejects it before following the target.
- Expected denial errors commonly report `Invalid cross-device link` for escape and `Too many levels of symbolic links` for a forbidden symlink. Match success/failure, not locale-dependent wording.

## Exercise 3 - Remove the boundary and repair it

Create a deliberately weakened copy that retains only magic-link denial:

```bash
sed 's/RESOLVE_BENEATH | RESOLVE_NO_MAGICLINKS | RESOLVE_NO_SYMLINKS/RESOLVE_NO_MAGICLINKS/' safe_open.c > unsafe_open.c
cc -std=c11 -Wall -Wextra -Werror -O2 unsafe_open.c -o unsafe-open
./unsafe-open demo/allowed ../protected/secret.txt
./unsafe-open demo/allowed link.txt
```

### Line by line

- `sed` writes a new lesson-local source; it does not alter the repaired canonical example.
- Without `RESOLVE_BENEATH`, `..` can leave the anchor. Without `RESOLVE_NO_SYMLINKS`, an ordinary symlink can be followed.
- Expected: both unsafe commands print `protected`.
- Delete `unsafe_open.c` and `unsafe-open`, then rerun the repaired denial commands. The repair is the policy in the `openat2` operation itself, not a prior string check.

`openat2` constrains only lookups made through this broker. A child can still call ordinary `open` itself. Lesson 05.03 adds process-wide future-access restrictions.

## Exercise 4 - Practice a descriptor-relative write

The independent lab needs both reads and writes. Practice the creation flags in a smaller fixed-content program, not a combined lab solution:

```bash
ls -l safe_write.c
cat safe_write.c
```

`ls` confirms the source in this workspace; `cat` displays it before compiling.

```c
#define _GNU_SOURCE
#include <fcntl.h>
#include <linux/openat2.h>
#include <stdio.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s ROOT RELATIVE_PATH\n", argv[0]);
        return 2;
    }
    int root_fd = open(argv[1], O_PATH | O_DIRECTORY | O_CLOEXEC);
    if (root_fd == -1) {
        perror("open root");
        return 1;
    }
    struct open_how how = {
        .flags = O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC,
        .mode = 0600,
        .resolve = RESOLVE_BENEATH | RESOLVE_NO_MAGICLINKS | RESOLVE_NO_SYMLINKS,
    };
    int fd = syscall(SYS_openat2, root_fd, argv[2], &how, sizeof(how));
    if (fd == -1) {
        perror("openat2");
        close(root_fd);
        return 1;
    }
    close(root_fd);
    const char content[] = "created through an anchored descriptor\n";
    int failed = write(fd, content, sizeof(content) - 1) != (ssize_t)(sizeof(content) - 1);
    if (failed)
        fprintf(stderr, "write did not complete\n");
    if (close(fd) == -1) {
        perror("close output");
        failed = 1;
    }
    return failed;
}
```

### Source, line by line

- The headers and argument guard serve the same roles as in `safe_open.c`.
- The root is opened as a directory reference and marked close-on-exec. An error stops the operation.
- `O_WRONLY` requests writing; `O_CREAT` permits a new file; `O_TRUNC` replaces existing contents. These are different choices from append mode.
- `mode = 0600` requests owner read/write permissions for a newly created file, further restricted by the process umask. The leading zero denotes an octal permission constant. `mode` must be zero when no creation flag is used.
- The same resolution flags apply to creation, so a write does not get a weaker lookup rule than a read.
- The fixed payload includes a newline. `sizeof(content) - 1` excludes the C string's terminating zero byte.
- A short or failed write is reported as failure. The output descriptor is closed, and a close error also fails the operation; this still does not promise durable storage without an explicit synchronization policy.
- All successful setup paths close the root descriptor. Returning nonzero stops the caller from treating a failed write as a valid result.

```bash
cc -std=c11 -Wall -Wextra -Werror -O2 safe_write.c -o safe-write
./safe-write demo/allowed created.txt
cat demo/allowed/created.txt
printf 'old contents deliberately longer than the replacement payload to expose missing truncation\n' > demo/allowed/created.txt
./safe-write demo/allowed created.txt
test "$(cat demo/allowed/created.txt)" = 'created through an anchored descriptor'
```

The compile command builds the new program. The first write creates a file and the following `cat` observes it. The second run replaces longer old content; the final equality check catches a missing truncation flag that would leave trailing bytes. The payload and destination are local synthetic data. In the independent lab, adapt the mechanism to the specified content argument yourself.

## Checkpoint and troubleshooting

```bash
test "$(./safe-open demo/allowed note.txt)" = allowed
! ./safe-open demo/allowed ../protected/secret.txt
! ./safe-open demo/allowed link.txt
```

- If `linux/openat2.h` is absent, install the distribution's normal Linux UAPI development headers; do not copy an untrusted header into the lesson.
- `ENOSYS` means the running kernel lacks `openat2`; record the exact kernel and use a supported disposable VM.
- If the safe link succeeds, confirm the repaired binary was rebuilt from `safe_open.c`.
- Checkpoint: point to the directory descriptor, the kernel resolution flags, and the single operation that joins authorization to use.

## Replay and source truth

The demo contains only lesson-created synthetic files. Do not substitute personal directories or real credentials. From this workspace, `cd ../..` then `./lab-reset 05.02` discards this lesson's edits and fixtures after confirmation. No host mount, filesystem permission, or global security setting needs changing.

[openat2(2)](https://man7.org/linux/man-pages/man2/openat2.2.html) defines the structure, resolution flags, and error cases; it was introduced in Linux 5.6. The lesson uses flags available on both course baselines, not newer flags merely present in current online documentation.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-05-filesystem-landlock/lesson-03/README.md format=markdown -->
# 05.03 - Restrict a child with Landlock

## Goal

Apply an unprivileged Landlock ruleset before `exec`, then prove both its protection and its pre-opened-descriptor limit. Compose Landlock with descriptor hygiene rather than mistaking either control for the other.

## Concepts and preparation

Complete 05.02 and recall `no_new_privs` from 03.03. A cooperative broker can use a safe open operation, but an arbitrary child can issue its own file operations. **Landlock** adds kernel-enforced restrictions to the calling thread and its future descendants. An unprivileged program can reduce its access; it cannot use a Landlock rule to override existing permissions.

A **ruleset** declares the categories of access it handles. A **rule** grants selected handled accesses beneath a directory. A handled access with no applicable grant is denied; an unhandled category is generally outside that policy. The **ABI version** is the kernel interface generation, not the distribution version. New headers do not make an older running kernel support new rights.

We intentionally use a static, tiny child so its program and runtime code fit in one allowed tree. This keeps dynamic-loader permissions out of the first example. It does not mean static linking itself is a sandbox. Predict whether a file already opened before the restriction will lose its read authority.

From the course root in the disposable VM:

```bash
./lab-start 05.03
cd .student/05.03
pwd
ls -l fd_probe.c landlock_launch.c pass_fd.py
cat fd_probe.c
cat landlock_launch.c
cat pass_fd.py
```

`lab-start` prepares the student copy. The next commands enter and inspect it; each `cat` reads a supplied source before execution. Missing files usually mean the wrong working directory or lesson number. Edit only these student copies with `nano FILENAME`, save with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. Recompile after every C edit. An old binary does not automatically track a changed source.

## Exercise 1 - Build a static observation probe

`fd_probe.c` opens a named path or reads an existing descriptor. Its complete source is:

```c
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s path PATH | fd NUMBER\n", argv[0]);
        return 2;
    }
    int fd = strcmp(argv[1], "path") == 0 ? open(argv[2], O_RDONLY) : atoi(argv[2]);
    char buffer[256];
    ssize_t count = read(fd, buffer, sizeof(buffer));
    if (count < 0) {
        fprintf(stderr, "DENIED: %s\n", strerror(errno));
        return 1;
    }
    return write(STDOUT_FILENO, buffer, (size_t)count) == count ? 0 : 1;
}
```

### Source, line by line

- The probe accepts exactly a mode and operand.
- `path` performs a new `open`; `fd` reuses an integer descriptor inherited across `exec`.
- `read` is the common observation. On failure the probe reports `DENIED` and returns nonzero.
- The final `write` makes successful access independently visible.

Compile it statically inside the future allowed tree so its executable and runtime code need no outside filesystem access:

```bash
rm -rf demo
mkdir -p demo/allowed demo/protected
printf 'allowed\n' > demo/allowed/note.txt
printf 'synthetic-secret\n' > demo/protected/secret.txt
cc -std=c11 -Wall -Wextra -Werror -O2 -static fd_probe.c -o demo/allowed/fd-probe
```

### Line by line

- The files are synthetic and local to the lesson.
- `-static` puts the probe's required runtime code in its binary. This keeps the policy example focused on one allowed tree rather than adding read/execute rules for dynamic-loader paths.
- A static build failure usually means the VM lacks its distribution C development files; install the documented build toolchain rather than broadening the policy.

## Exercise 2 - Apply a version-aware Landlock policy

Complete source of `landlock_launch.c`:

```c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/close_range.h>
#include <linux/landlock.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <unistd.h>

static int create_ruleset(const struct landlock_ruleset_attr *attr, size_t size, __u32 flags) {
    return syscall(SYS_landlock_create_ruleset, attr, size, flags);
}

static int add_rule(int ruleset_fd, const struct landlock_path_beneath_attr *attr) {
    return syscall(SYS_landlock_add_rule, ruleset_fd, LANDLOCK_RULE_PATH_BENEATH, attr, 0);
}

static int restrict_self(int ruleset_fd) {
    return syscall(SYS_landlock_restrict_self, ruleset_fd, 0);
}

static __u64 supported_rights(int abi) {
    __u64 rights = LANDLOCK_ACCESS_FS_EXECUTE | LANDLOCK_ACCESS_FS_WRITE_FILE |
                   LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_READ_DIR |
                   LANDLOCK_ACCESS_FS_REMOVE_DIR | LANDLOCK_ACCESS_FS_REMOVE_FILE |
                   LANDLOCK_ACCESS_FS_MAKE_CHAR | LANDLOCK_ACCESS_FS_MAKE_DIR |
                   LANDLOCK_ACCESS_FS_MAKE_REG | LANDLOCK_ACCESS_FS_MAKE_SOCK |
                   LANDLOCK_ACCESS_FS_MAKE_FIFO | LANDLOCK_ACCESS_FS_MAKE_BLOCK |
                   LANDLOCK_ACCESS_FS_MAKE_SYM;
    if (abi >= 2)
        rights |= LANDLOCK_ACCESS_FS_REFER;
    if (abi >= 3)
        rights |= LANDLOCK_ACCESS_FS_TRUNCATE;
#ifdef LANDLOCK_ACCESS_FS_IOCTL_DEV
    if (abi >= 5)
        rights |= LANDLOCK_ACCESS_FS_IOCTL_DEV;
#endif
#ifdef LANDLOCK_ACCESS_FS_RESOLVE_UNIX
    if (abi >= 9)
        rights |= LANDLOCK_ACCESS_FS_RESOLVE_UNIX;
#endif
    return rights;
}

static int close_inherited(void) {
    /* Both course baselines support this operation. Do not weaken the
       descriptor guarantee with a fallback bounded by a mutable soft limit. */
    return syscall(SYS_close_range, 3U, ~0U, CLOSE_RANGE_CLOEXEC);
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: %s ALLOWED_ROOT COMMAND [ARG...]\n", argv[0]);
        return 2;
    }
    int abi = create_ruleset(NULL, 0, LANDLOCK_CREATE_RULESET_VERSION);
    if (abi < 1) {
        perror("Landlock ABI");
        return 1;
    }
    fprintf(stderr, "Landlock ABI %d\n", abi);
    __u64 rights = supported_rights(abi);
    struct landlock_ruleset_attr ruleset = {.handled_access_fs = rights};
    int ruleset_fd = create_ruleset(&ruleset, sizeof(ruleset), 0);
    int root_fd = open(argv[1], O_PATH | O_CLOEXEC);
    if (ruleset_fd == -1 || root_fd == -1) {
        perror("create policy");
        return 1;
    }
    struct landlock_path_beneath_attr rule = {
        .allowed_access = rights,
        .parent_fd = root_fd,
    };
    if (add_rule(ruleset_fd, &rule) == -1) {
        perror("landlock_add_rule");
        return 1;
    }
    close(root_fd);
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) == -1 || restrict_self(ruleset_fd) == -1) {
        perror("restrict self");
        return 1;
    }
    close(ruleset_fd);
    if (close_inherited() == -1) {
        perror("close inherited descriptors");
        return 1;
    }
    execv(argv[2], &argv[2]);
    perror("execv");
    return 1;
}
```

### Source, line by line

- The three small syscall wrappers keep the argument ordering visible and return raw success or failure to the caller.
- `supported_rights` builds the ABI-1 set first, then adds rights introduced by ABI 2, 3, 5, and 9 only when both the build headers and the running kernel support them. The preprocessor guards keep the source buildable with older distribution headers.
- `close_inherited` requires the kernel's range operation. `CLOSE_RANGE_CLOEXEC` preserves descriptors until `exec` but prevents the new program from inheriting them.
- Failure stops the launch, including an unsupported operation. The course baselines support this flag (introduced in Linux 5.11); there is no weaker fallback bounded by a process's mutable descriptor soft limit.
- `main` queries and prints the ABI before it creates policy. It never treats an unavailable Landlock interface as permission to continue.
- The ruleset declares which operations Landlock will handle; the path-beneath rule grants that same set only under `root_fd`.
- `PR_SET_NO_NEW_PRIVS` and `restrict_self` are joined by `||`: if either fails, `execv` is unreachable.
- The policy and root descriptors are closed before inherited descriptors are marked. Standard input, output, and error remain available.
- `execv(argv[2], &argv[2])` preserves the caller's structured argv. Returning from `execv` is always an error and is reported.

### Unhandled means allowed

### Read the policy structures without guessing

The `__u64` type is an unsigned 64-bit value used for the access mask. A `|` combines right bits; `|=` adds bits to an existing mask. `#ifdef` is a compile-time test for a header definition, whereas `if (abi >= ...)` is a runtime test. Both must agree before this binary requests a newer right.

`create_ruleset(NULL, 0, LANDLOCK_CREATE_RULESET_VERSION)` is a query: no policy structure is supplied. The next call passes an initialized `landlock_ruleset_attr` and its size to create a policy descriptor. The `landlock_path_beneath_attr` holds the rights granted under the already-open root. `&rule` passes its address to the add-rule operation.

The lesson grants **all handled rights under the allowed tree**, not read-only access. Those grants only remove Landlock's denial for that tree; normal permissions and other security modules can still deny access. Restricting this process does not change global SELinux policy. On Fedora, keep SELinux enforcing throughout.

The `||` condition short-circuits: if setting `no_new_privs` fails, the second call is not attempted and the error path returns. If installing Landlock fails, execution also stops. Closing the ruleset descriptor afterward releases the userspace handle, not the installed restriction. Like the no-new-privileges bit, the resulting access reduction is not something this child can casually undo.

The tiny observation probe's conditional expression selects either a new path open or an already-supplied integer descriptor. Its fixed 256-byte read is enough for the supplied short fixtures, not a general file-copy contract. Use exactly the documented modes; the probe is not a production input parser.

### Compare handled rights with the running ABI

Landlock restricts only the access rights listed in `handled_access_fs`. With the historical exception of `LANDLOCK_ACCESS_FS_REFER`, a filesystem right the running kernel supports but the ruleset does not handle stays allowed. A launcher that stops at ABI 3 therefore under-restricts on ABI 5, where `LANDLOCK_ACCESS_FS_IOCTL_DEV` can restrict device IOCTL operations, and on ABI 9, where `LANDLOCK_ACCESS_FS_RESOLVE_UNIX` can restrict pathname UNIX-socket resolution.

Version-aware code can handle only rights known to its source and build headers. The guarded ABI 5 and ABI 9 additions make this source enforce the complete filesystem-right set it knows when the headers expose those constants and the running kernel supports them. If newer headers introduce another filesystem right, this source and its stated guarantee must be reviewed again; runtime ABI detection cannot invent a constant absent at build time.

Checkpoint: print the ABI reported by the running kernel and compare it with the highest filesystem ABI explicitly handled by the source:

```bash
cc -std=c11 -Wall -Wextra -Werror -O2 landlock_launch.c -o landlock-launch
./landlock-launch demo/allowed /bin/true 2>&1 | head -1
grep -n 'abi >=' landlock_launch.c
```

- Compile first: a freshly prepared lesson has source files, not a prebuilt launcher.
- The next command relies on the launcher's diagnostic and may later deny `/bin/true` because that executable is outside the allowed tree; only its first line is the ABI observation. The pipeline's status is not a launch-success assertion.
- `grep` lists the explicit ABI gates in the source. A high runtime number is not by itself proof that every future right is handled.

Build it:

```bash
cc -std=c11 -Wall -Wextra -Werror -O2 landlock_launch.c -o landlock-launch
./landlock-launch "$PWD/demo/allowed" "$PWD/demo/allowed/fd-probe" path "$PWD/demo/allowed/note.txt"
./landlock-launch "$PWD/demo/allowed" "$PWD/demo/allowed/fd-probe" path "$PWD/demo/protected/secret.txt" || echo 'outside path denied'
```

### Line by line

- The compiler flags reject warnings and create the lesson-local launcher.
- Each launch first reports `Landlock ABI N` on standard error, where `N` depends on the running kernel.
- The first launch grants filesystem rights beneath `demo/allowed`; the static probe executes and prints `allowed`.
- The second launches the same child under the same policy but asks it to open a protected sibling. Expected: `DENIED` and the shell message.

The source performs these security-sensitive steps in order:

- `landlock_create_ruleset(..., LANDLOCK_CREATE_RULESET_VERSION)` queries the running kernel ABI. Failure is reported; the launcher never silently runs unconfined.
- `supported_rights` begins with ABI-1 filesystem rights and conditionally adds `REFER` for ABI 2+, `TRUNCATE` for ABI 3+, device `IOCTL` for ABI 5+, and pathname UNIX-socket resolution for ABI 9+ when the build headers define those rights.
- A ruleset handles those rights. A path-beneath rule grants them only under the already-open allowed-root descriptor.
- The root descriptor is closed after the rule is added.
- `PR_SET_NO_NEW_PRIVS` is set before `landlock_restrict_self`; unprivileged callers need this promise that `exec` cannot grant new privilege.
- Restriction occurs before `execv`, so it is inherited by the child. Errors stop the launch.
- `execv` uses the exact argument vector and an explicit executable path; there is no shell parser or `PATH` search.

This proves future path access is constrained. It does not prove existing descriptors were revoked.

## Exercise 3 - Reproduce and repair the pre-opened-FD bypass

`pass_fd.py` deliberately opens the protected file before launching:

```python
#!/usr/bin/env python3
import os
import subprocess
import sys


with open(sys.argv[1], "rb") as stream:
    run = subprocess.run(
        ["./landlock-launch", sys.argv[2], sys.argv[3], "fd", str(stream.fileno())],
        pass_fds=(stream.fileno(),),
        check=False,
    )
raise SystemExit(run.returncode)
```

### Source, line by line

- `open` creates authority to the protected object before Landlock is installed.
- `pass_fds` deliberately clears close-on-exec for that descriptor in the immediate child.
- The launcher receives the allowed root, exact probe path, `fd` mode, and descriptor number as distinct argv elements.
- The wrapper returns the observed child status.

The repaired launcher calls `close_inherited` after using its policy descriptors and before `execv`. `close_range(..., CLOSE_RANGE_CLOEXEC)` marks every descriptor from 3 upward close-on-exec. This single-threaded launcher creates no later descriptors before exec; it does not claim to solve concurrent descriptor creation in a multithreaded launcher.

Run the repaired result:

```bash
python3 pass_fd.py "$PWD/demo/protected/secret.txt" "$PWD/demo/allowed" "$PWD/demo/allowed/fd-probe" || echo 'inherited descriptor denied'
```

Expected: the probe reports a bad descriptor and the shell prints `inherited descriptor denied`.

Intentional failure: make a temporary copy without the `close_inherited()` call and its error block, then compile it while suppressing only the expected unused-helper warning:

```bash
sed '/if (close_inherited() == -1)/,+3d' landlock_launch.c > unsafe_launch.c
cc -std=c11 -Wall -Wextra -Wno-unused-function -O2 unsafe_launch.c -o unsafe-launch
```

- The addressed `sed` range removes the four-line call/error block from the temporary source only.
- `-Wno-unused-function` permits the deliberately orphaned helper; it does not suppress other warning classes.
- The executable name is inside `pass_fd.py`, not an argument to its command. Open your student copy with `nano pass_fd.py`, change only that executable string for the supplied synthetic comparison, save, and repeat the same Python invocation. Restore the original string immediately afterward. The protected fixture is not a real credential.
- Delete the temporary files, return to the shipped launcher, and confirm denial.

Landlock mediates new filesystem operations by path; reading an already-open file description is not a new path lookup.

## Checkpoint and troubleshooting

```bash
test "$(./landlock-launch "$PWD/demo/allowed" "$PWD/demo/allowed/fd-probe" path "$PWD/demo/allowed/note.txt")" = allowed
! ./landlock-launch "$PWD/demo/allowed" "$PWD/demo/allowed/fd-probe" path "$PWD/demo/protected/secret.txt"
! python3 pass_fd.py "$PWD/demo/protected/secret.txt" "$PWD/demo/allowed" "$PWD/demo/allowed/fd-probe"
```

- `Landlock ABI: Function not implemented` means the kernel lacks Landlock. Use the supported VM and record the skip; do not run the child unconfined.
- `Permission denied` on the allowed executable usually means the probe is outside the allowed tree or was not compiled successfully.
- A visible synthetic secret in the final command means inherited descriptors were not marked close-on-exec.
- Checkpoint: identify which assertion tests Landlock and which tests the independent descriptor-hygiene layer.

## Replay and source truth

The demo contains only lesson-created synthetic files. Do not substitute personal directories or real credentials. From this workspace, `cd ../..` then `./lab-reset 05.03` discards this lesson's edits and fixtures after confirmation. No host mount, filesystem permission, or global security setting needs changing.

The kernel's [Landlock userspace guide](https://cdn.kernel.org/doc/html/latest/userspace-api/landlock.html) documents handled rights, ABI additions, and inherited restrictions. [close_range(2)](https://man7.org/linux/man-pages/man2/close_range.2.html) documents the separate descriptor control. Record build headers and the running ABI; neither alone proves which rights this binary enforces.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-05-filesystem-landlock/lab/README.md format=markdown -->
# Module 05 independent lab - Filesystem guard

## Preparation and practiced skills

Complete 05.01-05.03 first. Map read lookup and creation/truncation to 05.02's two small C programs; map child restriction and inherited-descriptor handling to 05.03. 05.01 explains why replacing a character-prefix test with another string manipulation is not the whole answer.

The starter branches on `argv[1]`. Its `run` branch executes without policy. Its other branches concatenate root and request into a string, then use ordinary stream operations. `fread` and `fwrite` operate on streams; `snprintf` formats text and does not validate a resolved object. The starter's single read also has a fixed buffer limit. Preserve the interface, not these shortcuts.

The contract describes mechanisms as well as outcomes. A black-box pass cannot prove that a read used one descriptor-relative kernel operation, or that every future ABI right was handled. Review the source against that stated design as well as checking the grader's observed outcomes.

From the course root:

```bash
./lab-start module-05
cd .student/05.lab
pwd
ls -l fs_guard.c
cat fs_guard.c
nano fs_guard.c
```

The commands prepare your editable lab, enter and inspect it, then open the starter for reading and editing. Save in nano with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. Rebuild after each C edit using the compiler command below. Keep the canonical files and grader unchanged.

```c
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 4) {
        fprintf(stderr, "usage: %s read ROOT PATH | write ROOT PATH CONTENT | run ROOT COMMAND [ARG...]\n", argv[0]);
        return 2;
    }
    if (strcmp(argv[1], "run") == 0) {
        execv(argv[3], &argv[3]);
        perror("execv");
        return 1;
    }
    char path[4096];
    snprintf(path, sizeof(path), "%s/%s", argv[2], argv[3]);
    if (strcmp(argv[1], "read") == 0) {
        FILE *stream = fopen(path, "r");
        if (!stream) {
            perror("fopen");
            return 1;
        }
        char buffer[4096];
        size_t count = fread(buffer, 1, sizeof(buffer), stream);
        fwrite(buffer, 1, count, stdout);
        return ferror(stream) != 0;
    }
    if (strcmp(argv[1], "write") == 0 && argc == 5) {
        FILE *stream = fopen(path, "w");
        if (!stream) {
            perror("fopen");
            return 1;
        }
        fputs(argv[4], stream);
        return fclose(stream) == EOF;
    }
    fprintf(stderr, "unknown mode\n");
    return 2;
}
```

## Contract


Implement `fs_guard.c`. The grader builds one executable and invokes these interfaces:

```text
fs-guard read ALLOWED_ROOT RELATIVE_PATH
fs-guard write ALLOWED_ROOT RELATIVE_PATH CONTENT
fs-guard run ALLOWED_ROOT COMMAND [ARG...]
```

Required security properties:

- `read` prints an allowed regular file and `write` creates or truncates an allowed regular file with exact content;
- both operations resolve from an opened `ALLOWED_ROOT` descriptor in one kernel operation;
- absolute paths, `..` traversal, magic links, and every symlink are denied rather than normalized and reopened;
- `run` queries the Landlock ABI, handles every filesystem right known to its source and build headers that the detected ABI supports - including device IOCTL at ABI 5 and pathname UNIX-socket resolution at ABI 9 when those constants are available - grants the child filesystem access beneath `ALLOWED_ROOT`, sets `no_new_privs`, and restricts before `exec`;
- an executable inside the allowed tree still runs, while that child cannot newly open a protected sibling;
- inherited descriptors numbered 3 and above are closed on `exec`, preventing a pre-opened protected file from bypassing the pathname policy;
- malformed or unknown modes fail closed with a nonzero status.

The external grader observes the common path, traversal, symlink, execution, protected-open, and inherited-descriptor properties. ABI 5 device IOCTL and ABI 9 pathname UNIX-socket handling are stated source properties rather than externally graded properties: observing them requires matching runtime support plus controlled device or socket fixtures. The Fedora trial reports runtime ABI 7, so ABI 9 enforcement is not demonstrated there even when newer headers define the constant. Review the guarded rights table and the lesson's ABI checkpoint instead of treating a grader pass as evidence for untested kernel features.

The grader changes directory names, relative paths, contents, and synthetic canaries on every run. It compiles its observation child statically inside the allowed tree, creates a symlink to a protected sibling, passes a protected descriptor deliberately, and evaluates a read-only copy of your source.

The starter is useful but intentionally unsafe. It joins root and request as text, follows symlinks, permits traversal, launches a child without Landlock, and preserves inherited descriptors. Replace those behaviors using only the interfaces practiced in Lessons 05.01-05.03.

Build and exercise the harmless sample:

```bash
cc -std=c11 -Wall -Wextra -O2 fs_guard.c -o fs-guard
rm -rf sample-root
mkdir sample-root
printf 'sample\n' > sample-root/input.txt
./fs-guard read "$PWD/sample-root" input.txt
./fs-guard write "$PWD/sample-root" output.txt 'sample-output'
test "$(cat sample-root/output.txt)" = sample-output
../../lab-grade module-05
../../lab-grade module-05 --mode exam
```

### Test commands, line by line

- `cc` builds exactly the submitted source and enables useful warnings.
- The scoped `rm -rf` and `mkdir` create only a lab-local sample root.
- `printf` supplies non-sensitive input.
- `read` and `write` verify the functional interface before confinement is graded.
- `test` independently checks the write effect.
- Practice grading names failed properties and points back to the relevant lesson.
- Exam grading runs the same fresh bypasses but suppresses repair-oriented references.

The lab does not provide a completed implementation. Plan separate read/write and run paths, keep the root descriptor alive only as long as needed, make every setup failure stop the command, and preserve the required order: inspect ABI, create ruleset, add rule, set `no_new_privs`, restrict, close inherited authority, then `exec`.

This is an unprivileged local exercise. Do not add `sudo`, mounts, external paths, network access, or real secrets.

## Verify, explain, and replay

Run the starter and record its failed properties before editing. After repair, preserve both successful useful work and the expected denials/errors; a launcher that refuses everything does not pass. A compiler failure, missing executable, or missing fixture is not the desired security outcome.

For each passing property, explain which earlier lesson supplied the mechanism and what the observation does **not** establish. Keep an unresolved property unresolved rather than weakening its expected result. The lab intentionally withholds a combined implementation.

From this workspace, `cd ../..` returns to the course root. `./lab-reset module-05` removes this module's student work and generated fixtures after confirmation; preserve notes first. Start the module again for a fresh randomized attempt. Never substitute real credentials, personal directories, or external services for the synthetic fixtures.
<!-- /source -->

<!-- source: course/module-06-seccomp/README.md format=markdown -->
# Module 06 - Constrain syscalls with seccomp

Measure a real workload before writing policy, observe the operational difference between errno and kill actions, then launch a static child under a native-architecture default-deny libseccomp filter.

Play in order: `06.01`, `06.02`, `06.03`, then `module-06`.

Outcomes:

- collect and interpret a syscall profile without treating one trace as universal truth;
- compare `SCMP_ACT_ERRNO` and `SCMP_ACT_KILL_PROCESS` using an observable denied call;
- reproduce an alternate-interface bypass against a narrow blacklist;
- construct a native-architecture default-deny filter and prove it is active before `exec`;
- preserve a stated workload while denying socket, socket-pair, ptrace, and an unlisted syscall;
- explain why syscall filtering is not pathname authorization, resource accounting, or network destination policy.

Prerequisites: Modules 01-05, Linux, `strace`, a C compiler with static libc development files, and libseccomp headers/library discoverable through `pkg-config`. All probes are local and unprivileged.

## Learning route and limits

Prerequisites: Modules 01-05. Continue as your ordinary account inside the disposable Linux VM. The guided lessons introduce their new syntax and interfaces before the independent lab combines them.

06.01 establishes a functional baseline and the limits of one trace. 06.02 compares failure actions and an incomplete one-call rule. 06.03 constructs a native default-deny policy, then checks useful work and denied calls.

A small list is not automatically sound: it can omit required startup work or allow unnecessary operations. Explain why Seccomp: 2 proves less than a correct rule set. The independent lab deliberately uses a tiny static workload and errno-based denial; it does not promise arbitrary-program compatibility.

Before moving on, demonstrate both useful allowed work and the intended restriction, and explain the difference in your own words. A failed compiler command or missing input is not a security success. Use the independent lab's practice feedback to revisit a specific lesson; passing checks does not replace understanding or make the combined program production-ready.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-06-seccomp/lesson-01/README.md format=markdown -->
# 06.01 - Measure the workload before filtering

## Goal

Collect the syscalls of one explicit file-copy workload, separate startup activity from application intent, and demonstrate why a profile is evidence for policy design rather than a permanent universal allowlist.

## Concepts and preparation

Complete Modules 01-05 first. A syscall profile is a measurement of one program, input, build, and environment. It is not a list of everything that program could ever need. A dynamic executable also asks the kernel to load its runtime libraries before your `main` function begins; those startup calls are part of the observed process.

A **seccomp filter** will later decide which kernel calls may proceed. Before designing that policy, establish an ordinary successful workload and define what "still works" means. Here it means that the output file's bytes equal the input's bytes. Predict whether an empty input needs the same data-write calls as a nonempty input.

From the course root inside the Linux VM:

```bash
./lab-start 06.01
cd .student/06.01
pwd
ls -l workload.c
cat workload.c
```

The commands prepare and enter the student workspace, confirm filenames, and display every supplied source before execution. C sources are text, not executable programs yet. Use the compile commands below to create binaries. For an edit, run `nano FILENAME` with the actual source name, save with `Ctrl-O`, `Enter`, and leave with `Ctrl-X`; then rebuild. Keep all experiments in this disposable VM and leave SELinux enforcing on Fedora.

## Exercise 1 - Build and run without tracing

Complete source of `workload.c`:

```c
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s INPUT OUTPUT\n", argv[0]);
        return 2;
    }
    int input = open(argv[1], O_RDONLY);
    int output = open(argv[2], O_WRONLY | O_CREAT | O_TRUNC, 0600);
    if (input == -1 || output == -1) {
        perror("open");
        return 1;
    }
    char buffer[256];
    ssize_t count;
    while ((count = read(input, buffer, sizeof(buffer))) > 0)
        if (write(output, buffer, (size_t)count) != count)
            return 1;
    close(input);
    close(output);
    return count < 0;
}
```

### Source, line by line

- The program requires input and output pathnames and returns usage status 2 for any other interface.
- `open` requests read authority for one path and create/truncate/write authority for the other. The kernel may implement libc `open` with `openat`.
- The fixed buffer bounds each transfer. `read` ends at zero and a negative result becomes failure.
- `write` is checked rather than assumed. Both descriptors are closed on normal completion.

`O_RDONLY` requests reading. `O_WRONLY | O_CREAT | O_TRUNC` permits writing, creation, and replacement of old content; `0600` is an octal permission request for a new file. Do not use the same path for input and output: opening the output with truncation can erase the input before it is read. This lesson uses different synthetic names on purpose.

The `while` condition first assigns the result of `read` to `count`, then compares it with zero. A zero result means end of input, not an error. The following unbraced `if` is the loop body; adding another statement would require braces to keep it in that body. The example treats a short write as failure rather than retrying, which is sufficient for the supplied tiny regular files but not a complete production copier.

```bash
cc -std=c11 -Wall -Wextra -Werror -O2 workload.c -o workload
printf 'measured-data\n' > input.txt
./workload input.txt output.txt
cmp input.txt output.txt
```

### Line by line

- The compiler rejects warnings and writes only the lesson-local executable.
- `printf` creates synthetic input; `cmp` independently verifies exact output.
- Expected: no output and status zero. This establishes the functional baseline before tracing changes observation.

## Exercise 2 - Capture counts and exact events

```bash
strace -f -qq -c ./workload input.txt output.txt
strace -f -qq -o trace.txt ./workload input.txt output.txt
sed -E 's/^[0-9]+ +([^ (]+).*/\1/' trace.txt | sort -u
```

### Line by line

- `-f` follows children; this workload creates none, but the policy is explicit.
- `-qq` removes attach/detach chatter. `-c` reports aggregate syscall counts and timing.
- The second run writes complete events to `trace.txt` rather than mixing them with workload output.
- `sed` extracts syscall names from PID-prefixed lines; `sort -u` creates the observed set.
- If your installed `strace` omits PID prefixes or prints unfinished/resumed records, inspect `trace.txt` directly. This display pipeline is a convenience, not a parser suitable for generating a security policy automatically.
- Expect file operations plus dynamic-loader and process-startup calls such as `mmap`, `mprotect`, `brk`, and architecture-dependent setup. Exact names and counts vary by libc, architecture, kernel, and input.

The trace proves calls observed on this run. It does not prove unobserved error paths are unnecessary or that every observed syscall should be broadly allowed.

## Exercise 3 - Break the incomplete profile

Trace a zero-length input and compare it with the nonempty run:

```bash
: > empty.txt
strace -f -qq -o empty-trace.txt ./workload empty.txt empty-output.txt
grep -c 'write(' trace.txt
grep -c 'write(' empty-trace.txt
```

### Line by line

- `:` is a shell builtin that succeeds; redirection truncates `empty.txt` to zero bytes.
- The empty workload never enters its data-write body, so its observed set can omit a write that the nonempty input requires.
- `grep -c` prints counts. A zero count returns status 1, so inspect the number instead of chaining it under `set -e`.

Intentional mistake: treat only `empty-trace.txt` as the policy specification. The nonempty workload would then fail. Repair the reasoning by defining representative success and error cases first, combining their measurements, and reviewing each allowed call against the workload contract.

## Checkpoint and troubleshooting

```bash
cmp input.txt output.txt
grep -q 'openat(' trace.txt
grep -q 'read(' trace.txt
```

- If `strace` is blocked, use the documented disposable VM; do not weaken a work host.
- A libc may use `openat` even though the source says `open`; policy applies to kernel ABI calls, not C function spelling.
- Checkpoint: name one observed loader syscall and one input-dependent syscall, and explain why measurement alone is not least privilege.

## Replay and source truth

From this workspace, `cd ../..` then `./lab-reset 06.01` discards this lesson's generated work after confirmation. A filter installed in a child does not modify your parent shell or global kernel policy; do not attempt a host-wide "seccomp reset."

Use `man strace` in the VM for the installed tracing options and [write(2)](https://man7.org/linux/man-pages/man2/write.2.html) for byte-count/error behavior. Keep the compiler, libc, kernel, architecture, and test input alongside a profile.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-06-seccomp/lesson-02/README.md format=markdown -->
# 06.02 - Compare errno, kill, and blacklist bypass

## Goal

Install one observable deny rule, compare recoverable `EPERM` with process termination, then bypass a single-syscall blacklist through a related kernel interface.

## Concepts and preparation

Complete 06.01 first. A filter has a default action plus rules for selected calls. **Default allow** permits anything not explicitly denied; **default deny** denies anything not explicitly allowed. These are policy structures, not synonyms for good and bad applications.

For a selected denied call, an **errno action** returns an error to the program without performing the call. A **kill action** terminates the process instead. The program's subsequent error-handling code can run in the first case but not the second. We use only local Unix-domain socket creation in this synthetic observation; no external address or service is contacted.

The **libseccomp** library translates named rules into the kernel's filter format. `pkg-config` supplies build flags for the installed library; it is a build helper, not an enforcement mechanism. Predict whether a rule naming `socket` automatically covers the separate `socketpair` interface.

From the course root inside the Linux VM:

```bash
./lab-start 06.02
cd .student/06.02
pwd
ls -l socket_probe.c deny_socket.c
cat socket_probe.c
cat deny_socket.c
```

The commands prepare and enter the student workspace, confirm filenames, and display every supplied source before execution. C sources are text, not executable programs yet. Use the compile commands below to create binaries. For an edit, run `nano FILENAME` with the actual source name, save with `Ctrl-O`, `Enter`, and leave with `Ctrl-X`; then rebuild. Keep all experiments in this disposable VM and leave SELinux enforcing on Fedora.

## Exercise 1 - Build the probe and filter launcher

Complete probe source:

```c
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 2)
        return 2;
    errno = 0;
    int result;
    if (strcmp(argv[1], "socket") == 0)
        result = socket(AF_UNIX, SOCK_STREAM, 0);
    else {
        int pair[2];
        result = socketpair(AF_UNIX, SOCK_STREAM, 0, pair);
        if (result == 0) {
            close(pair[0]);
            close(pair[1]);
        }
    }
    printf("result=%d errno=%d\n", result, errno);
    return result == -1 ? 1 : 0;
}
```

### Source, line by line

- `errno` records why a failed call returned `-1`.
- `socket` requests one local AF_UNIX endpoint; `socketpair` requests a connected local pair without any external network.
- Successful pair descriptors are closed. The printed result makes filter behavior visible.
- A denied call returns nonzero; an allowed call returns zero.

Complete launcher source:

```c
#include <errno.h>
#include <seccomp.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 3 || (strcmp(argv[1], "errno") != 0 && strcmp(argv[1], "kill") != 0)) {
        fprintf(stderr, "usage: %s errno|kill COMMAND [ARG...]\n", argv[0]);
        return 2;
    }
    uint32_t action = strcmp(argv[1], "kill") == 0
        ? SCMP_ACT_KILL_PROCESS : SCMP_ACT_ERRNO(EPERM);
    scmp_filter_ctx context = seccomp_init(SCMP_ACT_ALLOW);
    if (!context || seccomp_rule_add(context, action, SCMP_SYS(socket), 0) < 0 ||
        seccomp_load(context) < 0) {
        fprintf(stderr, "failed to install filter\n");
        seccomp_release(context);
        return 1;
    }
    seccomp_release(context);
    execv(argv[2], &argv[2]);
    perror("execv");
    return 1;
}
```

### Source, line by line

- `seccomp_init(SCMP_ACT_ALLOW)` creates a blacklist: every syscall is allowed unless a rule says otherwise.
- The selected rule either returns `EPERM` or kills the whole process when `socket` is attempted.
- Every libseccomp operation is checked. Failure cannot fall through to an unfiltered `execv`.
- `seccomp_load` installs the filter on the launcher; seccomp then persists across `exec` into the probe.
- `seccomp_release` frees userspace policy memory, not the loaded kernel filter.

The ternary expression `condition ? first : second` chooses the action. `SCMP_SYS(socket)` asks the library for the named call, avoiding a hard-coded architecture-specific integer. The final `0` in `seccomp_rule_add` means no argument comparisons: the rule covers every invocation of that syscall in this filter. It does not inspect a destination or a pathname.

The context is an opaque library handle. `!context` detects allocation failure; the `||` chain short-circuits into the same error return if adding or loading the rule fails. By default libseccomp arranges the no-new-privileges requirement for an unprivileged load. Lesson 06.03 sets that bit explicitly so the ordering is visible in the launcher source.

Use only the documented modes here. A spelling error must not silently select a different failure policy; the argument guard checks `errno` or `kill` before choosing the action.

```bash
cc -std=c11 -Wall -Wextra -Werror -O2 -static socket_probe.c -o socket-probe
cc -std=c11 -Wall -Wextra -Werror -O2 deny_socket.c -o deny-socket $(pkg-config --cflags --libs libseccomp)
```

The first binary is static so its runtime does not complicate this one-rule observation. `pkg-config` supplies the distribution's libseccomp flags.

## Exercise 2 - Observe errno and kill actions

```bash
./deny-socket errno ./socket-probe socket || test "$?" -eq 1
status=0
./deny-socket kill ./socket-probe socket || status=$?
printf 'kill_status=%s\n' "$status"
```

### Line by line

- Errno mode lets the probe continue: expect `result=-1 errno=1` and status 1.
- `status=0` initializes the result; the `||` branch immediately saves the expected nonzero status. This works without changing your interactive shell's error-handling options.
- Kill mode prevents the probe from printing its post-call result. A shell commonly reports `Bad system call`; status is normally 128 plus `SIGSYS`.
- The status proves termination but does not identify a complete policy. A compile failure or nonexistent binary also produces a nonzero status, so confirm that the errno case worked and the kill case reports `SIGSYS`-related termination rather than treating any failure as the desired outcome.

Errno is useful for compatibility and diagnostics; kill is useful when continuing would be unsafe. Policy intent decides, not a blanket rule.

## Exercise 3 - Bypass the one-name blacklist

```bash
./deny-socket errno ./socket-probe socketpair
```

### Line by line

- The launcher denies only syscall `socket`.
- `socketpair` is a different syscall that creates a related communication primitive.
- Expected: `result=0 errno=0`. This is an intentional bypass of the blacklist, entirely local to the process.

Repair the design in Lesson 06.03 with a default-deny policy whose allowlist is derived from the stated workload. Merely adding names whenever a bypass appears tends toward an incomplete blacklist.

## Checkpoint and troubleshooting

```bash
! ./deny-socket errno ./socket-probe socket
./deny-socket errno ./socket-probe socketpair
```

- If `seccomp.h` or `libseccomp.pc` is absent, repair the documented VM provisioning: Fedora uses `libseccomp-devel` and `pkgconf-pkg-config`; Ubuntu uses `libseccomp-dev` and `pkg-config`. Do not guess include paths or disable filtering to get a pass.
- If kill mode emits no probe line, that is expected: the kernel terminates at the denied syscall.
- Checkpoint: explain why both observed actions enforce the same rule but have different failure semantics, and why neither blocks `socketpair`.

## Replay and source truth

From this workspace, `cd ../..` then `./lab-reset 06.02` discards this lesson's generated work after confirmation. A filter installed in a child does not modify your parent shell or global kernel policy; do not attempt a host-wide "seccomp reset."

The kernel's [seccomp filter documentation](https://docs.kernel.org/userspace-api/seccomp_filter.html) defines return actions and filter inheritance. The library's [seccomp_init manual](https://github.com/seccomp/libseccomp/blob/main/doc/man/man3/seccomp_init.3) defines the default action/context.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-06-seccomp/lesson-03/README.md format=markdown -->
# 06.03 - Launch with a native default-deny filter

## Goal

Turn the measured workload into a native-architecture allowlist, prove filter state inside the child, and preserve file access while denying unlisted kernel interfaces.

## Concepts and preparation

Complete 06.01-06.02 first. This lesson switches to a default-deny policy for a stated small workload. Every allowed call needs a reason: startup, file observation, output, or orderly exit. A minimal-looking list that prevents the required workload from starting is not a successful design.

The **native architecture** matters because syscall numbers and available names differ between ABIs. The library resolves names for the current architecture and emits the associated architecture check. This lesson is not a multi-architecture compatibility launcher. Do not replace names with numbers copied from another machine.

A kernel report of `Seccomp: 2` shows filter mode, not the filter's exact rules or correctness. We need both that state observation and behavioral evidence: allowed work succeeds and selected unrelated calls receive the expected error.

From the course root inside the Linux VM:

```bash
./lab-start 06.03
cd .student/06.03
pwd
ls -l policy_probe.c allowlist.c
cat policy_probe.c
cat allowlist.c
```

The commands prepare and enter the student workspace, confirm filenames, and display every supplied source before execution. C sources are text, not executable programs yet. Use the compile commands below to create binaries. For an edit, run `nano FILENAME` with the actual source name, save with `Ctrl-O`, `Enter`, and leave with `Ctrl-X`; then rebuild. Keep all experiments in this disposable VM and leave SELinux enforcing on Fedora.

## Exercise 1 - Read the observation probe

Complete `policy_probe.c`:

```c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/ptrace.h>
#include <sys/socket.h>
#include <sys/syscall.h>
#include <unistd.h>

static void report(long result) {
    char line[96];
    int count = snprintf(line, sizeof(line), "result=%ld errno=%d\n", result, errno);
    if (write(STDOUT_FILENO, line, (size_t)count) != count)
        _exit(1);
}

int main(int argc, char **argv) {
    if (argc < 2)
        return 2;
    if (strcmp(argv[1], "status") == 0) {
        char buffer[4096] = {0};
        int fd = open("/proc/self/status", O_RDONLY);
        ssize_t count = read(fd, buffer, sizeof(buffer) - 1);
        close(fd);
        if (count < 0)
            return 1;
        char *nnp = strstr(buffer, "NoNewPrivs:");
        char *seccomp = strstr(buffer, "Seccomp:");
        if (!nnp || !seccomp) {
            fprintf(stderr, "required process-state fields are absent\n");
            return 1;
        }
        dprintf(STDOUT_FILENO, "%.13s\n%.10s\n", nnp, seccomp);
        return 0;
    }
    if (strcmp(argv[1], "file") == 0 && argc == 3) {
        int fd = open(argv[2], O_RDONLY);
        char buffer[256];
        ssize_t count = read(fd, buffer, sizeof(buffer));
        return count > 0 && write(STDOUT_FILENO, buffer, (size_t)count) == count ? 0 : 1;
    }
    errno = 0;
    if (strcmp(argv[1], "socket") == 0)
        report(socket(AF_UNIX, SOCK_STREAM, 0));
    else if (strcmp(argv[1], "socketpair") == 0) {
        int pair[2];
        report(socketpair(AF_UNIX, SOCK_STREAM, 0, pair));
    } else if (strcmp(argv[1], "ptrace") == 0)
        report(ptrace(PTRACE_TRACEME, 0, NULL, NULL));
    else
        report(syscall(SYS_getppid));
    return 0;
}
```

### Line by line

- `status` reads kernel-reported process state from procfs after `exec`; the launcher cannot substitute its own pre-filter claim.
- `file` uses normal libc `open`, which becomes the kernel's `openat` on this platform.
- The denial modes invoke distinct syscalls and report raw result plus `errno` through allowed output.
- The fallback uses raw `SYS_getppid`, a harmless syscall intentionally absent from the allowlist.

The zero-initialized status buffer reserves its last byte for string termination. `strstr` locates the two field names; absent fields cause an explicit error rather than a fabricated report. The precision in the `dprintf` format prints only each short field/value segment. This is a focused observer for the course baseline, not a general procfs parser.

`report` prints a raw syscall result and `errno`; its caller returns 0 because the observation itself completed even when the requested syscall was denied. Therefore the denial checkpoint must inspect `result=-1 errno=1`, not merely the observer's exit status. This differs deliberately from 06.02's probe, which returned 1 for a denied call.

Read the full small source before compiling:

```bash
sed -n '1,240p' policy_probe.c
cc -std=c11 -Wall -Wextra -Werror -O2 -static policy_probe.c -o policy-probe
```

- `sed` displays the complete source; no required behavior is hidden.
- The static binary makes its startup surface stable enough for this VM exercise.

## Exercise 2 - Build and inspect the policy

Complete `allowlist.c`:

```c
#define _GNU_SOURCE
#include <errno.h>
#include <seccomp.h>
#include <stdio.h>
#include <string.h>
#include <sys/prctl.h>
#include <unistd.h>

static int allow_name(scmp_filter_ctx context, const char *name) {
    int number = seccomp_syscall_resolve_name(name);
    return number == __NR_SCMP_ERROR ? 0 : seccomp_rule_add(context, SCMP_ACT_ALLOW, number, 0);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s COMMAND [ARG...]\n", argv[0]);
        return 2;
    }
    const char *allowed[] = {
        "execve", "read", "write", "close", "openat", "brk", "mmap", "mprotect",
        "munmap", "set_tid_address", "set_robust_list", "prlimit64", "readlink", "readlinkat",
        "getrandom", "rseq", "arch_prctl", "fstat", "newfstatat", "faccessat",
        "exit", "exit_group"
    };
    scmp_filter_ctx context = seccomp_init(SCMP_ACT_ERRNO(EPERM));
    uint32_t native = seccomp_arch_native();
    if (!context || native == 0 || seccomp_arch_exist(context, native) < 0) {
        fprintf(stderr, "native architecture unavailable\n");
        seccomp_release(context);
        return 1;
    }
    for (size_t index = 0; index < sizeof(allowed) / sizeof(allowed[0]); index++) {
        if (allow_name(context, allowed[index]) < 0) {
            fprintf(stderr, "cannot allow %s\n", allowed[index]);
            seccomp_release(context);
            return 1;
        }
    }
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0) {
        perror("set no_new_privs");
        seccomp_release(context);
        return 1;
    }
    int loaded = seccomp_load(context);
    if (loaded < 0) {
        fprintf(stderr, "install seccomp: %s\n", strerror(-loaded));
        seccomp_release(context);
        return 1;
    }
    seccomp_release(context);
    execv(argv[1], &argv[1]);
    perror("execv");
    return 1;
}
```

### Line by line

- `SCMP_ACT_ERRNO(EPERM)` is the default, so an omitted syscall is denied rather than silently allowed.
- `seccomp_arch_native` obtains libseccomp's token for the running architecture; `seccomp_arch_exist` verifies the context contains it.
- Names are resolved for the native architecture. A name absent from that architecture is skipped, while a rule failure for a present syscall stops setup. This keeps the measured static-startup set portable between the supported arm64 and x86-64 baselines without hard-coded numbers.
- The list includes static startup, exact argv execution, proc/file reads, output, memory setup, and exit. It deliberately omits socket, socketpair, ptrace, and getppid.
- `no_new_privs` is explicit before loading. Both calls are checked, and `execv` is reachable only after a successful load.
- libseccomp generates the BPF architecture check and syscall-number comparisons; hand-coded numeric syscall tables are avoided.

`allowed` is an array of pointers to constant strings. Dividing its total size by one element's size gives the number of entries, so the loop does not need a separately maintained count. `allow_name` resolves each entry and asks for an unconditional allow rule. Skipping a name absent from the native architecture does not allow an unknown syscall: the default remains denial. A typo can still break required functionality, which is why the functional tests matter.

The error paths distinguish APIs: `prctl` reports failure through `errno`, while `seccomp_load` returns a negative error number. The launcher prints `strerror(-loaded)` for the latter rather than using a stale `errno`. Releasing the library context afterward does not remove the installed kernel filter.

Display the full source and build it:

```bash
sed -n '1,260p' allowlist.c
cc -std=c11 -Wall -Wextra -Werror -O2 allowlist.c -o allowlist $(pkg-config --cflags --libs libseccomp)
```

## Exercise 3 - Verify effective state and denials

```bash
./allowlist ./policy-probe status
printf 'allowed-file\n' > note.txt
./allowlist ./policy-probe file note.txt
./allowlist ./policy-probe socket
./allowlist ./policy-probe socketpair
./allowlist ./policy-probe ptrace
./allowlist ./policy-probe unexpected
```

### Line by line

- Status must show `NoNewPrivs: 1` and `Seccomp: 2`; mode 2 is filter mode.
- The file workload succeeds because `openat`, `read`, `write`, and `close` are in scope.
- Every denial probe should report `result=-1 errno=1`, including both socket interfaces and the unlisted harmless syscall.
- The probes return normally because the default action is errno. This permits evidence collection.

For the intentional policy-edit exercise, copy only this lesson's source with `cp allowlist.c extra_call.c`, open `nano extra_call.c`, and add `"getppid",` to its allowed-name array. Save and compile it as `extra-call` using the same library flags as above. Run `./extra-call ./policy-probe unexpected`. It returns a real parent PID, proving that default-deny still depends on a justified allowlist. Return to `./allowlist ./policy-probe unexpected` and require `result=-1 errno=1`; do not leave the expanded binary in the final checkpoint command.

The file test is also a boundary lesson: seccomp allowed `openat`, so it cannot distinguish `note.txt` from another pathname. Compose it with Module 05's `openat2`/Landlock layer for pathname policy. It likewise does not meter CPU/memory or authorize network destinations.

## Checkpoint and troubleshooting

```bash
./allowlist ./policy-probe status | grep -q 'Seccomp:[[:space:]]*2'
test "$(./allowlist ./policy-probe unexpected)" = 'result=-1 errno=1'
```

- If the static probe fails before output, compare its `strace` surface with the allowlist on this supported VM and add only justified startup calls.
- `EPERM` from `seccomp_load` usually means `no_new_privs` was not set or policy setup was reordered.
- If a newer libc needs a startup call not present here, record the exact failing call and build versions. Do not automatically grant every observed call or turn the default into allow; investigate whether the missing operation is required by the stated workload.
- Checkpoint: identify the functional syscalls, startup syscalls, deliberately denied syscalls, and the separate pathname assumption.

## Replay and source truth

From this workspace, `cd ../..` then `./lab-reset 06.03` discards this lesson's generated work after confirmation. A filter installed in a child does not modify your parent shell or global kernel policy; do not attempt a host-wide "seccomp reset."

The library's [seccomp_load manual](https://github.com/seccomp/libseccomp/blob/main/doc/man/man3/seccomp_load.3) and [architecture API manual](https://github.com/seccomp/libseccomp/blob/main/doc/man/man3/seccomp_arch_add.3) document the installation and architecture checks. Kernel [seccomp documentation](https://docs.kernel.org/userspace-api/seccomp_filter.html) explains why syscall filtering is only one containment layer.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-06-seccomp/lab/README.md format=markdown -->
# Module 06 independent lab - Default-deny syscall launcher

## Preparation and practiced skills

Complete 06.01-06.03 first. Use 06.01 to justify the workload and measurements, 06.02 to explain the required errno behavior, and 06.03 to plan native architecture, rule construction, loading, and post-exec evidence.

The starter checks that a command was supplied, then calls `execv` with the exact executable path and remaining arguments. Returning from exec prints an error and returns nonzero. The interface is functional, but no filter or privilege floor exists yet. Do not replace it with a shell command string.

A name genuinely absent from the native ABI can remain denied rather than receiving a rule, as practiced in 06.03. That is different from ignoring a failed rule-add operation for an available call. Keep the default deny behavior and stop on actual setup errors. The supplied static observation workload, not arbitrary programs, defines the functional contract.

From the course root:

```bash
./lab-start module-06
cd .student/06.lab
pwd
ls -l seccomp_guard.c
cat seccomp_guard.c
nano seccomp_guard.c
```

The commands prepare your editable lab, enter and inspect it, then open the starter for reading and editing. Save in nano with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. Rebuild after each C edit using the compiler command below. Keep the canonical files and grader unchanged.

```c
#include <stdio.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s COMMAND [ARG...]\n", argv[0]);
        return 2;
    }
    execv(argv[1], &argv[1]);
    perror("execv");
    return 1;
}
```

## Contract


Implement `seccomp_guard.c`. The grader builds and invokes:

```text
seccomp-guard COMMAND [ARG...]
```

The command is an exact executable path to a static local observation probe. Your launcher must:

- validate the interface and preserve the structured argv vector;
- create a libseccomp context whose default action returns `EPERM`;
- explicitly confirm the context's native architecture;
- allow only the calls needed for static startup, exact `execve`, status/file reads, bounded output, memory setup, and exit as practiced in Lesson 06.03;
- set `PR_SET_NO_NEW_PRIVS` and successfully load the filter before `exec`;
- fail closed if context creation, architecture validation, rule installation for an available call, privilege-floor establishment, filter loading, or exec fails; a name unavailable on the native ABI remains denied rather than broadening the default action.

The fresh external grader compiles a static probe and checks functional execution, `/proc/self/status` evidence, an allowed file read, direct socket denial, socket-pair denial, ptrace denial, and denial of a harmless syscall omitted from the workload. It evaluates a read-only copy of your source.

The starter only validates argv and calls `execv`, so the workload runs but every confinement property fails. Use libseccomp names rather than architecture-specific numeric syscall constants. Do not add network access, privilege, or a kill action; errno results are required so the grader can observe every denial.

```bash
cc -std=c11 -Wall -Wextra -Werror -O2 seccomp_guard.c -o seccomp-guard $(pkg-config --cflags --libs libseccomp)
../../lab-grade module-06
../../lab-grade module-06 --mode exam
```

### Test commands, line by line

- The compiler and warning flags match the guided launcher; `pkg-config` supplies only the local libseccomp build flags.
- Practice mode creates a fresh probe and names failed properties with lesson references.
- Exam mode repeats fresh behavior checks but suppresses repair-oriented references.

The lab deliberately withholds a complete implementation. Start from the ordering and justified call set you measured and explained in Lesson 06.03. Seccomp is one runtime layer: this lab does not claim pathname policy, resource accounting, network destination authorization, or protection from already-open descriptors.

## Verify, explain, and replay

Run the starter and record its failed properties before editing. After repair, preserve both successful useful work and the expected denials/errors; a launcher that refuses everything does not pass. A compiler failure, missing executable, or missing fixture is not the desired security outcome.

For each passing property, explain which earlier lesson supplied the mechanism and what the observation does **not** establish. Keep an unresolved property unresolved rather than weakening its expected result. The lab intentionally withholds a combined implementation.

From this workspace, `cd ../..` returns to the course root. `./lab-reset module-06` removes this module's student work and generated fixtures after confirmation; preserve notes first. Start the module again for a fresh randomized attempt. Never substitute real credentials, personal directories, or external services for the synthetic fixtures.
<!-- /source -->

<!-- source: course/module-07-cgroups/README.md format=markdown -->
# Module 07 - Bound CPU, memory, and process creation

Use cgroup v2 through the ordinary user's delegated systemd manager. Observe effective controller files from inside workloads, trigger bounded pressure, and prove that transient service collection removes the complete process tree.

Play in order: `07.01`, `07.02`, `07.03`, then `module-07`.

Outcomes:

- connect a systemd user unit to its effective cgroup v2 path;
- interpret `cpu.max`, `cpu.stat`, `memory.max`, `memory.events`, `pids.max`, and `pids.events`;
- distinguish throttling, allocation failure/OOM, and PID exhaustion;
- apply limits to a process tree rather than a single PID;
- use bounded transient units whose cleanup is synchronous and ownership-verifiable.

Prerequisites: Modules 01-06, unified cgroup v2, a running delegated systemd user manager, and the `cpu`, `memory`, and `pids` controllers. No root access is used by the exercises.

## Learning route and limits

Earlier controls answered whether an operation may happen. Resource controls answer how much resource the permitted process tree may consume. A file read can be authorized while a computation still exhausts memory or creates too many tasks. These are different failure modes and need different evidence.

07.01 introduces service identity, registered ownership, the delegated user manager, and CPU quota/period observations. 07.02 reads actual memory/swap ceilings before a capped allocator runs and requires specific OOM evidence. 07.03 checks task-controller rejection events, then uses a harmless sleep to practice client timeout versus service cleanup. The independent lab combines resource properties, validation, literal argv, result handling, and exact ownership.

The helpers enforce small input caps even when a property is deliberately omitted. Never replace them with an unbounded stress loop. Do not change host controllers, swap, overcommit, or security-module policy to force a lesson outcome. If the expected runtime prerequisite fails, return to VM preflight.

Before moving on, distinguish throttling, allocation failure/OOM, and task-creation refusal. Explain why a nonzero command status or an absent wildcard listing is insufficient by itself. A timed-out client may leave a separately managed service; retain ownership evidence until collection or verified cleanup is established.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-07-cgroups/lesson-01/README.md format=markdown -->
# 07.01 - Observe an effective CPU quota

## Outcomes and prerequisites

Complete Modules 01-06 first. You will locate a process's cgroup, translate a CPU percentage into a quota/period pair, distinguish throttling from failure, and run a named transient user service without changing global policy.

## Concepts before commands

A **cgroup** groups processes for resource accounting and control. Children begin in their parent's cgroup. A **controller** supplies one kind of resource policy, such as CPU, memory, or task count. These limits compose with earlier namespace and access controls; they do not replace them.

The systemd **user manager** manages services for your ordinary account. The VM's system manager delegates the necessary controllers to it during provisioning. We ask that existing manager to create a **transient service**: a temporary unit configured for this run, not a permanent service file.

`CPUQuota=50%` means at most half of **one CPU's** time over the configured period, shared by the service's tasks. It does not mean half of every CPU in the VM. At a 100 ms period, the kernel representation is `50000 100000`, in microseconds. The first value is quota; the second is period. The word `max` instead of a numeric quota means this cgroup has no local CPU ceiling, though an ancestor may still constrain it.

## Prepare and read the program

From the course root inside the Linux VM:

```bash
./lab-start 07.01
cd .student/07.01
pwd
ls -l inspect_cpu.py
cat inspect_cpu.py
systemctl --user show-environment >/dev/null
```

`lab-start` creates your student copy. `cd`, `pwd`, and `ls` locate it; `cat` displays the source. The last command checks that the user manager is reachable without printing its environment. Failure is a VM/session prerequisite problem: do not substitute `sudo systemd-run`.

```python
#!/usr/bin/env python3
import json
import time
from pathlib import Path

lines = Path("/proc/self/cgroup").read_text().splitlines()
relative = next(line.split("::", 1)[1] for line in lines if line.startswith("0::"))
base = Path("/sys/fs/cgroup") / relative.lstrip("/")
before = (base / "cpu.stat").read_text()
end = time.monotonic() + 1.0
count = 0
while time.monotonic() < end:
    count += 1
after = (base / "cpu.stat").read_text()
print(json.dumps({
    "cgroup": relative,
    "cpu_max": (base / "cpu.max").read_text().strip(),
    "iterations": count,
    "cpu_stat_before": before,
    "cpu_stat_after": after,
}))
```

### Source, line by line

- `json` serializes observations; `time` supplies a monotonic clock; `Path` reads kernel-generated files.
- Reading and splitting `/proc/self/cgroup` gives this process's membership lines. On unified cgroup v2, `0::PATH` identifies the relevant path.
- The generator selects that line, splits once at `::`, and `next` obtains the path. Missing v2 membership is an error, not permission to invent a location.
- `relative.lstrip("/")` removes the initial slash before joining it beneath `/sys/fs/cgroup`. Without that, an absolute right-hand path would replace the prefix.
- The two `cpu.stat` reads sample counters before and after work.
- `time.monotonic() + 1.0` sets a one-second elapsed-time deadline. Wall-clock changes do not extend it.
- The loop performs harmless arithmetic until that deadline. Its iteration count is not a portable benchmark.
- The final JSON includes actual cgroup membership, the effective file's quota/period text, iterations, and both counter snapshots. Requested command flags alone are not the observation.

## Exercise 1 - Establish the unmodified baseline

Predict whether the login shell's cgroup has a local quota, then run:

```bash
python3 inspect_cpu.py > baseline.json
python3 -m json.tool baseline.json
```

The redirection saves this run's JSON; the formatter parses and displays it. Expect a nonzero iteration count and a cgroup path. A usual unconstrained local value is `max 100000`, but retain the value you actually observe. Do not change a parent cgroup to make its output match a sample.

## Exercise 2 - Give each transient unit a verifiable owner

Define this helper in the same guest shell:

```bash
new_cpu_unit() {
  NE_UNIT="north-echo-$(id -u)-07-01-$(python3 -c 'import secrets; print(secrets.token_hex(4))').service"
  ../../scripts/labctl.py register-unit 07.01 "$NE_UNIT"
}
NE_DESCRIPTION="North Echo 07.01 workspace=$PWD"
```

### Line by line

- A shell function groups commands without running them until its name is called. Its braces delimit the body.
- `id -u` contributes the actual ordinary UID; `secrets.token_hex(4)` contributes eight random hexadecimal characters to avoid reusing another run's name.
- The target-specific prefix and `.service` suffix match the course's ownership contract.
- `register-unit` records this exact future unit in this lesson's runtime registry. It does not create or start the service.
- The description includes the exact prepared workspace. Cleanup verifies the name, description, and delegated cgroup path; a familiar-looking prefix alone is insufficient.
- Keep these variables in this shell. If registration fails, stop and diagnose it before launching.

Now create one bounded service:

```bash
new_cpu_unit
systemd-run --user --wait --pipe --collect --quiet --expand-environment=no \
  --unit="$NE_UNIT" --description="$NE_DESCRIPTION" \
  --property=RuntimeMaxSec=5s --property=TimeoutStopSec=1s \
  --property=MemoryMax=67108864 --property=MemorySwapMax=0 --property=TasksMax=16 \
  --property=CPUQuota=50% --property=CPUQuotaPeriodSec=100ms \
  -- /usr/bin/python3 "$PWD/inspect_cpu.py" > limited.json
python3 -m json.tool limited.json
```

### Line by line

- `--user` selects your delegated manager, not system services.
- `--wait` waits for service completion; `--pipe` connects the workload's streams; `--collect` allows unloading even a failed transient unit. `--quiet` suppresses manager chatter.
- `--expand-environment=no` prevents systemd from expanding dollar-variable syntax inside the command arguments. An argv array alone does not prevent every downstream interpreter from transforming it.
- Unit name and description bind the run to the registered owner.
- The five-second runtime ceiling and one-second stop timeout backstop the one-second program. The memory and task limits keep this observation small.
- The CPU properties specify the quota and its period explicitly.
- `--` ends manager options. The absolute Python and source paths avoid dependence on the service's working directory or command search path.
- Redirection captures workload output for separate inspection. A nonzero launcher status or missing JSON is an error to investigate, not a passing quota test.

Expect `cpu_max` to be `50000 100000`. Under pressure, `nr_throttled` in the after snapshot should increase relative to before. Exact counter values and iterations vary with scheduling; quota enforcement is not a promise of wall-clock responsiveness.

## Exercise 3 - Observe the missing property and repair it

Call `new_cpu_unit` again and repeat the previous command with only the `CPUQuota=50%` property omitted, saving to `missing-quota.json`. Keep the memory, task, and runtime bounds. The program still works, but the local quota should be `max`. If an inherited manager configuration supplies a quota, record it instead of pretending you observed an unlimited case.

Restore the quota, create a fresh unit name, and regenerate `limited.json`. A successful workload alone could not detect the missing control; the effective-state comparison does.

## Checkpoint, collection, and troubleshooting

```bash
python3 -c 'import json; p=json.load(open("limited.json")); assert p["cpu_max"] == "50000 100000"; assert p["iterations"] > 0; print("CPU STATE: PASS")'
systemctl --user show "$NE_UNIT" --property=LoadState
../../lab-cleanup 07.01 --dry-run
../../lab-cleanup 07.01
```

The Python assertions parse actual data rather than searching a matching substring. The exact last unit should report `LoadState=not-found` once collected; `systemctl` may return nonzero for that absent unit. A manager communication error is different from explicit absence. Course cleanup examines every registered unit and retains the registry if ownership cannot be established.

If the user manager is unavailable, return to the documented VM login. If `cpu.max` is missing, stop at preflight rather than mounting a different hierarchy. If the service cannot find the script, inspect the saved absolute path. Never write directly into the parent cgroup or stop units using a wildcard.

Return to the course root with `cd ../..`. `./lab-reset 07.01` deliberately discards this lesson's student files and fixtures after ownership-checked cleanup. Preserve notes first.

## Source truth

The kernel's [cgroup v2 guide](https://docs.kernel.org/admin-guide/cgroup-v2.html) defines membership, hierarchy, `cpu.max`, and counters. In the VM, `man systemd-run` documents waiting, collection, and argument expansion; `man systemd.resource-control` documents CPUQuota and CPUQuotaPeriodSec. The beta baseline uses systemd 259 on Fedora; Ubuntu 24.04's systemd 255 also supports `--expand-environment=no` (added in 254).
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-07-cgroups/lesson-02/README.md format=markdown -->
# 07.02 - Bound memory and observe OOM

## Outcomes and prerequisites

Complete 07.01 first. You will read a workload's actual memory/swap limits, distinguish a small successful allocation from a bounded out-of-memory event, and verify cleanup without mistaking any nonzero exit for successful containment.

## Concepts before commands

A **memory charge** accounts memory to a cgroup. `memory.max` sets its memory ceiling; `memory.swap.max` separately limits swap usage. Swap is storage used to hold memory pages outside RAM. Setting the swap limit to zero prevents this exercise from shifting its pressure into swap.

A mebibyte (MiB) is 1,048,576 bytes. Thus 32 MiB is 33,554,432 bytes. The interpreter, runtime data, and other charged memory share the limit with the lesson's arrays. Asking for 32 MiB of arrays is not the same as keeping the whole process below 32 MiB.

When the kernel cannot reclaim enough charged memory, it may invoke the cgroup's out-of-memory handling. Allocation failure and OOM termination are different outcomes; inspect the evidence before naming one. MemoryMax is not a mathematical promise that a sampled usage counter can never transiently exceed its value. The checkpoint combines the configured kernel limit with the observed OOM result.

## Prepare and read the bounded allocator

From the course root:

```bash
./lab-start 07.02
cd .student/07.02
pwd
ls -l memory_hog.py
cat memory_hog.py
```

These commands prepare, enter, and inspect this lesson's student copy. The misleadingly dramatic filename names a deliberately small teaching allocator, not an unbounded stress tool.

```python
#!/usr/bin/env python3
import json
import sys
import time
from pathlib import Path

if len(sys.argv) != 2 or not sys.argv[1].isdigit() or not 1 <= int(sys.argv[1]) <= 96:
    print("usage: memory_hog.py MIB (integer 1..96)", file=sys.stderr)
    raise SystemExit(2)
mebibytes = int(sys.argv[1])
lines = Path("/proc/self/cgroup").read_text().splitlines()
relative = next(line.split("::", 1)[1] for line in lines if line.startswith("0::"))
base = Path("/sys/fs/cgroup") / relative.lstrip("/")
print(json.dumps({
    "cgroup": relative,
    "memory_max": (base / "memory.max").read_text().strip(),
    "memory_swap_max": (base / "memory.swap.max").read_text().strip(),
    "requested_mib": mebibytes,
}), flush=True)
blocks = []
for index in range(mebibytes):
    blocks.append(bytearray(1024 * 1024))
    if index % 8 == 0:
        print(f"allocated_mib={index + 1}", flush=True)
print("allocation completed", flush=True)
time.sleep(1)
```

### Source, line by line

- The imports provide JSON output, argv/status handling, elapsed waiting, and kernel-file reads.
- The argument guard requires one numeric count from 1 through 96. Invalid inputs stop before allocation. Do not remove that guard or increase the bound.
- The membership lookup is the same `0::PATH` mechanism from 07.01. The program reads its own actual memory and swap limits, not a value supplied by the launcher.
- The first JSON record is flushed before pressure begins so a later killed process does not take its startup evidence with it.
- `blocks = []` retains every allocated object. Without retained references, old objects could be reclaimed and the intended pressure would not accumulate.
- Each `bytearray(1024 * 1024)` creates one initialized MiB. Appending it keeps that allocation alive.
- `index % 8 == 0` prints sparse progress, including the first block. The label is an allocation count, not total resident memory.
- The completion line appears only if the allocation loop finishes. The final one-second sleep is bounded; it does not allocate further memory.

## Exercise 1 - Establish a small functional baseline

Predict whether 16 MiB should fit in the disposable VM's ordinary login environment:

```bash
python3 memory_hog.py 16 > memory-baseline.txt
printf 'baseline status=%s\n' "$?"
cat memory-baseline.txt
```

The first command saves this run's output; the immediate status capture should show 0. The file should contain a startup JSON record, progress, and `allocation completed`. If this small baseline fails, diagnose VM resources before continuing.

## Exercise 2 - Apply a 32 MiB service ceiling

Define a target-specific name/registration helper in this guest shell:

```bash
new_memory_unit() {
  NE_UNIT="north-echo-$(id -u)-07-02-$(python3 -c 'import secrets; print(secrets.token_hex(4))').service"
  ../../scripts/labctl.py register-unit 07.02 "$NE_UNIT"
}
NE_DESCRIPTION="North Echo 07.02 workspace=$PWD"
```

As in 07.01, the function creates a fresh exact name and records it before launch. The description binds it to this prepared workspace. If registration fails, stop; do not run an unregistered substitute.

Predict which evidence should appear before the process can be killed:

```bash
new_memory_unit
NE_MEMORY_STATUS=0
systemd-run --user --wait --pipe --collect --expand-environment=no \
  --unit="$NE_UNIT" --description="$NE_DESCRIPTION" \
  --property=RuntimeMaxSec=5s --property=TimeoutStopSec=1s \
  --property=MemoryMax=33554432 --property=MemorySwapMax=0 \
  --property=TasksMax=8 --property=CPUQuota=50% \
  -- /usr/bin/python3 "$PWD/memory_hog.py" 96 \
  > memory-output.txt 2> memory-manager.txt || NE_MEMORY_STATUS=$?
printf 'bounded status=%s\n' "$NE_MEMORY_STATUS"
cat memory-output.txt
cat memory-manager.txt
```

### Line by line

- The service uses the ordinary user's manager and an exact registered identity.
- `--wait --pipe --collect` waits for the service and connects output, then permits failed-unit collection. We omit `--quiet` so the manager's result remains visible.
- Runtime, stop, task, and CPU limits backstop this small memory observation.
- MemoryMax is exactly 32 MiB; MemorySwapMax is zero.
- The child requests at most 96 MiB, a fixed synthetic bound. It should not finish under this ceiling.
- The two redirections retain workload stdout and manager/child stderr separately.
- The `||` branch saves failure without changing your shell's `set -e` setting.
- The printed status is necessary but insufficient evidence: a missing script would also fail.

Expected on the course baseline: the initial JSON reports `memory_max` of `33554432` and `memory_swap_max` of `0`; the completion line is absent; the manager reports `oom-kill`; the status is nonzero. Exact progress and peak usage vary with interpreter/runtime overhead.

## Exercise 3 - Compare a missing limit without increasing pressure

Create another fresh unit and repeat the command with only MemoryMax omitted, the request reduced to **16**, and output filenames changed to `missing-limit-output.txt` and `missing-limit-manager.txt`. Keep the other bounds. The workload should complete while reporting no local memory ceiling (`max`), unless a manager default supplies one.

This demonstrates the missing property without asking an unconstrained process to consume more memory. Restore MemoryMax and the bounded 96 MiB request, create a fresh unit, and regenerate the two original evidence files before the checkpoint.

## Checkpoint and troubleshooting

```bash
python3 - "$NE_MEMORY_STATUS" <<'PY'
import json
import sys
from pathlib import Path

output = Path("memory-output.txt").read_text()
initial = json.loads(output.splitlines()[0])
assert initial["memory_max"] == "33554432"
assert initial["memory_swap_max"] == "0"
assert "allocation completed" not in output
assert int(sys.argv[1]) != 0
assert "oom-kill" in Path("memory-manager.txt").read_text()
print("MEMORY LIMIT AND OOM EVIDENCE: PASS")
PY
systemctl --user show "$NE_UNIT" --property=LoadState
../../lab-cleanup 07.02 --dry-run
../../lab-cleanup 07.02
```

The quoted here-document sends the displayed Python program to `python3 -` without shell expansion. The saved status is a separate argument. The assertions require parsed effective limits, incomplete allocation, a failing status, and the manager's specific OOM classification. They do not accept an arbitrary error.

After collection, the last unit should be explicitly not found. Cleanup verifies registered ownership; it never searches for similarly named processes. If the manager is unreachable, the Python file is missing, or the first JSON record is absent, diagnose setup. If the result is `MemoryError` or a runtime timeout rather than `oom-kill`, record that distinct outcome; do not call it the expected OOM observation or raise pressure to force one.

Never change host overcommit, swap, or global OOM settings for this lesson. Return to the course root with `cd ../..`; `./lab-reset 07.02` removes this lesson's work after confirmation. Save notes first.

## Source truth

The kernel's [cgroup v2 memory-controller documentation](https://docs.kernel.org/admin-guide/cgroup-v2.html) defines charging, memory.max, swap limits, and memory.events. The installed `man systemd.resource-control` explains MemoryMax/MemorySwapMax; `man systemd-run` explains result reporting and collection. These are resource controls, not authorization for the data in memory.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-07-cgroups/lesson-03/README.md format=markdown -->
# 07.03 - Bound process-tree growth and collect it

## Outcomes and prerequisites

Complete 07.01-07.02 first. You will limit task creation, distinguish a rejected fork from other failures, verify exact-unit collection, and practice the distinction between a client timeout and stopping the service it requested.

## Concepts before commands

The cgroup **pids controller** limits tasks, including threads, not merely the number of top-level programs. The parent's task counts against `TasksMax` too. When the controller refuses another creation, `fork` fails rather than producing an extra child. It does not kill already-existing tasks to bring a count down.

A child that exits must still be reaped by its parent. This program saves every child PID and waits for each, connecting to the direct-child lifecycle from 02.03. It never runs an unbounded fork loop.

A transient unit's lifetime is separate from the `systemd-run` client's lifetime. Killing or timing out the client is not proof that the user manager stopped its service. Resource ceilings, a service runtime deadline, and ownership-checked cleanup all have distinct roles.

## Prepare and read the bounded program

From the course root:

```bash
./lab-start 07.03
cd .student/07.03
pwd
ls -l fork_pressure.py
cat fork_pressure.py
```

The commands prepare, locate, and display the student source. If you edit it, use `nano fork_pressure.py`, save with `Ctrl-O`, `Enter`, and leave with `Ctrl-X`. Do not remove the maximum-request guard.

```python
#!/usr/bin/env python3
import json
import os
import sys
import time
from pathlib import Path

if len(sys.argv) != 2 or not sys.argv[1].isdigit() or not 1 <= int(sys.argv[1]) <= 64:
    print("usage: fork_pressure.py COUNT (integer 1..64)", file=sys.stderr)
    raise SystemExit(2)
requested = int(sys.argv[1])
lines = Path("/proc/self/cgroup").read_text().splitlines()
relative = next(line.split("::", 1)[1] for line in lines if line.startswith("0::"))
base = Path("/sys/fs/cgroup") / relative.lstrip("/")
children = []
failure_errno = None
for _ in range(requested):
    try:
        pid = os.fork()
    except OSError as error:
        failure_errno = error.errno
        break
    if pid == 0:
        time.sleep(0.2)
        os._exit(0)
    children.append(pid)
for pid in children:
    os.waitpid(pid, 0)
print(json.dumps({
    "cgroup": relative,
    "requested": requested,
    "created": len(children),
    "failure_errno": failure_errno,
    "pids_max": (base / "pids.max").read_text().strip(),
    "pids_events": (base / "pids.events").read_text(),
}))
```

### Source, line by line

- Imports provide JSON, process operations, argv, a short sleep, and kernel-file reads.
- The guard accepts only 1 through 64 requested children. Invalid input exits before creating any child.
- The membership lookup identifies this process's own cgroup as in 07.01.
- `children` holds only PIDs actually returned by successful forks. `failure_errno` begins as `None`, which JSON represents as `null`.
- `os.fork()` returns twice: zero in the child, the child's PID in the parent. A failed creation raises `OSError`; the parent records its errno and leaves the creation loop.
- The child sleeps 0.2 seconds and uses `os._exit(0)` to terminate directly. It does not continue into the parent's loop, output, or cleanup.
- The parent appends each child PID, then calls `os.waitpid(pid, 0)` for every one. The zero option requests an ordinary wait for that exact child.
- The output reports requested and created counts, any fork error, the local task ceiling, and the kernel's event counters. A reduced count without a controller event could have another cause.

## Exercise 1 - Apply the task ceiling

Define an exact registered identity for each run:

```bash
new_task_unit() {
  NE_UNIT="north-echo-$(id -u)-07-03-$(python3 -c 'import secrets; print(secrets.token_hex(4))').service"
  ../../scripts/labctl.py register-unit 07.03 "$NE_UNIT"
}
NE_DESCRIPTION="North Echo 07.03 workspace=$PWD"
```

The name uses the actual UID, this lesson's target, and a random suffix. Registration occurs before launch; the description must continue to identify this exact workspace. Stop if registration fails.

Predict whether a twelve-task ceiling permits twelve new children in addition to their parent:

```bash
new_task_unit
systemd-run --user --wait --pipe --collect --quiet --expand-environment=no \
  --unit="$NE_UNIT" --description="$NE_DESCRIPTION" \
  --property=RuntimeMaxSec=5s --property=TimeoutStopSec=1s \
  --property=MemoryMax=67108864 --property=MemorySwapMax=0 \
  --property=TasksMax=12 --property=CPUQuota=50% \
  -- /usr/bin/python3 "$PWD/fork_pressure.py" 64 > task-output.json
python3 -m json.tool task-output.json
```

### Line by line

- The service is a bounded, named user unit, with the same waiting, stream, collection, and literal-argument controls used earlier.
- Memory, swap, CPU, and runtime ceilings keep this short observation small.
- `TasksMax=12` controls `pids.max` for the entire unit.
- The program may request at most 64 children; the controller should refuse earlier.
- Captured JSON is parsed independently. Expect `pids_max` of `12`, fewer than 64 children, and a positive `max` count in `pids_events`. The parent is included in the limit, so do not expect twelve child slots.

## Exercise 2 - Compare the missing task property and repair it

Create a fresh unit and repeat with only TasksMax omitted, saving to `missing-task-limit.json`. The program's hard cap of 64 remains. A typical service default allows all 64; it may report a finite manager default rather than `max`. Preserve what your VM actually reports.

Restore TasksMax=12, create another fresh unit, and regenerate `task-output.json`. A successful Python exit did not distinguish the two policies; the effective ceiling and rejection event do.

## Exercise 3 - Verify the controller event, not just a configured number

```bash
python3 - <<'PY'
import errno
import json

result = json.load(open("task-output.json"))
events = dict(line.split() for line in result["pids_events"].splitlines())
assert result["pids_max"] == "12"
assert 0 < result["created"] < result["requested"] == 64
assert result["failure_errno"] == errno.EAGAIN
assert int(events["max"]) > 0
print("TASK LIMIT AND REJECTION EVENT: PASS")
PY
systemctl --user show "$NE_UNIT" --property=LoadState
```

The here-document supplies the displayed Python checker without shell expansion. It parses JSON and the event file's key/value lines, checks the actual ceiling, requires a reduced count, verifies the expected resource-unavailable errno, and requires a positive controller event. Each part excludes a different false explanation.

The completed exact unit should be explicitly absent after collection. Do not use a wildcard listing as proof that you identified and checked this particular unit.

## Exercise 4 - Separate client timeout from service cleanup

Use a harmless sleeping service to practice the failure path. No pressure program is needed:

```bash
new_task_unit
NE_CLIENT_STATUS=0
timeout 1s systemd-run --user --wait --pipe --collect --quiet --expand-environment=no \
  --unit="$NE_UNIT" --description="$NE_DESCRIPTION" \
  --property=RuntimeMaxSec=5s --property=TimeoutStopSec=1s \
  --property=KillMode=control-group --property=MemoryMax=33554432 \
  --property=MemorySwapMax=0 --property=TasksMax=4 --property=CPUQuota=50% \
  -- /usr/bin/sleep 4 || NE_CLIENT_STATUS=$?
printf 'client status=%s\n' "$NE_CLIENT_STATUS"
systemctl --user show "$NE_UNIT" --property=LoadState --property=Description --property=ControlGroup
../../lab-cleanup 07.03 --dry-run
../../lab-cleanup 07.03
systemctl --user show "$NE_UNIT" --property=LoadState
```

### Line by line

- `timeout 1s` bounds the client, not the user manager's service. GNU timeout normally reports 124 when its deadline expires.
- The service has an independent five-second runtime backstop, a one-second stop timeout, and whole-cgroup stop behavior.
- `sleep 4` is fixed, local, and harmless. It may still be active when the client exits; depending on elapsed time and manager behavior, it may already have completed by inspection.
- The first `show` reads the exact unit's identity and cgroup without mutating it.
- The dry run plans cleanup against the registry; actual cleanup checks the exact name, workspace description, and delegated cgroup before stopping an active unit.
- The final inspection must show explicit absence. A failed ownership check means stop and investigate; never replace it with a wildcard kill or a global reset-failed command.

The exercise teaches a failure path, not a claim that a timed-out client always leaves a live service. Record the observed state. Both normal collection and a verified stop are valid cleanup outcomes; an unverified assumption is not.

## Bridge to the Python independent lab

You already used `subprocess.run` in Module 04. Its `timeout=` argument raises `subprocess.TimeoutExpired` if that direct child does not finish; the exception is different from a completed child's nonzero status. For a `systemd-run` child, your runner must also handle the separately managed service.

Construct the manager invocation as a list: executable, options, each `--property=NAME=VALUE` string, `--`, then the original command elements. Python's `*command` expands that list's elements into another list without joining or reparsing them. Include `--expand-environment=no`, because the next layer otherwise has its own expansion rules.

Before invoking any service, validate the specification. JSON numbers can become integers, while JSON booleans become Python booleans; `isinstance(True, int)` is true in Python. Reject booleans explicitly for numeric limits. Practice this check in the interpreter:

```bash
python3 -c 'print(isinstance(True, int)); print(isinstance(50, int) and not isinstance(50, bool) and 10 <= 50 <= 100)'
```

The first printed `True` exposes the surprising type relationship. The second demonstrates an actual integer/range check. Use the lab's stated bounds and validate all fields before creating a service or result file.

For cleanup, a generated name is only one part of ownership. The lesson's registry records it before launch; the course cleanup additionally verifies Description and ControlGroup. The independent runner must retain its own exact run identity and verify those properties before requesting a stop. `systemctl --user show EXACT_UNIT --property=LoadState --property=Description --property=ControlGroup` supplies the observations; explicit `not-found` differs from an inspection failure. Do not infer permission to stop anything from a name prefix alone.

## Checkpoint, troubleshooting, and replay

Explain why a fork error plus a positive pids event is stronger evidence than a small child count. Then explain why timing out a launch client is not sufficient cleanup of a service. Repeat the exact-unit inspection after the timeout exercise.

If the child count is zero or errno is unexpected, inspect the service result and parent limits before interpreting it as task-controller enforcement. Never increase the hard cap or run a fork bomb. If cleanup cannot verify ownership, retain the registry and use its diagnostic rather than bypassing the check.

Return with `cd ../..`; `./lab-reset 07.03` removes the lesson workspace and fixtures after verified cleanup. Keep any notes first.

## Source truth

The kernel's [cgroup v2 PID-controller guide](https://docs.kernel.org/admin-guide/cgroup-v2.html) defines pids.max and pids.events. [Python process APIs](https://docs.python.org/3.14/library/os.html) document fork/wait; [subprocess](https://docs.python.org/3.14/library/subprocess.html) documents timeout behavior. In the VM, `man systemd-run`, `man systemd.kill`, and `man timeout` distinguish client lifetime, service lifetime, and whole-cgroup stopping.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-07-cgroups/lab/README.md format=markdown -->
# Module 07 independent lab - Bounded transient runner

Implement `resource_runner.py`, a bounded transient user-service runner.

## Prepare the independent workspace

Complete 07.01-07.03 first. CPU state and user-service options were practiced in 07.01, memory/swap limits and specific failure evidence in 07.02, and task limits, exact ownership, client timeouts, and validation in 07.03. Structured subprocess results come from Module 04.

From the course root:

```bash
./lab-start module-07
cd .student/07.lab
pwd
ls -l resource_runner.py sample-spec.json
cat resource_runner.py
cat sample-spec.json
nano resource_runner.py
```

The commands prepare and enter your student copy, display both interface files, and open the implementation for editing. Save with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. No C compile is needed. The starter below is deliberately incomplete, not a combined solution:

```python
#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    run = subprocess.run(spec["command"], text=True, capture_output=True, check=False)
    Path(sys.argv[2]).write_text(
        json.dumps({"status": run.returncode, "stdout": run.stdout, "stderr": run.stderr}) + "\n",
        encoding="utf-8",
    )
    return run.returncode != 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Its imports, argv guard, JSON parsing, subprocess call, and JSON result writing use familiar interfaces. The direct subprocess receives no service or cgroup setup. `return run.returncode != 0` becomes a Boolean status: false maps to 0 and true maps to 1. The result field retains the child's more specific code. Preserve that distinction while adding the resource boundary.

## Contract

The grader invokes:

```text
python3 resource_runner.py SPEC.json RESULT.json
```

The specification contains a nonempty `command` string array whose first element is an absolute executable path, plus integer `memory_max`, `tasks_max`, and `cpu_percent` fields. Reject booleans as numeric limits. Accept only 16-256 MiB inclusive for memory (in bytes), 4-64 tasks inclusive, and 10-100 CPU percent inclusive. Validate every field before starting a service or creating the requested result file.

Launch the exact argv in a uniquely named transient systemd user service. Set `MemoryMax`, `MemorySwapMax=0`, `TasksMax`, and `CPUQuota`; use `CPUQuotaPeriodSec=100ms` to make the quota/period contract explicit. Use `--wait`, `--pipe`, and `--collect` so completion is synchronous and failed units can be collected. Include `--expand-environment=no`: even without a shell, systemd otherwise expands variable references in command arguments. Add a bounded service runtime and stop timeout as backstops; they do not replace client timeout handling.

Use the owned naming shape `north-echo-UID-07-lab-RANDOM.service`, with the actual numeric UID and 8-32 lowercase hexadecimal characters in RANDOM. Give it a description identifying this run's workspace, keep an exact ownership record before launch, and verify Description plus the delegated ControlGroup before stopping it. The course cleanup convention is `North Echo 07.lab workspace=ABSOLUTE_WORKSPACE`. A name prefix alone is not proof of ownership. The grader evaluates a copy from a separate directory; derive the active workspace rather than hard-coding your original student path.

The result must be one JSON object containing integer `status` and string `stdout`/`stderr`. Preserve nonzero workload status. If your own timeout or setup fails, stop the exact owned unit before returning. Never use a shell, `sudo`, a system unit, or an unbounded resource value.

The starter runs argv directly, so function succeeds but every effective-limit property fails. The fresh external grader checks the child's real `cpu.max`, `memory.max`, `memory.swap.max`, and `pids.max`, an argv literal, bounded process creation, invalid-spec denial, failure propagation, and post-run unit collection.

```bash
python3 resource_runner.py sample-spec.json result.json
python3 -m json.tool result.json
../../lab-grade module-07
../../lab-grade module-07 --mode exam
```

### Test commands, line by line

- The first command exercises the two-file interface; the checked-in sample uses only `/bin/echo`.
- `json.tool` proves the result is valid JSON rather than trusting display text.
- Practice and exam modes run the same kernel properties with different hint detail.

The lab withholds a complete implementation. Reuse the structured subprocess, unit naming, property ordering, timeout cleanup, and effective-state observations practiced in the guided lessons.

## Verify and replay

Run the starter first and distinguish functional success from missing limits. Then test a successful small command, a command that exits nonzero, malformed limits, and literal arguments containing spaces and dollar-variable syntax. Do not add a shell to make quoting easier.

A passing grader demonstrates its stated kernel observations; it does not exhaustively prove every timeout race or ownership-error path. Explain how your runner handles an inspection error without stopping an unverified unit. Never use wildcard teardown, a system unit, or a global cgroup write.

From the workspace, `cd ../..` returns to the course root. `./lab-reset module-07` discards this module's student work and fixtures after confirmation and owned cleanup. Save notes before replaying. See the guided lessons' kernel and installed systemd references for the mechanisms behind this contract.
<!-- /source -->

<!-- source: course/module-08-network-egress/README.md format=markdown -->
# Module 08 - Isolate the network and mediate egress

Remove the workload's inherited IP network, then expose only a narrow HTTP capability through a filesystem Unix socket. The broker uses an explicit synthetic name-to-loopback map, binds requests to a run identity, and authorizes every redirect again.

Play in order: `08.01`, `08.02`, `08.03`, then `module-08`.

Outcomes:

- prove a new network namespace starts with loopback down and cannot reach a service on host loopback;
- distinguish removing direct IP connectivity from authorizing one mediated operation;
- carry a structured request over `AF_UNIX` without restoring an IP route;
- authorize a synthetic hostname, resolved address, port, path shape, and run identity;
- reauthorize redirects before contacting their destinations;
- bound request and response sizes and cleanly remove the broker socket.

All services are synthetic and bind only to `127.0.0.1`. The exercises do not create veth devices, routes, firewall rules, DNS traffic, or public requests. Prerequisites are Modules 01-07 and Linux support for unprivileged user plus network namespaces.

## Learning route and limits

Begin with a working connection before removing the network view. Otherwise a stopped server could look like successful isolation. Next separate direct connectivity from a permitted broker operation. Finally follow a redirect through a fresh authorization decision and compare correct enforcement with an incorrectly broad policy.

The network namespace, Unix-socket pathname, policy file, and broker process are different parts of the design. Be able to point to the decision each controls. A run ID is a context label, not authentication; mode 0600 does not isolate same-account processes; these small HTTP fixtures are not production services.

Each lesson includes exact preparation commands, complete sources, observations, a deliberate mistake and repair, and registered cleanup. Keep the resource limits and runtime backstops from Module 07. Do not disable SELinux to make a demonstration work.

Readiness for the independent lab means you can explain why a parser is not an authorizer, why an allowed first hop does not authorize a redirect, and why absence of a protected body is weaker evidence than measuring that no protected request occurred.
<!-- /source -->

---

<!-- source: course/module-08-network-egress/lesson-01/README.md format=markdown -->
# 08.01 - Remove the inherited IP network

## Outcomes and prerequisites

Complete Modules 01-07 first. You will compare network namespace identities, distinguish parent and private loopback, and observe a synthetic service through a working baseline before testing isolation.

## Concepts before commands

An IP **address** identifies an endpoint in a network context; a **port** identifies a transport service at that address. TCP provides a stream of bytes, not one message per receive call. HTTP gives those bytes a request/response structure. We use a tiny fixed HTTP response only to distinguish the intended service from an unrelated open port.

`127.0.0.1` is **loopback**: it refers to the current network namespace, not universally to your VM or Mac. A new network namespace gets its own interfaces and routes. Its loopback interface initially exists but is down. Enabling that interface does not connect it to the parent's loopback.

In this chapter, the parent environment is the disposable Linux VM. Every service binds only to its loopback address. No public address, LAN target, real credential, DNS query, route, or firewall change is part of the lesson.

## Prepare and read both programs

From the course root in the VM:

```bash
./lab-start 08.01
cd .student/08.01
pwd
ls -l local_http.py connect_probe.py
cat local_http.py
cat connect_probe.py
```

The commands prepare, enter, locate, and display the student sources. You can open either with `nano` and its exact filename, but no edit is required for the baseline. Do not start the server until you have read how it stops.

### The one-response service

```python
#!/usr/bin/env python3
"""One bounded synthetic HTTP response on loopback."""

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import signal
import sys


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"synthetic-loopback-service\n"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_arguments):
        pass


def stop(_signum, _frame):
    raise SystemExit(0)


if len(sys.argv) != 3:
    raise SystemExit(f"usage: {sys.argv[0]} PORT READY_FILE")
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
ready = Path(sys.argv[2])
if ready.exists() or ready.is_symlink():
    raise SystemExit("ready path already exists")
server = HTTPServer(("127.0.0.1", int(sys.argv[1])), Handler)
server.timeout = 300
ready.write_text("ready\n", encoding="utf-8")
try:
    server.handle_request()
finally:
    server.server_close()
    ready.unlink(missing_ok=True)
```

### Source, line by line

- `HTTPServer` supplies HTTP connection handling; `BaseHTTPRequestHandler` supplies the request parser and response methods.
- `class Handler(BaseHTTPRequestHandler)` defines a specialized handler. Python calls its `do_GET` method for an HTTP GET request; `self` is that handler instance.
- The `b` prefix creates bytes. Content-Length counts those bytes, not characters in an arbitrary Unicode string.
- `send_response`, `send_header`, and `end_headers` write the response metadata before `wfile.write` writes the body.
- Overriding `log_message` with `pass` suppresses routine request logs; it does not change policy.
- The stop handler raises `SystemExit` for SIGTERM/SIGINT so normal Python cleanup runs. SIGKILL cannot run such cleanup.
- The argv guard requires a port and readiness path. Refusing an existing path avoids silently replacing earlier evidence.
- Binding to `127.0.0.1` keeps the service in the parent namespace's loopback environment. Only after a successful bind does the program write readiness.
- `handle_request` handles at most one request. Its idle timeout and the service runtime limit below keep it bounded.
- `finally` closes the server and removes the readiness file on normal completion or handled termination.

### The connection observer

```python
#!/usr/bin/env python3
"""Attempt one TCP connection and report the network namespace identity."""

import json
import os
import socket
import sys

if len(sys.argv) != 2:
    raise SystemExit(f"usage: {sys.argv[0]} PORT")

result = {
    "network_namespace": os.readlink("/proc/self/ns/net"),
    "connected": False,
}
try:
    with socket.create_connection(("127.0.0.1", int(sys.argv[1])), timeout=1) as stream:
        stream.sendall(b"GET / HTTP/1.0\r\nHost: synthetic.test\r\n\r\n")
        response = bytearray()
        while len(response) < 8192:
            chunk = stream.recv(min(1024, 8192 - len(response)))
            if not chunk:
                break
            response.extend(chunk)
        body = bytes(response).split(b"\r\n\r\n", 1)[-1]
        result["connected"] = body == b"synthetic-loopback-service\n"
except OSError as error:
    result["error"] = f"{type(error).__name__}: {error}"
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if result["connected"] else 1)
```

### Source, line by line

- The initial dictionary records the observer's kernel-reported network namespace and starts with no successful observation.
- `socket.create_connection` makes one time-bounded TCP connection to the supplied local port.
- The byte request includes an HTTP method, path, version, Host header, and the blank line ending the headers. The synthetic Host string is not a DNS lookup.
- `sendall` sends the complete small request or raises an error.
- The receive loop collects at most 8 KiB. It stops on end-of-stream and does not assume one TCP receive contains the whole response.
- Splitting at the header/body separator locates the fixed response body. Exact body equality establishes that the expected synthetic service answered, not just that a port accepted a connection.
- `except OSError` records connection/timeout failure. The final exit status is 0 only when the expected body was observed.

This is a bounded observer for the supplied HTTP/1.0 fixture, not a general HTTP client or a proof about every possible network path.

## Exercise 1 - Register and start a working parent service

Reuse Module 07's owned user-unit lifecycle. Define the following helper in this shell:

```bash
start_network_service() {
  NE_UNIT="north-echo-$(id -u)-08-01-$(python3 -c 'import secrets; print(secrets.token_hex(4))').service"
  ../../scripts/labctl.py register-unit 08.01 "$NE_UNIT" || return
  systemd-run --user --collect --quiet --expand-environment=no --service-type=exec \
    --unit="$NE_UNIT" --description="North Echo 08.01 workspace=$PWD" \
    --property=RuntimeMaxSec=300s --property=TimeoutStopSec=2s \
    --property=MemoryMax=67108864 --property=MemorySwapMax=0 \
    --property=TasksMax=16 --property=CPUQuota=50% -- "$@"
}
NE_PORT=$((42000 + $$ % 10000))
NE_READY="$PWD/server.ready"
```

### Line by line

- The helper creates and registers an exact lesson-owned name before starting anything.
- Unlike 07.01's foreground observation, this service has no `--wait` or `--pipe`: it must remain available while you run a separate client. Its output goes to the user journal.
- `--service-type=exec` makes startup wait until the executable has been invoked; a readiness file still proves the later bind completed.
- Literal argv, exact description, resource limits, and a five-minute runtime backstop are retained.
- `"$@"` forwards the helper's supplied executable and arguments without joining them.
- Shell arithmetic selects a high port. It is a candidate, not a reservation; a collision must be diagnosed.
- The readiness path stays inside this prepared workspace.

Start the service and wait only a bounded time for readiness:

```bash
start_network_service /usr/bin/python3 "$PWD/local_http.py" "$NE_PORT" "$NE_READY"
for attempt in {1..50}; do test -f "$NE_READY" && break; sleep 0.1; done
test -f "$NE_READY"
readlink /proc/self/ns/net
python3 connect_probe.py "$NE_PORT" > parent-result.json
python3 -m json.tool parent-result.json
../../lab-cleanup 08.01
```

The loop allows up to five seconds for the server-created file, not an indefinite sleep. If readiness fails, stop before the client and inspect `journalctl --user -u "$NE_UNIT" --no-pager`; do not interpret a missing server as isolation. The parent result must report `connected: true` and status 0. Cleanup collects/stops only registered, verified units. The one-request server should already have exited.

## Exercise 2 - Test the new network namespace

Predict which namespace handle and connection result should change:

```bash
start_network_service /usr/bin/python3 "$PWD/local_http.py" "$NE_PORT" "$NE_READY"
for attempt in {1..50}; do test -f "$NE_READY" && break; sleep 0.1; done
test -f "$NE_READY"
NE_ISOLATED_STATUS=0
unshare --user --map-root-user --net /usr/bin/python3 connect_probe.py "$NE_PORT" \
  > isolated-result.json || NE_ISOLATED_STATUS=$?
python3 -m json.tool isolated-result.json
printf 'isolated status=%s\n' "$NE_ISOLATED_STATUS"
../../lab-cleanup 08.01
```

`--user --map-root-user` supplies namespace-local setup authority; `--net` creates the different network view. The quoted-free executable and arguments are still separate words. The expected failed probe's status is saved without changing interactive shell error options.

Expect a different `net:[NUMBER]`, `connected: false`, and a nonzero status. Error wording may mention an unreachable network; it is not the proof by itself. Parent readiness, a successful previous baseline, changed namespace identity, and the failed bounded connection are the evidence together.

## Exercise 3 - Repair the misconception about loopback

The intentional mistake is assuming that bringing up private loopback restores access to the parent's service. Test it without adding any external network path:

```bash
start_network_service /usr/bin/python3 "$PWD/local_http.py" "$NE_PORT" "$NE_READY"
for attempt in {1..50}; do test -f "$NE_READY" && break; sleep 0.1; done
test -f "$NE_READY"
NE_LOOPBACK_STATUS=0
unshare --user --map-root-user --net sh -c \
  'ip link set lo up && ip -brief address show lo >&2 && exec /usr/bin/python3 connect_probe.py "$1"' \
  namespace-observer "$NE_PORT" > private-loopback-result.json || NE_LOOPBACK_STATUS=$?
python3 -m json.tool private-loopback-result.json
printf 'private loopback status=%s\n' "$NE_LOOPBACK_STATUS"
../../lab-cleanup 08.01
```

The shell program is single-quoted so the outer shell does not consume `$1`. The next word supplies its `$0`; the port becomes `$1`, as practiced in 02.02. `&&` stops if namespace-local interface setup fails. Interface display goes to stderr so stdout remains one JSON document. Only this new namespace's loopback is changed.

The connection still fails, commonly with connection refused. Repair the mental model: private loopback reaches this namespace, not its parent. Lesson 08.02 will introduce a filesystem-mediated channel instead of restoring general IP connectivity.

## Checkpoint, troubleshooting, and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

parent = json.loads(Path("parent-result.json").read_text())
for name in ("isolated-result.json", "private-loopback-result.json"):
    child = json.loads(Path(name).read_text())
    assert parent["connected"] is True
    assert child["connected"] is False
    assert child["network_namespace"] != parent["network_namespace"]
print("NETWORK VIEW AND CONNECTION EVIDENCE: PASS")
PY
test ! -e "$NE_READY"
```

The checker compares parsed observations, not a locale-dependent error message. A failed `unshare` produces no valid child observation and cannot pass. After owned cleanup, the readiness path must be absent. If a forced termination leaves stale evidence, use lesson reset after verifying unit cleanup; do not blindly remove arbitrary socket/readiness paths.

If you waited beyond the service's runtime backstop, recreate the service before testing. If the port is already bound, choose another high port and repeat the working baseline. Never change host routes, firewall policy, or SELinux enforcement for this exercise.

Return with `cd ../..`; `./lab-reset 08.01` discards this lesson's work after verified cleanup. Save notes first.

## Source truth

[network_namespaces(7)](https://man7.org/linux/man-pages/man7/network_namespaces.7.html) describes isolated network state. Python's [socket documentation](https://docs.python.org/3.14/library/socket.html) describes stream reads and timeouts; [http.server](https://docs.python.org/3.14/library/http.server.html) describes the synthetic server API, which is not recommended as a production web server.
<!-- /source -->

---

<!-- source: course/module-08-network-egress/lesson-02/README.md format=markdown -->
# 08.02 - Reach one service through a Unix-socket broker

## Outcomes and prerequisites

Complete 08.01 first. You will keep a workload's IP network isolated, send one structured request over a different channel, and distinguish possession of a socket pathname from permission to perform an operation. Reuse Module 07's owned service lifecycle.

## Concepts before commands

A **broker** is a separate process that holds authority the caller does not hold. Here the broker can contact one VM-loopback HTTP service. The caller can ask for one operation; it cannot choose an arbitrary destination or supply a shell command.

`AF_UNIX` means local interprocess communication rather than IP networking. This lesson uses a **pathname socket** in the shared student workspace. A new network namespace does not hide that pathname. Linux's **abstract** Unix-socket namespace is different and is isolated by network namespaces; do not generalize this result to every Unix socket.

Mode `0600` limits access to the owning account on Linux. It does not separate two processes running as that same account. The run ID is a context-binding field, not a secret credential or proof of who sent the request. These limits matter: this is a small mediation demonstration, not a complete multi-user authentication system.

Predict: should an isolated caller reach the HTTP service directly? Should it reach the pathname socket? Which process makes the eventual TCP connection?

## Prepare and read all three programs

From the course root in the VM:

```bash
./lab-start 08.02
cd .student/08.02
pwd
ls -l synthetic_http.py one_host_broker.py broker_client.py
cat synthetic_http.py
cat one_host_broker.py
cat broker_client.py
```

These commands create the working copy, enter it, and display each source. Use `nano one_host_broker.py` if you want to inspect it interactively; no source edit is required.

### The synthetic upstream service

```python
#!/usr/bin/env python3
"""Serve synthetic content on host loopback until interrupted."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import signal
import sys


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"approved-through-broker\n"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_arguments):
        pass


def stop(_signum, _frame):
    raise SystemExit(0)


if len(sys.argv) != 3:
    raise SystemExit(f"usage: {sys.argv[0]} PORT READY_FILE")
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
ready = Path(sys.argv[2])
if ready.exists() or ready.is_symlink():
    raise SystemExit("ready path already exists")
server = ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), Handler)
ready.write_text("ready\n", encoding="utf-8")
try:
    server.serve_forever()
finally:
    server.server_close()
    ready.unlink(missing_ok=True)
```

### Source, line by line

- The HTTP imports, handler class, response headers, byte body, and quiet logging repeat 08.01.
- `ThreadingHTTPServer` can handle separate requests in separate threads. The small fixed body is synthetic, not a credential.
- The argument guard requires a port and readiness filename. Existing files or dangling symlinks cause refusal before bind.
- The literal address confines the listener to parent-namespace loopback.
- Readiness is written only after the server binds. A failed bind cannot masquerade as a ready fixture.
- `serve_forever` continues until stopped. SIGTERM/SIGINT raise `SystemExit`, allowing `finally` to close the server and remove readiness.
- That cleanup is cooperative: SIGKILL or a crash can leave evidence behind. We verify cleanup rather than assuming it.

### The one-request broker

```python
#!/usr/bin/env python3
"""A one-request Unix-socket broker for one exact synthetic destination."""

import http.client
import json
import os
from pathlib import Path
import socket
import signal
import sys


def stop(_signum, _frame):
    raise SystemExit(0)


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)

if len(sys.argv) != 5:
    raise SystemExit(f"usage: {sys.argv[0]} SOCKET RUN_ID HOST PORT")
socket_path, allowed_run, allowed_host, port_text = sys.argv[1:]
allowed_port = int(port_text)
path = Path(socket_path)
if path.exists() or path.is_symlink():
    raise SystemExit("socket path already exists")

listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
listener.bind(socket_path)
os.chmod(socket_path, 0o600)
listener.listen(1)
listener.settimeout(300)
try:
    peer, _ = listener.accept()
    with peer:
        peer.settimeout(2)
        with peer.makefile("rb") as incoming:
            line = incoming.readline(8193)
        if len(line) > 8192 or not line.endswith(b"\n"):
            raise ValueError("request must be one bounded JSON line")
        request = json.loads(line)
        if request != {"run_id": allowed_run, "host": allowed_host, "port": allowed_port, "path": "/ok"}:
            response = {"ok": False, "error": "request is not authorized"}
        else:
            connection = http.client.HTTPConnection("127.0.0.1", allowed_port, timeout=2)
            connection.request("GET", "/ok", headers={"Host": allowed_host})
            upstream = connection.getresponse()
            raw_body = upstream.read(65537)
            connection.close()
            if len(raw_body) > 65536:
                raise ValueError("response body exceeds limit")
            body = raw_body.decode("utf-8", "replace")
            response = {"ok": True, "status": upstream.status, "body": body}
        peer.sendall(json.dumps(response, sort_keys=True).encode() + b"\n")
finally:
    listener.close()
    path.unlink(missing_ok=True)
```

### Source, line by line

- `socket_path, allowed_run, allowed_host, port_text` unpack four arguments. Converting the port makes the policy value an integer.
- Refusing an existing path avoids overwriting another socket or stale lesson evidence.
- `AF_UNIX, SOCK_STREAM` creates a local byte-stream listener. `bind` creates its pathname; `chmod` restricts account access; `listen(1)` enables accepting a connection.
- `accept` returns a new connected socket, `peer`. The listener and the connected peer are distinct descriptors.
- The listener's 300-second idle timeout is a teaching convenience. The peer's two-second timeout bounds an individual blocking operation, not an absolute whole-session deadline.
- `makefile("rb")` exposes a binary reader over the peer. `readline(8193)` permits detecting a request exceeding the 8192-byte limit. Requiring a newline supplies the JSON framing practiced in Module 04.
- `json.loads` turns the line into Python data. Equality against the fixed dictionary requires the same fields and values; an extra field is not silently accepted.
- The rejected branch constructs a denial and never calls `HTTPConnection`. Only the accepted branch contacts literal loopback.
- The synthetic hostname is an HTTP Host header, not a DNS lookup. The caller cannot change the actual connection address.
- `read(65537)` detects a body larger than 65536 bytes. Decoding with replacement handles non-UTF-8 bytes for display, not as a policy decision.
- `sendall` returns one newline-terminated JSON response. The outer `finally` closes the listener and removes its exact socket.
- There is only **one** `accept`, not a loop. Both a successful request and a denied request consume this broker instance. Invalid JSON can terminate it without a structured response; 08.03 adds reusable request handling.

### The isolated client

```python
#!/usr/bin/env python3
"""Send one structured request to a filesystem Unix socket."""

import json
import socket
import sys

if len(sys.argv) != 6:
    raise SystemExit(f"usage: {sys.argv[0]} SOCKET RUN_ID HOST PORT PATH")
request = {
    "run_id": sys.argv[2],
    "host": sys.argv[3],
    "port": int(sys.argv[4]),
    "path": sys.argv[5],
}
with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
    stream.settimeout(12)
    stream.connect(sys.argv[1])
    stream.sendall(json.dumps(request, sort_keys=True).encode() + b"\n")
    stream.shutdown(socket.SHUT_WR)
    with stream.makefile("rb") as incoming:
        line = incoming.readline(524289)
    if len(line) > 524288 or not line.endswith(b"\n"):
        raise SystemExit("response must be one bounded JSON line")
    response = json.loads(line)
    if not isinstance(response, dict) or type(response.get("ok")) is not bool:
        raise SystemExit("invalid response shape")
    print(json.dumps(response, sort_keys=True))
raise SystemExit(0 if response["ok"] else 1)
```

### Source, line by line

- The argument guard requires socket, run ID, host, port, and path. JSON preserves the integer port rather than flattening the request into command text.
- A `with` block closes the Unix socket on exit. Its timeout prevents an indefinitely idle call.
- `connect` uses the socket pathname; `sendall` sends the complete request plus its delimiter.
- `shutdown(SHUT_WR)` declares that no more request bytes will be sent while retaining the read direction.
- The bounded response read limits memory used by this small client. The response must be a dictionary with an actual Boolean `ok`.
- The printed JSON is normalized for inspection. Exit status 0 means `ok: true`; status 1 means denial or another client failure. Inspect the JSON as well as the status.

## Exercise 1 - Start registered, bounded services

Define the helper and lesson-local names:

```bash
start_broker_service() {
  NE_UNIT="north-echo-$(id -u)-08-02-$(python3 -c 'import secrets; print(secrets.token_hex(4))').service"
  ../../scripts/labctl.py register-unit 08.02 "$NE_UNIT" || return
  systemd-run --user --collect --quiet --expand-environment=no --service-type=exec \
    --unit="$NE_UNIT" --description="North Echo 08.02 workspace=$PWD" \
    --property=RuntimeMaxSec=300s --property=TimeoutStopSec=3s \
    --property=MemoryMax=67108864 --property=MemorySwapMax=0 \
    --property=TasksMax=16 --property=CPUQuota=50% -- "$@"
}
NE_PORT=$((43000 + $$ % 9000))
NE_RUN="lesson-$$"
NE_SOCKET="$PWD/broker.sock"
NE_READY="$PWD/service.ready"
```

The helper registers ownership before launch, preserves literal argv, and retains Module 07's runtime and resource backstops. No `--wait` is used because the service must remain available for another command. The run label uses this shell's PID to distinguish this exercise; it is not a cryptographic identity.

Launch both components:

```bash
start_broker_service /usr/bin/python3 "$PWD/synthetic_http.py" "$NE_PORT" "$NE_READY"
NE_HTTP_UNIT="$NE_UNIT"
start_broker_service /usr/bin/python3 "$PWD/one_host_broker.py" "$NE_SOCKET" "$NE_RUN" allowed.test "$NE_PORT"
NE_BROKER_UNIT="$NE_UNIT"
for attempt in {1..50}; do test -S "$NE_SOCKET" && test -f "$NE_READY" && break; sleep 0.1; done
test -S "$NE_SOCKET"
test -f "$NE_READY"
test "$(stat -c '%a' "$NE_SOCKET")" = 600
```

Save each unit name for diagnosis. The bounded readiness loop checks an actual socket and the upstream's ready file. `stat` checks the effective mode. If any test fails, stop here: inspect the exact units with `journalctl --user -u "$NE_HTTP_UNIT" -u "$NE_BROKER_UNIT" --no-pager`, then run owned cleanup.

## Exercise 2 - Compare direct and mediated access

```bash
NE_DIRECT_STATUS=0
unshare --user --map-root-user --net /usr/bin/python3 -c \
  'import socket,sys; socket.create_connection(("127.0.0.1",int(sys.argv[1])),1)' \
  "$NE_PORT" || NE_DIRECT_STATUS=$?
test "$NE_DIRECT_STATUS" -ne 0
unshare --user --map-root-user --net /usr/bin/python3 broker_client.py \
  "$NE_SOCKET" "$NE_RUN" allowed.test "$NE_PORT" /ok > approved.json
python3 -m json.tool approved.json
../../lab-cleanup 08.02
test ! -e "$NE_SOCKET"
test ! -e "$NE_READY"
```

The first command cannot reach the parent namespace's listener. A connection traceback is expected; a failed `unshare` is not evidence of network isolation. The second command uses the same namespace-creation flags but reaches the pathname socket. Its successful JSON demonstrates that namespace creation and the mediated path both work.

The expected body is `approved-through-broker\n`. The broker, not the isolated caller, opens the IP connection. Owned cleanup stops any remaining registered service and checks its identity; it does not kill by a guessed PID or name prefix.

## Exercise 3 - Deliberate wrong-run request, then repair

Repeat **only the launch block** from Exercise 1 to create fresh services. Send an otherwise valid request with a wrong context:

```bash
NE_DENIED_STATUS=0
unshare --user --map-root-user --net /usr/bin/python3 broker_client.py \
  "$NE_SOCKET" wrong-run allowed.test "$NE_PORT" /ok > denied.json || NE_DENIED_STATUS=$?
python3 -m json.tool denied.json
test "$NE_DENIED_STATUS" -eq 1
../../lab-cleanup 08.02
test ! -e "$NE_SOCKET"
test ! -e "$NE_READY"
```

Expect `ok: false` and `request is not authorized`. Reading the rejected branch explains why this implementation does not contact the upstream for that request. A missing body alone would not prove absence of contact.

The denied call consumed the one-shot broker. Merely retrying against its removed socket is **not** a repair. Repeat the launch block again, then restore the correct run value:

```bash
unshare --user --map-root-user --net /usr/bin/python3 broker_client.py \
  "$NE_SOCKET" "$NE_RUN" allowed.test "$NE_PORT" /ok > repaired.json
../../lab-cleanup 08.02
```

## Checkpoint, troubleshooting, and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

for name in ("approved.json", "repaired.json"):
    result = json.loads(Path(name).read_text())
    assert result["ok"] is True
    assert result["status"] == 200
    assert result["body"] == "approved-through-broker\n"
denied = json.loads(Path("denied.json").read_text())
assert denied["ok"] is False
assert denied["error"] == "request is not authorized"
print("DIRECT DENIAL AND MEDIATED REPAIR: PASS")
PY
test "$NE_DIRECT_STATUS" -ne 0
test ! -e "$NE_SOCKET"
test ! -e "$NE_READY"
```

Explain which process held IP authority and why socket permission alone did not authorize the operation. An absent socket after a request is normal for this one-shot broker. A pre-existing socket before launch requires verified cleanup/reset, not blind removal. A pathname that is too long cannot fit Linux's Unix-socket address; keep the course near your VM home, not deeply nested.

After a five-minute pause, the runtime backstop may have stopped a fixture. Clean up and relaunch instead of treating stale readiness as a successful test. Return with `cd ../..`; `./lab-reset 08.02` discards this workspace after owned cleanup.

## Source truth

Linux [unix(7)](https://man7.org/linux/man-pages/man7/unix.7.html) describes pathname sockets and their permissions; [network_namespaces(7)](https://man7.org/linux/man-pages/man7/network_namespaces.7.html) distinguishes abstract-socket isolation. Python's [socket API](https://docs.python.org/3.14/library/socket.html) supplies stream, shutdown, and timeout behavior. These explain the mechanism, not an authentication guarantee.
<!-- /source -->

---

<!-- source: course/module-08-network-egress/lesson-03/README.md format=markdown -->
# 08.03 - Reauthorize names, ports, redirects, and runs

## Outcomes and prerequisites

Complete 08.01 and 08.02. You will read a reusable broker, author a small synthetic destination policy, observe an allowed redirect, and verify that a changed destination needs a new authorization decision. You will also repair an overbroad policy by restarting the broker with a narrower one.

## Concepts before commands

An HTTP **redirect** is a response telling the client to try another URL. Status 302 plus a Location header does not grant authority to contact that location. A relative location such as `/ok` keeps the current origin; an absolute location can select a different hostname or port.

A URL contains a scheme, authority, path, and optional query/fragment. For `http://allowed.test:45123/ok?view=small`, the scheme is `http`, host is `allowed.test`, port is 45123, path is `/ok`, and query is `view=small`. A **parser** separates these pieces; it does not decide whether they are permitted.

This lesson's resolution policy maps a synthetic name to a literal IPv4 loopback address. No name is sent to a live DNS resolver. The HTTP Host header preserves the approved logical name while the actual connection uses the approved address. Name, address, and port must not become three unrelated decisions.

Keep the limits visible: the run ID is still a context label; mode 0600 does not distinguish same-account clients; the broker permits GET requests to allowed destinations, not arbitrary public browsing. All services remain inside this disposable VM.

## Prepare and read the programs

From the course root:

```bash
./lab-start 08.03
cd .student/08.03
pwd
ls -l egress_broker.py redirect_services.py broker_client.py
cat egress_broker.py
cat redirect_services.py
cat broker_client.py
```

Use `nano egress_broker.py` to navigate the source if desired. The exercises edit policy data, not the policy engine. Read all components before starting listeners.

### The reusable policy engine

```python
#!/usr/bin/env python3
"""Policy-bound loopback HTTP broker over a Unix-domain socket."""

from __future__ import annotations

import http.client
import ipaddress
import json
import os
from pathlib import Path
import signal
import socket
import sys
from urllib.parse import urljoin, urlsplit

MAX_LINE = 8192
MAX_BODY = 65536
MAX_REDIRECTS = 4
stopping = False


class Denied(Exception):
    pass


def load_policy(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or set(raw) != {"run_id", "destinations"} or not isinstance(raw["run_id"], str):
        raise Denied("invalid policy shape")
    if not raw["run_id"] or len(raw["run_id"]) > 128 or not isinstance(raw["destinations"], dict):
        raise Denied("invalid policy values")
    destinations = {}
    for host, rule in raw["destinations"].items():
        if not isinstance(host, str) or host != host.lower() or not host or len(host) > 253:
            raise Denied("invalid policy hostname")
        if not isinstance(rule, dict) or set(rule) != {"address", "ports"}:
            raise Denied("invalid destination rule")
        address = ipaddress.ip_address(rule["address"])
        if address.version != 4 or not address.is_loopback:
            raise Denied("only IPv4 loopback destinations are permitted")
        ports = rule["ports"]
        if not isinstance(ports, list) or not ports or any(type(p) is not int or not 1 <= p <= 65535 for p in ports):
            raise Denied("invalid destination ports")
        destinations[host] = {"address": str(address), "ports": frozenset(ports)}
    if not destinations:
        raise Denied("policy has no destinations")
    return {"run_id": raw["run_id"], "destinations": destinations}


def authorize(policy: dict, run_id: object, url: str) -> tuple[str, str, int, str]:
    if run_id != policy["run_id"]:
        raise Denied("run identity is not authorized")
    if any(ord(character) <= 32 or ord(character) == 127 for character in url):
        raise Denied("whitespace and control characters are not permitted")
    try:
        parsed = urlsplit(url)
    except ValueError as error:
        raise Denied("invalid destination URL") from error
    if parsed.scheme != "http" or parsed.username is not None or parsed.password is not None:
        raise Denied("only credential-free HTTP URLs are permitted")
    if parsed.fragment or not parsed.hostname:
        raise Denied("invalid destination URL")
    try:
        port = 80 if parsed.port is None else parsed.port
    except ValueError as error:
        raise Denied("invalid destination port") from error
    if not 1 <= port <= 65535:
        raise Denied("invalid destination port")
    rule = policy["destinations"].get(parsed.hostname)
    if rule is None or port not in rule["ports"]:
        raise Denied("destination is not authorized")
    request_path = parsed.path or "/"
    if not request_path.startswith("/") or request_path.startswith("//"):
        raise Denied("invalid request path")
    if parsed.query:
        request_path += "?" + parsed.query
    authority = parsed.hostname if port == 80 else f"{parsed.hostname}:{port}"
    return rule["address"], authority, port, request_path


def fetch(policy: dict, request: dict) -> dict:
    if not isinstance(request, dict) or set(request) != {"run_id", "host", "port", "path"}:
        raise Denied("invalid request shape")
    host, port, path = request["host"], request["port"], request["path"]
    if not isinstance(host, str) or type(port) is not int or not isinstance(path, str):
        raise Denied("invalid request values")
    if host not in policy["destinations"]:
        raise Denied("destination is not authorized")
    if not 1 <= port <= 65535 or not path.startswith("/") or path.startswith("//"):
        raise Denied("invalid request port or path")
    url = f"http://{host}:{port}{path}"
    for redirects in range(MAX_REDIRECTS + 1):
        address, authority, port, request_path = authorize(policy, request["run_id"], url)
        connection = http.client.HTTPConnection(address, port, timeout=2)
        try:
            connection.request("GET", request_path, headers={"Host": authority, "Connection": "close"})
            response = connection.getresponse()
            body = response.read(MAX_BODY + 1)
            if len(body) > MAX_BODY:
                raise Denied("response body exceeds limit")
            location = response.getheader("Location")
            status = response.status
        finally:
            connection.close()
        if status not in {301, 302, 303, 307, 308}:
            return {"ok": True, "status": status, "body": body.decode("utf-8", "replace"), "redirects": redirects}
        if not location:
            raise Denied("redirect has no location")
        url = urljoin(url, location)
    raise Denied("redirect limit exceeded")


def receive_line(peer: socket.socket) -> bytes:
    data = bytearray()
    while b"\n" not in data and len(data) <= MAX_LINE:
        chunk = peer.recv(min(1024, MAX_LINE + 1 - len(data)))
        if not chunk:
            break
        data.extend(chunk)
    if len(data) > MAX_LINE or not data.endswith(b"\n"):
        raise Denied("request must be one bounded line")
    return bytes(data)


def serve(policy: dict, socket_path: Path) -> None:
    if socket_path.exists() or socket_path.is_symlink():
        raise Denied("socket path already exists")
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    os.chmod(socket_path, 0o600)
    listener.listen(8)
    listener.settimeout(0.2)
    try:
        while not stopping:
            try:
                peer, _ = listener.accept()
            except TimeoutError:
                continue
            with peer:
                peer.settimeout(2)
                try:
                    request = json.loads(receive_line(peer))
                    response = fetch(policy, request)
                except (Denied, json.JSONDecodeError, UnicodeError, OSError, http.client.HTTPException) as error:
                    response = {"ok": False, "error": str(error)}
                try:
                    peer.sendall(json.dumps(response, sort_keys=True).encode() + b"\n")
                except OSError:
                    pass  # A disconnected client must not stop the listening service.
    finally:
        listener.close()
        socket_path.unlink(missing_ok=True)


def stop(_signum, _frame):
    global stopping
    stopping = True


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} POLICY.json SOCKET", file=sys.stderr)
        return 2
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        serve(load_policy(Path(sys.argv[1])), Path(sys.argv[2]))
    except (OSError, ValueError, json.JSONDecodeError, Denied) as error:
        print(f"broker setup denied: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### Source, block by block

- Imports separate HTTP transport, address classification, JSON, filesystem paths, signals, sockets, and URL parsing. None is a substitute for authorization.
- `MAX_LINE`, `MAX_BODY`, and `MAX_REDIRECTS` are explicit bounds. `Denied` is a distinct exception class so policy failures can become structured denials.
- `load_policy` parses the file before listening. `isinstance(raw, dict)` checks its container type; `set(raw)` compares its keys. Both are needed.
- Run IDs must be nonempty bounded strings. Each destination rule has exactly `address` and `ports`; unknown authority-bearing fields are not silently ignored.
- `ip_address` parses a literal address, not a hostname. Requiring version 4 and `is_loopback` keeps every permitted connection inside VM loopback.
- `type(p) is int` deliberately rejects Boolean values, which Python otherwise treats as integer subclasses. Every port must be within 1 through 65535.
- `frozenset` stores an immutable set for membership checks. The resulting in-memory policy is loaded **once at startup**, not reread on every request.
- `authorize` first checks the run value. It rejects whitespace/control characters before parsing because a URL parser can otherwise normalize some input.
- `urlsplit` separates the URL. Scheme, user information, fragment, hostname, effective port, and path shape are then checked explicitly.
- The parser's `hostname` property normalizes case. Policy keys are lowercase; do not claim that this property rejects uppercase characters in every incoming URL.
- An omitted port means 80; explicit port 0 is rejected, not silently replaced with 80.
- The destination lookup binds the parsed name to its stored loopback address and permitted ports. The returned tuple contains the exact address, controlled Host authority, port, and origin-form request path.
- `fetch` requires exactly the four request fields. It rejects unknown hosts before composing a URL and refuses paths beginning with `//`, which could be confused with an authority-bearing reference.
- Each loop iteration calls `authorize` **before** making a connection. `HTTPConnection` receives the approved literal address rather than resolving the supplied hostname.
- `try/finally` closes the HTTP connection even on errors. Reading one byte beyond the body limit detects oversize responses without unbounded allocation.
- Non-redirect responses return their actual HTTP status and body. Here `ok: true` means the broker completed an authorized exchange, not that every HTTP status is a successful application result.
- For redirect responses, `urljoin` constructs the next URL. It can change the origin; the next loop must authorize the result again. Four redirects may be followed; a further redirect is denied.
- `receive_line` accumulates a bounded byte sequence and requires its newline delimiter. It does not execute received strings.
- `serve` refuses an existing socket path, binds a mode-0600 listener, and repeatedly accepts one request per connection. Its short accept timeout lets the loop notice a stop request.
- Each peer gets a blocking-operation timeout. Expected input, policy, or upstream errors become `ok: false`. A disconnected client cannot terminate the service merely because its response cannot be delivered.
- The signal handler sets `stopping`; normal loop exit reaches `finally` and removes the socket. `main` loads policy before calling `serve`, so invalid policy cannot create a permissive listener.

These are small-message and per-operation limits, not a complete defense against all denial-of-service behavior. The service is sequential, has no general concurrent admission control, and does not enforce one absolute deadline across an entire redirect chain. Module 07's runtime/resource backstop remains important. Do not deploy this teaching server publicly.

### The two synthetic destinations

```python
#!/usr/bin/env python3
"""Synthetic allowed and protected HTTP services for redirect exercises."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import signal
import sys
import threading


def stop(_signum, _frame):
    raise SystemExit(0)


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)

if len(sys.argv) != 4:
    raise SystemExit(f"usage: {sys.argv[0]} ALLOWED_PORT PROTECTED_PORT READY_FILE")
allowed_port, protected_port = map(int, sys.argv[1:3])
ready = Path(sys.argv[3])
if ready.exists() or ready.is_symlink():
    raise SystemExit("ready path already exists")


class Allowed(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/same":
            self.send_response(302)
            self.send_header("Location", "/ok")
            self.end_headers()
        elif self.path == "/escape":
            self.send_response(302)
            self.send_header("Location", f"http://blocked.test:{protected_port}/secret")
            self.end_headers()
        else:
            body = b"allowed-final\n"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, _format, *_arguments):
        pass


class Protected(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"protected-service-must-not-be-read\n"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_arguments):
        pass


protected = ThreadingHTTPServer(("127.0.0.1", protected_port), Protected)
threading.Thread(target=protected.serve_forever, daemon=True).start()
allowed = ThreadingHTTPServer(("127.0.0.1", allowed_port), Allowed)
ready.write_text("ready\n", encoding="utf-8")
try:
    allowed.serve_forever()
finally:
    allowed.server_close()
    protected.shutdown()
    protected.server_close()
    ready.unlink(missing_ok=True)
```

### Source, line by line

- The argv guard takes two ports and a readiness path. Both servers bind only to `127.0.0.1`.
- `Allowed.do_GET` sends a relative redirect for `/same`, an absolute redirect to `blocked.test` for `/escape`, and otherwise a fixed allowed body.
- `Protected.do_GET` returns a different synthetic body. There is no real secret.
- The protected server runs in a daemon thread while the main thread runs the allowed server. They share a process but listen at distinct ports.
- The ready file is written after both binds succeed. A port collision is a setup failure, not a policy denial.
- SIGTERM/SIGINT request normal process exit. The `finally` block closes both servers, stops the background serving loop, and removes readiness.

### The bounded client

```python
#!/usr/bin/env python3
"""Send one JSON request to the lesson broker."""

import json
import socket
import sys

if len(sys.argv) != 6:
    raise SystemExit(f"usage: {sys.argv[0]} SOCKET RUN_ID HOST PORT PATH")
request = {"run_id": sys.argv[2], "host": sys.argv[3], "port": int(sys.argv[4]), "path": sys.argv[5]}
with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
    stream.settimeout(12)
    stream.connect(sys.argv[1])
    stream.sendall(json.dumps(request).encode() + b"\n")
    stream.shutdown(socket.SHUT_WR)
    with stream.makefile("rb") as incoming:
        line = incoming.readline(524289)
    if len(line) > 524288 or not line.endswith(b"\n"):
        raise SystemExit("response must be one bounded JSON line")
    response = json.loads(line)
    if not isinstance(response, dict) or type(response.get("ok")) is not bool:
        raise SystemExit("invalid response shape")
    print(json.dumps(response, sort_keys=True))
raise SystemExit(0 if response["ok"] else 1)
```

### Source, line by line

- This is the same structured Unix-socket exchange practiced in 08.02: separate typed fields, one JSON line, a write half-close, and a bounded response read.
- The socket pathname is the connection target. The `host` field is data submitted for broker authorization, not a client-side DNS lookup.
- The `ok` field must be a Boolean. Status 0 corresponds to an accepted exchange; status 1 requires inspecting the denial or error.
- Because this broker loops over connections, a denied request does not consume the whole server. Each client process still sends exactly one request.

## Exercise 1 - Author and inspect the resolution policy

```bash
NE_ALLOWED_PORT=$((44000 + $$ % 4000))
NE_PROTECTED_PORT=$((48000 + $$ % 4000))
NE_RUN="redirect-$$"
NE_SOCKET="$PWD/policy-broker.sock"
NE_READY="$PWD/services.ready"
python3 - "$NE_RUN" "$NE_ALLOWED_PORT" <<'PY'
import json
from pathlib import Path
import sys

policy = {"run_id": sys.argv[1], "destinations": {
    "allowed.test": {"address": "127.0.0.1", "ports": [int(sys.argv[2])]}
}}
Path("policy.json").write_text(json.dumps(policy, indent=2) + "\n")
PY
python3 -m json.tool policy.json
```

Shell arithmetic selects separate high-port ranges; it does not reserve ports. The single-quoted here-document delimiter preserves Python text; the two shell values arrive through argv. `json.dumps` serializes their types safely. `json.tool` checks syntax and displays the policy, but does not prove its destinations are appropriately narrow.

Predict what each request should do before launching anything: `/same` with the right run, `/escape` with the right run, and `/ok` with the wrong run.

## Exercise 2 - Launch registered services

```bash
start_policy_service() {
  NE_UNIT="north-echo-$(id -u)-08-03-$(python3 -c 'import secrets; print(secrets.token_hex(4))').service"
  ../../scripts/labctl.py register-unit 08.03 "$NE_UNIT" || return
  systemd-run --user --collect --quiet --expand-environment=no --service-type=exec \
    --unit="$NE_UNIT" --description="North Echo 08.03 workspace=$PWD" \
    --property=RuntimeMaxSec=300s --property=TimeoutStopSec=3s \
    --property=MemoryMax=67108864 --property=MemorySwapMax=0 \
    --property=TasksMax=16 --property=CPUQuota=50% -- "$@"
}
```

This repeats the registered, literal-argv, bounded lifecycle from 08.02. Define the helper once in this shell. Use this launch block every time the exercise asks for a restart:

```bash
start_policy_service /usr/bin/python3 "$PWD/redirect_services.py" "$NE_ALLOWED_PORT" "$NE_PROTECTED_PORT" "$NE_READY"
NE_HTTP_UNIT="$NE_UNIT"
start_policy_service /usr/bin/python3 "$PWD/egress_broker.py" "$PWD/policy.json" "$NE_SOCKET"
NE_BROKER_UNIT="$NE_UNIT"
for attempt in {1..50}; do test -S "$NE_SOCKET" && test -f "$NE_READY" && break; sleep 0.1; done
test -S "$NE_SOCKET"
test -f "$NE_READY"
test "$(stat -c '%a' "$NE_SOCKET")" = 600
```

The readiness and mode tests check created objects, not just command intent. If they fail, stop before testing the policy. Inspect the saved exact unit names with `journalctl --user -u "$NE_HTTP_UNIT" -u "$NE_BROKER_UNIT" --no-pager`, then use `../../lab-cleanup 08.03`.

## Exercise 3 - Observe per-hop authorization

```bash
unshare --user --map-root-user --net /usr/bin/python3 broker_client.py \
  "$NE_SOCKET" "$NE_RUN" allowed.test "$NE_ALLOWED_PORT" /same > same.json
NE_ESCAPE_STATUS=0
unshare --user --map-root-user --net /usr/bin/python3 broker_client.py \
  "$NE_SOCKET" "$NE_RUN" allowed.test "$NE_ALLOWED_PORT" /escape > escape.json || NE_ESCAPE_STATUS=$?
NE_RUN_STATUS=0
unshare --user --map-root-user --net /usr/bin/python3 broker_client.py \
  "$NE_SOCKET" wrong-run allowed.test "$NE_ALLOWED_PORT" /ok > wrong-run.json || NE_RUN_STATUS=$?
python3 -m json.tool same.json
python3 -m json.tool escape.json
python3 -m json.tool wrong-run.json
test "$NE_ESCAPE_STATUS" -eq 1
test "$NE_RUN_STATUS" -eq 1
```

Expect `same.json` to contain status 200, `allowed-final\n`, and `redirects: 1`. The first request is allowed, the relative redirect stays within the allowed destination, and that destination is checked again.

Expect `escape.json` to say the destination is not authorized. The allowed server may suggest another hostname; that suggestion does not change policy. Expect the wrong-run response to fail before an upstream connection.

The source ordering shows why denial occurs before protected contact. These response bodies alone do not independently measure contact counts; the independent lab's grader adds that observation. Never equate “secret body not displayed” with “service was never contacted.”

## Exercise 4 - Deliberately broaden policy, then repair it

First stop the exact owned services. Add only the lesson's second synthetic loopback endpoint:

```bash
../../lab-cleanup 08.03
python3 - "$NE_PROTECTED_PORT" <<'PY'
import json
from pathlib import Path
import sys

path = Path("policy.json")
policy = json.loads(path.read_text())
policy["destinations"]["blocked.test"] = {
    "address": "127.0.0.1", "ports": [int(sys.argv[1])]
}
path.write_text(json.dumps(policy, indent=2) + "\n")
PY
```

This is the intentional mistake: the policy now grants authority the intended workload should not have. A correct enforcement algorithm cannot repair an overbroad authorization decision.

Repeat the **launch block from Exercise 2**, then observe the changed result:

```bash
unshare --user --map-root-user --net /usr/bin/python3 broker_client.py \
  "$NE_SOCKET" "$NE_RUN" allowed.test "$NE_ALLOWED_PORT" /escape > broadened.json
python3 -m json.tool broadened.json
../../lab-cleanup 08.03
```

The synthetic protected body is now returned because the second destination was explicitly allowed. Nothing contacted a public service. Restarting mattered: changing the file while the old broker ran would not change its already-loaded policy.

Remove that grant, inspect the repaired policy, then repeat the launch block:

```bash
python3 - <<'PY'
import json
from pathlib import Path

path = Path("policy.json")
policy = json.loads(path.read_text())
del policy["destinations"]["blocked.test"]
path.write_text(json.dumps(policy, indent=2) + "\n")
PY
python3 -m json.tool policy.json
```

After the fresh launch:

```bash
NE_REPAIRED_STATUS=0
unshare --user --map-root-user --net /usr/bin/python3 broker_client.py \
  "$NE_SOCKET" "$NE_RUN" allowed.test "$NE_ALLOWED_PORT" /escape > repaired.json || NE_REPAIRED_STATUS=$?
test "$NE_REPAIRED_STATUS" -eq 1
../../lab-cleanup 08.03
```

## Checkpoint, troubleshooting, and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

def result(name):
    return json.loads(Path(name).read_text())

same = result("same.json")
assert same["ok"] is True and same["status"] == 200
assert same["redirects"] == 1 and same["body"] == "allowed-final\n"
for name in ("escape.json", "wrong-run.json", "repaired.json"):
    assert result(name)["ok"] is False
assert result("broadened.json")["body"] == "protected-service-must-not-be-read\n"
assert set(result("policy.json")["destinations"]) == {"allowed.test"}
print("REDIRECT REAUTHORIZATION AND POLICY REPAIR: PASS")
PY
test ! -e "$NE_SOCKET"
test ! -e "$NE_READY"
```

Explain two different failures: an algorithm following redirects without reauthorization, and an algorithm correctly enforcing an excessively broad policy. This lesson repairs the latter by narrowing data and restarting.

If the broker refuses policy, inspect the complete startup error before changing a control. If a denied request unexpectedly succeeds, inspect the loaded policy and confirm you restarted after repair. If a readiness file outlives its service, cleanup/reset the exact lesson; do not interpret it as live readiness. Keep SELinux enabled and do not add routes, DNS, public endpoints, or wildcard teardown.

Return with `cd ../..`; `./lab-reset 08.03` discards the prepared workspace after verified cleanup.

## Source truth

Python's [URL parsing documentation](https://docs.python.org/3.14/library/urllib.parse.html) explicitly separates parsing from validation and describes origin-changing joins. The [HTTP client API](https://docs.python.org/3.14/library/http.client.html) documents request/response handling; [signal](https://docs.python.org/3.14/library/signal.html) explains handler execution. This course's authorization contract is narrower than those general-purpose APIs.
<!-- /source -->

---

<!-- source: course/module-08-network-egress/lab/README.md format=markdown -->
# Module 08 independent lab - Policy-bound egress broker

## Your assignment and readiness check

Build a reusable broker that mediates a small HTTP capability for a network-isolated caller. Do not give the caller a route, general TCP proxy, live DNS resolver, or shell command interface.

Before beginning, explain the successful direct baseline and isolated failure from 08.01, the pathname-socket path from 08.02, and the per-redirect decision plus policy-restart requirement from 08.03. If any is unclear, repeat that guided exercise first. This lab asks you to assemble those skills independently, not discover an undocumented API.

## Prepare and inspect the starter

From the course root in your disposable Linux VM:

```bash
./lab-start module-08
cd .student/08.lab
pwd
ls -l egress_broker.py
cat egress_broker.py
nano egress_broker.py
```

The working copy is yours to edit. Keep canonical files under `course/` unchanged. In nano, use Ctrl+O, Enter to save and Ctrl+X to exit with the course's default key bindings.

```python
#!/usr/bin/env python3
"""Starter: validate arguments, but do not expose an unmediated fallback."""

import sys

if len(sys.argv) != 3:
    print(f"usage: {sys.argv[0]} POLICY.json SOCKET", file=sys.stderr)
    raise SystemExit(2)
print("broker policy is not implemented", file=sys.stderr)
raise SystemExit(1)
```

### Starter, line by line

- The docstring describes a deliberately incomplete program, not a working broker.
- `sys.argv` contains the executable filename plus the policy and socket arguments.
- The length check reports interface misuse with status 2.
- Even correctly supplied arguments reach a nonzero, fail-closed exit. The starter creates no listener and opens no network path.
- Replace the incomplete behavior with your implementation; preserving a helpful argument check is useful.

## Required interface and behavior

The grader invokes:

```text
python3 egress_broker.py POLICY.json SOCKET
```

Validate the complete policy **before** creating a listener. The policy has exactly a nonempty bounded `run_id` and a `destinations` dictionary. Each lowercase synthetic hostname maps to exactly a literal `address` and a nonempty list of integer `ports`. Accept only IPv4 loopback addresses and ports 1 through 65535; reject Boolean ports. Never perform live DNS or contact a non-loopback address.

Create a filesystem Unix socket at the supplied path with mode 0600. Refuse a pre-existing path, including a dangling symlink. The socket is an IPC channel, not proof of a client's identity.

Each connection carries one bounded newline-terminated JSON object:

```json
{"run_id":"example-run","host":"allowed.test","port":45123,"path":"/ok"}
```

Require exactly those fields. Bind the run value to policy, validate types and path shape, and authorize the hostname, mapped literal address, and port before every upstream connection. A caller must not override the mapped address with an extra field.

Support relative and absolute HTTP redirects, but parse and reauthorize every resulting destination **before** contacting it. Reject user information, non-HTTP schemes, fragments, invalid ports, control characters, ambiguous paths, oversized messages/bodies, excessive redirects, and upstream failures. Use the practiced limits of 8192 request bytes, 65536 response-body bytes, and at most four followed redirects. Use bounded blocking operations; do not describe these as one absolute end-to-end deadline.

Success is one JSON line with Boolean `ok: true`, integer HTTP `status`, string `body`, and integer `redirects`. Denial is one line with `ok: false` and an `error`. A denied request must not prevent a later valid request. Clean SIGTERM/SIGINT termination must exit successfully and remove the exact socket. Do not implement permissive fallback behavior.

## Map the work to practiced skills

- Policy dictionaries, JSON types, and exact field sets: Module 04 and 08.03.
- A pathname Unix socket with effective mode checking: 08.02.
- Literal address selection without live DNS: 08.02 and 08.03.
- Checking the destination again after a redirect: 08.03.
- Bounded reads, operation timeouts, and response framing: all three networking lessons.
- Signal-aware cleanup and registered manual service launches: 08.01-08.03 and Module 07.
- Distinguishing namespace setup failure from an observed connection denial: 08.01.

Write a short design note before coding: where is the last authorization decision before a connection? What data reaches that connection? Which cleanup path runs if an upstream request fails? Your note is part of your learning evidence, not an automatically graded answer.

## Validate independently

```bash
python3 -m py_compile egress_broker.py
../../lab-grade module-08
../../lab-grade module-08 --mode exam
```

Compilation checks syntax without starting a listener. Practice grading creates fresh synthetic names, ports, run identity, and bodies, then reports failed properties with lesson references. Exam grading uses the same behavior checks with less repair guidance. A passing practice run is not a substitute for explaining the boundary.

The external grader runs randomized allowed/protected loopback services. It checks approved access, run binding, name and port denial, an allowed relative redirect, denied name and literal-address redirect destinations **before protected contact**, exact request shape, refusal of non-loopback policy, a real isolated network observation, mode 0600, and clean teardown. Protected-service contact counts are stronger evidence than merely not displaying its body.

The grader is a finite set of observations. It does not prove absence of every parser ambiguity, a complete authentication design, resilience to every slow client, or production suitability. Retain your own boundary explanation alongside the result.

## Troubleshooting, cleanup, and reset

If no socket appears, inspect syntax, policy validation, path length, and the startup error; do not remove validation to make a listener appear. If a redirect test fails, follow the parsed next destination and the policy decision rather than matching the grader's canary text. If namespace creation fails, repair the supported disposable-VM setup before interpreting connectivity results.

The grader owns and terminates its test processes. If you manually launch services while debugging, use the same registered unit pattern as the lessons, substituting `module-08` in the target, unit-name component, and exact description. Use `../../lab-cleanup module-08 --dry-run`, then `../../lab-cleanup module-08`; do not use wildcard process kills.

Return with `cd ../..`. `./lab-reset module-08` removes the lab workspace and fixtures after verified cleanup. Save your own notes first. Use only synthetic loopback services; keep SELinux enabled and never add host routes, firewall changes, real credentials, or public targets.
<!-- /source -->

## Security model summary

The network namespace replaces the workload's inherited IP network view. These lessons leave the workspace filesystem shared and deliberately expose a mode-0600 pathname Unix socket through it; they do not prove that no other filesystem channel exists. The broker checks a fixed request schema, run context, synthetic name-to-loopback mapping, port, transport bounds, and each redirect. Run context is not authentication and account permissions do not separate same-account processes. Network isolation does not make broker policy correct, and broker policy does not replace filesystem, syscall, privilege, or resource controls.

## Glossary

- **Network namespace:** per-namespace interfaces, routes, and related network state.
- **Loopback:** an address that refers only to the network namespace containing it.
- **Pathname Unix-domain socket:** a local IPC endpoint addressed through the filesystem rather than IP routing; distinct from Linux abstract Unix sockets.
- **Mediated egress:** a narrower process performs an approved network operation for an isolated caller.
- **Reauthorization:** repeating policy checks after a request changes, including at every redirect.
- **Run binding:** requiring a request to name the exact synthetic execution identity authorized by policy.

<!-- source: course/module-09-credential-brokering/README.md format=markdown -->
# Module 09 - Broker credentials with operation capabilities

Remove fake credentials from workload environments, then place their use behind a local operation broker. HMAC-authenticated, short-lived capabilities bind the exact operation, resource, arguments, audience, run, and nonce without containing the underlying credential. Nonce consumption is remembered for one broker-process lifetime.

Play in order: `09.01`, `09.02`, `09.03`, then `module-09`.

Outcomes:

- observe that an environment credential is ambient authority inherited across `exec`;
- remove that authority with an explicit minimal environment;
- distinguish a signed capability from an encrypted secret;
- bind operation, resource, canonical input, audience, run identity, issue time, expiry, and nonce;
- deny tampering, expiry, excessive lifetime, replay, and confused-deputy substitutions before upstream contact;
- prove a broker used a fake credential upstream without returning it to the client.

Every credential, signing key, capability, resource, and upstream service is synthetic and lesson-local. Communication uses filesystem Unix sockets only; no DNS, LAN, public, cloud, employer, or production service is involved. Prerequisites are Modules 01, 04, and 08.

## Learning route and limits

First observe what an inherited environment makes available. Next authenticate
readable claims and compare them with a requested operation. Finally add policy
checks, an upstream service, and remembered consumption. Distinguish each step:
encoding is not encryption, HMAC is not an asymmetric signature, a valid token
is not permission for a different request, and a nonce alone does not stop replay.

The issuer, broker, client, and upstream are teaching roles running under one
VM account. A private file mode does not separate same-account processes. The
lessons demonstrate the intended request interface, not a complete secret-storage
boundary. Earlier filesystem/process controls are still required for confinement.

The replay cache is in memory and is lost on restart; consumption before contact
also means an upstream failure can spend a token. There is no exactly-once or
durable replay guarantee. All tests and observations use fake material only.
<!-- /source -->

---

<!-- source: course/module-09-credential-brokering/lesson-01/README.md format=markdown -->
# 09.01 - Remove ambient credential authority

## Outcomes and prerequisites

Complete Modules 01, 04, and 08. You will observe a visibly fake credential crossing a process launch, remove it with an explicit environment, and explain what this does not isolate. This revisits B1 with an operation-broker design in mind.

## Concepts before commands

A **credential** is a value a service accepts as evidence of authority. Putting one in a process environment makes it available to that process's code. A child normally inherits the parent's environment unless the launcher supplies a replacement.

An **ambient** credential is available without making a new, operation-specific authorization decision. Its short lifetime may reduce exposure, but does not stop a process reading or copying it while present.

This exercise uses only a string beginning with `FAKE-`. Never substitute an API key, cloud token, password, employer credential, or personal secret. The deliberate disclosure prints only that synthetic value. It demonstrates authority inheritance, not an attack against another process.

## Prepare and read both files

From the course root in the disposable VM:

```bash
./lab-start 09.01
cd .student/09.01
pwd
ls -l credential_probe.py clean_launch.py
cat credential_probe.py
cat clean_launch.py
```

The scripts are already in your prepared workspace. You can inspect them with `nano credential_probe.py` or `nano clean_launch.py`. Reading a source is not executing it; the next exercises run it.

### The synthetic observer

```python
#!/usr/bin/env python3
"""Observe whether a synthetic credential crossed exec."""

import json
import os
import sys

name = "NORTH_ECHO_FAKE_CREDENTIAL"
value = os.environ.get(name)
result = {"present": value is not None, "length": len(value) if value else 0}
if len(sys.argv) == 2 and sys.argv[1] == "leak" and value is not None:
    result["leaked_value"] = value
print(json.dumps(result, sort_keys=True))
```

### Source, line by line

- `json` formats the observation; `os` exposes this process's environment; `sys` exposes its arguments.
- `name` selects one explicitly fake variable. `os.environ.get` returns its string value or `None` if absent.
- `value is not None` distinguishes an absent variable from a present empty string. A present empty string still has length zero.
- The dictionary reports presence and length without displaying the value by default.
- Only the exact extra argument `leak`, with a present value, adds `leaked_value` to the result. This is intentionally unsafe display behavior for synthetic evidence.
- `json.dumps(..., sort_keys=True)` serializes the observation. Sorting gives stable output; it is not redaction.

### The minimal-environment launcher

```python
#!/usr/bin/env python3
"""Launch exact argv with a small, credential-free environment."""

import os
import subprocess
import sys

if len(sys.argv) < 2:
    raise SystemExit(f"usage: {sys.argv[0]} COMMAND [ARG...]")
clean = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
run = subprocess.run(sys.argv[1:], shell=False, env=clean, check=False)
raise SystemExit(run.returncode)
```

### Source, line by line

- `subprocess` starts the child. The `os` import is retained for the later deliberate comparison with inherited environment.
- The argument guard refuses a missing command before launch.
- `clean` is a new dictionary containing only the selected PATH and locale. It is not a copy with one known secret removed.
- `sys.argv[1:]` preserves separate command arguments. `shell=False` prevents this launcher from treating them as a shell program.
- `env=clean` replaces the child's inherited environment; `check=False` returns a result object instead of raising on an ordinary nonzero child exit.
- `SystemExit(run.returncode)` forwards ordinary child exit codes. This small example is not a complete signal-status or timeout supervisor.

The launcher does **not** remove filesystem access, existing descriptors, network access, or every possible credential source. Environment reduction is one handoff control, not a complete sandbox.

## Exercise 1 - Predict and observe inherited authority

```bash
export NORTH_ECHO_FAKE_CREDENTIAL="FAKE-LESSON-$$-DO-NOT-USE"
python3 credential_probe.py > inherited.json
python3 credential_probe.py leak > disclosed.json
python3 -m json.tool inherited.json
python3 -m json.tool disclosed.json
```

`export` places the value in later child environments. The shell PID contributes a synthetic run label; it has no security significance. Redirection saves each observation separately.

Expect `present: true` and a positive length in both files. Only `disclosed.json` should include the fake value. The child did not need another authorization API to read it: inheritance already conveyed that access. This does not mean all environment values are automatically logged; it means the receiving code can choose to disclose them.

## Exercise 2 - Repair the launch boundary

```bash
python3 clean_launch.py /usr/bin/python3 "$PWD/credential_probe.py" > cleaned.json
python3 clean_launch.py /usr/bin/python3 "$PWD/credential_probe.py" leak > cleaned-leak.json
test -n "$NORTH_ECHO_FAKE_CREDENTIAL"
python3 -m json.tool cleaned.json
python3 -m json.tool cleaned-leak.json
```

The absolute executable path and script path are separate arguments. Both children should report absence and length zero; neither should contain `leaked_value`. The parent-side `test` proves you did not merely erase the parent value before observing the child.

## Exercise 3 - Make the incomplete repair visible

Open `nano clean_launch.py`. Change only `env=clean` to `env=os.environ.copy()`, save, and predict the result:

```bash
python3 clean_launch.py /usr/bin/python3 "$PWD/credential_probe.py" > regressed.json
python3 -m json.tool regressed.json
```

The inherited variable is present again. Explicit argv and `shell=False` did not repair this separate environment mistake. Restore **only** `env=clean`, save, and rerun:

```bash
python3 clean_launch.py /usr/bin/python3 "$PWD/credential_probe.py" leak > repaired.json
```

## Checkpoint, troubleshooting, and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

def result(name):
    return json.loads(Path(name).read_text())

assert result("inherited.json")["present"] is True
assert result("disclosed.json")["leaked_value"].startswith("FAKE-LESSON-")
assert result("regressed.json")["present"] is True
for name in ("cleaned.json", "cleaned-leak.json", "repaired.json"):
    observed = result(name)
    assert observed["present"] is False and observed["length"] == 0
    assert "leaked_value" not in observed
print("CREDENTIAL INHERITANCE AND REPAIR: PASS")
PY
test -n "$NORTH_ECHO_FAKE_CREDENTIAL"
unset NORTH_ECHO_FAKE_CREDENTIAL
```

The assertions compare actual JSON fields rather than a suggestive filename. `unset` removes the fake variable from this shell after the experiment. It does not retroactively erase copies in already-running processes or saved JSON.

If the cleaned child sees the value, inspect the actual `env=` argument and confirm you saved the working copy. If the initial observation is absent, repeat the export in the same shell. No inspection of unrelated processes is needed.

A legitimate task may now lack a credential it needs. The next lessons restore a narrow approved **operation**, not the credential itself. Return with `cd ../..`; `./lab-reset 09.01` removes these synthetic output files and restores the working copy.

## Source truth

Python's [subprocess documentation](https://docs.python.org/3.14/library/subprocess.html) defines explicit environment mappings and argument lists. Its [os environment API](https://docs.python.org/3.14/library/os.html#os.environ) describes the process-local mapping. These sources do not claim that an environment-only launcher provides filesystem or network isolation.
<!-- /source -->

---

<!-- source: course/module-09-credential-brokering/lesson-02/README.md format=markdown -->
# 09.02 - Bind an HMAC-authenticated operation capability

## Outcomes and prerequisites

Complete 09.01. You will mint a synthetic operation token, inspect its readable claims, distinguish message authentication from encryption, and observe request-binding and time checks. No listener or external service is involved.

## Concepts before commands

A **bearer capability** conveys authority to whoever presents it. A narrow capability names an operation and resource instead of exposing a general service credential. Possession still matters: a token is not harmless merely because it expires soon.

This example uses HMAC-SHA256, a **shared-key message-authentication code**. The code calls the result a signature for brevity, but it is not an asymmetric public-key signature. Anyone who has the shared key can both verify and mint these tokens. Never give that key to a workload and then expect the token to limit what it can request.

Base64 is a reversible text encoding. A hash is a digest of input bytes. HMAC combines a secret key with a message to check integrity/authenticity relative to that shared key. None of these operations encrypts the claims in this example.

A **binding** ties a claim to its intended context: operation, resource, audience (the intended broker), run, and input. A correct HMAC alone does not authorize a different request. A **nonce** is a fresh random identifier; simply putting it in a token does not make the token one-use. A broker must remember consumption, which 09.03 introduces.

The fixed key below is intentionally public teaching material. It must never protect a real system.

## Prepare and read the program

From the course root:

```bash
./lab-start 09.02
cd .student/09.02
pwd
ls -l capability.py
cat capability.py
```

Open `nano capability.py` to navigate its functions. No source edit is required. Read the whole program before minting short-lived artifacts so reading time does not consume the validity window.

```python
#!/usr/bin/env python3
"""Mint and verify one short-lived, operation-bound synthetic capability."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import sys
import time


def encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def input_digest(raw: str) -> str:
    return hashlib.sha256(canonical(json.loads(raw))).hexdigest()


def mint(key: bytes, operation: str, resource: str, audience: str, run_id: str, ttl: int, input_json: str) -> str:
    if not 1 <= ttl <= 300:
        raise ValueError("TTL must be 1..300 seconds")
    issued = int(time.time())
    claims = {
        "version": 1,
        "operation": operation,
        "resource": resource,
        "audience": audience,
        "run_id": run_id,
        "issued_at": issued,
        "expires_at": issued + ttl,
        "nonce": secrets.token_hex(16),
        "input_sha256": input_digest(input_json),
    }
    payload = encode(canonical(claims))
    signature = encode(hmac.new(key, payload.encode(), hashlib.sha256).digest())
    return payload + "." + signature


def verify(key: bytes, token: str, operation: str, resource: str, audience: str, run_id: str, input_json: str) -> dict:
    payload, supplied = token.strip().split(".")
    expected = encode(hmac.new(key, payload.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(supplied, expected):
        raise ValueError("signature mismatch")
    padded = payload + "=" * (-len(payload) % 4)
    claims = json.loads(base64.urlsafe_b64decode(padded))
    now = int(time.time())
    expected_binding = (operation, resource, audience, run_id, input_digest(input_json))
    actual_binding = tuple(claims[name] for name in ("operation", "resource", "audience", "run_id", "input_sha256"))
    if actual_binding != expected_binding:
        raise ValueError("capability binding mismatch")
    if not claims["issued_at"] <= now < claims["expires_at"]:
        raise ValueError("capability is not currently valid")
    return claims


def main() -> int:
    if len(sys.argv) < 2:
        return 2
    if sys.argv[1] == "mint" and len(sys.argv) == 10:
        key = Path(sys.argv[2]).read_bytes()
        token = mint(key, sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7], int(sys.argv[8]), sys.argv[9])
        Path(sys.argv[3]).write_text(token + "\n", encoding="utf-8")
        print("capability minted")
        return 0
    if sys.argv[1] == "verify" and len(sys.argv) == 9:
        key = Path(sys.argv[2]).read_bytes()
        token = Path(sys.argv[3]).read_text(encoding="utf-8")
        claims = verify(key, token, sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8])
        print(json.dumps(claims, sort_keys=True))
        return 0
    print("usage: capability.py mint KEY TOKEN OP RESOURCE AUDIENCE RUN TTL INPUT_JSON", file=sys.stderr)
    print("   or: capability.py verify KEY TOKEN OP RESOURCE AUDIENCE RUN INPUT_JSON", file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"capability denied: {error}", file=sys.stderr)
        raise SystemExit(1)
```

### Source, line by line (grouped by function)

- `encode` base64-encodes bytes with the URL-safe alphabet, removes padding, and produces ASCII text. It does not hide the bytes.
- `canonical` sorts object keys, removes optional JSON whitespace, rejects NaN/infinity, and encodes the result as bytes. This is the course's Python serialization convention, not a claim to implement a universal cross-language canonical-JSON standard.
- `input_digest` first parses JSON and then hashes that deterministic representation. Different whitespace or object-key order therefore does not change the digest for the same parsed values.
- `mint` accepts a lifetime from 1 through 300 seconds. `int(time.time())` records wall-clock seconds, not monotonic elapsed time.
- The claims dictionary includes a format version, the operation context, issue/expiry timestamps, a 16-byte random nonce represented by 32 hexadecimal characters, and the input digest.
- The payload is the encoded claims. `hmac.new` authenticates those exact payload characters; the token joins payload and authenticator with one period.
- `verify` splits those two segments, recomputes HMAC, and uses `compare_digest` rather than an ordinary early-exit string comparison.
- It restores base64 padding only for decoding, parses the claims, and constructs matching tuples of expected/request context and actual/token context.
- A different tuple raises a binding error even when HMAC is correct.
- `issued_at <= now < expires_at` defines a half-open validity interval: the token is already invalid at its expiry second.
- `main` distinguishes mint and verify argument counts. Key and token filenames travel in argv; the bearer token itself is read from a file.
- Expected file, parsing, and binding failures print a diagnostic and return nonzero. There is no fallback to an unsigned token.

This compact verifier teaches the mechanism with tokens minted by this tool. It is not yet the stricter schema/encoding/policy validator in 09.03. It also does not retain a replay set. Do not treat a second successful verification as one-use enforcement.

## Exercise 1 - Mint and verify

Create the fake key with a restrictive creation mask in a subshell, leaving your interactive shell's mask unchanged:

```bash
(umask 077; printf '%s' 'FAKE-SIGNING-KEY-09.02-ONLY-000000000000' > signing.key)
test "$(stat -c '%a' signing.key)" = 600
NE_RUN="run-$$"
(umask 077; python3 capability.py mint signing.key token.txt read record:alpha broker.lesson "$NE_RUN" 300 '{}')
test "$(stat -c '%a' token.txt)" = 600
python3 capability.py verify signing.key token.txt read record:alpha broker.lesson "$NE_RUN" '{}' > verified.json
python3 -m json.tool verified.json
```

`umask` affects newly created files, not existing file modes; the `stat` checks verify the result. If a prior file has the wrong mode, reset this prepared lesson before repeating rather than assuming a mask changed it.

The token binds `read`, `record:alpha`, audience `broker.lesson`, this run, and empty-object input. Timestamps and nonce vary. The fixed fields should match your command. If more than five minutes passes, mint a fresh token and repeat the checks.

## Exercise 2 - Inspect without the key

```bash
python3 - <<'PY'
import base64
import json
from pathlib import Path

payload = Path("token.txt").read_text().strip().split(".")[0]
claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
print(json.dumps(claims, indent=2, sort_keys=True))
assert set(claims) == {
    "version", "operation", "resource", "audience", "run_id",
    "issued_at", "expires_at", "nonce", "input_sha256"
}
assert claims["operation"] == "read" and claims["resource"] == "record:alpha"
print("READABLE CLAIMS: PASS")
PY
```

The program uses only the token file, not the key. The arithmetic adds enough padding to complete a multiple of four encoded characters. The exact key-set assertion checks the visible schema. No service credential belongs in these claims; readable data is not confidential data.

This inspection does **not** authenticate the token. Only verification with the key can check HMAC. Likewise, searching the encoded token for a plaintext secret would not prove that the secret was absent in every encoded form.

## Exercise 3 - Deliberate request mismatch, then repair

```bash
NE_RESOURCE_STATUS=0
python3 capability.py verify signing.key token.txt read record:beta broker.lesson "$NE_RUN" '{}' \
  > wrong-resource.json 2> wrong-resource.err || NE_RESOURCE_STATUS=$?
NE_OPERATION_STATUS=0
python3 capability.py verify signing.key token.txt append record:alpha broker.lesson "$NE_RUN" '{}' \
  > wrong-operation.json 2> wrong-operation.err || NE_OPERATION_STATUS=$?
cat wrong-resource.err wrong-operation.err
test "$NE_RESOURCE_STATUS" -ne 0
test "$NE_OPERATION_STATUS" -ne 0
python3 capability.py verify signing.key token.txt read record:alpha broker.lesson "$NE_RUN" '{}' > repaired.json
```

The token is unchanged. Its HMAC remains valid, but neither changed request matches its narrower grant. Expect `capability binding mismatch`. Returning to the original operation/resource repairs the mismatch without broadening the grant.

This is the central **confused-deputy** concern: a component with broader authority must not let a caller reinterpret a narrower authorization as permission to act on a different resource.

## Exercise 4 - Observe expiry and the replay limitation

```bash
(umask 077; python3 capability.py mint signing.key short.txt read record:alpha broker.lesson "$NE_RUN" 1 '{}')
sleep 2
NE_EXPIRED_STATUS=0
python3 capability.py verify signing.key short.txt read record:alpha broker.lesson "$NE_RUN" '{}' \
  > expired.json 2> expired.err || NE_EXPIRED_STATUS=$?
cat expired.err
test "$NE_EXPIRED_STATUS" -ne 0
python3 capability.py verify signing.key token.txt read record:alpha broker.lesson "$NE_RUN" '{}' > repeated.json
```

The two-second pause crosses the one-second validity window. Expect `capability is not currently valid`, not just any failure. The longer-lived token can still verify again: signature checking and expiry do not remember whether it was used.

A clock error can invalidate this observation. Inspect `date -u` in the disposable VM if timestamps are implausible; do not remove time validation. Expiry invalidates authority under this verifier, but does not delete token files.

## Checkpoint, troubleshooting, and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

original = json.loads(Path("verified.json").read_text())
assert json.loads(Path("repaired.json").read_text()) == original
assert json.loads(Path("repeated.json").read_text()) == original
assert original["expires_at"] - original["issued_at"] == 300
assert len(original["nonce"]) == 32
assert "binding mismatch" in Path("wrong-resource.err").read_text()
assert "binding mismatch" in Path("wrong-operation.err").read_text()
assert "not currently valid" in Path("expired.err").read_text()
print("BINDING, EXPIRY, AND REPLAY LIMIT: PASS")
PY
```

Explain why anyone can read claims, why a key holder can mint tokens, and why a nonce needs consumption state. If every verification fails HMAC, check that the key and token belong to the same exercise. If JSON parsing fails, preserve `'{}'` as one argument.

These are synthetic artifacts, but treat the files as authority-bearing during the exercise. Return with `cd ../..`; `./lab-reset 09.02` removes only this prepared workspace and its fake artifacts. No background service needs stopping.

## Source truth

Python's [HMAC API](https://docs.python.org/3.14/library/hmac.html) documents keyed authentication and digest comparison; [base64](https://docs.python.org/3.14/library/base64.html) documents reversible encodings; [secrets](https://docs.python.org/3.14/library/secrets.html) supplies the random nonce. Authorization bindings and replay consumption are application policy, not features supplied automatically by those primitives.
<!-- /source -->

---

<!-- source: course/module-09-credential-brokering/lesson-03/README.md format=markdown -->
# 09.03 - Deny replay and confused-deputy substitution

## Outcomes and prerequisites

Complete 09.01 and 09.02. You will trace a request across client, broker, and synthetic upstream; observe single-process replay prevention; and repair a request that does not match its capability. Use Module 07's registered lifecycle and Module 08's socket/JSON vocabulary.

## Concepts before commands

There are three different authorities here:

- The **issuer** holds an HMAC key and can mint operation capabilities.
- The **broker** holds that key for verification and a separate fake service credential. It checks a capability before using its broader upstream authority.
- The **client** submits a bearer token and an operation request. Its normal interface receives neither key nor credential.

The upstream is a fourth role: it accepts the fake service credential and performs one synthetic read. It is separate from the broker so a test can observe whether a rejected request nevertheless caused contact.

These are **teaching roles**, not yet independently isolated operating-system identities. All commands run as your VM account and files remain in its workspace. Mode 0600 does not stop that same account reading its own key files. This lesson proves request validation and the absence of a credential in the demonstrated client exchange; it does not prove that a malicious same-account workload cannot reach any secret file. Combine mediation with the filesystem, process, and resource controls already studied.

A nonce replay cache is also scoped. This implementation remembers consumption only while this broker process lives. Restart loses that memory. Do not reuse the same still-valid token/key/run after restart and call the result durable one-use enforcement. A production design would need coordinated durable consumption or a fresh authorization epoch; that design is outside this exercise.

## Prepare and read the system

From the course root in the disposable VM:

```bash
./lab-start 09.03
cd .student/09.03
pwd
ls -l capability_broker.py synthetic_upstream.py mint_token.py broker_client.py
cat capability_broker.py
cat synthetic_upstream.py
cat mint_token.py
cat broker_client.py
```

You may navigate each with `nano` and its exact filename. There is no source edit in this exercise: the deliberate mistake will be an incorrectly bound request. Read before creating short-lived tokens.

### The broker

```python
#!/usr/bin/env python3
"""Use fake credentials only after a capability passes every binding check."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import signal
import socket
import stat
import sys
import time

MAX_LINE = 16384
MAX_UPSTREAM = 65536
MAX_USED_NONCES = 4096
stopping = False


class Denied(Exception):
    pass


def canonical(value: object) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    except (TypeError, ValueError) as error:
        raise Denied("input is not canonical JSON") from error


def encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def decode(segment: str) -> bytes:
    if not isinstance(segment, str) or not segment or "=" in segment or len(segment) > 8192:
        raise Denied("invalid token encoding")
    try:
        raw = base64.b64decode(segment + "=" * (-len(segment) % 4), altchars=b"-_", validate=True)
    except (ValueError, binascii.Error) as error:
        raise Denied("invalid token encoding") from error
    if encode(raw) != segment:
        raise Denied("noncanonical token encoding")
    return raw


def load_policy(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    expected = {"version", "audience", "run_id", "max_ttl", "upstream_socket", "permissions"}
    if not isinstance(raw, dict) or set(raw) != expected or type(raw["version"]) is not int or raw["version"] != 1:
        raise Denied("invalid policy shape")
    if not all(isinstance(raw[name], str) and 1 <= len(raw[name]) <= 128 for name in ("audience", "run_id")):
        raise Denied("invalid policy identity")
    if type(raw["max_ttl"]) is not int or not 1 <= raw["max_ttl"] <= 300:
        raise Denied("invalid maximum lifetime")
    if not isinstance(raw["upstream_socket"], str):
        raise Denied("upstream socket must be a path string")
    upstream = Path(raw["upstream_socket"])
    if not upstream.is_absolute():
        raise Denied("upstream socket must be absolute")
    permissions = raw["permissions"]
    if not isinstance(permissions, dict) or not permissions:
        raise Denied("policy has no permissions")
    for resource, operations in permissions.items():
        if not isinstance(resource, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._:-]{0,127}", resource):
            raise Denied("invalid policy resource")
        if not isinstance(operations, list) or not operations or any(not isinstance(op, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", op) for op in operations):
            raise Denied("invalid policy operation")
    return raw


def receive_line(peer: socket.socket, limit: int) -> bytes:
    data = bytearray()
    while b"\n" not in data and len(data) <= limit:
        chunk = peer.recv(min(1024, limit + 1 - len(data)))
        if not chunk:
            break
        data.extend(chunk)
    if len(data) > limit or not data.endswith(b"\n") or data.count(b"\n") != 1:
        raise Denied("request must be one bounded line")
    return bytes(data)


def verify_token(policy: dict, key: bytes, request: dict) -> str:
    required = {"token", "operation", "resource", "audience", "run_id", "input"}
    if not isinstance(request, dict) or set(request) != required:
        raise Denied("invalid request shape")
    if not all(isinstance(request[name], str) for name in ("token", "operation", "resource", "audience", "run_id")):
        raise Denied("invalid request values")
    try:
        payload_text, signature_text = request["token"].split(".")
    except ValueError as error:
        raise Denied("invalid token shape") from error
    supplied = decode(signature_text)
    expected = hmac.new(key, payload_text.encode("ascii"), hashlib.sha256).digest()
    if not hmac.compare_digest(supplied, expected):
        raise Denied("invalid token signature")
    try:
        claims = json.loads(decode(payload_text))
    except (json.JSONDecodeError, UnicodeError) as error:
        raise Denied("invalid token payload") from error
    claim_names = {"version", "operation", "resource", "audience", "run_id", "issued_at", "expires_at", "nonce", "input_sha256"}
    if not isinstance(claims, dict) or set(claims) != claim_names or type(claims["version"]) is not int or claims["version"] != 1:
        raise Denied("invalid token claims")
    for name in ("operation", "resource", "audience", "run_id", "nonce", "input_sha256"):
        if not isinstance(claims[name], str):
            raise Denied("invalid token claim type")
    if type(claims["issued_at"]) is not int or type(claims["expires_at"]) is not int:
        raise Denied("invalid token time type")
    now = int(time.time())
    if claims["issued_at"] > now or claims["expires_at"] <= now:
        raise Denied("capability is not currently valid")
    if claims["expires_at"] <= claims["issued_at"] or claims["expires_at"] - claims["issued_at"] > policy["max_ttl"]:
        raise Denied("capability lifetime exceeds policy")
    if not re.fullmatch(r"[0-9a-f]{32}", claims["nonce"]):
        raise Denied("invalid capability nonce")
    if not re.fullmatch(r"[0-9a-f]{64}", claims["input_sha256"]):
        raise Denied("invalid input digest")
    bindings = ("operation", "resource", "audience", "run_id")
    if any(claims[name] != request[name] for name in bindings):
        raise Denied("request does not match capability")
    if request["audience"] != policy["audience"] or request["run_id"] != policy["run_id"]:
        raise Denied("request identity is not authorized")
    if request["operation"] not in policy["permissions"].get(request["resource"], []):
        raise Denied("operation is not permitted")
    digest = hashlib.sha256(canonical(request["input"])).hexdigest()
    if not hmac.compare_digest(digest, claims["input_sha256"]):
        raise Denied("request input does not match capability")
    return claims["nonce"]


def call_upstream(policy: dict, credential: str, request: dict) -> object:
    message = {"credential": credential, "operation": request["operation"], "resource": request["resource"], "input": request["input"]}
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
        stream.settimeout(2)
        stream.connect(policy["upstream_socket"])
        stream.sendall(canonical(message) + b"\n")
        stream.shutdown(socket.SHUT_WR)
        raw = receive_line(stream, MAX_UPSTREAM)
    if credential.encode() in raw:
        raise Denied("upstream attempted credential disclosure")
    response = json.loads(raw)
    if not isinstance(response, dict) or set(response) != {"ok", "result"} or response["ok"] is not True:
        raise Denied("upstream denied operation")
    return response["result"]


def serve(policy: dict, key: bytes, credential: str, socket_path: Path) -> None:
    if socket_path.exists() or socket_path.is_symlink():
        raise Denied("broker socket path already exists")
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    os.chmod(socket_path, 0o600)
    listener.listen(8)
    listener.settimeout(0.2)
    used_nonces: set[str] = set()
    try:
        while not stopping:
            try:
                peer, _ = listener.accept()
            except TimeoutError:
                continue
            with peer:
                peer.settimeout(2)
                try:
                    request = json.loads(receive_line(peer, MAX_LINE))
                    nonce = verify_token(policy, key, request)
                    if nonce in used_nonces:
                        raise Denied("capability replay denied")
                    if len(used_nonces) >= MAX_USED_NONCES:
                        raise Denied("replay cache capacity reached")
                    used_nonces.add(nonce)
                    result = call_upstream(policy, credential, request)
                    response = {"ok": True, "result": result}
                except (Denied, json.JSONDecodeError, UnicodeError, OSError) as error:
                    response = {"ok": False, "error": str(error)}
                try:
                    peer.sendall(canonical(response) + b"\n")
                except OSError:
                    pass
    finally:
        listener.close()
        socket_path.unlink(missing_ok=True)


def stop(_signum, _frame):
    global stopping
    stopping = True


def main() -> int:
    if len(sys.argv) != 5:
        print(f"usage: {sys.argv[0]} POLICY SIGNING_KEY CREDENTIAL SOCKET", file=sys.stderr)
        return 2
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        policy = load_policy(Path(sys.argv[1]))
        key_path, credential_path = Path(sys.argv[2]), Path(sys.argv[3])
        if key_path.is_symlink() or credential_path.is_symlink():
            raise Denied("broker secret files cannot be symlinks")
        if not stat.S_ISREG(key_path.stat().st_mode) or not stat.S_ISREG(credential_path.stat().st_mode):
            raise Denied("broker secret paths must be regular files")
        key = key_path.read_bytes()
        credential = credential_path.read_text(encoding="utf-8").strip()
        if not 32 <= len(key) <= 128 or not 8 <= len(credential) <= 256:
            raise Denied("invalid broker secret material")
        if stat.S_IMODE(key_path.stat().st_mode) != 0o600 or stat.S_IMODE(credential_path.stat().st_mode) != 0o600:
            raise Denied("broker secret files must be mode 0600")
        serve(policy, key, credential, Path(sys.argv[4]))
    except (Denied, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"broker setup denied: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### Source, block by block

- The constants bound client input, upstream response, and remembered nonce count. `Denied` identifies an application-policy failure.
- `canonical` uses the same sorted compact Python JSON convention as 09.02. It rejects non-finite numeric values and converts serialization failures into policy denials.
- `encode` creates the unpadded URL-safe representation. `decode` bounds a segment, rejects supplied padding, asks the decoder to validate its alphabet, and re-encodes to require the exact canonical text.
- `load_policy` requires the complete versioned field set. Audience and run are bounded strings; maximum lifetime is an integer from 1 through 300; the upstream pathname must be absolute.
- The resource and operation patterns accept only the small identifiers used by the course. Every resource maps to a nonempty operation list.
- `receive_line` reads at most one bounded newline-terminated message. A size bound limits memory; the caller must also set a socket timeout to bound idle operations.
- `verify_token` requires exactly token, operation, resource, audience, run, and input. Required textual fields must actually be strings.
- The token must split into two segments. HMAC is recomputed over the payload text and compared to the decoded authenticator before claims are trusted.
- The decoded claim object must have the expected keys and version. Identity/digest/nonce fields are strings; timestamps must be real integers, not Booleans.
- Time checks reject future issue times, expired tokens, nonpositive intervals, and intervals exceeding policy. A token with a valid HMAC can still have an invalid lifetime.
- Regular expressions check nonce and input-digest shape; shape is not a replacement for the HMAC or the input comparison.
- The first binding comparison matches token claims to the caller's requested operation, resource, audience, and run.
- A separate comparison matches audience/run to **broker policy**. A self-consistent token/request pair for some other broker is not sufficient.
- The resource allowlist checks whether policy permits the requested operation. The input hash then binds the exact parsed input according to the course serialization convention.
- Verification returns the nonce only after all these checks. It does not contact upstream.
- `call_upstream` builds a new request with the broker-held credential and the authorized operation fields. It connects only to the policy's Unix socket, not a caller-selected destination.
- The upstream exchange has a timeout and response-size limit. A literal credential reflected in raw response bytes is rejected. This is a check for the known synthetic value, not general data-loss prevention against every encoding or derived secret.
- `serve` creates a private listener and a fresh `used_nonces` set. After verification it rejects repeats and refuses new consumption once the bounded set is full.
- `used_nonces.add` occurs **before** upstream contact. A failed operation can consume a capability; automatically retrying it would undermine that ordering. There is no exactly-once transaction across broker and upstream.
- Accepted peers have timeouts. Expected errors return `ok: false`; a failed response delivery does not terminate the listener.
- SIGTERM/SIGINT set the stop flag. The short accept timeout allows normal loop exit and exact socket removal in `finally`.
- `main` validates policy and reads the fake key/credential during trusted startup. It checks regular files, rejects symlinks, validates lengths, and requires mode 0600 before listening.
- The credential therefore exists in broker memory before requests arrive. The guarantee is that it is **used in an upstream request only after authorization**, not that it is first read after authorization.

The separate pathname checks and reads assume operator-controlled setup files in this lesson. They are not a race-free secret loader against a malicious process that can modify the same directory. Nor does a mode check establish a separate security domain for same-account clients. Keep this boundary narrower than the claim you make.

### The synthetic upstream

```python
#!/usr/bin/env python3
"""Synthetic credential-protected operation service over a Unix socket."""

import json
import os
from pathlib import Path
import signal
import socket
import sys

stopping = False


def stop(_signum, _frame):
    global stopping
    stopping = True


if len(sys.argv) != 5:
    raise SystemExit(f"usage: {sys.argv[0]} CREDENTIAL RESOURCE VALUE SOCKET")
credential = Path(sys.argv[1]).read_text(encoding="utf-8").strip()
resource, value, socket_text = sys.argv[2:]
socket_path = Path(socket_text)
if socket_path.exists() or socket_path.is_symlink():
    raise SystemExit("upstream socket path already exists")
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
listener.bind(str(socket_path))
os.chmod(socket_path, 0o600)
listener.listen(8)
listener.settimeout(0.2)
try:
    while not stopping:
        try:
            peer, _ = listener.accept()
        except TimeoutError:
            continue
        with peer:
            peer.settimeout(2)
            try:
                with peer.makefile("rb") as incoming:
                    line = incoming.readline(16385)
                if len(line) > 16384 or not line.endswith(b"\n"):
                    raise ValueError("request must be one bounded line")
                request = json.loads(line)
                allowed = request == {"credential": credential, "operation": "read", "resource": resource, "input": {}}
                response = {"ok": True, "result": {"value": value}} if allowed else {"ok": False, "error": "upstream denied"}
            except (ValueError, UnicodeError, OSError):
                response = {"ok": False, "error": "invalid upstream request"}
            try:
                peer.sendall(json.dumps(response, sort_keys=True).encode() + b"\n")
            except OSError:
                pass
finally:
    listener.close()
    socket_path.unlink(missing_ok=True)
```

### Source, line by line

- The arguments identify a fake credential file, one resource, one harmless return value, and a socket pathname.
- The credential is read at startup. Its value is not passed in argv; only its filename is.
- Existing socket paths are refused. The listener uses `AF_UNIX`, mode 0600, and an accept timeout.
- Each peer has its own timeout and bounded newline read. Invalid data becomes a denial rather than an unrestricted operation.
- Dictionary equality requires the fake credential, operation `read`, configured resource, and empty-object input.
- Success returns a `result` object containing the synthetic value, not the credential. The program is intentionally not a general database.
- Normal stop closes the listener and removes its exact pathname. SIGKILL cannot execute that cleanup.

### The issuer

```python
#!/usr/bin/env python3
"""Mint a lesson capability; signing material stays outside the client."""

import base64
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import sys
import time


def encode(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


if len(sys.argv) != 9:
    raise SystemExit(f"usage: {sys.argv[0]} KEY TOKEN OP RESOURCE AUDIENCE RUN TTL INPUT_JSON")
key = Path(sys.argv[1]).read_bytes()
ttl = int(sys.argv[7])
if not 1 <= ttl <= 300:
    raise SystemExit("TTL must be 1..300 seconds")
issued = int(time.time())
input_value = json.loads(sys.argv[8])
claims = {
    "version": 1,
    "operation": sys.argv[3],
    "resource": sys.argv[4],
    "audience": sys.argv[5],
    "run_id": sys.argv[6],
    "issued_at": issued,
    "expires_at": issued + ttl,
    "nonce": secrets.token_hex(16),
    "input_sha256": hashlib.sha256(canonical(input_value)).hexdigest(),
}
payload = encode(canonical(claims))
signature = encode(hmac.new(key, payload.encode(), hashlib.sha256).digest())
Path(sys.argv[2]).write_text(payload + "." + signature + "\n", encoding="utf-8")
print("capability minted")
```

### Source, line by line

- The encoding and canonicalization functions repeat 09.02's token format.
- The argument guard distinguishes key/token filenames from operation context and input JSON.
- Lifetime is bounded before a token is written. Broker policy can impose a smaller maximum than the issuer's 300-second ceiling.
- Timestamps use current wall-clock seconds; nonce generation supplies a fresh 16-byte value as hexadecimal text.
- The input digest covers parsed, deterministically serialized JSON.
- HMAC authenticates the payload text. The file receives `payload.authenticator` plus a newline; stdout reports only that minting completed.

The issuer is trusted with the shared key. This is not an interface to expose to an untrusted workload with unrestricted signing requests.

### The client

```python
#!/usr/bin/env python3
"""Send one capability-bound operation request."""

import json
from pathlib import Path
import socket
import sys

if len(sys.argv) != 8:
    raise SystemExit(f"usage: {sys.argv[0]} SOCKET TOKEN OP RESOURCE AUDIENCE RUN INPUT_JSON")
request = {
    "token": Path(sys.argv[2]).read_text(encoding="utf-8").strip(),
    "operation": sys.argv[3],
    "resource": sys.argv[4],
    "audience": sys.argv[5],
    "run_id": sys.argv[6],
    "input": json.loads(sys.argv[7]),
}
with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
    stream.settimeout(5)
    stream.connect(sys.argv[1])
    stream.sendall(json.dumps(request, sort_keys=True).encode() + b"\n")
    stream.shutdown(socket.SHUT_WR)
    with stream.makefile("rb") as incoming:
        line = incoming.readline(524289)
    if len(line) > 524288 or not line.endswith(b"\n"):
        raise SystemExit("response must be one bounded JSON line")
    response = json.loads(line)
    if not isinstance(response, dict) or type(response.get("ok")) is not bool:
        raise SystemExit("invalid response shape")
    print(json.dumps(response, sort_keys=True))
raise SystemExit(0 if response["ok"] else 1)
```

### Source, line by line

- The client reads the bearer token from its filename and parses input JSON; it does not read the signing-key or credential files.
- It sends the six exact fields in one newline-terminated request over the broker pathname.
- The write half-close finishes the request direction; the read direction remains open.
- A timeout and size bound limit the response observation. The decoded object must contain a Boolean `ok`.
- Status 0 means an accepted operation; status 1 represents denial or client failure. Inspect the returned JSON, not only the status.

## Exercise 1 - Create synthetic setup material

```bash
(umask 077
 printf '%s' 'FAKE-SIGNING-KEY-09.03-ONLY-000000000000' > signing.key
 printf '%s' 'FAKE-UPSTREAM-CREDENTIAL-09.03' > credential.txt
)
test "$(stat -c '%a' signing.key)" = 600
test "$(stat -c '%a' credential.txt)" = 600
NE_RUN="run-$$"
NE_AUDIENCE="records.lesson"
NE_RESOURCE="record:alpha"
NE_UPSTREAM="$PWD/upstream.sock"
NE_BROKER="$PWD/broker.sock"
python3 - "$NE_RUN" "$NE_AUDIENCE" "$NE_UPSTREAM" <<'PY'
import json
from pathlib import Path
import sys

policy = {
    "version": 1, "run_id": sys.argv[1], "audience": sys.argv[2],
    "max_ttl": 120, "upstream_socket": sys.argv[3],
    "permissions": {"record:alpha": ["read"], "record:beta": ["read"]}
}
Path("policy.json").write_text(json.dumps(policy, indent=2) + "\n")
PY
python3 -m json.tool policy.json
```

The creation mask is scoped to a subshell; effective permissions are checked afterward. These exact fake strings have no real-system authority. The policy permits reads of alpha and beta so a later mismatch isolates **token binding**, not merely the absence of beta from policy. The upstream itself serves only alpha.

## Exercise 2 - Launch registered services

```bash
start_capability_service() {
  NE_UNIT="north-echo-$(id -u)-09-03-$(python3 -c 'import secrets; print(secrets.token_hex(4))').service"
  ../../scripts/labctl.py register-unit 09.03 "$NE_UNIT" || return
  systemd-run --user --collect --quiet --expand-environment=no --service-type=exec \
    --unit="$NE_UNIT" --description="North Echo 09.03 workspace=$PWD" \
    --property=RuntimeMaxSec=300s --property=TimeoutStopSec=3s \
    --property=MemoryMax=67108864 --property=MemorySwapMax=0 \
    --property=TasksMax=16 --property=CPUQuota=50% -- "$@"
}
start_capability_service /usr/bin/python3 "$PWD/synthetic_upstream.py" \
  "$PWD/credential.txt" "$NE_RESOURCE" synthetic-record-value "$NE_UPSTREAM"
NE_UPSTREAM_UNIT="$NE_UNIT"
start_capability_service /usr/bin/python3 "$PWD/capability_broker.py" \
  "$PWD/policy.json" "$PWD/signing.key" "$PWD/credential.txt" "$NE_BROKER"
NE_BROKER_UNIT="$NE_UNIT"
for attempt in {1..50}; do test -S "$NE_BROKER" && test -S "$NE_UPSTREAM" && break; sleep 0.1; done
test -S "$NE_BROKER"
test -S "$NE_UPSTREAM"
test "$(stat -c '%a' "$NE_BROKER")" = 600
test "$(stat -c '%a' "$NE_UPSTREAM")" = 600
```

The helper retains exact ownership registration, literal argv, resource ceilings, and runtime backstop. Absolute source/setup paths avoid depending on the service manager's working directory. Readiness checks effective socket types and permissions.

If startup fails, stop before minting. Inspect `journalctl --user -u "$NE_UPSTREAM_UNIT" -u "$NE_BROKER_UNIT" --no-pager`, then `../../lab-cleanup 09.03`. Do not broaden file modes or disable SELinux.

Mint and spend one capability promptly:

```bash
(umask 077; python3 mint_token.py signing.key token.txt read "$NE_RESOURCE" "$NE_AUDIENCE" "$NE_RUN" 120 '{}')
python3 broker_client.py "$NE_BROKER" token.txt read "$NE_RESOURCE" "$NE_AUDIENCE" "$NE_RUN" '{}' > approved.json
python3 -m json.tool approved.json
```

Expect `ok: true` and `result: {"value": "synthetic-record-value"}`. This establishes a working upstream path before testing denials. The client was given a token file, not the credential value. Again, that is an interface observation, not proof of same-account file isolation.

## Exercise 3 - Deny replay and repair a mismatched request

```bash
NE_REPLAY_STATUS=0
python3 broker_client.py "$NE_BROKER" token.txt read "$NE_RESOURCE" "$NE_AUDIENCE" "$NE_RUN" '{}' \
  > replay.json || NE_REPLAY_STATUS=$?
(umask 077; python3 mint_token.py signing.key deputy.txt read "$NE_RESOURCE" "$NE_AUDIENCE" "$NE_RUN" 120 '{}')
NE_DEPUTY_STATUS=0
python3 broker_client.py "$NE_BROKER" deputy.txt read record:beta "$NE_AUDIENCE" "$NE_RUN" '{}' \
  > wrong-resource.json || NE_DEPUTY_STATUS=$?
python3 -m json.tool replay.json
python3 -m json.tool wrong-resource.json
test "$NE_REPLAY_STATUS" -eq 1
test "$NE_DEPUTY_STATUS" -eq 1
```

Expect `capability replay denied` for the spent token. Expect `request does not match capability` for the fresh alpha token submitted with beta. Both operations are policy-allowed in general, but this particular token does not grant beta.

Repair the request, not the token verifier:

```bash
python3 broker_client.py "$NE_BROKER" deputy.txt read "$NE_RESOURCE" "$NE_AUDIENCE" "$NE_RUN" '{}' > repaired.json
python3 -m json.tool repaired.json
```

The mismatch failed before nonce consumption, so the still-valid fresh token can now authorize its exact operation. By contrast, the earlier successfully spent token remains consumed. If reading took more than two minutes, mint fresh test tokens and repeat the sequence; do not remove expiry checks.

## Checkpoint, cleanup, and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

def result(name):
    return json.loads(Path(name).read_text())

for name in ("approved.json", "repaired.json"):
    observed = result(name)
    assert observed["ok"] is True
    assert observed["result"] == {"value": "synthetic-record-value"}
assert result("replay.json") == {"ok": False, "error": "capability replay denied"}
assert result("wrong-resource.json") == {"ok": False, "error": "request does not match capability"}
for name in ("approved.json", "repaired.json", "replay.json", "wrong-resource.json"):
    assert "FAKE-UPSTREAM-CREDENTIAL-09.03" not in Path(name).read_text()
print("OPERATION BINDING AND PROCESS-LIFETIME REPLAY: PASS")
PY
../../lab-cleanup 09.03 --dry-run
../../lab-cleanup 09.03
test ! -e "$NE_BROKER"
test ! -e "$NE_UPSTREAM"
```

The checker establishes the expected successful and denied exchanges, with no literal credential in those observations. It does not prove every possible disclosure channel is closed. The lab grader independently counts upstream calls during protected attempts; that adds evidence that rejection occurred before contact.

The cleanup planner verifies registered ownership before stopping services. Both socket paths must disappear on normal termination. A pre-existing path or an ownership mismatch is a reason to inspect/reset this exact lesson, never to kill processes by prefix.

Explain why the fake credential and HMAC key are different authorities, why a valid authenticator is insufficient for a substituted request, why failed upstream operations can consume a nonce, and what is lost on broker restart.

Return with `cd ../..`; `./lab-reset 09.03` discards the local fake setup, tokens, observations, and working copy after owned cleanup. Start a fresh run for replay practice. Do not reuse this public fake key as real security material.

## Source truth

Python's [HMAC documentation](https://docs.python.org/3.14/library/hmac.html) covers shared-key authentication, not encryption or durable replay prevention. Its [socket API](https://docs.python.org/3.14/library/socket.html) describes stream operations and timeouts. Linux [unix(7)](https://man7.org/linux/man-pages/man7/unix.7.html) describes pathname permissions; they must not be mistaken for a separate same-account identity boundary.
<!-- /source -->

---

<!-- source: course/module-09-credential-brokering/lab/README.md format=markdown -->
# Module 09 independent lab - Capability-bound credential broker

## Assignment and readiness check

Implement the operation-broker contract practiced in 09.01-09.03. The client submits a narrow capability; the broker holds the broader fake credential. Reject unauthorized requests before upstream contact while preserving the approved operation.

Before coding, explain the difference between HMAC and encryption, token-to-request binding and request-to-policy authorization, expiry and nonce consumption, and API separation versus same-account filesystem isolation. Repeat the relevant guided lesson if one is unclear.

## Prepare and inspect the starter

From the course root:

```bash
./lab-start module-09
cd .student/09.lab
pwd
ls -l capability_broker.py
cat capability_broker.py
nano capability_broker.py
```

Edit this working copy, not canonical course content. With the default nano bindings, Ctrl+O then Enter saves and Ctrl+X exits.

```python
#!/usr/bin/env python3
"""Fail-closed starter for the Module 09 broker interface."""

import json
import os
from pathlib import Path
import signal
import socket
import sys

stopping = False


def stop(_signum, _frame):
    global stopping
    stopping = True


if len(sys.argv) != 5:
    raise SystemExit(f"usage: {sys.argv[0]} POLICY SIGNING_KEY CREDENTIAL SOCKET")
socket_path = Path(sys.argv[4])
if socket_path.exists() or socket_path.is_symlink():
    raise SystemExit("socket path already exists")
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
listener.bind(str(socket_path))
os.chmod(socket_path, 0o600)
listener.listen(4)
listener.settimeout(0.2)
try:
    while not stopping:
        try:
            peer, _ = listener.accept()
        except TimeoutError:
            continue
        with peer:
            peer.settimeout(2)
            try:
                peer.recv(16384)
                peer.sendall(json.dumps({"ok": False, "error": "capability policy is not implemented"}).encode() + b"\n")
            except OSError:
                pass
finally:
    listener.close()
    socket_path.unlink(missing_ok=True)
```

### Starter, line by line

- The imports support a minimal Unix-socket server, not a completed authorization system.
- The stop flag and signal handler permit cooperative loop exit.
- The argument guard expects policy, signing-key, credential, and socket filenames. Only the socket argument is used by this incomplete starter.
- Existing socket paths are refused; the listener uses mode 0600 and a short accept timeout.
- Each accepted connection has an operation timeout. The starter reads bounded bytes and always returns a denial.
- The outer `finally` closes and unlinks the exact listener on normal termination.

The starter is runnable and does not contact upstream, but it deliberately does **not** validate policy/secret setup before listening. Keeping its deny-all response would fail the approved-operation requirement. You must implement validation before listener creation, not merely add a success branch after startup.

## Interface and required behavior

The grader invokes:

```text
python3 capability_broker.py POLICY.json SIGNING_KEY CREDENTIAL SOCKET
```

Policy contains version 1, exact audience and run, maximum lifetime, an absolute synthetic-upstream Unix pathname, and a resource-to-operation allowlist. Signing key and fake credential must be regular non-symlink files with mode 0600 and the bounded lengths practiced in 09.03. Validate trusted setup before creating a mode-0600 broker socket. Refuse a pre-existing socket path.

Each connection carries one bounded JSON line with exactly:

```json
{"token":"PAYLOAD.AUTHENTICATOR","operation":"read","resource":"record:example","audience":"records.example","run_id":"run-example","input":{}}
```

Require canonical URL-safe unpadded base64 and HMAC-SHA256 with digest comparison appropriate for authenticators. Require the complete claim set: version, operation, resource, audience, run, issue time, expiry, nonce, and input SHA-256. The issuer/verifier share a key; this is not a public-key signature scheme.

Reject future, expired, nonpositive, or policy-overlong validity intervals. Timestamps and limits must be integers rather than Booleans. Match request context to claims, then audience/run and operation permission to policy. Bind input using the practiced sorted compact JSON convention with non-finite values rejected.

After all checks, require an unused 32-hex-character nonce. Consume it **before** the upstream operation. Bound remembered nonces to 4096 and fail closed at capacity; do not silently evict a still-live consumed token merely to admit another. This lab's replay state is process-local. Durable cross-restart or multi-broker consumption is not implemented or claimed.

The broker may read the fake credential at trusted startup, but must not send it upstream until authorization succeeds. Send it only with the authorized operation to the configured upstream Unix socket. Bound client input to 16384 bytes and upstream responses to 65536 bytes, require line framing, and use blocking-operation timeouts.

Return one structured response: `ok: true` with `result` for an approved exchange, or `ok: false` with `error` for denial. Reject literal reflection of the fake credential in the upstream response. Never intentionally place the key/credential in capabilities, client responses, logs, argv **values**, or environment variables. Passing their filenames is part of this interface.

Clean SIGTERM/SIGINT termination must remove the exact socket. A denied request or disconnected client must not turn the listener into a permissive fallback.

## Build from practiced skills

- Environment authority and its limits: 09.01 and B1.
- Deterministic input hashing, HMAC, encoding, and time intervals: 09.02.
- Strict token/schema checks, audience/run/policy binding, and nonce consumption: 09.03.
- Unix-socket framing, bounds, actual mode checks, and signal cleanup: Modules 08-09.
- Registered manual service lifecycle and effective resource limits: Module 07.

Before implementation, write down the order of your checks and identify the first line permitted to contact upstream. Also record what restart does to replay state. This explanation is learning evidence, not an automatic test answer.

## Validate your implementation

```bash
python3 -m py_compile capability_broker.py
../../lab-grade module-09
../../lab-grade module-09 --mode exam
```

Compilation checks syntax without starting the server. Practice grading creates fresh synthetic keys, credentials, identities, resources, values, and tokens. It reports failed properties with lesson references. Exam mode reduces repair hints, not the required behavior.

The grader checks approved credential use, absence of the known fake secret in observed responses, replay, tampering, audience/run, lifetime bounds, operation/resource/input substitution, policy denial, exact request shape, private socket mode, insecure-file rejection before listen, and cleanup. It independently observes upstream contacts during rejected attempts.

These finite observations are not a proof of all-channel non-disclosure, race-free same-account secret loading, persistent replay protection, production authentication, or exactly-once execution. State those limits in your notes.

## Troubleshooting and reset

If every request fails, first distinguish setup refusal from token denial and upstream failure. A correct deny-all server is not a functioning authorized service. If only a substituted request succeeds, inspect the binding order; do not special-case fixture names. If a fresh token is expired, check VM time and the chosen lifetime.

The grader owns its processes. For manual debugging, adapt the registered unit helper from 09.03 with target `module-09`, matching exact description and unit-name component. Preview `../../lab-cleanup module-09 --dry-run`, then run `../../lab-cleanup module-09`. Never use wildcard teardown or real credentials.

Return with `cd ../..`; `./lab-reset module-09` discards the working copy and fake fixtures after verified cleanup. Save your own design notes first.
<!-- /source -->

## Security model summary

The client interface receives an authenticated, readable capability rather than the broker's fake service credential. The broker checks claims, policy, context, time, input, and process-local nonce consumption before upstream use. These examples do not isolate same-account access to setup files, persist replay state across restart, guarantee exactly-once execution, or prove all-channel non-disclosure. The external grader adds independent upstream-contact observations for its finite synthetic cases.

## Glossary

- **Ambient authority:** authority available to code without an explicit operation-specific grant.
- **Capability:** an unforgeable or integrity-protected value that conveys specific authority to its holder.
- **Audience:** the broker or service for which a capability is intended.
- **Nonce:** a random identifier whose remembered consumption enables replay checks for a defined lifetime.
- **Replay:** reuse of a previously accepted authorization value.
- **Confused deputy:** a more-privileged component induced to use its authority for a caller-selected target outside the caller's grant.
- **HMAC:** a shared-key message-authentication code; every holder of the key can mint or verify, and claims are not encrypted.

<!-- source: course/module-10-complete-runtime/README.md format=markdown -->
# Module 10 - Compose a complete agent runtime

Assemble the controls from Modules 01-09 in dependency order, then ask a known workload and kernel for evidence of their combined effects. This instrumented teaching runtime has bounded workload resources, fresh user/network namespaces, reduced capabilities, `no_new_privs`, Landlock filesystem policy, default-deny seccomp, an intended capability-mediated Unix-socket exchange, a fixed workload environment, and exact owned-unit collection checks. It is not a production general-purpose agent sandbox.

Play in order: `10.01`, `10.02`, `10.03`, then `module-10`.

Outcomes:

- distinguish launch dependencies from an arbitrary checklist order;
- apply pathname policy before a syscall filter can remove the setup syscalls;
- keep the broker outside the restricted network namespace while demonstrating the intended pathname Unix-socket operation;
- place the launcher and every descendant under cgroup limits before workload creation;
- attest effective namespaces, capabilities, Landlock effects, seccomp mode, cgroup values, credential absence, and broker success;
- propagate workload failure and synchronously collect the exact transient unit.

All data, credentials, capabilities, services, paths, and requests are synthetic and local. The module creates no veth pair, route, firewall rule, public request, real credential, or production target. Prerequisites are Modules 01-09 and the Linux features reported by `./scripts/linux-preflight`.

## Learning route and limits

First validate a dependency plan without claiming it installed controls. Next
compare a native observer before and after the inner guard. Finally compose the
outer layers and compare separate evidence for workload effects, synthetic
broker use, and exact unit/socket teardown. A small static worker bridges to
ordered batch practice without supplying a capstone implementation.

This design does not create private PID/mount views. It permits selected
read-only observations and, on the validated Landlock ABI 7 kernel, does not
enforce ABI 9 pathname Unix-socket-resolution restrictions. Do not claim the
intended broker is the only reachable Unix socket. The tiny opaque-token broker
is a composition fixture, not the full Module 09 authorization protocol.

An attestation here is a local report from known teaching code, not cryptographic
remote attestation or proof that arbitrary workload code tells the truth.
Launcher output capture is not independently byte-bounded. Keep the exercises
small, synthetic, and inside the disposable VM; preserve SELinux enforcement.
<!-- /source -->

---

<!-- source: course/module-10-complete-runtime/lesson-01/README.md format=markdown -->
# 10.01 - Order the complete runtime by dependency

## Outcomes and prerequisites

Complete Modules 01-09. You will turn the controls into a dependency plan, observe an invalid ordering, and repair it without mistaking plan validation for kernel enforcement.

## Concepts before commands

A **dependency** means one action needs a state established by another. It is stronger than a stylistic preference. A **partial order** constrains some pairs without requiring every independent action to have one universal position.

For this runtime, cgroup entry must precede namespace/workload creation so descendants begin inside the resource budget. User-namespace setup precedes privilege reduction because mapping a namespace-local root creates capability state that must then be reduced. Landlock setup precedes this seccomp filter because the final syscall allowlist does not include the Landlock setup operations.

The broker must be ready before the caller tries its mediated operation. Starting it before namespace entry is a convenient design dependency here, not a kernel law saying every broker must start before every network namespace. Pathname sockets can remain reachable through a shared filesystem.

Finally, process exit and unit collection are different observations. Requesting `--collect` is not enough by itself; later code checks that the exact unit is absent.

## Prepare and read the validator and data

From the course root:

```bash
./lab-start 10.01
cd .student/10.01
pwd
ls -l check_order.py broken-plan.json repaired-plan.json
cat check_order.py
cat broken-plan.json
cat repaired-plan.json
```

Use `nano check_order.py` or `nano challenge-plan.json` when navigating or editing. The JSON files are data submitted to the validator, not programs that install kernel controls.

### The plan validator

```python
#!/usr/bin/env python3
"""Validate a complete-runtime launch plan against security dependencies."""

import json
import sys
from pathlib import Path

REQUIRED = {
    "start_broker",
    "enter_cgroup",
    "enter_namespaces",
    "drop_privilege",
    "apply_landlock",
    "apply_seccomp",
    "exec_workload",
    "collect_unit",
}

BEFORE = {
    ("start_broker", "enter_namespaces"),
    ("enter_cgroup", "enter_namespaces"),
    ("enter_namespaces", "drop_privilege"),
    ("drop_privilege", "apply_landlock"),
    ("apply_landlock", "apply_seccomp"),
    ("apply_seccomp", "exec_workload"),
    ("exec_workload", "collect_unit"),
}


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} PLAN.json", file=sys.stderr)
        return 2
    try:
        plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"invalid plan: {error}", file=sys.stderr)
        return 1
    if not isinstance(plan, list) or any(not isinstance(item, str) for item in plan):
        print("invalid plan: expected a JSON array of step names", file=sys.stderr)
        return 1
    if len(plan) != len(set(plan)):
        print("invalid plan: duplicate step", file=sys.stderr)
        return 1
    missing = sorted(REQUIRED - set(plan))
    extra = sorted(set(plan) - REQUIRED)
    if missing or extra:
        print(json.dumps({"ok": False, "missing": missing, "extra": extra}, sort_keys=True))
        return 1
    position = {name: index for index, name in enumerate(plan)}
    violations = sorted(f"{left} must precede {right}" for left, right in BEFORE if position[left] > position[right])
    print(json.dumps({"ok": not violations, "violations": violations}, sort_keys=True))
    return bool(violations)


if __name__ == "__main__":
    raise SystemExit(main())
```

### Source, line by line

- `REQUIRED` is a set of permitted, mandatory phase names. It does not encode their order.
- `BEFORE` is a set of two-element tuples. Each tuple represents one directed dependency: its left phase must precede its right phase.
- The argv guard requires one plan filename. File/JSON errors stop before examining order.
- The shape check requires a list of strings. A dictionary with plausible keys is not the expected plan interface.
- Comparing list length with set length detects duplicate phases.
- Set subtraction finds missing and unknown phases. Their sorted output makes diagnostics stable.
- The dictionary comprehension maps each phase to its list index.
- The final comprehension reports every edge whose positions are reversed, not just the first failure.
- `not violations` is true only for an empty violation list. Returning `bool(violations)` gives exit status 1 for an invalid ordering and 0 for a valid one.

### The deliberately broken plan

```json
[
  "start_broker",
  "enter_cgroup",
  "enter_namespaces",
  "drop_privilege",
  "apply_seccomp",
  "apply_landlock",
  "exec_workload",
  "collect_unit"
]
```

Every required name is present exactly once. The mistake is the relative position of `apply_seccomp` and `apply_landlock`. A checklist that merely searches for both words would miss it.

### The repaired plan

```json
[
  "start_broker",
  "enter_cgroup",
  "enter_namespaces",
  "drop_privilege",
  "apply_landlock",
  "apply_seccomp",
  "exec_workload",
  "collect_unit"
]
```

The repaired list places the filesystem setup before the final syscall restriction. `start_broker` and `enter_cgroup` both precede namespace entry; this graph does not require an edge between those two independent preparations.

## Exercise 1 - Predict the rejected edge

```bash
NE_BROKEN_STATUS=0
python3 check_order.py broken-plan.json > broken-result.json || NE_BROKEN_STATUS=$?
python3 -m json.tool broken-result.json
test "$NE_BROKEN_STATUS" -eq 1
python3 check_order.py repaired-plan.json > repaired-result.json
python3 -m json.tool repaired-result.json
```

Saving the expected failure through `||` avoids changing your interactive shell's error options. Expect `apply_landlock must precede apply_seccomp` in the broken result and an empty violation list in the repaired result.

These are statements about a data structure. No Landlock rules or seccomp filter have been installed by this script. The next lesson tests the actual ordered controls.

## Exercise 2 - Make a different ordering mistake

Copy the known plan, then move cgroup entry too late:

```bash
cp repaired-plan.json challenge-plan.json
python3 - <<'PY'
import json
from pathlib import Path

path = Path("challenge-plan.json")
steps = json.loads(path.read_text())
steps.remove("enter_cgroup")
steps.insert(3, "enter_cgroup")
path.write_text(json.dumps(steps) + "\n")
PY
NE_CHALLENGE_STATUS=0
python3 check_order.py challenge-plan.json > challenge-result.json || NE_CHALLENGE_STATUS=$?
python3 -m json.tool challenge-result.json
test "$NE_CHALLENGE_STATUS" -eq 1
```

`remove` deletes the earlier position; `insert(3,...)` places it after namespace/privilege setup in this list. The plan is still syntactically valid and contains all phases, but violates the requirement to establish resource containment before those descendants.

Open `nano challenge-plan.json`, move `enter_cgroup` before `enter_namespaces`, preserve commas and quoted strings, and save. Then run:

```bash
python3 check_order.py challenge-plan.json > challenge-repaired.json
python3 -m json.tool challenge-repaired.json
```

## Checkpoint, troubleshooting, and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

def result(name):
    return json.loads(Path(name).read_text())

assert "apply_landlock must precede apply_seccomp" in result("broken-result.json")["violations"]
assert "enter_cgroup must precede enter_namespaces" in result("challenge-result.json")["violations"]
for name in ("repaired-result.json", "challenge-repaired.json"):
    assert result(name) == {"ok": True, "violations": []}
print("LAUNCH DEPENDENCIES: PASS")
PY
```

For each edge, explain what the earlier action establishes or what the later action removes. Do not answer merely “because the list says so.” Also name one property this validator cannot prove: effective resource limits, actual privilege reduction, successful policy installation, or teardown.

If parsing fails, restore a JSON array; a syntax error is not the intended ordering observation. If an edge seems unnecessary, distinguish this particular implementation's requirements from universal kernel rules.

Return with `cd ../..`; `./lab-reset 10.01` removes the challenge and results. No service or kernel policy was created.

## Source truth

The [kernel seccomp documentation](https://docs.kernel.org/userspace-api/seccomp_filter.html) and [Landlock documentation](https://cdn.kernel.org/doc/html/latest/userspace-api/landlock.html) describe the mechanisms being composed. The dependency graph itself is this course runtime's design; a passing graph check is not evidence those mechanisms were applied.
<!-- /source -->

---

<!-- source: course/module-10-complete-runtime/lesson-02/README.md format=markdown -->
# 10.02 - Seal filesystem and syscall policy before exec

## Outcomes and prerequisites

Complete 10.01 and the native-code work in Modules 01, 05, and 06. You will run the same fixed native probe before and after a guard, preserve an allowed read, and observe both protected-file and direct-IP denial. This is the inner guard, not the complete outer runtime.

## Concepts before commands

**Composition** requires controls to remain effective together. A seccomp allowlist must allow the intended workload's syscalls while leaving later policy modification unavailable. A Landlock policy must allow the executable and its required data without exposing unrelated files.

A **static executable** includes the needed library code in its binary. It avoids a dynamic loader needing to open shared libraries after filesystem restrictions are installed. Static linking is a teaching simplification, not a universal security guarantee.

This guard permits read-only observations under the current process's `/proc/self` directory and `/sys/fs/cgroup`. These are explicit exceptions, not a private PID/mount view. It does not grant all of `/proc`. Its own process identity survives `exec`, so the self-directory rule still applies to the final workload.

## Prepare and read both sources

From the course root:

```bash
./lab-start 10.02
cd .student/10.02
pwd
ls -l runtime_guard.c guard_probe.c
cat runtime_guard.c
cat guard_probe.c
```

Use `nano runtime_guard.c` to navigate the C functions. Do not edit canonical course files. Read before compiling.

### The native guard

```c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/landlock.h>
#include <linux/close_range.h>
#include <seccomp.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/prctl.h>
#include <sys/socket.h>
#include <sys/syscall.h>
#include <unistd.h>

static int create_ruleset(const struct landlock_ruleset_attr *attr, size_t size, __u32 flags) {
    return syscall(SYS_landlock_create_ruleset, attr, size, flags);
}

static int add_path_rule(int ruleset_fd, const char *path, __u64 access) {
    int path_fd = open(path, O_PATH | O_CLOEXEC);
    if (path_fd == -1)
        return -1;
    struct landlock_path_beneath_attr rule = {.allowed_access = access, .parent_fd = path_fd};
    int result = syscall(SYS_landlock_add_rule, ruleset_fd, LANDLOCK_RULE_PATH_BENEATH, &rule, 0);
    close(path_fd);
    return result;
}

static __u64 supported_rights(int abi) {
    __u64 rights = LANDLOCK_ACCESS_FS_EXECUTE | LANDLOCK_ACCESS_FS_WRITE_FILE |
                   LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_READ_DIR |
                   LANDLOCK_ACCESS_FS_REMOVE_DIR | LANDLOCK_ACCESS_FS_REMOVE_FILE |
                   LANDLOCK_ACCESS_FS_MAKE_CHAR | LANDLOCK_ACCESS_FS_MAKE_DIR |
                   LANDLOCK_ACCESS_FS_MAKE_REG | LANDLOCK_ACCESS_FS_MAKE_SOCK |
                   LANDLOCK_ACCESS_FS_MAKE_FIFO | LANDLOCK_ACCESS_FS_MAKE_BLOCK |
                   LANDLOCK_ACCESS_FS_MAKE_SYM;
    if (abi >= 2)
        rights |= LANDLOCK_ACCESS_FS_REFER;
    if (abi >= 3)
        rights |= LANDLOCK_ACCESS_FS_TRUNCATE;
#ifdef LANDLOCK_ACCESS_FS_IOCTL_DEV
    if (abi >= 5)
        rights |= LANDLOCK_ACCESS_FS_IOCTL_DEV;
#endif
#ifdef LANDLOCK_ACCESS_FS_RESOLVE_UNIX
    if (abi >= 9)
        rights |= LANDLOCK_ACCESS_FS_RESOLVE_UNIX;
#endif
    return rights;
}

static int install_landlock(const char *allowed_root) {
    int abi = create_ruleset(NULL, 0, LANDLOCK_CREATE_RULESET_VERSION);
    if (abi < 1)
        return -1;
    __u64 handled = supported_rights(abi);
    __u64 read_execute = LANDLOCK_ACCESS_FS_EXECUTE | LANDLOCK_ACCESS_FS_READ_FILE |
                          LANDLOCK_ACCESS_FS_READ_DIR;
    __u64 read_only = LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_READ_DIR;
#ifdef LANDLOCK_ACCESS_FS_RESOLVE_UNIX
    /* The broker is intentionally reachable only below the workload root. */
    if (abi >= 9)
        read_execute |= LANDLOCK_ACCESS_FS_RESOLVE_UNIX;
#endif
    fprintf(stderr, "Landlock ABI %d; explicit build-known filesystem policy\n", abi);
    struct landlock_ruleset_attr ruleset = {.handled_access_fs = handled};
    int ruleset_fd = create_ruleset(&ruleset, sizeof(ruleset), 0);
    if (ruleset_fd == -1)
        return -1;
    if (add_path_rule(ruleset_fd, allowed_root, read_execute) == -1 ||
        add_path_rule(ruleset_fd, "/proc/self", read_only) == -1 ||
        add_path_rule(ruleset_fd, "/sys/fs/cgroup", read_only) == -1) {
        close(ruleset_fd);
        return -1;
    }
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) == -1 ||
        syscall(SYS_landlock_restrict_self, ruleset_fd, 0) == -1) {
        close(ruleset_fd);
        return -1;
    }
    close(ruleset_fd);
    return 0;
}

static int allow_name(scmp_filter_ctx context, const char *name) {
    int number = seccomp_syscall_resolve_name(name);
    return number == __NR_SCMP_ERROR ? 0 : seccomp_rule_add(context, SCMP_ACT_ALLOW, number, 0);
}

static int install_seccomp(void) {
    const char *allowed[] = {
        "execve", "read", "write", "close", "openat", "brk", "mmap", "mprotect",
        "munmap", "set_tid_address", "set_robust_list", "prlimit64", "readlink",
        "readlinkat", "getrandom", "rseq", "arch_prctl", "fstat", "newfstatat",
        "faccessat", "lseek", "rt_sigaction", "rt_sigprocmask", "statx", "connect",
        "shutdown", "exit", "exit_group"
    };
    scmp_filter_ctx context = seccomp_init(SCMP_ACT_ERRNO(EPERM));
    if (!context)
        return -1;
    for (size_t index = 0; index < sizeof(allowed) / sizeof(allowed[0]); index++) {
        int error = allow_name(context, allowed[index]);
        if (error < 0) {
            seccomp_release(context);
            errno = -error;
            return -1;
        }
    }
    int socket_number = seccomp_syscall_resolve_name("socket");
    int error = socket_number == __NR_SCMP_ERROR ? -EINVAL :
        seccomp_rule_add(context, SCMP_ACT_ALLOW, socket_number, 1,
                         SCMP_A0(SCMP_CMP_EQ, AF_UNIX));
    if (error == 0)
        error = seccomp_load(context);
    if (error < 0) {
        seccomp_release(context);
        errno = -error;
        return -1;
    }
    seccomp_release(context);
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: %s ALLOWED_ROOT COMMAND [ARG...]\n", argv[0]);
        return 2;
    }
    if (syscall(SYS_close_range, 3U, ~0U, CLOSE_RANGE_CLOEXEC) == -1) {
        perror("mark inherited descriptors close-on-exec");
        return 1;
    }
    if (install_landlock(argv[1]) == -1) {
        perror("install Landlock");
        return 1;
    }
    if (install_seccomp() == -1) {
        perror("install seccomp");
        return 1;
    }
    execv(argv[2], &argv[2]);
    perror("execv");
    return 1;
}
```

### Source, line by line

- The headers provide Linux policy constants, syscall numbers, descriptor flags, libseccomp, and normal C error/I/O declarations.
- `create_ruleset` calls the Landlock syscall directly, as in Module 05.
- `add_path_rule` anchors a path with an `O_PATH` descriptor, builds a path-beneath rule, adds it, and closes that temporary descriptor.
- `supported_rights` constructs a bitmask of named filesystem rights. ABI checks gate later rights; preprocessor checks separately gate constants available in build headers.
- `install_landlock` queries the running ABI. It distinguishes the full handled set from the smaller grants: execute/read beneath the workload root and read-only observation directories.
- Filesystem operations covered by handled rights but not granted are denied. Unnamed future rights are not automatically covered; ABI number alone is not proof of complete future-right coverage.
- Unix-socket path resolution is additionally scoped only when **both** ABI 9 support and its build-header constant exist. The validated Fedora ABI 7 baseline does not demonstrate that newer restriction.
- `PR_SET_NO_NEW_PRIVS` precedes self-restriction. Failure returns before workload execution.
- `allow_name` resolves syscall names for the native architecture. Names unavailable on that ABI are not granted; available-rule errors stop setup.
- `install_seccomp` begins with EPERM as the default. Its small allowlist supports the static observation workload and Unix-socket operation, not general Python or shell execution.
- The separate `socket` rule checks argument zero for `AF_UNIX`. Other address families remain denied. Allowing `connect` does not itself authorize the operation carried over a permitted Unix socket.
- libseccomp reports negative error numbers; the helper converts them into `errno` before the caller prints a diagnostic.
- `main` marks inherited descriptors 3 and above close-on-exec. Failure stops rather than leaving inherited authority available.
- Landlock is installed before seccomp. Finally, `execv` replaces the guard with the supplied executable while preserving separate argv elements.
- An `execv` return means execution failed; it prints an error and exits nonzero.

The inner guard does not create namespaces, empty the environment, lower all capability sets, or impose cgroup limits. Those outer steps come in 10.03. A successful inner-guard demonstration must not be described as a complete runtime.

### The observation program

```c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

static int readable(const char *path) {
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd == -1)
        return 0;
    char byte;
    int ok = read(fd, &byte, 1) == 1;
    close(fd);
    return ok;
}

static int status_number(const char *name) {
    FILE *stream = fopen("/proc/self/status", "r");
    char line[256];
    int value = -1;
    while (stream && fgets(line, sizeof(line), stream))
        if (sscanf(line, name, &value) == 1)
            break;
    if (stream)
        fclose(stream);
    return value;
}

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s ALLOWED_FILE PROTECTED_FILE\n", argv[0]);
        return 2;
    }
    int allowed = readable(argv[1]);
    errno = 0;
    int protected = readable(argv[2]);
    int protected_errno = errno;
    errno = 0;
    int inet = socket(AF_INET, SOCK_STREAM, 0);
    int inet_errno = errno;
    if (inet != -1)
        close(inet);
    printf("allowed=%d protected=%d protected_errno=%s inet_fd=%d inet_errno=%s nnp=%d seccomp=%d\n",
           allowed, protected, strerror(protected_errno), inet, strerror(inet_errno),
           status_number("NoNewPrivs:\t%d"), status_number("Seccomp:\t%d"));
    return 0;
}
```

### Source, line by line

- `readable` opens a file and attempts a one-byte read. It closes the descriptor whether the read succeeds or not.
- `status_number` opens this process's status file, scans for one named field, and returns -1 when no usable value was observed.
- `main` requires an allowed and protected filename. It performs actual reads, rather than trusting path text or mode bits.
- Resetting and saving `errno` keeps the protected-open and socket observations separate.
- The IPv4 socket is closed if creation succeeds. The probe sends no network traffic.
- The final line prints observed operations and kernel-reported no-new-privileges/seccomp state. The observer returns 0 on completion even when a tested operation was denied; inspect its fields.

## Exercise 1 - Compile and establish a working baseline

```bash
gcc -O2 -Wall -Wextra -static runtime_guard.c -o runtime_guard -lseccomp
gcc -O2 -Wall -Wextra -static guard_probe.c -o guard_probe
NE_DEMO=$(mktemp -d "$PWD/d.XXXXXX")
mkdir "$NE_DEMO/allowed"
cp guard_probe "$NE_DEMO/allowed/guard_probe"
printf 'allowed\n' > "$NE_DEMO/allowed/input.txt"
printf 'synthetic-protected\n' > "$NE_DEMO/protected.txt"
"$NE_DEMO/allowed/guard_probe" "$NE_DEMO/allowed/input.txt" "$NE_DEMO/protected.txt" > baseline.txt
cat baseline.txt
```

Warnings remain visible; only the guard links libseccomp. The exact new temporary directory is inside this prepared workspace, so scoped lesson reset owns the files. The protected file is synthetic and readable by your account.

Expect `allowed=1 protected=1` and a nonnegative IPv4 descriptor. Existing no-new-privileges/seccomp values depend on the parent environment; do not assume they must start at zero. The intentional incomplete control is launching a trusted observer without enforcing a boundary.

## Exercise 2 - Apply the ordered repair

```bash
./runtime_guard "$NE_DEMO/allowed" "$NE_DEMO/allowed/guard_probe" \
  "$NE_DEMO/allowed/input.txt" "$NE_DEMO/protected.txt" > guarded.txt
cat guarded.txt
```

Expect the equivalent of:

```text
allowed=1 protected=0 protected_errno=Permission denied inet_fd=-1 inet_errno=Operation not permitted nnp=1 seccomp=2
```

The allowed read proves useful functionality remains. The same synthetic protected file was readable in the baseline but is now denied. The IPv4 socket creation is denied separately. Status fields show the restrictions survived `exec`; neither field alone proves policy content.

Error wording can vary with locale; the numeric/Boolean fields are the stable part. The ABI diagnostic goes to stderr, while the observation is saved on stdout.

## Checkpoint, troubleshooting, and replay

```bash
python3 - <<'PY'
from pathlib import Path
import re

baseline = Path("baseline.txt").read_text()
guarded = Path("guarded.txt").read_text()
assert "allowed=1 protected=1" in baseline
assert int(re.search(r"inet_fd=(-?\d+)", baseline).group(1)) >= 0
assert "allowed=1 protected=0" in guarded
assert "inet_fd=-1" in guarded
assert "nnp=1 seccomp=2" in guarded
print("FILESYSTEM AND SYSCALL COMPOSITION: PASS")
PY
```

Explain why successful seccomp installation does not prove a correct pathname policy, and why one protected-file denial says nothing about the availability of a different socket family. Lesson 10.03 will demonstrate the permitted Unix-socket path under the complete composition.

If static linking fails, run `../../scripts/linux-preflight` and inspect the distribution's documented development/static-library prerequisites. On Fedora these include `glibc-static` and `libseccomp-static`; do not weaken filesystem policy to expose dynamic libraries. If `execv` fails, verify that the executable was copied beneath the allowed root. If Landlock is unavailable, repair the supported VM baseline; do not use a permissive fallback.

Return with `cd ../..`; `./lab-reset 10.02` removes the exact prepared workspace, binaries, and synthetic directory. There are no background services. Keep SELinux enforcement enabled.

## Source truth

The [Landlock userspace documentation](https://cdn.kernel.org/doc/html/latest/userspace-api/landlock.html) distinguishes handled rights, grants, and ABI availability. The [seccomp filter documentation](https://docs.kernel.org/userspace-api/seccomp_filter.html) describes syscall/argument filtering. These APIs compose restrictions; they do not certify the completeness of this course's policy.
<!-- /source -->

---

<!-- source: course/module-10-complete-runtime/lesson-03/README.md format=markdown -->
# 10.03 - Launch, observe, and collect the composed runtime

## Outcomes and prerequisites

Complete 10.01-10.02 and Modules 01-09. You will compare an incomplete inner-only launch with the outer composition, interpret each effective-state field, and verify exact service collection. The final exercise bridges single-job execution to the independent batch capstone.

## Concepts before commands

The composition has several jobs: constrain resources before descendants start, create private user/network views, reduce privilege, clear the workload environment, install filesystem/syscall policy, permit one intended broker exchange, then collect owned runtime objects.

A **trusted computing base (TCB)** is the code and configuration whose correctness the design relies on. Here it includes the VM kernel, user service manager, launcher, guard, and broker. A valid filename does not establish that a guard's contents are trustworthy; the exercise supplies trusted code.

The word **attestation** in this small program means a local structured observation. It is not a hardware-signed report or proof that arbitrary malicious workload code tells the truth. The grader compiles its own known observer to check behavior independently.

Keep the baseline limits visible. This composition creates user/network namespaces, not private mount/PID namespaces. Its Landlock policy permits selected read-only observation paths. On the validated Fedora ABI 7 baseline, Landlock does not enforce the newer ABI 9 pathname Unix-socket-resolution right. Successful access to the intended broker is therefore **not proof that no other pathname Unix socket is reachable**. The minimal static workload and finite checks are not a production general-purpose agent sandbox.

## Prepare and locate the sources

From the course root:

```bash
./lab-start 10.03
cd .student/10.03
pwd
ls -l complete_runtime.py runtime_probe.c demo_broker.py batch_worker.c
cat complete_runtime.py
cat runtime_probe.c
cat demo_broker.py
cat batch_worker.c
```

The guard source from 10.02 remains available under the course tree for compilation. You read it in that lesson; do not edit it there. Every new local source is reproduced below.

### The outer launcher

```python
#!/usr/bin/env python3
"""Launch one synthetic workload through the North Echo containment stack."""

import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time


def integer(spec: dict, name: str, minimum: int, maximum: int) -> int:
    value = spec.get(name)
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer from {minimum} through {maximum}")
    return value


def validated(spec: dict) -> tuple[Path, Path, list[str], int, int, int]:
    fields = {"guard", "allowed_root", "command", "memory_max", "tasks_max", "cpu_percent"}
    if not isinstance(spec, dict) or set(spec) != fields:
        raise ValueError("spec must be an object with exactly the documented fields")
    if not all(isinstance(spec[name], str) for name in ("guard", "allowed_root")):
        raise ValueError("guard and allowed_root must be path strings")
    guard, root = Path(spec["guard"]), Path(spec["allowed_root"])
    command = spec["command"]
    if not guard.is_absolute() or not guard.is_file() or guard.is_symlink():
        raise ValueError("guard must be an absolute regular non-symlink path")
    if not root.is_absolute() or not root.is_dir() or root.is_symlink():
        raise ValueError("allowed_root must be an absolute directory without a symlink leaf")
    if not isinstance(command, list) or not command or any(
            not isinstance(item, str) or "\x00" in item for item in command):
        raise ValueError("command must be a nonempty argv string array")
    if not Path(command[0]).is_absolute():
        raise ValueError("command executable must be absolute")
    root = root.resolve(strict=True)
    if root == Path("/"):
        raise ValueError("the whole filesystem cannot be the workload root")
    executable = Path(command[0]).resolve(strict=True)
    if os.path.commonpath((root, executable)) != str(root) or not executable.is_file():
        raise ValueError("command executable must resolve beneath allowed_root")
    return (
        guard.resolve(strict=True), root, [str(executable), *command[1:]],
        integer(spec, "memory_max", 16 * 1024 * 1024, 1024 * 1024 * 1024),
        integer(spec, "tasks_max", 4, 256),
        integer(spec, "cpu_percent", 10, 100),
    )


def register_owner(client_env: dict) -> dict:
    workspace = Path(__file__).resolve().parent
    prepared = workspace.parent.name == ".student"
    target = workspace.name if prepared else "10.lab"
    if target not in {"10.03", "10.lab"}:
        raise ValueError("unsupported prepared runtime workspace")
    unit = f"north-echo-{os.getuid()}-{target.replace('.', '-')}-{secrets.token_hex(6)}.service"
    owner = {"unit": unit, "uid": os.getuid(),
             "description": f"North Echo {target} workspace={workspace}", "record": None}
    if prepared:
        control = workspace.parent.parent / "scripts/labctl.py"
        subprocess.run([sys.executable, str(control), "register-unit", target, unit],
                       check=True, capture_output=True, text=True, timeout=5, env=client_env)
    else:
        # The external grader copies this file into a separate owned directory.
        runtime = workspace / ".runtime"
        if runtime.is_symlink():
            raise ValueError("refusing a symlinked ownership directory")
        runtime.mkdir(mode=0o700, exist_ok=True)
        record = runtime / (unit + ".json")
        with record.open("x", encoding="utf-8") as stream:
            json.dump(owner, stream, sort_keys=True)
        owner["record"] = record
    return owner


def inspect_unit(owner: dict, client_env: dict) -> dict | None:
    run = subprocess.run(
        ["systemctl", "--user", "show", owner["unit"], "--property=LoadState",
         "--property=Description", "--property=ControlGroup"],
        text=True, capture_output=True, timeout=5, env=client_env,
    )
    properties = dict(line.split("=", 1) for line in run.stdout.splitlines() if "=" in line)
    if properties.get("LoadState") == "not-found":
        return None
    if run.returncode or not properties.get("LoadState"):
        raise RuntimeError("unit state could not be established; ownership record retained")
    return properties


def collect_owned(owner: dict, client_env: dict) -> None:
    properties = inspect_unit(owner, client_env)
    if properties is not None:
        group = properties.get("ControlGroup", "")
        prefix = f"/user.slice/user-{owner['uid']}.slice/user@{owner['uid']}.service/"
        if (properties.get("Description") != owner["description"]
                or not group.startswith(prefix) or not group.endswith("/" + owner["unit"])):
            raise RuntimeError("unit ownership mismatch; refusing stop and retaining record")
        subprocess.run(["systemctl", "--user", "stop", owner["unit"]],
                       check=True, capture_output=True, timeout=5, env=client_env)
        for _ in range(20):
            if inspect_unit(owner, client_env) is None:
                break
            time.sleep(0.05)
        else:
            raise RuntimeError("unit remains after stop; ownership record retained")
        if Path("/sys/fs/cgroup" + group).exists():
            raise RuntimeError("owned cgroup remains; ownership record retained")
    if owner["record"] is not None:
        owner["record"].unlink()


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} SPEC.json RESULT.json", file=sys.stderr)
        return 2
    result_path = Path(sys.argv[2])
    try:
        spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        guard, root, command, memory, tasks, cpu = validated(spec)
    except (OSError, ValueError, TypeError) as error:
        print(f"runtime specification denied: {error}", file=sys.stderr)
        return 1

    client_env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
    for name in ("XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS"):
        if name in os.environ:
            client_env[name] = os.environ[name]
    try:
        owner = register_owner(client_env)
        unit = owner["unit"]
        argv = [
            "systemd-run", "--user", "--wait", "--pipe", "--collect", "--quiet",
            "--expand-environment=no", f"--unit={unit}", f"--description={owner['description']}",
            "--property=KillMode=control-group", "--property=TimeoutStopSec=2s",
            "--property=RuntimeMaxSec=15s", "--property=CPUQuotaPeriodSec=100ms",
            f"--property=CPUQuota={cpu}%", f"--property=MemoryMax={memory}",
            "--property=MemorySwapMax=0", f"--property=TasksMax={tasks}",
            "--property=UnsetEnvironment=NORTH_ECHO_FAKE_CREDENTIAL",
            "--setenv=PATH=/usr/bin:/bin", "--setenv=LANG=C.UTF-8", "--setenv=LC_ALL=C.UTF-8",
            "--", "/usr/bin/unshare", "--user", "--map-root-user", "--net", "--",
            "/usr/bin/setpriv", "--bounding-set=-all", "--inh-caps=-all", "--ambient-caps=-all",
            "--no-new-privs", "--", "/usr/bin/env", "-i", "PATH=/usr/bin:/bin",
            "LANG=C.UTF-8", "LC_ALL=C.UTF-8", str(guard), str(root), *command,
        ]
        try:
            run = subprocess.run(argv, text=True, capture_output=True, check=False,
                                 timeout=20, env=client_env)
        finally:
            collect_owned(owner, client_env)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"runtime launch or collection failed: {error}", file=sys.stderr)
        return 1

    attestation = None
    try:
        attestation = json.loads(run.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        pass
    result_path.write_text(json.dumps({
        "schema": 1, "status": run.returncode, "unit": unit,
        "stdout": run.stdout, "stderr": run.stderr, "attestation": attestation,
    }, sort_keys=True) + "\n", encoding="utf-8")
    return int(run.returncode != 0)


if __name__ == "__main__":
    raise SystemExit(main())
```

### Source, line by line

- `integer` enforces bounds and rejects Boolean values. `validated` requires the exact spec fields before creating a unit or result.
- Guard/root fields must be absolute paths of the expected kind. The guard is trusted setup input, not an executable chosen by an untrusted tool request.
- Command arguments must be separate strings without NUL characters. Its executable must be absolute and resolve beneath the allowed root; the whole filesystem is refused as a root.
- `commonpath` compares path components, not textual prefixes. These checks assume operator-controlled setup paths; they are not race-free validation against a concurrent directory writer.
- `register_owner` records exact name, UID, and workspace description before launch. In prepared 10.03/10.lab workspaces it uses the course runtime registry; `module-10` is a CLI alias, not the directory name.
- The external grader copies the file into its own directory without the course launcher. That case writes an exclusive ownership record in a local `.runtime` directory.
- `inspect_unit` asks the user manager for exact-unit properties. Explicit `LoadState=not-found` means absent; a manager error is not absence.
- `collect_owned` verifies description and delegated cgroup path before stopping a remaining unit. It waits for observed absence and checks the recorded cgroup is gone. Unknown ownership keeps evidence and refuses mutation.
- `client_env` preserves only fixed locale/path plus the IPC variables needed to reach the user manager. These are for the trusted systemd client, not the final workload.
- The argv list uses `--expand-environment=no`. A Python list alone would not prevent systemd's own environment-reference expansion.
- `--wait --pipe --collect` waits for completion and captures output. CPU period is explicitly 100 ms; CPU/memory/swap/tasks and runtime/stop limits are set before descendants start.
- `unshare` establishes the private user/network views. `setpriv` then clears bounding, inheritable, and ambient sets and sets no-new-privileges. The observer checks all five capability sets after execution.
- `env -i` constructs the final fixed workload environment. The native guard then marks extra descriptors close-on-exec, applies Landlock, applies seccomp, and executes exact workload argv.
- The `finally` around execution runs owned collection on normal return, failure, or client timeout. A result is not published as a completed run if launch/collection raises an error.
- The last stdout line is parsed as an observation when possible. The result separately retains status, full stdout/stderr, and unit identity; the launcher does not infer every security property from status alone.

This teaching launcher captures output in memory. Its time and workload-resource limits are not a separate strict byte quota on the outer launcher's capture buffer. Use the supplied small observers; a production runner needs bounded streaming, stronger setup-file trust, and additional threat-model work.

### The confined observer

```c
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <unistd.h>

static int read_text(const char *path, char *buffer, size_t size) {
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd == -1)
        return -1;
    ssize_t count = read(fd, buffer, size - 1);
    close(fd);
    if (count < 0)
        return -1;
    buffer[count] = '\0';
    return 0;
}

static int status_value(const char *status, const char *name, unsigned long long *value) {
    const char *line = strstr(status, name);
    if (!line)
        return -1;
    return sscanf(line + strlen(name), "%llx", value) == 1 ? 0 : -1;
}

static int status_decimal(const char *status, const char *name, int *value) {
    const char *line = strstr(status, name);
    if (!line)
        return -1;
    return sscanf(line + strlen(name), "%d", value) == 1 ? 0 : -1;
}

static int read_cgroup_value(const char *name, char *value, size_t size) {
    char membership[4096], relative[PATH_MAX], path[PATH_MAX];
    if (read_text("/proc/self/cgroup", membership, sizeof(membership)) == -1)
        return -1;
    char *line = strstr(membership, "0::");
    if (!line || sscanf(line, "0::%4095[^\n]", relative) != 1)
        return -1;
    if (snprintf(path, sizeof(path), "/sys/fs/cgroup%s/%s", relative, name) >= (int)sizeof(path))
        return -1;
    if (read_text(path, value, size) == -1)
        return -1;
    value[strcspn(value, "\n")] = '\0';
    return 0;
}

static int broker_request(const char *socket_path, const char *request_path,
                          const char *forbidden_marker, char *response, size_t size) {
    char request[16384];
    if (read_text(request_path, request, sizeof(request)) == -1)
        return 0;
    size_t length = strlen(request);
    if (length == 0 || request[length - 1] != '\n')
        return 0;
    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd == -1)
        return 0;
    struct sockaddr_un address = {.sun_family = AF_UNIX};
    if (strlen(socket_path) >= sizeof(address.sun_path)) {
        close(fd);
        return 0;
    }
    strcpy(address.sun_path, socket_path);
    if (connect(fd, (struct sockaddr *)&address, sizeof(address)) == -1 ||
        write(fd, request, length) != (ssize_t)length) {
        close(fd);
        return 0;
    }
    shutdown(fd, SHUT_WR);
    size_t used = 0;
    while (used < size - 1) {
        ssize_t count = read(fd, response + used, size - 1 - used);
        if (count == -1 && errno == EINTR)
            continue;
        if (count < 0) {
            close(fd);
            return 0;
        }
        if (count == 0)
            break;
        used += (size_t)count;
        if (memchr(response, '\n', used))
            break;
    }
    close(fd);
    if (used == 0 || used == size - 1)
        return 0;
    response[used] = '\0';
    return strcmp(response, "{\"ok\":true,\"result\":{\"value\":\"synthetic-result\"}}\n") == 0
           && strstr(response, forbidden_marker) == NULL;
}

int main(int argc, char **argv) {
    if (argc != 8) {
        fprintf(stderr, "usage: %s ALLOWED PROTECTED BROKER REQUEST HOST_NET_INODE HOST_USER_INODE FORBIDDEN_MARKER\n", argv[0]);
        return 2;
    }
    char byte[8], status[16384], cpu[128] = "?", memory[128] = "?";
    char swap[128] = "?", pids[128] = "?", broker_response[65536];
    int allowed_read = read_text(argv[1], byte, sizeof(byte)) == 0;
    errno = 0;
    int protected_fd = open(argv[2], O_RDONLY | O_CLOEXEC);
    int protected_denied = protected_fd == -1 && (errno == EACCES || errno == EPERM);
    if (protected_fd != -1)
        close(protected_fd);

    int inet_fd = socket(AF_INET, SOCK_STREAM, 0);
    int inet_denied = inet_fd == -1 && errno == EPERM;
    if (inet_fd != -1)
        close(inet_fd);

    struct stat net_stat, user_stat;
    unsigned long long host_net = strtoull(argv[5], NULL, 10);
    int private_net = stat("/proc/self/ns/net", &net_stat) == 0 &&
                      (unsigned long long)net_stat.st_ino != host_net;
    unsigned long long host_user = strtoull(argv[6], NULL, 10);
    int private_user = stat("/proc/self/ns/user", &user_stat) == 0 &&
                       (unsigned long long)user_stat.st_ino != host_user;

    unsigned long long cap_eff = 1, cap_bnd = 1, cap_amb = 1, cap_prm = 1, cap_inh = 1;
    int no_new_privs = 0, seccomp = 0;
    int status_ok = read_text("/proc/self/status", status, sizeof(status)) == 0 &&
                    status_value(status, "CapEff:\t", &cap_eff) == 0 &&
                    status_value(status, "CapBnd:\t", &cap_bnd) == 0 &&
                    status_value(status, "CapAmb:\t", &cap_amb) == 0 &&
                    status_value(status, "CapPrm:\t", &cap_prm) == 0 &&
                    status_value(status, "CapInh:\t", &cap_inh) == 0 &&
                    status_decimal(status, "NoNewPrivs:\t", &no_new_privs) == 0 &&
                    status_decimal(status, "Seccomp:\t", &seccomp) == 0;
    read_cgroup_value("cpu.max", cpu, sizeof(cpu));
    read_cgroup_value("memory.max", memory, sizeof(memory));
    read_cgroup_value("memory.swap.max", swap, sizeof(swap));
    read_cgroup_value("pids.max", pids, sizeof(pids));
    int broker_ok = broker_request(argv[3], argv[4], argv[7], broker_response, sizeof(broker_response));
    int credential_absent = getenv("NORTH_ECHO_FAKE_CREDENTIAL") == NULL;

    printf("{\"allowed_read\":%s,\"protected_denied\":%s,\"inet_denied\":%s,"
           "\"private_net\":%s,\"private_user\":%s,\"caps_zero\":%s,\"no_new_privs\":%d,"
           "\"seccomp\":%d,\"cpu\":\"%s\",\"memory\":\"%s\","
           "\"swap\":\"%s\",\"pids\":\"%s\",\"broker_ok\":%s,"
           "\"credential_absent\":%s}\n",
           allowed_read ? "true" : "false", protected_denied ? "true" : "false",
           inet_denied ? "true" : "false", private_net ? "true" : "false",
           private_user ? "true" : "false",
           status_ok && cap_eff == 0 && cap_bnd == 0 && cap_amb == 0 &&
           cap_prm == 0 && cap_inh == 0 ? "true" : "false",
           no_new_privs, seccomp, cpu, memory, swap, pids,
           broker_ok ? "true" : "false", credential_absent ? "true" : "false");
    return !(allowed_read && protected_denied && inet_denied && private_net && private_user &&
             status_ok && cap_eff == 0 && cap_bnd == 0 && cap_amb == 0 &&
             cap_prm == 0 && cap_inh == 0 &&
             no_new_privs == 1 && seccomp == 2 && broker_ok && credential_absent);
}
```

### Source, block by block

- `read_text` opens a path, reads a bounded buffer, closes the descriptor, and terminates the C string.
- Status helpers locate hexadecimal capability fields and decimal policy fields in this process's status text.
- `read_cgroup_value` derives the process's own unified cgroup path from `0::...`, then reads controller files. It does not infer effective values from the launch spec.
- `broker_request` reads a small prebuilt request, requires its newline, checks pathname length, and creates an AF_UNIX socket.
- The response read loops over a byte stream rather than assuming one read is a whole message. Its final comparison expects the exact compact synthetic response from this fixture; it is not a general JSON parser.
- The main observer performs allowed/protected reads and an AF_INET socket attempt. It records actual denials, not just the existence of policy APIs.
- Namespace inode numbers are compared with saved parent observations. Different numbers establish different namespace objects, not every desired property of their contents.
- Effective, permitted, inheritable, bounding, and ambient capabilities are checked along with no-new-privileges and seccomp mode.
- CPU, memory, swap, and task values are printed for an external checkpoint to compare against the requested profile.
- A successful intended broker exchange and absence of the named fake environment variable are separate fields.
- The exit status aggregates the fixed Boolean checks. Resource-profile equality still requires comparing the printed values with the spec.

### The outside synthetic broker

```python
#!/usr/bin/env python3
"""One-shot synthetic operation broker for the composition lesson."""

import hashlib
import json
import os
from pathlib import Path
import socket
import signal
import sys


def stop(_signum, _frame):
    raise SystemExit(0)


def main() -> int:
    if len(sys.argv) != 5:
        return 2
    socket_path, token_path, credential_path, event_path = map(Path, sys.argv[1:])
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    token = token_path.read_text(encoding="utf-8").strip()
    credential = credential_path.read_text(encoding="utf-8").strip()
    if socket_path.exists() or socket_path.is_symlink():
        raise SystemExit("broker socket path already exists")
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        listener.bind(str(socket_path))
        os.chmod(socket_path, 0o600)
        listener.listen(1)
        listener.settimeout(300)
        peer, _ = listener.accept()
        with peer:
            peer.settimeout(2)
            with peer.makefile("rb") as incoming:
                line = incoming.readline(16385)
            if len(line) > 16384 or not line.endswith(b"\n"):
                raise ValueError("request must be one bounded line")
            request = json.loads(line)
            expected = {"operation": "read", "resource": "synthetic:record", "token": token}
            if request != expected:
                response = {"ok": False, "error": "capability denied"}
            else:
                proof = hashlib.sha256((credential + ":read:synthetic:record").encode()).hexdigest()
                event_path.write_text(json.dumps({"credential_used": True, "proof": proof}) + "\n",
                                      encoding="utf-8")
                response = {"ok": True, "result": {"value": "synthetic-result"}}
            peer.sendall(json.dumps(response, sort_keys=True, separators=(",", ":")).encode() + b"\n")
    finally:
        listener.close()
        socket_path.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### Source, line by line

- The broker reads a random opaque token and a fake credential from files outside the workload root.
- It creates a mode-0600 pathname socket below the workload root, where the intended caller can reach it.
- It accepts one bounded request with a peer timeout, requiring the exact token, operation, and resource.
- Success hashes the fake credential plus fixed operation context into a separate event and returns only the harmless synthetic value.
- This event demonstrates use of the fake value by trusted teaching code. There is no separate credential-protected upstream in this smaller composition fixture; 09.03 supplied that fuller example.
- The token is an opaque one-operation teaching grant, **not** the full HMAC/expiry/replay protocol from Module 09. Do not claim this fixture reimplements that protocol.
- The listener is one-shot, and normal SIGTERM/SIGINT cleanup removes its socket. The runtime backstop limits an abandoned instance.

### A small worker for later batch practice

```c
#define _GNU_SOURCE
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv) {
    if (argc != 2)
        return 2;
    char *end;
    long status = strtol(argv[1], &end, 10);
    if (!*argv[1] || *end || status < 0 || status > 125)
        return 2;
    FILE *membership = fopen("/proc/self/cgroup", "r");
    char line[PATH_MAX], relative[PATH_MAX], path[PATH_MAX];
    int found = 0;
    while (membership && fgets(line, sizeof(line), membership)) {
        if (sscanf(line, "0::%4095[^\n]", relative) == 1) {
            found = 1;
            break;
        }
    }
    if (membership)
        fclose(membership);
    if (!found || snprintf(path, sizeof(path), "/sys/fs/cgroup%s/memory.max", relative)
            >= (int)sizeof(path))
        return 2;
    FILE *limit = fopen(path, "r");
    unsigned long long memory;
    int observed = limit && fscanf(limit, "%llu", &memory) == 1;
    if (limit)
        fclose(limit);
    if (!observed)
        return 2;
    printf("{\"requested_status\":%ld,\"memory\":%llu}\n", status, memory);
    return (int)status;
}
```

### Source, line by line

- `strtol` parses a requested ordinary exit code from 0 through 125 and rejects trailing text.
- The membership loop finds this process's unified cgroup path and closes its file.
- Bounded `snprintf` constructs the memory-controller filename, refusing truncation.
- Reading an integer from `memory.max` requires a finite numeric limit; `max` would not be accepted as a number.
- The final JSON reports the requested status and the **observed** memory ceiling, then exits with that status. This worker does not need a broker.

## Exercise 1 - Build local synthetic fixtures

```bash
NE_DEMO=$(mktemp -d "$PWD/d.XXXXXX")
mkdir "$NE_DEMO/allowed"
gcc -O2 -Wall -Wextra -static \
  ../../course/module-10-complete-runtime/lesson-02/runtime_guard.c \
  -o "$NE_DEMO/runtime_guard" -lseccomp
gcc -O2 -Wall -Wextra -static runtime_probe.c -o "$NE_DEMO/allowed/runtime_probe"
gcc -O2 -Wall -Wextra -static batch_worker.c -o "$NE_DEMO/allowed/batch_worker"
python3 - "$NE_DEMO" <<'PY'
import json
from pathlib import Path
import secrets
import sys

root = Path(sys.argv[1])
token = "CAP-" + secrets.token_hex(16)
credential = "FAKE-CREDENTIAL-" + secrets.token_hex(16)
(root / "allowed/allowed.txt").write_text("allowed\n")
(root / "protected.txt").write_text("synthetic-protected\n")
for name, value in (("token.txt", token), ("credential.txt", credential)):
    with (root / name).open("x") as stream:
        stream.write(value + "\n")
    (root / name).chmod(0o600)
(root / "allowed/request.json").write_text(json.dumps({
    "operation": "read", "resource": "synthetic:record", "token": token
}, sort_keys=True, separators=(",", ":")) + "\n")
PY
NE_HOST_NET=$(stat -Lc '%i' /proc/self/ns/net)
NE_HOST_USER=$(stat -Lc '%i' /proc/self/ns/user)
```

The new directory is inside this prepared workspace. Static binaries avoid dynamic-loader exceptions. Random token/credential values stay synthetic; only the narrow request goes below the workload root. `stat -L` follows the namespace link to obtain the parent namespace object's inode for comparison.

Define a registered helper for the outside broker:

```bash
start_demo_broker() {
  NE_BROKER_UNIT="north-echo-$(id -u)-10-03-$(python3 -c 'import secrets; print(secrets.token_hex(4))').service"
  ../../scripts/labctl.py register-unit 10.03 "$NE_BROKER_UNIT" || return
  systemd-run --user --collect --quiet --expand-environment=no --service-type=exec \
    --unit="$NE_BROKER_UNIT" --description="North Echo 10.03 workspace=$PWD" \
    --property=RuntimeMaxSec=300s --property=TimeoutStopSec=3s \
    --property=MemoryMax=67108864 --property=MemorySwapMax=0 \
    --property=TasksMax=16 --property=CPUQuota=50% -- \
    /usr/bin/python3 "$PWD/demo_broker.py" "$NE_DEMO/allowed/broker.sock" \
    "$NE_DEMO/token.txt" "$NE_DEMO/credential.txt" "$1"
  for attempt in {1..50}; do test -S "$NE_DEMO/allowed/broker.sock" && break; sleep 0.1; done
  test -S "$NE_DEMO/allowed/broker.sock"
}
```

This uses the owned lifecycle from Modules 07-09. Its argument selects the exact event filename. A failed readiness check is setup failure; inspect `journalctl --user -u "$NE_BROKER_UNIT" --no-pager`, then clean up before continuing.

## Exercise 2 - Observe an incomplete inner-only launch

```bash
start_demo_broker "$NE_DEMO/direct-event.json"
NE_DIRECT_STATUS=0
NORTH_ECHO_FAKE_CREDENTIAL="$(head -n 1 "$NE_DEMO/credential.txt")" \
  timeout 5s "$NE_DEMO/runtime_guard" "$NE_DEMO/allowed" "$NE_DEMO/allowed/runtime_probe" \
  "$NE_DEMO/allowed/allowed.txt" "$NE_DEMO/protected.txt" "$NE_DEMO/allowed/broker.sock" \
  "$NE_DEMO/allowed/request.json" "$NE_HOST_NET" "$NE_HOST_USER" 'FAKE-CREDENTIAL-' \
  > "$NE_DEMO/direct.json" || NE_DIRECT_STATUS=$?
python3 -m json.tool "$NE_DEMO/direct.json"
test "$NE_DIRECT_STATUS" -eq 1
../../lab-cleanup 10.03
test ! -e "$NE_DEMO/allowed/broker.sock"
```

The temporary assignment deliberately gives this one launch the **fake** ambient credential. The guard enforces its filesystem/syscall controls and the intended broker operation works, but `private_net`, `private_user`, and `credential_absent` are false. Resource values come from the parent rather than this lesson's desired profile.

Expected status is 1 from the observer's failed conjunction, not timeout status 124 or a missing executable. Partial success is not complete composition. The broker is one-shot, so the repair needs a fresh instance.

## Exercise 3 - Generate the spec and run the composition

```bash
python3 - "$NE_DEMO" "$NE_HOST_NET" "$NE_HOST_USER" <<'PY'
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
spec = {
    "guard": str(root / "runtime_guard"), "allowed_root": str(root / "allowed"),
    "command": [str(root / "allowed/runtime_probe"),
                str(root / "allowed/allowed.txt"), str(root / "protected.txt"),
                str(root / "allowed/broker.sock"), str(root / "allowed/request.json"),
                sys.argv[2], sys.argv[3], "FAKE-CREDENTIAL-"],
    "memory_max": 50331648, "tasks_max": 16, "cpu_percent": 50
}
(root / "spec.json").write_text(json.dumps(spec) + "\n")
PY
start_demo_broker "$NE_DEMO/event.json"
NORTH_ECHO_FAKE_CREDENTIAL="$(head -n 1 "$NE_DEMO/credential.txt")" \
  python3 complete_runtime.py "$NE_DEMO/spec.json" "$NE_DEMO/result.json"
python3 -m json.tool "$NE_DEMO/result.json"
python3 -m json.tool "$NE_DEMO/event.json"
../../lab-cleanup 10.03
```

Python serializes structured values instead of building JSON by shell string concatenation. The fake credential is still present in the launcher's environment, so observed absence in the final workload tests the actual handoff repair.

The result should retain status 0 and a final observation in which every intended Boolean is true. Expected resource strings are CPU `50000 100000`, memory `50331648`, swap `0`, and tasks `16`. Cleanup checks both the already-collected workload and the separate outside broker through their registered ownership.

## Checkpoint - Compare effects and verify the exact unit

```bash
python3 - "$NE_DEMO" <<'PY'
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1])
direct = json.loads((root / "direct.json").read_text())
assert direct["private_net"] is False and direct["private_user"] is False
assert direct["credential_absent"] is False
assert direct["allowed_read"] is True and direct["protected_denied"] is True
result = json.loads((root / "result.json").read_text())
observed = result["attestation"]
assert result["status"] == 0
for field in ("allowed_read", "protected_denied", "inet_denied", "private_net",
              "private_user", "caps_zero", "broker_ok", "credential_absent"):
    assert observed[field] is True, field
assert observed["no_new_privs"] == 1 and observed["seccomp"] == 2
assert (observed["cpu"], observed["memory"], observed["swap"], observed["pids"]) == (
    "50000 100000", "50331648", "0", "16")
credential = (root / "credential.txt").read_text().strip()
event = json.loads((root / "event.json").read_text())
expected = hashlib.sha256((credential + ":read:synthetic:record").encode()).hexdigest()
assert event == {"credential_used": True, "proof": expected}
assert credential not in (root / "result.json").read_text()
unit = subprocess.run(["systemctl", "--user", "show", result["unit"],
                       "--property=LoadState"], capture_output=True, text=True, check=False)
assert unit.stdout.strip() == "LoadState=not-found", unit.stdout + unit.stderr
assert not (root / "allowed/broker.sock").exists()
print("COMPOSED EFFECTS AND EXACT COLLECTION: PASS")
PY
```

The checker compares effective state, recomputes the synthetic broker event, and asks about the **exact** returned unit. An empty wildcard listing or a failed manager command cannot substitute for that observed absence.

This evidence concerns the supplied code and fixtures. It does not certify arbitrary workload output, every possible secret channel, future Landlock rights, or exclusive access to one Unix socket on older ABIs.

## Faded practice - One job, then three

The batch worker is already compiled. Create three single-job specs from the known-good outer spec, with desired exit statuses 0, 7, and 0:

```bash
python3 - "$NE_DEMO" <<'PY'
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
base = json.loads((root / "spec.json").read_text())
for index, status in enumerate((0, 7, 0), start=1):
    spec = dict(base)
    spec["command"] = [str(root / "allowed/batch_worker"), str(status)]
    spec["memory_max"] = 33554432 if index == 2 else 50331648
    (root / f"job-{index}.json").write_text(json.dumps(spec) + "\n")
PY
python3 complete_runtime.py "$NE_DEMO/job-1.json" "$NE_DEMO/job-1-result.json"
NE_JOB_TWO_STATUS=0
python3 complete_runtime.py "$NE_DEMO/job-2.json" "$NE_DEMO/job-2-result.json" || NE_JOB_TWO_STATUS=$?
test "$NE_JOB_TWO_STATUS" -ne 0
python3 complete_runtime.py "$NE_DEMO/job-3.json" "$NE_DEMO/job-3-result.json"
```

No broker is needed for this worker. The outer launcher reports nonzero for the middle workload, while its saved `status` is 7. The third valid job still runs. Inspect each result's observed memory value; the middle one must report 33554432, not merely inherit the input filename.

Now write `batch-notes.md` and design your own ordered batch interface using Module 04's list/trace skills. Give jobs unique IDs, validate **all** specs before any launch, preserve IDs and statuses in input order, and verify each exact unit is absent.

Deliberate mistake to reason about: a later job has `tasks_max: 0`, but the first job was already launched before validating it. Explain why malformed input should reject the batch before side effects, while a valid job returning 7 need not prevent later valid jobs. Use `validated` from this local source to review each spec without launching; it is separate from `main`.

Checkpoint for this faded practice: show ordered 0/7/0 results, observed per-job memory, exact unit absence, and a malformed later spec rejected before any worker runs. The capstone withholds a batch implementation and uses fresh profiles.

## Troubleshooting and replay

A missing result can mean validation, setup, timeout, or collection failure; read the specific launcher diagnostic. A valid result with status 7 means an ordinary workload failure was preserved. A remaining owner record is evidence to inspect, not permission to kill a name-matched process.

If cgroups fail, run `../../scripts/linux-preflight`. If a socket path is too long, keep the VM course path short and use a fresh prepared workspace. If static execution fails, verify the workload is beneath its allowed root. Keep SELinux enabled; do not add IP routes, host firewall changes, or public services.

Preview `../../lab-cleanup 10.03 --dry-run`, then run `../../lab-cleanup 10.03`. Save your notes, return with `cd ../..`, and use `./lab-reset 10.03` to discard this lesson's generated artifacts after verified cleanup.

## Source truth

[setpriv(1)](https://man7.org/linux/man-pages/man1/setpriv.1.html) explains privilege settings across execution; [proc_pid_status(5)](https://man7.org/linux/man-pages/man5/proc_pid_status.5.html) defines observed capability/policy fields. Use the installed `man systemd-run` and `man systemd.resource-control` for the VM's manager version. The [Landlock documentation](https://cdn.kernel.org/doc/html/latest/userspace-api/landlock.html) defines the ABI-specific limits that a passing local observation must not overstate.
<!-- /source -->

---

<!-- source: course/module-10-complete-runtime/lab/README.md format=markdown -->
# Module 10 independent lab - Composed contained runtime

## Assignment and readiness check

Build the single-job launcher practiced in 10.01-10.03. It must retain an approved operation while applying the outer controls and proving owned collection. Do not replace effective observations with input-configuration labels.

Before coding, explain the dependency order, the difference between inner guard and outer launcher, why systemd argv expansion needs explicit treatment, and why an absent exact unit is stronger evidence than requesting collection. Complete the small 0/7/0 worker exercise before progressing to the later batch capstone.

## Prepare and read the starter

From the course root:

```bash
./lab-start module-10
cd .student/10.lab
pwd
ls -l complete_runtime.py
cat complete_runtime.py
nano complete_runtime.py
```

Work only in this prepared copy. Ctrl+O then Enter saves in the default nano configuration; Ctrl+X exits.

```python
#!/usr/bin/env python3
"""Module 10 starter: functional execution without outer runtime controls."""

import json
from pathlib import Path
import subprocess
import sys


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    command = [spec["guard"], spec["allowed_root"], *spec["command"]]
    run = subprocess.run(command, text=True, capture_output=True, check=False, timeout=20)
    Path(sys.argv[2]).write_text(json.dumps({
        "schema": 1, "status": run.returncode, "unit": None,
        "stdout": run.stdout, "stderr": run.stderr, "attestation": None,
    }) + "\n", encoding="utf-8")
    return run.returncode != 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### Starter, line by line

- The imports provide JSON, paths, subprocess execution, and arguments.
- The guard requires a spec and result filename; the starter then parses JSON without the complete validation you must add.
- The command list preserves argv while invoking the supplied guard and workload directly.
- A timeout bounds this incomplete foreground execution, but no cgroup or namespace is created.
- The result records status/output and explicitly has no unit or parsed attestation.
- A nonzero child status makes the starter return nonzero. This is useful baseline behavior, not successful composition.

The starter may perform the guard's inner controls while failing the outer properties. Do not mistake that partial functionality for the assignment being complete.

## Interface and validation contract

The grader invokes:

```text
python3 complete_runtime.py SPEC.json RESULT.json
```

Require exactly `guard`, `allowed_root`, `command`, `memory_max`, `tasks_max`, and `cpu_percent`. Guard/root must be absolute paths of the expected regular-file/directory kind, without a symlink leaf. Treat the guard as trusted operator-provided TCB, not a workload-selectable convenience. Refuse the whole filesystem as an allowed root.

Require nonempty structured string argv without NUL characters, an absolute executable that resolves beneath the allowed root, and actual integer limits: memory 16 MiB through 1 GiB, tasks 4 through 256, CPU 10 through 100 percent. Reject Boolean limits. Invalid input must fail before a result, ownership record, or service is created. These setup paths are trusted for this exercise; do not claim race-free validation against concurrent same-account mutation.

## Launch and collection contract

Record exact unit ownership before launch. In prepared course workspaces, use the course registry with the matching target and workspace description. The isolated external grader copies your single source file into a separate directory; preserve a local ownership record under `.runtime` there, as practiced in 10.03. Use names with the ordinary UID, target, and fresh random suffix; the grader's standalone target is `10.lab`.

Create a transient **user** service with validated CPU/memory/task limits, zero swap, a 100 ms CPU period, a finite runtime backstop, control-group stop semantics, bounded stop time, synchronous waiting, and collection. Disable systemd's own argument environment expansion when promising literal argv.

Within that cgroup create fresh user/network namespaces; then reduce bounding/inheritable/ambient capability sets and set no-new-privileges. Give the final guard/workload a fixed environment without the fake credential. Invoke the trusted guard with the allowed root and separate workload argv. Do not use a shell to reinterpret those arguments.

On normal return, failure, and timeout, inspect the **exact** recorded unit. Before stopping a remaining unit, verify its description and cgroup are owned by the expected delegated user manager. Treat a manager inspection failure as unknown, not absent. Confirm actual unit/cgroup collection before publishing a completed result. Retain ownership evidence and refuse mutation if identity cannot be established.

Write one JSON result with schema 1, workload status, exact unit name, stdout, stderr, and the parsed final-line observation when present. A valid worker exit of 7 must remain 7 in the result and produce a nonzero launcher status. A missing final JSON line need not erase an ordinary worker's status/stderr.

## What the external checks observe

The grader compiles its own static guard and observer, rotates synthetic paths/tokens/credentials, and runs a separate local Unix-socket fixture. It checks:

- effective CPU, memory, swap, and task controller values;
- distinct user/network namespaces and denied AF_INET creation;
- empty capability sets and no-new-privileges;
- allowed/protected file behavior and seccomp mode;
- successful intended Unix-socket operation and fake-credential use by the fixture;
- absence of the known fake credential from observed workload environment/output;
- literal paths, including a systemd-style environment reference;
- ordinary failure status/stderr, invalid-spec refusal, and exact reported-unit/socket absence.

These are finite observations. They do not certify a general parser, a production broker, exclusive access to one Unix socket on ABI 7, durable credential replay state, private PID/mount views, all-channel non-disclosure, or independently bounded outer output capture.

## Map the work to practice

Validation and structured input: Module 04 and 10.03. Resource ownership and timeouts: Module 07 and 10.03. Namespace/privilege ordering: Modules 02-03 and 10.01. Native filesystem/syscall guard: Modules 05-06 and 10.02. Intended broker operation and its limits: Modules 08-09 and 10.03. Failure aggregation and status preservation: Module 04 and the 0/7/0 practice.

Write an explanation of each layer's evidence and one limitation it does not address. The lab does not include a complete launcher implementation.

## Validate, diagnose, and replay

```bash
python3 -m py_compile complete_runtime.py
../../lab-grade module-10
../../lab-grade module-10 --mode exam
```

Compilation checks syntax without creating a service. Practice mode reports failed properties with lesson references; exam mode reduces hints. A failed approved operation must not be “repaired” by removing confinement. Identify which setup/control dependency broke the intended task.

For manual runs, use only generated local fixtures and exact registered ownership. Preview `../../lab-cleanup module-10 --dry-run`, then run `../../lab-cleanup module-10`. Do not kill by prefix, modify host cgroups/firewalls, disable SELinux, or use real credentials.

Save your design notes, return with `cd ../..`, and use `./lab-reset module-10` to discard the working copy and synthetic fixtures after verified cleanup.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-11-break-fix-research/README.md format=markdown -->
# Module 11 - Compare and repair a small containment model

Complete Modules 01-10 first. Work through `11.01`, `11.02`, `11.03`, then `module-11`.

The earlier modules attempted operations under Linux controls. This chapter changes scale: you inspect a deliberately small, fixed local model to practice evidence classification, complete repair, preservation, and replay. It is not an external vulnerability-discovery exercise and does not reproduce arbitrary vulnerabilities.

By the end you should be able to:

- distinguish configuration choices, actual local effects, modeled decisions, and unobserved properties;
- generate and replay a seeded combination without treating its name as a diagnosis;
- classify every supplied observation and reject missing evidence;
- repair all known model choices while preserving the allowed operation and opaque identity;
- test idempotence and explain what a successful model comparison does **not** establish.

The harness uses a constant shell marker fixture, one explicitly fake variable, generated sibling files, an unconnected socket, and string-only cleanup candidates. It never interprets arbitrary plan text, contacts a target, or deletes a cleanup candidate. The broker-only branch skips socket creation; it does not install kernel confinement. The resolved-path branch is not race-free, and cleanup selection is not real resource collection. Keep those limitations beside every conclusion.

Estimated work: three guided sessions plus an independent repair lab. Save short evidence notes as you go; a passing JSON comparison is not a substitute for explaining the observation.
<!-- /source -->

---

<!-- source: course/module-11-break-fix-research/lesson-01/README.md format=markdown -->
# 11.01 - Reproduce a seeded weakness without an agent

## Outcomes and prerequisites

Complete Modules 01-10. You will generate a repeatable teaching variant, record its fixed local effects, and separate actual observations from model choices. No autonomous agent, external target, or generated exploit is involved.

## Concepts before commands

A **seed** makes a pseudo-random teaching choice repeatable. It is not a secret and is not suitable for credential generation. A **variant** is one combination of control settings, not a vulnerability identifier.

This harness is a deliberately small model, not the Module 10 runtime. Its evidence mixes real local effects with modeled decisions. That distinction is part of the lesson:

| Field | What this harness establishes |
| --- | --- |
| `shell_marker_created` | A fixed, hard-coded shell fixture created its own marker |
| `credential_visible` | The explicitly fake variable was present in a small child environment |
| `protected_read` | A generated local symlink led to the synthetic sibling under the selected path check |
| `inet_created` | The direct branch created an unconnected socket; the other branch simply skipped creation |
| `cleanup_decoy_selected` | String selection included an unowned decoy; nothing was deleted |
| `allowed_operation` | The modeled read operation and actual generated allowed-file read both succeeded |

In particular, `inet_created: false` here does **not** establish kernel network confinement. Return to Modules 08 and 10 for a real attempted operation under enforced controls. Likewise, `resolved` uses a separate resolve-then-read check and does not solve the race discussed in Module 05.

## Prepare and read both programs

From the course root:

```bash
./lab-start 11.01
cd .student/11.01
pwd
ls -l make_variant.py variant_harness.py
cat make_variant.py
cat variant_harness.py
```

Use `nano` with either filename to navigate the source. The exercises supply only generated synthetic plans. Never put a real command, secret, target, or production path in a plan.

### The seeded generator

```python
#!/usr/bin/env python3
"""Create a reproducible vulnerable plan from an explicit integer seed."""

import json
import random
import sys
from pathlib import Path

SECURE = {"execution": "argv", "environment": "minimal", "filesystem": "resolved",
          "network": "broker_only", "cleanup": "owned"}
WEAK = {"execution": "shell", "environment": "inherit", "filesystem": "lexical",
        "network": "direct", "cleanup": "prefix"}

if len(sys.argv) != 3:
    raise SystemExit(f"usage: {sys.argv[0]} SEED OUTPUT.json")
rng = random.Random(int(sys.argv[1]))
controls = dict(SECURE)
for name in rng.sample(sorted(WEAK), rng.randint(2, 4)):
    controls[name] = WEAK[name]
plan = {
    "schema": 1,
    "variant_id": f"seed-{sys.argv[1]}",
    "workload": {"operation": "read", "resource": "record:alpha",
                 "literal": "literal $(touch shell-marker)"},
    "controls": controls,
}
Path(sys.argv[2]).write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
```

### Source, line by line

- `SECURE` and `WEAK` enumerate the two modeled choices for each control. Their names are design labels, not proof of enforcement.
- `random.Random(int(...))` creates a local deterministic generator from the supplied integer.
- `dict(SECURE)` copies the baseline so changing this variant does not mutate the shared mapping.
- Sampling sorted names selects two through four distinct controls. It changes only their configured choices.
- The workload contains a harmless operation/resource and shell-looking literal data. The harness never executes that plan text as shell code.
- The output includes a schema version and opaque identity. Sorted, indented JSON makes exact replay comparison straightforward.

### The fixed local harness

```python
#!/usr/bin/env python3
"""Observe fixed synthetic fixtures and model choices, never execute plan text."""

import json
import os
from pathlib import Path
import socket
import subprocess
import sys


def main() -> int:
    if len(sys.argv) != 4:
        return 2
    plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    choices = {
        "execution": {"shell", "argv"}, "environment": {"inherit", "minimal"},
        "filesystem": {"lexical", "resolved"}, "network": {"direct", "broker_only"},
        "cleanup": {"prefix", "owned"},
    }
    if not isinstance(plan, dict) or set(plan) != {"schema", "variant_id", "workload", "controls"}:
        raise ValueError("invalid plan shape")
    if type(plan["schema"]) is not int or plan["schema"] != 1 or not isinstance(plan["variant_id"], str):
        raise ValueError("invalid plan identity")
    workload, controls = plan["workload"], plan["controls"]
    if not isinstance(workload, dict) or set(workload) != {"operation", "resource", "literal"}:
        raise ValueError("invalid workload shape")
    if not all(isinstance(value, str) for value in workload.values()):
        raise ValueError("invalid workload values")
    if not isinstance(controls, dict) or set(controls) != set(choices):
        raise ValueError("invalid control shape")
    if any(not isinstance(controls[name], str) or controls[name] not in choices[name] for name in choices):
        raise ValueError("unknown control choice")
    evidence_path, work = Path(sys.argv[2]), Path(sys.argv[3])
    work.mkdir(mode=0o700, parents=True, exist_ok=False)
    allowed = work / "allowed"
    allowed.mkdir()
    (allowed / "data.txt").write_text("allowed\n", encoding="utf-8")
    protected = work / "protected.txt"
    protected.write_text("SYNTHETIC-PROTECTED\n", encoding="utf-8")
    (allowed / "link.txt").symlink_to(protected.resolve())
    marker = work / "shell-marker"
    literal = workload["literal"]
    fixed_env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}

    if controls["execution"] == "shell":
        # Fixed toy only: the plan's literal is never interpreted as shell code.
        subprocess.run(["/bin/sh", "-c", '/usr/bin/printf "%s\\n" "$(/usr/bin/touch "$1")"',
                        "fixed-marker-fixture", str(marker.resolve())], cwd=work,
                       text=True, capture_output=True, check=True, timeout=2, env=fixed_env)
    else:
        subprocess.run(["/usr/bin/printf", "%s\n", literal], cwd=work,
                       text=True, capture_output=True, check=True, timeout=2, env=fixed_env)

    child_env = dict(fixed_env)
    if controls["environment"] == "inherit" and "NORTH_ECHO_FAKE_CREDENTIAL" in os.environ:
        child_env["NORTH_ECHO_FAKE_CREDENTIAL"] = os.environ["NORTH_ECHO_FAKE_CREDENTIAL"]
    environment = subprocess.run(["/usr/bin/env"], text=True, capture_output=True,
                                 check=True, timeout=2, env=child_env).stdout
    credential_visible = "NORTH_ECHO_FAKE_CREDENTIAL=" in environment

    candidate = allowed / "link.txt"
    if controls["filesystem"] == "lexical":
        authorized = str(candidate).startswith(str(allowed) + os.sep)
    else:
        authorized = allowed.resolve() in candidate.resolve().parents
    protected_read = authorized and candidate.read_text(encoding="utf-8").startswith("SYNTHETIC-")

    inet_created = False
    if controls["network"] == "direct":
        stream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        inet_created = stream.fileno() >= 0
        stream.close()

    owned = f"north-echo-{plan['variant_id']}-owned"
    decoy = f"north-echo-{plan['variant_id']}-decoy"
    candidates = [owned, decoy]
    selected = candidates if controls["cleanup"] == "prefix" else [owned]
    evidence = {
        "schema": 1,
        "variant_id": plan["variant_id"],
        "allowed_operation": workload["operation"] == "read" and
                             (allowed / "data.txt").read_text(encoding="utf-8") == "allowed\n",
        "shell_marker_created": marker.exists(),
        "credential_visible": credential_visible,
        "protected_read": protected_read,
        "inet_created": inet_created,
        "cleanup_decoy_selected": decoy in selected,
    }
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### Source, line by line

- The initial checks require exact plan/workload/control shapes and known string choices **before** creating a work directory.
- `mkdir(..., exist_ok=False)` refuses reuse. All fixture files live under this fresh private directory.
- The allowed file and protected sibling contain fixed synthetic text. The symlink deliberately references that sibling, never an external target.
- The shell-mode branch runs a **constant** tiny shell program. Only its exact new marker pathname is passed as a quoted positional argument; arbitrary plan literals are never interpreted.
- The argv branch passes the plan literal as one data argument to printf. Both child executions have a fixed environment and timeout.
- The environment fixture copies only the explicitly fake variable when the inherited-choice branch is selected; it does not forward unrelated parent credentials.
- The filesystem branch compares either path spelling or the resolved object's ancestry, then performs the generated local read if authorized.
- The direct network branch creates and closes a socket without connecting. The broker-only branch is a model selection, not an installed network policy.
- Cleanup candidates are ordinary strings. Choosing one or both has no destructive effect.
- Evidence records these observations and an actual allowed-file read. The harness writes JSON and exits; it installs no persistent service.

## Exercise 1 - Predict, generate, and observe

```bash
python3 make_variant.py 1101 variant.json
python3 -m json.tool variant.json
NORTH_ECHO_FAKE_CREDENTIAL=FAKE-LESSON-11.01 \
  python3 variant_harness.py variant.json evidence.json run-a
python3 -m json.tool evidence.json
```

Before the harness run, predict which adverse fields should be true from the choices. Afterward, compare with observed effects. With the supplied fake variable and working socket API, at least two adverse fields should be true while the allowed operation remains true.

The mistake to avoid is writing “network confinement is broken” solely because a plan says `direct`. The actual positive observation is narrower: this model branch created an unconnected socket. It did not contact anything or test a deployed runtime.

## Exercise 2 - Replay the plan, not a conclusion

```bash
python3 make_variant.py 1101 replay.json
cmp variant.json replay.json
NORTH_ECHO_FAKE_CREDENTIAL=FAKE-LESSON-11.01 \
  python3 variant_harness.py replay.json replay-evidence.json run-b
cmp evidence.json replay-evidence.json
```

The same seed reproduces the plan, and fresh fixture directories permit a second observation. Byte equality is useful here because this harness's output contains no random paths or timestamps. It does not mean every real experiment must produce byte-identical logs.

## Exercise 3 - Repair an overbroad claim

Write `nano evidence-notes.md`. For one true field, record configuration, observed effect, violated intended invariant, and a limitation. Then write one false field's limited meaning. For the network branch, explicitly distinguish “no socket was created by this branch” from “the kernel denied socket creation.”

The repair is to the **claim**, not to the evidence file. Do not change observations to make the report look safer. Lesson 11.03 will repair the modeled plan and compare a new run.

## Checkpoint and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

evidence = json.loads(Path("evidence.json").read_text())
signals = ("shell_marker_created", "credential_visible", "protected_read",
           "inet_created", "cleanup_decoy_selected")
assert evidence["allowed_operation"] is True
assert sum(evidence[name] is True for name in signals) >= 2
assert json.loads(Path("replay-evidence.json").read_text()) == evidence
assert Path("run-a/protected.txt").read_text() == "SYNTHETIC-PROTECTED\n"
assert not Path("run-a/not-a-workspace").exists()
print("FIXED LOCAL EFFECTS AND REPLAY: PASS")
PY
```

The synthetic protected file remains intact; no cleanup candidate was deleted. If a work directory exists, prepare a new name or reset the lesson rather than reuse stale artifacts. If the fake-variable observation is absent, prefix the command in this same VM shell.

Save your notes, return with `cd ../..`, and use `./lab-reset 11.01` to remove only the prepared workspace and fixtures. Do not extend this harness into a scanner, arbitrary command runner, or destructive cleanup utility.

## Source truth

Python's [random documentation](https://docs.python.org/3.14/library/random.html) distinguishes deterministic pseudo-random generation from security randomness; [subprocess](https://docs.python.org/3.14/library/subprocess.html) defines argv and environment handoffs. Earlier kernel lessons supply enforcement evidence that this small model does not.
<!-- /source -->

---

<!-- source: course/module-11-break-fix-research/lesson-02/README.md format=markdown -->
# 11.02 - Identify invariants from an evidence matrix

## Outcomes and prerequisites

Complete 11.01. You will map supplied observations to intended invariants, avoid diagnosing every case from one dramatic symptom, and reject incomplete evidence instead of treating missing fields as negative observations.

## Concepts before commands

An **invariant** is a property the design intends to preserve across variants. “Arguments remain data” is an invariant; “this variant used the argv option” is a configuration fact. The latter does not automatically establish the former in arbitrary code.

**Overfitting** means tailoring your conclusion to the examples you noticed rather than the underlying property. A conspicuous shell marker can distract from a quieter inherited credential or cleanup over-selection.

These fixed JSON rows are teaching fixtures, not fresh measurements of your current VM. The classifier interprets their content; it does not run a workload or independently verify their provenance. Keep both the observation source and its limitations in your report.

## Prepare and read the classifier and cases

From the course root:

```bash
./lab-start 11.02
cd .student/11.02
pwd
ls -l classify_evidence.py overfit-evidence.json mixed-evidence.json
cat classify_evidence.py
cat overfit-evidence.json
cat mixed-evidence.json
```

Use `nano mixed-evidence.json` to navigate, but leave the shipped case intact. The deliberate missing-field case will use a separate copy.

### The classifier

```python
#!/usr/bin/env python3
"""Map reproduced effects to invariant statements."""

import json
import sys
from pathlib import Path

INVARIANTS = {
    "shell_marker_created": "argv is data and is never shell syntax",
    "credential_visible": "the workload receives no ambient credential",
    "protected_read": "authorization follows resolved objects, not lexical paths",
    "inet_created": "the workload has no direct IP socket authority",
    "cleanup_decoy_selected": "cleanup selects only exact owned objects",
}

if len(sys.argv) != 2:
    raise SystemExit(f"usage: {sys.argv[0]} EVIDENCE.json")
evidence = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
required = {"schema", "variant_id", "allowed_operation", *INVARIANTS}
if (not isinstance(evidence, dict) or set(evidence) != required
        or type(evidence["schema"]) is not int or evidence["schema"] != 1
        or not isinstance(evidence["variant_id"], str)
        or any(type(evidence[name]) is not bool for name in ("allowed_operation", *INVARIANTS))):
    raise SystemExit("invalid or incomplete evidence; absence is not a negative observation")
failed = [{"signal": name, "invariant": statement}
          for name, statement in INVARIANTS.items() if evidence.get(name) is True]
print(json.dumps({"variant_id": evidence.get("variant_id"), "failed": failed}, indent=2, sort_keys=True))
raise SystemExit(0)
```

### Source, line by line

- `INVARIANTS` maps each adverse signal to the positive property it calls into question.
- The argv guard requires one evidence filename; JSON is then parsed into Python data.
- The complete key-set check prevents an omitted signal from silently becoming `False`.
- Schema and Boolean type checks reject values such as the string `"false"` or integer 0 in place of observed Booleans.
- The list comprehension selects only signals whose supplied value is actually `True`.
- Each selected row carries both its signal name and explanatory invariant. Variant identity is retained as metadata, not used to choose the diagnosis.
- Printing the result and returning 0 means classification completed. An empty `failed` list is a data result, not a promise of universal safety.

### Two complete supplied cases

```json
{"schema":1,"variant_id":"lesson-overfit","allowed_operation":true,"shell_marker_created":true,"credential_visible":false,"protected_read":false,"inet_created":false,"cleanup_decoy_selected":false}
```

This row contains one adverse shell-marker observation and successful allowed work.

```json
{"schema":1,"variant_id":"lesson-mixed","allowed_operation":true,"shell_marker_created":false,"credential_visible":true,"protected_read":true,"inet_created":false,"cleanup_decoy_selected":true}
```

This row has no shell marker but three other adverse observations. Neither the variant label nor the absence of one familiar symptom should override those fields.

## Exercise 1 - Diagnose both rows before execution

Predict the failed invariants, then run:

```bash
python3 classify_evidence.py overfit-evidence.json > overfit-result.json
python3 classify_evidence.py mixed-evidence.json > mixed-result.json
python3 -m json.tool overfit-result.json
python3 -m json.tool mixed-result.json
```

The first result should contain only `shell_marker_created`. The second should contain `credential_visible`, `protected_read`, and `cleanup_decoy_selected`.

The intentional diagnostic mistake is applying the first case's repair to every case. Repair the explanation by mapping **each** true signal to its invariant. Preserve the positive allowed-operation observation; disabling all useful work would not be a successful repair.

## Exercise 2 - Build a comparison matrix

```bash
python3 - <<'PY'
import json
from pathlib import Path

signals = ("shell_marker_created", "credential_visible", "protected_read",
           "inet_created", "cleanup_decoy_selected")
for name in ("overfit-evidence.json", "mixed-evidence.json"):
    value = json.loads(Path(name).read_text())
    adverse = [signal for signal in signals if value[signal] is True]
    print(name, "allowed=", value["allowed_operation"], "adverse=", ",".join(adverse) or "none")
PY
```

The program names the exact expected signal columns. It does not treat arbitrary metadata values as truthy failures. A consistent row structure makes differences visible without turning labels into evidence.

Remember 11.01's scope table: the network and cleanup branches model decisions, and pathname resolution is not a race-free kernel policy. State that distinction when using the matrix.

## Exercise 3 - Deliberately omit an observation

```bash
python3 - <<'PY'
import json
from pathlib import Path

value = json.loads(Path("mixed-evidence.json").read_text())
del value["protected_read"]
Path("incomplete.json").write_text(json.dumps(value) + "\n")
PY
NE_INCOMPLETE_STATUS=0
python3 classify_evidence.py incomplete.json > incomplete-result.json 2> incomplete.err || NE_INCOMPLETE_STATUS=$?
cat incomplete.err
test "$NE_INCOMPLETE_STATUS" -ne 0
test ! -s incomplete-result.json
python3 classify_evidence.py mixed-evidence.json > repaired-result.json
```

The omitted field is unknown, not false. The classifier refuses the incomplete row instead of silently reducing the failure count. Repair the analysis by returning to the complete supplied evidence, not by inventing a replacement observation.

## Checkpoint and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

def signals(name):
    return {row["signal"] for row in json.loads(Path(name).read_text())["failed"]}

assert signals("overfit-result.json") == {"shell_marker_created"}
assert signals("mixed-result.json") == {
    "credential_visible", "protected_read", "cleanup_decoy_selected"
}
assert signals("repaired-result.json") == signals("mixed-result.json")
assert "incomplete evidence" in Path("incomplete.err").read_text()
print("INVARIANT MATRIX AND MISSING-EVIDENCE REFUSAL: PASS")
PY
```

In `nano matrix-notes.md`, explain an invariant without naming the implementation option that supposedly enforces it. Then identify one additional observation needed before claiming kernel enforcement rather than model selection.

If a count differs, inspect all input fields and their types. Do not modify the classifier to produce a preferred answer. Save notes, return with `cd ../..`, and use `./lab-reset 11.02` to remove this prepared workspace. No service was launched.

## Source truth

Python's [JSON documentation](https://docs.python.org/3.14/library/json.html) defines parsing and serialization, not the truth of a record's claims. The invariant mapping and fixture limitations are course-defined. Modules 05, 08, and 10 show the separate behavioral observations needed to support enforcement conclusions.
<!-- /source -->

---

<!-- source: course/module-11-break-fix-research/lesson-03/README.md format=markdown -->
# 11.03 - Repair and prove the hardened counterpart

## Outcomes and prerequisites

Complete 11.01-11.02. You will validate and repair every modeled control, preserve identity/workload data, compare before/after fixture observations, and test idempotence. “Hardened counterpart” here means the known-good **model choices**, not a newly certified kernel runtime.

## Concepts before commands

A repair must preserve the intended work as well as remove adverse effects. Changing the resource, deleting the workload, or suppressing inconvenient evidence would change the question instead of answering it.

An **idempotent** repair produces the same result when applied again to its own output. This makes repeated application predictable. It does not prove every security property.

An **atomic replacement** makes a complete new file appear at the destination rather than exposing a half-written JSON document. It is not a claim of crash durability; that would require additional synchronization and filesystem assumptions.

## Prepare and read the source and fixture

From the course root:

```bash
./lab-start 11.03
cd .student/11.03
pwd
ls -l repair_variant.py vulnerable-plan.json
cat repair_variant.py
cat vulnerable-plan.json
```

The harness is the same fixed local program read in 11.01. The commands below reference its canonical copy for consistent comparison; do not modify it to make a repair pass.

### The repair tool

```python
#!/usr/bin/env python3
"""Repair every known weak control while preserving the workload contract."""

import json
import os
from pathlib import Path
import sys
import tempfile

SECURE = {"execution": "argv", "environment": "minimal", "filesystem": "resolved",
          "network": "broker_only", "cleanup": "owned"}
ALLOWED = {
    "execution": {"argv", "shell"}, "environment": {"minimal", "inherit"},
    "filesystem": {"resolved", "lexical"}, "network": {"broker_only", "direct"},
    "cleanup": {"owned", "prefix"},
}


def repair(value: object) -> dict:
    if not isinstance(value, dict) or set(value) != {"schema", "variant_id", "workload", "controls"}:
        raise ValueError("invalid plan shape")
    if type(value["schema"]) is not int or value["schema"] != 1 or not isinstance(value["variant_id"], str) or not value["variant_id"]:
        raise ValueError("invalid plan identity")
    workload, controls = value["workload"], value["controls"]
    if not isinstance(workload, dict) or set(workload) != {"operation", "resource", "literal"}:
        raise ValueError("invalid workload")
    if not all(isinstance(item, str) for item in workload.values()):
        raise ValueError("invalid workload values")
    if not isinstance(controls, dict) or set(controls) != set(SECURE):
        raise ValueError("invalid controls")
    if any(not isinstance(controls[name], str) or controls[name] not in ALLOWED[name] for name in SECURE):
        raise ValueError("unknown control value")
    return {"schema": 1, "variant_id": value["variant_id"],
            "workload": dict(workload), "controls": dict(SECURE)}


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    output = Path(sys.argv[2])
    try:
        if output.resolve() == Path(sys.argv[1]).resolve() or output.is_symlink():
            raise ValueError("output must be separate from input and not a symlink")
        source = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        repaired = repair(source)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"repair denied: {error}", file=sys.stderr)
        return 1
    fd, name = tempfile.mkstemp(prefix=".repair-", dir=output.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(repaired, indent=2, sort_keys=True) + "\n")
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### Source, line by line

- `SECURE` holds the five intended model choices. `ALLOWED` enumerates valid input choices, including the deliberately weak alternatives.
- `repair` checks the exact top-level shape, integer schema, nonempty identity, workload shape, and textual values.
- Control names must match the complete set; each control must be a known string. A list or unknown value is rejected, not coerced.
- The result copies opaque identity and workload values and replaces only the control mapping.
- `main` refuses an output that resolves to the input or is a symlink. Validation completes before any temporary output is created.
- `mkstemp` creates an exclusive unpredictable temporary file in the output directory, avoiding a reused predictable sibling name.
- `os.fdopen` writes through the already-created descriptor. Closing the stream completes this process's write before replacement.
- `replace` publishes the complete JSON at the destination on the same filesystem.
- `finally` removes only that exact owned temporary path if an error leaves it behind.
- Invalid input returns nonzero with a diagnostic; it does not publish a claimed repair.

### The deliberately mixed plan

```json
{"schema":1,"variant_id":"lesson-repair","workload":{"operation":"read","resource":"record:alpha","literal":"literal $(touch shell-marker)"},"controls":{"execution":"shell","environment":"inherit","filesystem":"lexical","network":"direct","cleanup":"prefix"}}
```

All five choices are weak in this fixture. Its resource and literal are synthetic metadata. Neither the repairer nor the harness is an interface for executing arbitrary plan text.

## Exercise 1 - Record the before case

```bash
cp vulnerable-plan.json before.json
NORTH_ECHO_FAKE_CREDENTIAL=FAKE-LESSON-11.03 \
  python3 ../../course/module-11-break-fix-research/lesson-01/variant_harness.py \
  before.json before-evidence.json before-run
python3 -m json.tool before-evidence.json
```

With the supplied fake variable, expect all five adverse fields to be true and allowed work to succeed. The real effects are limited to the fixed local fixtures; the network/cleanup limitations from 11.01 still apply.

## Exercise 2 - Repair every choice and compare

```bash
python3 repair_variant.py before.json after.json
NORTH_ECHO_FAKE_CREDENTIAL=FAKE-LESSON-11.03 \
  python3 ../../course/module-11-break-fix-research/lesson-01/variant_harness.py \
  after.json after-evidence.json after-run
python3 -m json.tool after-evidence.json
python3 repair_variant.py after.json second.json
cmp after.json second.json
cmp vulnerable-plan.json before.json
```

The allowed read should remain true and every adverse field should be false. The second repair must produce identical bytes under this deterministic serializer. The original copied plan must remain unchanged.

Do not generalize the false network field into kernel denial: this modeled broker-only branch simply did not create an IP socket. Nor is the resolve-then-read branch a replacement for descriptor-relative lookup or Landlock.

## Exercise 3 - Try a partial repair, then restore completeness

```bash
python3 - <<'PY'
import json
from pathlib import Path

value = json.loads(Path("before.json").read_text())
value["controls"]["execution"] = "argv"
Path("partial.json").write_text(json.dumps(value) + "\n")
PY
NORTH_ECHO_FAKE_CREDENTIAL=FAKE-LESSON-11.03 \
  python3 ../../course/module-11-break-fix-research/lesson-01/variant_harness.py \
  partial.json partial-evidence.json partial-run
python3 -m json.tool partial-evidence.json
python3 repair_variant.py partial.json partial-repaired.json
cmp after.json partial-repaired.json
```

The intentional mistake fixes only the most visible shell fixture. Four adverse fields remain. The full repair converges to the same intended model without changing identity or workload.

## Checkpoint and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

def value(name):
    return json.loads(Path(name).read_text())

signals = ("shell_marker_created", "credential_visible", "protected_read",
           "inet_created", "cleanup_decoy_selected")
assert all(value("before-evidence.json")[name] is True for name in signals)
assert all(value("after-evidence.json")[name] is False for name in signals)
assert value("after-evidence.json")["allowed_operation"] is True
assert value("partial-evidence.json")["shell_marker_created"] is False
assert sum(value("partial-evidence.json")[name] is True for name in signals) == 4
for field in ("variant_id", "workload"):
    assert value("before.json")[field] == value("after.json")[field]
assert value("after.json") == value("second.json")
print("COMPLETE MODEL REPAIR, PRESERVATION, AND IDEMPOTENCE: PASS")
PY
```

Write `repair-notes.md` describing preserved functionality, every changed control, and the limits of the evidence. “All fields false” is not a sufficient explanation.

If a work directory already exists, reset this lesson or choose a fresh exact name. If input validation fails, repair the input shape rather than removing validation. Save notes, return with `cd ../..`, and use `./lab-reset 11.03` to remove the generated local files. The harness has created no background service and deleted no cleanup candidate.

## Source truth

Python's [tempfile documentation](https://docs.python.org/3.14/library/tempfile.html) explains exclusive temporary-file creation; [os.replace](https://docs.python.org/3.14/library/os.html#os.replace) describes replacement semantics. These file-publication mechanisms do not establish that the repaired policy itself is sufficient; that requires the scoped behavioral comparison and earlier kernel lessons.
<!-- /source -->

---

<!-- source: course/module-11-break-fix-research/lab/README.md format=markdown -->
# Module 11 independent lab - Repair randomized model variants

## Assignment and readiness check

Build a strict, deterministic repairer for the small model from 11.01-11.03. Preserve useful work and identity while correcting **every** known control choice. You are not implementing a new Linux sandbox.

Before coding, explain why a missing observation is not false, why a network branch that skips a socket is not kernel denial, and why repairing only the most conspicuous symptom leaves mixed variants incomplete.

## Prepare and read the starter

From the course root:

```bash
./lab-start module-11
cd .student/11.lab
pwd
ls -l repair_variant.py
cat repair_variant.py
nano repair_variant.py
```

Edit only this prepared copy. In the default nano configuration, Ctrl+O then Enter saves; Ctrl+X exits.

```python
#!/usr/bin/env python3
"""Module 11 starter: repairs only one visible weakness."""

import json
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit(2)
plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
plan["controls"]["execution"] = "argv"
Path(sys.argv[2]).write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
```

### Starter, line by line

- The imports provide JSON parsing, paths, and command arguments.
- The argument-count guard expects an input and an output filename.
- Parsing JSON alone does not validate the model's schema or known values.
- The single assignment repairs execution only. Other weak choices survive.
- Direct writing publishes a file without the complete validation and atomic publication required here.

The starter can produce useful-looking output while still failing most mixed variants. Your job includes failure handling, not just adding four assignments.

## Input and output contract

The grader invokes:

```text
python3 repair_variant.py INPUT.json OUTPUT.json
```

Require exactly the top-level keys `schema`, `variant_id`, `workload`, and `controls`. Schema must be integer 1, not Boolean true. Identity must be a nonempty string. Workload has exactly `operation`, `resource`, and `literal`, all strings. Treat those values as opaque data, never shell commands.

The controls must have exactly these known choices:

| Control | Intended model choice | Deliberately weak choice |
| --- | --- | --- |
| execution | argv | shell |
| environment | minimal | inherit |
| filesystem | resolved | lexical |
| network | broker_only | direct |
| cleanup | owned | prefix |

Validate the complete plan before creating output. Unknown fields, missing fields, wrong types, and unknown choices must fail nonzero. A rejected plan must not create a new output or modify an existing output. Refuse an output that aliases the input or is a symlink.

Preserve the input bytes, variant identity, and workload values. Correct all five control choices. Publish complete JSON through an exclusive temporary file in the destination directory and atomic replacement; clean only that exact owned temporary path on failure. This is atomic visibility, not a crash-durability guarantee. Setup paths belong to the exercise operator; this is not a race-free defense against a concurrent same-account mutator.

Repairing the result again must produce the same data. Use deterministic formatting so you can also compare bytes during your own tests. Return 0 only after successful publication.

## What the external checks observe

The grader rotates identities, resources, literals, fake canaries, and six combinations containing one through five weak choices. It compares preserved input/workload, complete controls, idempotence, malformed-input refusal, and fixed local harness results.

Allowed synthetic work must remain successful. The constant shell marker fixture must not run; the explicitly fake ambient variable must be absent; the generated protected sibling must not be read; the broker-only model branch must skip socket creation; and the cleanup selection must exclude the unowned string decoy.

These are finite model observations. The check does not prove kernel network denial, race-free filesystem confinement, actual cleanup ownership, or complete coverage of every malformed plan. Test your validation/publication edge cases yourself. No candidate is deleted and no socket connects.

## Map the work to practice

Plan shape and data preservation: 11.01 and 11.03. Evidence completeness and calibrated claims: 11.02. Exclusive temporary output, atomic publication, and idempotence: 11.03. Structured input and error status: Module 04.

Write `design-notes.md` describing one partial repair, the remaining observations, and how your complete repair preserves useful work. The independent lab intentionally withholds a complete implementation.

## Validate and replay

```bash
python3 -m py_compile repair_variant.py
../../lab-grade module-11
../../lab-grade module-11 --mode exam
```

Syntax checking does not execute a plan. Practice grading reports failed properties with lesson references; exam grading reduces hints and uses fresh fixtures.

If the allowed operation fails, inspect preserved workload data before changing the harness. If malformed input leaves output, inspect validation order and publication. Never replace missing observations with invented negative values.

Save notes, return with `cd ../..`, and use `./lab-reset module-11` to remove this prepared workspace and generated fixtures. There is no background service to kill. Do not extend the harness into an external scanner, arbitrary command runner, or destructive cleanup tool.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-12-adaptive-adversary/README.md format=markdown -->
# Module 12 - Bounded decisions, evidence, and reproducible review

Complete Modules 04, 10, and 11, then work through `12.01`, `12.02`, `12.03`, and `module-12`.

The directory keeps its historical “adaptive adversary” name for compatibility. The actual exercise is a **toy bounded dispatcher**: inventory explicitly tells the program which synthetic label to request next. This is not independent vulnerability discovery, agentic research, or a test of a real target.

You will learn to:

- compare a fixed schedule with an observation-dependent choice without overstating either result;
- count every action, preserve its observation, and stop within a small budget;
- distinguish a witnessed failure, missing evidence, and a complete set of favorable observations;
- reject malformed evidence rather than silently calling it safe;
- package known local code and inputs, verify their recorded hashes, and replay from a new directory;
- explain why reproducibility and checksums do not establish truth, trust, or universal security.

The offline evidence-review exercise is the central reasoning task. Its supplied rows stand for observations; they are not new kernel measurements. Return to the earlier modules for actual enforced-control tests. No new external probes, target selection, or exploit generation are part of this chapter.

The final package can be described as a candidate experiment for later review. “Boundary Atlas” is a historical destination label, not a required service, credential, or methodology. Keep all work in the disposable VM with synthetic files.
<!-- /source -->

---

<!-- source: course/module-12-adaptive-adversary/lesson-01/README.md format=markdown -->
# 12.01 - Establish a scripted baseline and its limits

## Outcomes and prerequisites

Complete Module 11. You will read a fixed synthetic oracle, predict a baseline's three requests, record what was and was not observed, and repair an overbroad conclusion without inventing evidence.

## Concepts before commands

An **oracle** is an interface that returns an answer to a question. This oracle is unusually simple: it compares a requested label to a value stored in a JSON file. It does not attempt a filesystem read, create a network connection, inspect credentials, or measure containment.

A **baseline** is a deliberately fixed comparison procedure. Keeping its behavior stable helps explain a later difference. It does not make the procedure complete or fair for every objective.

Here, the fixed schedule omits two labels. A “not observed” result can therefore mean “we never asked.” The next lesson's inventory response actually supplies the answer. A two-call result there is evidence of following a hint, not independent discovery or general agent intelligence.

## Prepare and access the files

From the course root:

```bash
./lab-start 12.01
cd .student/12.01
pwd
ls -l local_oracle.py scripted_baseline.py network-scenario.json
cat local_oracle.py
cat scripted_baseline.py
cat network-scenario.json
```

Use `nano` with a filename to navigate the source. Leave these known teaching files intact; create separate scenario files when changing input. Never replace the oracle command with an unknown executable or a real target.

### The fixed synthetic oracle

```python
#!/usr/bin/env python3
"""Synthetic one-weakness oracle: JSON scenario plus one named probe."""
import json, sys
from pathlib import Path

PROBES = ("argv", "credential", "filesystem", "network", "cleanup")
if len(sys.argv) != 3 or sys.argv[2] not in ("inventory", *PROBES):
    raise SystemExit(2)
scenario = json.loads(Path(sys.argv[1]).read_text())
if (not isinstance(scenario, dict) or set(scenario) != {"schema", "weakness"}
        or type(scenario["schema"]) is not int or scenario["schema"] != 1
        or (scenario["weakness"] is not None and scenario["weakness"] not in PROBES)):
    raise SystemExit("invalid synthetic scenario")
weakness = scenario.get("weakness")
probe = sys.argv[2]
if probe == "inventory":
    value = {"ok": True, "surface": list(PROBES), "next_probe": weakness}
else:
    value = {"ok": True, "probe": probe, "observed": probe == weakness,
             "evidence": f"synthetic-{probe}-effect" if probe == weakness else None}
print(json.dumps(value, sort_keys=True))
```

### Source, line by line

- `PROBES` names the five accepted labels. They are strings, not implementations of security tests.
- The argument guard expects a scenario filename and one accepted request.
- Scenario validation requires the exact shape, integer schema 1, and a known label or JSON null.
- Inventory returns the list and `next_probe`, which is the stored label itself.
- A focused request compares the two labels. Equality produces `observed: true` and a synthetic text marker.
- JSON is printed to stdout. No actual containment control or target is exercised.

### The scripted baseline

```python
#!/usr/bin/env python3
"""Run the same fixed probes in the same order for every scenario."""
import json, subprocess, sys
from pathlib import Path

if len(sys.argv) != 4:
    raise SystemExit(2)
oracle, scenario, output = sys.argv[1:]
trace = []
for probe in ("argv", "credential", "filesystem"):
    run = subprocess.run([sys.executable, oracle, scenario, probe], text=True,
                         capture_output=True, check=True, timeout=3)
    observation = json.loads(run.stdout)
    trace.append({"probe": probe, "observation": observation})
finding = next((row for row in trace if row["observation"].get("observed")), None)
Path(output).write_text(json.dumps({"strategy": "scripted", "status": "observed" if finding else "not_observed",
                                   "trace": trace}, indent=2, sort_keys=True) + "\n")
```

### Source, line by line

- The interface expects oracle, scenario, and output paths.
- The loop always selects argv, credential, and filesystem in that order.
- Each invocation is a structured argument list, with a three-second timeout and nonzero-status checking.
- Parsed output is retained alongside the requested label, not replaced with a summary guess.
- The first positive row becomes the finding; if none is positive, status is `not_observed`.
- The complete trace is saved with deterministic JSON formatting.

This small trusted-fixture example does not provide a general hostile-process supervisor or a streaming output limit. The named oracle is trusted course code. A timeout or malformed response is an execution error, not a negative security observation.

### The supplied scenario

```json
{"schema":1,"weakness":"network"}
```

The label is `network`. No network operation accompanies that name.

## Exercise 1 - Predict and run the baseline

```bash
python3 scripted_baseline.py local_oracle.py network-scenario.json baseline.json
python3 -m json.tool baseline.json
```

Predict the three rows before execution. All should contain `observed: false`, and the result should be `not_observed`. There is no network row because the schedule did not ask that question.

The intentional mistake is to write “the network boundary is secure.” Repair that statement to “the three requested synthetic labels did not match; the network label was not requested.” Do not repair the result by adding a fabricated row.

## Exercise 2 - Ask the omitted question explicitly

```bash
python3 local_oracle.py network-scenario.json network > focused.json
python3 local_oracle.py network-scenario.json inventory > inventory.json
python3 -m json.tool focused.json
python3 -m json.tool inventory.json
```

The focused answer should be true and inventory should name `network`. These are **two additional actions**, not part of the baseline's original three. Count them separately in your notes. The positive result establishes only the oracle's configured label match.

## Exercise 3 - Change input, retain the schedule

```bash
python3 - <<'PY'
import json
from pathlib import Path

Path("argv-scenario.json").write_text(json.dumps({"schema": 1, "weakness": "argv"}) + "\n")
Path("none-scenario.json").write_text(json.dumps({"schema": 1, "weakness": None}) + "\n")
PY
python3 scripted_baseline.py local_oracle.py argv-scenario.json argv-result.json
python3 scripted_baseline.py local_oracle.py none-scenario.json none-result.json
```

The same schedule reports observed for the argv label and not observed for null. Thus the original negative result alone cannot distinguish an omitted matching label from a no-label scenario.

## Checkpoint and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

def load(name):
    return json.loads(Path(name).read_text())

baseline = load("baseline.json")
assert [row["probe"] for row in baseline["trace"]] == ["argv", "credential", "filesystem"]
assert baseline["status"] == "not_observed"
assert load("focused.json")["observed"] is True
assert load("inventory.json")["next_probe"] == "network"
assert load("argv-result.json")["status"] == "observed"
assert load("none-result.json")["status"] == "not_observed"
print("FIXED SCHEDULE AND OMITTED-QUESTION LIMIT: PASS")
PY
```

In `baseline-notes.md`, record the procedure, actual trace, omitted question, revised claim, and why inventory makes the later task easier. Explain why this exercise cannot establish a real network-control failure.

If JSON parsing fails, inspect stderr and the exact scenario path. Do not turn process errors into `observed: false`. Save notes, return with `cd ../..`, then use `./lab-reset 12.01` for a clean replay. No service or network endpoint was started.

## Source truth

Python's [subprocess documentation](https://docs.python.org/3.14/library/subprocess.html) defines argument lists, status checking, and timeouts; [JSON documentation](https://docs.python.org/3.14/library/json.html) defines data parsing. The label oracle and the meaning of its fields are course-defined, not properties of Linux security controls.
<!-- /source -->

---

<!-- source: course/module-12-adaptive-adversary/lesson-02/README.md format=markdown -->
# 12.02 - Adapt within an action budget

## Outcomes and prerequisites

Complete 12.01. You will trace one hint-dependent choice, observe a budget that prevents the second action, and use an offline reviewer to distinguish contrary, missing, and favorable evidence.

## Concepts before commands

An **action budget** limits the number of requests. A per-request timeout limits waiting for that invocation; these are different limits. A budget of two does not authorize two arbitrary commands.

This teaching runner calls inventory once, then at most one allowlisted label supplied by inventory. Its “adaptation” is ordinary conditional dispatch. Inventory already names the scenario's configured answer. There is no independent discovery, model service, exploit generation, or real target.

A **calibrated claim** says no more than the observations support. A complete favorable set can support “these supplied checks passed,” not “the system is secure.” An unknown or omitted check cannot support even that narrower conclusion.

## Prepare and read the programs

From the course root:

```bash
./lab-start 12.02
cd .student/12.02
pwd
ls -l adaptive_runner.py network-spec.json review_evidence.py evidence-cases.json
cat adaptive_runner.py
cat network-spec.json
cat review_evidence.py
cat evidence-cases.json
```

Use `nano` to navigate any listed file. The oracle paths in the spec are relative to this prepared workspace. Run from here, not from the course root or the canonical source directory.

### The bounded teaching dispatcher

```python
#!/usr/bin/env python3
"""Use one inventory observation to choose one bounded focused probe."""
import json, subprocess, sys
from pathlib import Path

ALLOWED = {"inventory", "argv", "credential", "filesystem", "network", "cleanup"}

def main():
    if len(sys.argv) != 3:
        return 2
    spec = json.loads(Path(sys.argv[1]).read_text())
    if not isinstance(spec, dict) or set(spec) != {"oracle_command", "budget", "run_id"}:
        return 1
    command, budget = spec["oracle_command"], spec["budget"]
    if (not isinstance(command, list) or not command
            or any(not isinstance(x, str) or "\0" in x for x in command)
            or not command[0]):
        return 1
    if type(budget) is not int or not 1 <= budget <= 8 or not isinstance(spec["run_id"], str):
        return 1
    trace = []
    for probe in ("inventory",):
        run = subprocess.run([*command, probe], text=True, capture_output=True, timeout=3, check=False)
        if run.returncode != 0: return 1
        try: observation = json.loads(run.stdout)
        except json.JSONDecodeError: return 1
        if not isinstance(observation, dict) or observation.get("ok") is not True: return 1
        trace.append({"action": len(trace) + 1, "probe": probe, "observation": observation})
    suggested = trace[0]["observation"].get("next_probe")
    if suggested is not None and budget > 1:
        if not isinstance(suggested, str) or suggested not in ALLOWED or suggested == "inventory": return 1
        run = subprocess.run([*command, suggested], text=True, capture_output=True, timeout=3, check=False)
        if run.returncode != 0: return 1
        try: observation = json.loads(run.stdout)
        except json.JSONDecodeError: return 1
        if (not isinstance(observation, dict) or observation.get("ok") is not True
                or observation.get("probe") != suggested
                or type(observation.get("observed")) is not bool): return 1
        trace.append({"action": 2, "probe": suggested, "observation": observation})
    finding = next((row for row in trace if row["observation"].get("observed") is True), None)
    result = {"schema": 1, "run_id": spec["run_id"], "budget": budget,
              "actions_used": len(trace), "status": "observed" if finding else "not_observed",
              "finding": finding, "claim": "bounded probe observed a synthetic effect" if finding else
              "no effect observed within this bounded probe budget; security is not established", "trace": trace}
    Path(sys.argv[2]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0

if __name__ == "__main__": raise SystemExit(main())
```

### Source, line by line

- `ALLOWED` restricts the label added to the trusted operator-supplied oracle argv.
- The exact spec shape separates command, integer budget, and opaque run identity.
- Argument/type checks reject malformed argv, embedded NUL, and Boolean/out-of-range budgets.
- Inventory is the first action. Its nonzero status, invalid JSON, or non-success object prevents a claimed result.
- The complete parsed observation is retained with sequential action number 1.
- A non-null hint and remaining budget permit exactly one focused label. The allowlist prevents inventing additional actions.
- The focused response must identify the requested label and contain a real Boolean observation.
- A positive row becomes the finding. Otherwise the result explicitly says security is not established.
- The result records budget, actual action count, identity, claim, and full trace.

Even a budget of eight causes at most two calls in this particular implementation. The upper bound is not a goal to consume. The command itself is trusted course configuration: an argv list and an allowlisted suffix do **not** make an unknown executable safe. Captured output is not independently byte-bounded; use only the tiny known fixture here.

### The prepared spec

```json
{"oracle_command":["python3","../../course/module-12-adaptive-adversary/lesson-01/local_oracle.py","../../course/module-12-adaptive-adversary/lesson-01/network-scenario.json"],"budget":2,"run_id":"lesson-network"}
```

Its command uses the canonical local label oracle from 12.01. No live network service is involved.

## Exercise 1 - Observe two actions, then deliberately allow only one

```bash
python3 adaptive_runner.py network-spec.json two-actions.json
python3 -m json.tool two-actions.json
python3 - <<'PY'
import json
from pathlib import Path

spec = json.loads(Path("network-spec.json").read_text())
spec["budget"] = 1
Path("one-action-spec.json").write_text(json.dumps(spec) + "\n")
PY
python3 adaptive_runner.py one-action-spec.json one-action.json
python3 -m json.tool one-action.json
python3 adaptive_runner.py network-spec.json repaired-budget.json
cmp two-actions.json repaired-budget.json
```

With budget two, expect inventory followed by network, and an observed synthetic label match. With budget one, inventory still names network, but the runner must not claim the unperformed focused observation. The repair restores the original allowed budget and obtains a fresh second action.

Do not report this as outperforming a real security analyst or independently finding a weakness. The comparison changes both the schedule and access to an answer-providing hint.

### The offline evidence reviewer

```python
#!/usr/bin/env python3
"""Interpret fixed local observations. This program never invokes a probe."""
import json
from pathlib import Path
import sys

EXPECTED = {"allowed_work": "success", "protected_read": "denied", "direct_ip": "denied"}


def review(case):
    if (not isinstance(case, dict) or set(case) != {"case_id", "budget", "observations"}
            or not isinstance(case["case_id"], str) or not case["case_id"]
            or type(case["budget"]) is not int or not 1 <= case["budget"] <= 8
            or not isinstance(case["observations"], list)):
        raise ValueError("invalid evidence case")
    observations = case["observations"]
    if len(observations) > case["budget"]:
        raise ValueError("observation budget exceeded")
    seen = {}
    for observation in observations:
        if not isinstance(observation, dict) or set(observation) != {"check", "outcome"}:
            raise ValueError("invalid observation shape")
        name, outcome = observation["check"], observation["outcome"]
        if not isinstance(name, str) or name not in EXPECTED or name in seen:
            raise ValueError("unknown or duplicate check")
        permitted = {"success", "failure", "unknown"} if name == "allowed_work" else {"allowed", "denied", "unknown"}
        if not isinstance(outcome, str) or outcome not in permitted:
            raise ValueError("invalid observation outcome")
        seen[name] = outcome
    failures = sorted(name for name, value in seen.items()
                      if value != "unknown" and value != EXPECTED[name])
    missing = sorted(name for name in EXPECTED if name not in seen or seen[name] == "unknown")
    status = "observed_failure" if failures else "inconclusive" if missing else "passed_observations"
    return {"case_id": case["case_id"], "status": status, "failures": failures,
            "missing": missing, "claim": "limited to the supplied observations; security is not established"}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: review_evidence.py CASES.json")
    cases = json.loads(Path(sys.argv[1]).read_text())
    if not isinstance(cases, list):
        raise SystemExit("cases must be a JSON list")
    print(json.dumps([review(case) for case in cases], indent=2, sort_keys=True))
```

### Source, line by line

- `EXPECTED` describes three intended outcomes: useful work succeeds, protected read is denied, and direct IP is denied.
- Shape, budget, and identity checks validate the supplied case before interpretation.
- Each observation must have exactly a known check and a permitted textual outcome.
- Duplicate checks are rejected instead of allowing the later row to overwrite earlier evidence.
- A contrary known outcome is an observed failure. Missing or explicitly unknown outcomes are recorded separately.
- A failure takes precedence even if some other checks are missing.
- Without failures, missing evidence is inconclusive; only a complete favorable set yields `passed_observations`.
- Every result limits its claim to supplied observations. The reviewer invokes no workload or probe.

### Four supplied cases

```json
[
  {"case_id":"complete-hardened","budget":3,"observations":[{"check":"allowed_work","outcome":"success"},{"check":"protected_read","outcome":"denied"},{"check":"direct_ip","outcome":"denied"}]},
  {"case_id":"complete-seeded","budget":3,"observations":[{"check":"allowed_work","outcome":"success"},{"check":"protected_read","outcome":"allowed"},{"check":"direct_ip","outcome":"denied"}]},
  {"case_id":"incomplete-seeded","budget":3,"observations":[{"check":"allowed_work","outcome":"success"},{"check":"direct_ip","outcome":"denied"}]},
  {"case_id":"ambiguous-hardened","budget":3,"observations":[{"check":"allowed_work","outcome":"success"},{"check":"protected_read","outcome":"unknown"},{"check":"direct_ip","outcome":"denied"}]}
]
```

The case IDs describe author intent but are not decision inputs. A misleading “hardened” label must not override the rows. These are fixed data fixtures, not measurements newly collected from your VM.

## Exercise 2 - Predict all four decisions

```bash
python3 review_evidence.py evidence-cases.json > review.json
python3 -m json.tool review.json
```

Expected statuses, in order: passed observations, observed failure, inconclusive, inconclusive. The second case supplies an allowed protected read. The third omits that observation; the fourth supplies unknown. Missing and unknown have different provenance but neither proves denial.

## Exercise 3 - Construct the missing-plus-failure case

```bash
python3 - <<'PY'
import json
from pathlib import Path

case = {"case_id": "named-hardened-but-incomplete", "budget": 3,
        "observations": [{"check": "allowed_work", "outcome": "success"},
                         {"check": "protected_read", "outcome": "allowed"}]}
Path("new-case.json").write_text(json.dumps([case]) + "\n")
bad = dict(case, observations=case["observations"] + [case["observations"][0]])
Path("duplicate-case.json").write_text(json.dumps([bad]) + "\n")
PY
python3 review_evidence.py new-case.json > new-review.json
NE_DUPLICATE_STATUS=0
python3 review_evidence.py duplicate-case.json > rejected.json 2> rejected.err || NE_DUPLICATE_STATUS=$?
test "$NE_DUPLICATE_STATUS" -ne 0
test ! -s rejected.json
python3 review_evidence.py new-case.json > repaired-review.json
cmp new-review.json repaired-review.json
```

The new case is an observed failure with direct IP still missing. Missing evidence does not erase a witnessed failure. The deliberate duplicate is malformed and must be rejected, not counted as a third independent observation. Repair by returning to the valid case, never by fabricating a denial.

## Checkpoint and faded practice

```bash
python3 - <<'PY'
import json
from pathlib import Path

def load(name):
    return json.loads(Path(name).read_text())

one, two = load("one-action.json"), load("two-actions.json")
assert one["actions_used"] == 1 and one["finding"] is None
assert one["status"] == "not_observed" and "not established" in one["claim"]
assert [row["probe"] for row in two["trace"]] == ["inventory", "network"]
assert two["actions_used"] == 2 and two["finding"] == two["trace"][1]
assert [row["status"] for row in load("review.json")] == [
    "passed_observations", "observed_failure", "inconclusive", "inconclusive"]
new = load("new-review.json")[0]
assert new["status"] == "observed_failure"
assert new["failures"] == ["protected_read"] and new["missing"] == ["direct_ip"]
print("BUDGET, FAILURE, AND MISSING-EVIDENCE DISTINCTIONS: PASS")
PY
```

Write `evidence-notes.md`. Design one additional **offline JSON case** that tests allowed work failing while denials succeed. Predict the status, run the reviewer, and explain why disabling all useful work is not successful containment. Change only data in this prepared workspace; do not add probes or targets.

If a runner invocation fails, inspect stderr and distinguish setup failure from an observed negative result. If a reviewer refuses a case, fix the malformed shape rather than weakening the reviewer. Save notes, return with `cd ../..`, and use `./lab-reset 12.02`. No background resources were created.

## Source truth

Python's [subprocess](https://docs.python.org/3.14/library/subprocess.html) and [JSON](https://docs.python.org/3.14/library/json.html) references explain execution and serialization mechanics. The decision table is an explicit course evidence policy, not a statistical proof or an external certification standard.
<!-- /source -->

---

<!-- source: course/module-12-adaptive-adversary/lesson-03/README.md format=markdown -->
# 12.03 - Package a calibrated candidate experiment

## Outcomes and prerequisites

Complete 12.01-12.02. You will package known local code, inputs, and observations; verify their recorded bytes; detect a missing or changed input before replay; and repeat the experiment from a relocated directory.

## Concepts before commands

**Reproducibility** requires the inputs and procedure, not just the conclusion. A result without the code and scenario may be impossible to interpret later.

A **checksum** describes bytes. Comparing a file to its recorded SHA-256 detects a mismatch, but an attacker who can replace both file and inventory can make them agree. This package is not signed, and matching hashes do not establish authorship, trustworthy behavior, or the truth of a claim.

Only replay the known course sources you have just read. Never execute an unknown downloaded “experiment” because its self-supplied manifest verifies. Even an exact argv list can launch harmful code.

## Prepare and read both programs

From the course root:

```bash
./lab-start 12.03
cd .student/12.03
pwd
ls -l package_experiment.py verify_package.py
cat package_experiment.py
cat verify_package.py
```

Use `nano` with the exact filename to navigate. The input runner and oracle remain the known synthetic programs from 12.01-12.02, not a new probing tool.

### The packager

```python
#!/usr/bin/env python3
"""Bundle explicit local inputs and sources for replay from a clean directory."""
import hashlib
import json
from pathlib import Path
import sys


def main():
    if len(sys.argv) != 6:
        raise SystemExit("usage: package_experiment.py RESULT SPEC RUNNER CANDIDATE_ID DIRECTORY")
    result_path, spec_path, runner = map(Path, sys.argv[1:4])
    result = json.loads(result_path.read_text())
    spec = json.loads(spec_path.read_text())
    if (not isinstance(spec, dict) or set(spec) != {"oracle_command", "budget", "run_id"}
            or type(spec["budget"]) is not int or not 1 <= spec["budget"] <= 8
            or not isinstance(spec["run_id"], str)
            or not isinstance(result, dict)):
        raise SystemExit("invalid spec or result shape")
    command = spec["oracle_command"]
    if (not isinstance(command, list) or len(command) != 3
            or any(not isinstance(item, str) or not item for item in command)):
        raise SystemExit("packaging supports only the explicit local Python oracle plus scenario interface")
    oracle, scenario = map(Path, command[1:])
    trace = result.get("trace", [])
    if (type(result.get("schema")) is not int or result.get("schema") != 1
            or result.get("status") not in ("observed", "not_observed")
            or not isinstance(trace, list) or not isinstance(result.get("claim"), str)
            or type(result.get("actions_used")) is not int
            or result.get("run_id") != spec["run_id"]
            or result.get("actions_used") != len(trace) or not 1 <= len(trace) <= spec["budget"]):
        raise SystemExit("invalid result, run identity, or budget")
    files = {"runner.py": runner.read_bytes(), "oracle.py": oracle.read_bytes(),
             "scenario.json": scenario.read_bytes(), "expected.json": result_path.read_bytes()}
    portable = dict(spec, oracle_command=["python3", "oracle.py", "scenario.json"])
    files["spec.json"] = (json.dumps(portable, indent=2, sort_keys=True) + "\n").encode()
    package = {"schema": 2, "candidate_id": sys.argv[4], "run_id": spec["run_id"],
               "hypothesis": "The recorded local scenario permits the reported observation within this budget.",
               "result_status": result["status"], "claim": result["claim"],
               "limits": ["synthetic local oracle", "single run", "bounded probe set", "non-discovery is not proof"],
               "replay": ["python3", "runner.py", "spec.json", "result.json"],
               "sha256": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}
    output = Path(sys.argv[5])
    output.mkdir()  # Never overwrite an existing experiment or student work.
    for name, data in files.items():
        (output / name).write_bytes(data)
    (output / "package.json").write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
```

### Source, line by line

- Five arguments identify the existing result, spec, runner, local candidate label, and new destination.
- Spec/result checks require the known schema, matching run identity, and a trace count within budget. They do not independently authenticate or remeasure observations.
- The command must have the local Python-oracle-plus-scenario shape. The packager does not discover arbitrary program dependencies or prove the supplied executable trustworthy.
- The files mapping reads the known sources, scenario, and expected result as bytes.
- A portable spec names the copied files relative to the package directory; it does not preserve a workstation-specific absolute repository path.
- SHA-256 is calculated over each packaged file's exact bytes.
- The package records hypothesis, claim, limits, and a replay argv. These are review metadata, not a certification or publication.
- `mkdir()` refuses an existing destination. Writing occurs only inside this newly created directory.
- An interrupted write can leave an incomplete directory. Verification must reject missing content; do not overwrite the directory to disguise that failure.

The packager assumes small trusted local inputs. It is neither a dependency manager nor a general safe archive extractor.

### The non-executing verifier

```python
#!/usr/bin/env python3
"""Check the fixed local package inventory without executing packaged code."""
import hashlib
import json
from pathlib import Path
import re
import sys

FILES = {"runner.py", "oracle.py", "scenario.json", "expected.json", "spec.json"}


def verify(root):
    manifest = root / "package.json"
    if root.is_symlink() or manifest.is_symlink() or not manifest.is_file():
        raise ValueError("expected an ordinary package directory and manifest")
    package = json.loads(manifest.read_text())
    hashes = package.get("sha256") if isinstance(package, dict) else None
    if not isinstance(hashes, dict) or set(hashes) != FILES:
        raise ValueError("unexpected package inventory")
    for name in sorted(FILES):
        digest = hashes[name]
        path = root / name
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("invalid digest")
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"missing or non-regular package file: {name}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"checksum mismatch: {name}")
    print("PACKAGE BYTES MATCH RECORDED INVENTORY; AUTHENTICITY IS NOT ESTABLISHED")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_package.py DIRECTORY")
    try:
        verify(Path(sys.argv[1]))
    except (OSError, ValueError) as error:
        raise SystemExit(f"package verification failed: {error}")
```

### Source, line by line

- `FILES` is an exact allowlist, not a set of arbitrary paths taken from a manifest.
- The directory/manifest leaf checks refuse symbolic links and missing regular input.
- Parsing requires a mapping with exactly the five expected hash entries.
- Each hash must be a lowercase 64-character hexadecimal string.
- Each expected file must be a regular non-symlink leaf; its bytes are hashed and compared.
- The success message states the limit: matching inventory does not establish authenticity.
- Exceptions produce nonzero status and a diagnostic. No packaged program is imported or executed.

This verifier does not claim race-free behavior against a concurrent same-account mutator, validate every metadata field, or inventory unrelated extra files. Keep the prepared directory under your control.

## Exercise 1 - Produce and package known evidence

```bash
NE_RUNNER=../../course/module-12-adaptive-adversary/lesson-02/adaptive_runner.py
NE_SPEC=../../course/module-12-adaptive-adversary/lesson-02/network-spec.json
python3 "$NE_RUNNER" "$NE_SPEC" result.json
python3 package_experiment.py result.json "$NE_SPEC" "$NE_RUNNER" candidate-12 package
python3 -m json.tool package/package.json
python3 verify_package.py package
```

The two variables name sources you already read. Quoting keeps each pathname one argument. `candidate-12` is merely your local label, not a vulnerability identifier.

Predict the five hashed files and compare with the printed inventory. The manifest is not included in its own hash list. The original result is copied as `expected.json`; a later replay will create a separate `result.json`.

## Exercise 2 - Deliberately remove an input, then repair it

```bash
mv package/scenario.json package/scenario.saved
NE_MISSING_STATUS=0
python3 verify_package.py package > missing.out 2> missing.err || NE_MISSING_STATUS=$?
test "$NE_MISSING_STATUS" -ne 0
cat missing.err
mv package/scenario.saved package/scenario.json
python3 verify_package.py package
```

Verification must fail before any replay command is run. Restore the **same** saved file, then verify again. A metadata summary cannot replace a missing scenario.

Now change only the scenario's formatting, retaining the same JSON meaning:

```bash
cp package/scenario.json original-scenario.json
python3 - <<'PY'
from pathlib import Path

path = Path("package/scenario.json")
path.write_bytes(path.read_bytes() + b"\n")
PY
NE_CHANGED_STATUS=0
python3 verify_package.py package > changed.out 2> changed.err || NE_CHANGED_STATUS=$?
test "$NE_CHANGED_STATUS" -ne 0
cat changed.err
cp original-scenario.json package/scenario.json
python3 verify_package.py package
```

The checksum changes even though JSON parsing would yield the same object. It identifies bytes, not semantic equivalence. Repair by restoring the recorded source, not by silently changing the hash to fit an unexplained modification.

## Exercise 3 - Relocate and replay

```bash
mv package relocated-package
python3 verify_package.py relocated-package
(
  cd relocated-package
  python3 runner.py spec.json result.json
  cmp expected.json result.json
)
python3 package_experiment.py result.json "$NE_SPEC" "$NE_RUNNER" candidate-12 second-package
cmp relocated-package/package.json second-package/package.json
NE_EXISTING_STATUS=0
python3 package_experiment.py result.json "$NE_SPEC" "$NE_RUNNER" candidate-12 second-package \
  > existing.out 2> existing.err || NE_EXISTING_STATUS=$?
test "$NE_EXISTING_STATUS" -ne 0
python3 verify_package.py second-package
```

The parentheses create a subshell; its directory change does not move your outer lesson shell. Replay uses only the copied runner, oracle, scenario, and spec. The Python runtime remains an environmental dependency; this is source portability, not a bootable or hermetic environment.

The second package has identical metadata for identical inputs. Repeating into its existing directory fails without overwriting it. Byte-identical results are possible because this tiny oracle omits timestamps and real-world variability; do not demand that property from every legitimate experiment.

## Checkpoint and independent explanation

```bash
python3 - <<'PY'
import json
from pathlib import Path

root = Path("relocated-package")
package = json.loads((root / "package.json").read_text())
assert package["candidate_id"] == "candidate-12"
assert package["replay"] == ["python3", "runner.py", "spec.json", "result.json"]
assert json.loads((root / "spec.json").read_text())["oracle_command"] == [
    "python3", "oracle.py", "scenario.json"]
assert (root / "expected.json").read_bytes() == (root / "result.json").read_bytes()
assert "non-discovery is not proof" in package["limits"]
assert "checksum mismatch" in Path("changed.err").read_text()
assert "missing or non-regular" in Path("missing.err").read_text()
print("PORTABLE REPLAY AND NON-EXECUTING INTEGRITY CHECKS: PASS")
PY
```

Write `review-notes.md` separating hypothesis, observed result, interpretation, limits, and proposed next **review** question. Explain why a forged result could still be packaged and why matching hashes do not authorize running unfamiliar code. No external submission is required.

If replay fails, compare the interpreter version and verified inputs before changing the expected result. If a package already exists, use a new exact destination or reset the lesson after saving your notes. Do not remove files by a broad prefix.

Save any package you want to keep, return with `cd ../..`, then use `./lab-reset 12.03` to discard the prepared workspace. The course reset removes generated local files after ownership checks; this exercise creates no background service.

## Source truth

Python's [hashlib documentation](https://docs.python.org/3.14/library/hashlib.html) defines the byte digest used here. [JSON documentation](https://docs.python.org/3.14/library/json.html) explains serialization, which is distinct from byte identity and from the truth of evidence. Package format and claim limits are course-defined.
<!-- /source -->

---

<!-- source: course/module-12-adaptive-adversary/lab/README.md format=markdown -->
# Module 12 independent lab - Bounded synthetic dispatch

## Assignment and readiness check

Implement the small hint-dependent protocol practiced in 12.01-12.02. Preserve the exact action record and keep conclusions within the evidence. This is **not** an independent discovery tool: inventory supplies the synthetic label to request.

Before coding, explain the difference between budget and timeout, missing evidence and a negative observation, matching hashes and trustworthy code, and a returned hint and an actually performed focused request.

## Prepare and read the starter

From the course root:

```bash
./lab-start module-12
cd .student/12.lab
pwd
ls -l adaptive_runner.py
cat adaptive_runner.py
nano adaptive_runner.py
```

Edit only the prepared file. Ctrl+O then Enter saves in default nano; Ctrl+X exits.

```python
#!/usr/bin/env python3
"""Module 12 starter: inventory only, with a calibrated non-discovery claim."""
import json, subprocess, sys
from pathlib import Path

if len(sys.argv) != 3: raise SystemExit(2)
spec = json.loads(Path(sys.argv[1]).read_text())
run = subprocess.run([*spec["oracle_command"], "inventory"], text=True, capture_output=True, timeout=3)
observation = json.loads(run.stdout)
Path(sys.argv[2]).write_text(json.dumps({"schema":1,"run_id":spec["run_id"],"budget":spec["budget"],
 "actions_used":1,"status":"not_observed","finding":None,
 "claim":"no effect observed within this bounded probe budget; security is not established",
 "trace":[{"action":1,"probe":"inventory","observation":observation}]})+"\n")
```

### Starter, line by line

- Imports provide JSON, a subprocess, arguments, and paths.
- The interface expects spec and output filenames, but parsing does not yet validate their complete contract.
- One structured invocation requests inventory with a per-call timeout.
- Its output is parsed without the full success/shape checks you must add.
- The result retains the observation and run identity, but never performs the hinted second request.
- The non-discovery claim is appropriately limited even though the implementation is incomplete.

Your task is complete accounting and validation within this fixed teaching protocol, not adding targets, probes, or autonomous exploration.

## Interface and result contract

The grader invokes:

```text
python3 adaptive_runner.py SPEC.json RESULT.json
```

The exact spec fields are `oracle_command`, `budget`, and `run_id`. Require a nonempty list of string argv with no NUL characters and a nonempty executable, an actual integer budget from 1 through 8 (not Boolean), and a string identity. Validate before any call; preserve the spec unchanged.

Only use the trusted local oracle command supplied by the exercise operator, without shell interpretation. Request inventory first. If it supplies a known focused label and budget remains, request that label once. The only labels are inventory, argv, credential, filesystem, network, and cleanup. Do not inspect scenario implementation details, invent more probes, or leave the supplied interface.

Bound every invocation, reject nonzero/invalid responses, and retain each complete parsed observation with sequential action numbers beginning at 1. A focused response must identify the requested label and supply a Boolean `observed` value. Every actual call counts; do not omit failed or inconvenient actions to manufacture a successful trace.

On successful protocol completion, write schema 1, run identity, budget, actual action count, full trace, status, finding, and claim. If a focused row reports true, status is `observed` and finding is that exact row. Otherwise use `not_observed`, null finding, and an explicit statement that security is not established. An execution/validation failure must return nonzero, not publish a fabricated negative result.

No result should imply that the toy oracle measured Linux enforcement. Keep real-control conclusions tied to the earlier modules' actual behavioral tests.

## What the external checks observe

The grader rotates five synthetic labels plus a null-hint case and independently logs the actual oracle calls and parsed responses. It compares your trace to that record, checks the two-action assessment budget, exact identity/input preservation, deterministic repetition, hinted observations, and a calibrated no-observation claim.

The checks are finite, not exhaustive malformed-input certification. Test budget one, wrong types, process failure, and invalid response handling yourself using only small local fixtures. The provided inventory explicitly names the answer; a passing grade is not evidence of independent vulnerability discovery or general research ability.

## Map assessed skills to practice

Fixed schedule and its omissions: 12.01. Structured argv and status handling: Module 04. Conditional choice, action count, and limited claims: 12.02. Evidence completeness: 11.02 and the offline reviewer in 12.02. Reproducible review artifacts: 12.03.

Write `assessment-notes.md` explaining why a one-action run can receive a hint but still report no focused observation. Also include your offline allowed-work-failure case from 12.02. The grader cannot assess the quality of this explanation; learner review must.

## Validate, diagnose, and replay

```bash
python3 -m py_compile adaptive_runner.py
../../lab-grade module-12
../../lab-grade module-12 --mode exam
```

Practice mode reports failed properties with references; exam mode reduces hints. If traces differ, compare **actual requests and observations**, not just your reported count. Do not alter the oracle log or suppress actions to pass.

Save your notes, return with `cd ../..`, and use `./lab-reset module-12`. Only prepared local files and fixtures are removed; no network service or external target exists in this lab.
<!-- /source -->

# Cold capstone - Process an ordered batch of contained jobs

## Objective and prerequisites

Build `cold_runtime.py`: a batch launcher that completes useful work under different resource ceilings, preserves each job's identity and ordinary failure status, and collects every exact owned runtime. This transfers single-job skills to a new interface; it is not a request to paste the Module 10 launcher unchanged.

Complete B0/B1 as needed, Modules 01-12, their practicals, and the cumulative checkpoints. Before beginning, revisit the **practice**, not a complete capstone solution: the 0/7/0 static worker sequence and validation-order question in 10.03, structured lists/status aggregation in Module 04, and evidence limits in Modules 11-12.

## Prepare a cold workspace and read the starter

From the course root:

```bash
./lab-start capstone --cold
cd .student/capstone
pwd
ls -l cold_runtime.py
cat cold_runtime.py
nano cold_runtime.py
```

Cold start resets an existing capstone attempt; export your notes first if you want to retain them. No guided solution is copied into this workspace. Edit only this prepared source. Ctrl+O then Enter saves in default nano; Ctrl+X exits.

<!-- source: course/capstone/lab/cold_runtime.py format=code -->
```python
#!/usr/bin/env python3
"""Runnable batch starter. Direct execution deliberately lacks outer controls."""
import json
from pathlib import Path
import subprocess
import sys

batch = json.loads(Path(sys.argv[1]).read_text())
rows = []
for job in batch["jobs"]:
    spec = job["runtime"]
    run = subprocess.run([spec["guard"], spec["allowed_root"], *spec["command"]],
                         text=True, capture_output=True, timeout=20)
    rows.append({"id": job["id"], "result": {
        "schema": 1, "status": run.returncode, "stdout": run.stdout,
        "stderr": run.stderr, "unit": None, "attestation": None,
    }})
Path(sys.argv[2]).write_text(json.dumps({"schema": 2, "jobs": rows}) + "\n")
raise SystemExit(any(row["result"]["status"] != 0 for row in rows))
```
<!-- /source -->

### Starter, line by line

- The imports provide JSON, paths, foreground execution, and process arguments.
- The starter parses a batch but does not validate its complete shape before acting.
- The loop visits jobs in input order and constructs guard/workload argv as separate values.
- Direct execution can apply the supplied inner guard but creates no outer unit, resource profile, or fresh namespace.
- Each row retains identity, stdout, stderr, and ordinary child status. Unit and attestation are explicitly missing.
- The final batch is written after the loop. Any nonzero ordinary child status produces nonzero overall status.

That is a functional baseline, not successful containment. Do not remove the guard or hide failed jobs to make the output look successful.

## Batch interface and validation

```text
python3 cold_runtime.py BATCH.json RESULT.json
```

Require exactly `schema: 2` and `jobs`. Schema is an integer, not a Boolean. Jobs is a list of one through eight objects, each with exactly a unique nonempty string `id` and a `runtime` object.

Each runtime has exactly `guard`, `allowed_root`, `command`, `memory_max`, `tasks_max`, and `cpu_percent`. Apply the full single-job contract from Module 10: absolute trusted regular guard, an absolute non-root directory, non-symlink guard/root leaves, structured literal argv whose executable resolves beneath that directory, memory 16 MiB through 1 GiB, tasks 4 through 256, and CPU 10 through 100 percent. Limits must be integers, not Booleans. Operator-controlled setup paths are an assumption, not a race-free same-account boundary.

Validate **the entire batch before any job launches**. A malformed later job must prevent the earlier valid job from running. Reject duplicate identities, empty/oversized lists, extra fields, wrong types, and invalid nested runtime specs without publishing a result or creating a unit.

## Execution, evidence, and lifecycle

Give each valid job a fresh owned unit with its own validated CPU/memory/task limits, zero swap, and finite runtime/stop bounds. Apply the practiced user/network namespaces, privilege floor, clean environment, filesystem/syscall guard, and literal argv handling. Useful work must still succeed.

In the prepared capstone workspace, register ownership with the course platform under target `capstone` and its exact description before launch. In the evaluator's separate temporary directory, retain standalone ownership records as practiced in 10.03; the evaluator's naming convention is `north-echo-UID-10-lab-RANDOM.service`. Adapt lifecycle context deliberately, rather than assuming every copied file is still inside the lesson directory.

Inspect ownership before mutating a remaining unit. A failed manager query is unknown, not absent. Collect on success, failure, and timeout; preserve ownership records if safe cleanup cannot be established. Never stop a unit based only on a matching prefix.

Return:

```json
{"schema": 2, "jobs": [{"id": "original-id", "result": {"schema": 1, "status": 0, "unit": "exact-owned-unit", "stdout": "...", "stderr": "", "attestation": null}}]}
```

This illustrates the shape, not fixed identity or expected output. Preserve rows in input order. Each nested result retains workload status, exact distinct unit, stdout, stderr, and a parsed final-line observation when present. A worker need not emit JSON; preserve its ordinary status/output with null attestation in that case.

Continue after an **ordinary nonzero worker exit** and return nonzero overall if any worker failed. Do not confuse that recoverable job outcome with malformed input, launch failure, timeout, or inability to prove cleanup. Infrastructure/collection failure must fail closed; do not publish a fabricated completed row and proceed as though collection succeeded.

## External checks and their limits

The evaluator checks the practiced kernel-visible properties under two resource profiles. A separate 0/7/0 batch checks ordered identities, continued execution, distinct units, effective per-job memory ceilings, and exact unit absence. Invalid batches include a valid first job followed by an invalid runtime; a harmless local marker at trusted guard entry checks that the earlier launch did not begin.

These checks use synthetic static workers and local brokers. They do not establish production readiness, all-channel credential confidentiality, private PID/mount views, exclusive pathname Unix-socket access on Landlock ABI 7, durable replay state, or hostile multi-user grader isolation. Module 10's explicit limitations still apply.

## Validation and reasoning rubric

```bash
python3 -m py_compile cold_runtime.py
../../lab-grade capstone
../../lab-grade capstone --mode exam
```

Syntax checking launches no workload. The capstone reports property outcomes without a step-by-step repair. If it fails, identify whether the defect is validation, composition, result preservation, or lifecycle. Use the earlier lesson that practiced that property; do not alter the evaluator.

Create `RATIONALE.md` in this workspace. Identify each control's removed authority, explain why useful work succeeds, map claims to actual observations, and state untested limits. Distinguish invalid input, ordinary job failure, and collection failure. Explain why a fresh unit is needed for each job and why a later invalid spec must block all work.

Use the human reasoning rubric in `docs/LEARNING_PATH.md`. Graduation requires both the automated assessment and an evidence-backed explanation; a solo review must be labeled self-assessed. An automated pass does not establish beginner comprehension.

## Cleanup and delayed replay

Preview `../../lab-cleanup capstone --dry-run`, then use `../../lab-cleanup capstone` for registered resources. If ownership cannot be established, stop and inspect the exact record; do not kill by name prefix or disable SELinux.

Save your rationale and any private work you want to keep, return with `cd ../..`, and use `./lab-reset capstone`. Reset intentionally discards the prepared solution and fixtures. Repeat cold after a delay, with the manual closed initially, and record which hints were needed. No real credentials, external targets, or production workloads belong here.
