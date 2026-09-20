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
