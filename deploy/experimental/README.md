# Fedora compatibility trial

This is the historical, ARM64-only developer trial, not a tagged-course
installer. For the v2 learner-review beta, use `deploy/north-echo-fedora.yaml`
and `docs/VM_SETUP.md`; Ubuntu remains a compatibility deployment.
See [the trial record](../../validation/fedora-trial-20260919/RESULTS.md)
for the exact candidate and coverage.

From the repository root on an Apple Silicon host with Lima 2.2 or newer:

```bash
limactl validate deploy/experimental/fedora-trial.yaml
limactl start --name north-echo-fedora-trial deploy/experimental/fedora-trial.yaml
limactl shell north-echo-fedora-trial
```

The VM has 4 CPUs, 6 GiB RAM, and a 30 GiB disk. The Fedora 44 Cloud image URL
and SHA-256 come from Lima 2.2.0's bundled `_images/fedora-44.yaml`. No host
directories are mounted, SSH-agent forwarding is disabled, and plain mode
disables the guest agent and dynamic port forwarding. SELinux must remain
enforcing. Do not apply the Ubuntu AppArmor workaround to Fedora.

`fedora-packages.txt` supplies Fedora package names, including explicit static
C and seccomp libraries. The image is pinned; packages resolved by `dnf` are
**not** pinned. Record installed RPM revisions for every acceptance run.
The root-owned package marker skips repeat installation on ordinary restarts;
it is not a course-validation marker. Recreate the trial to test a changed
package manifest. Linger is enabled for the actual non-root Lima user.

The readiness probe checks only package provisioning, SELinux state, and the
user manager. It does not fetch a release or claim the course passed. Transfer
an explicitly reviewed candidate archive using `limactl copy`, verify its
checksum in the guest, and extract into a new directory under the guest's home.
Do not keep the course or student work under `/tmp`: the tested Fedora image
mounts it as tmpfs, and its contents disappear on reboot. Never include host
credentials, `.git`, existing student work, or runtime state. Include the
repository's `.north-echo-root` marker and create empty `.student`, `.fixtures`,
`.runtime`, and `.state` directories in the extracted candidate.

From that candidate's root inside the VM:

```bash
./scripts/linux-preflight
python3 scripts/run_tests.py --require-no-skips
./scripts/attest-course
python3 scripts/build_field_manual.py --check
```

Only use synthetic local exercises. Follow `docs/LINUX_VALIDATION.md` for the
remaining gates; automated tests alone do not establish a complete platform
port or learning effectiveness. Stop this separate VM when finished:

```bash
limactl stop north-echo-fedora-trial
```

The initial trial required platform-specific documentation, a release installer,
and repeatable kernel validation before a Fedora-first beta. Those steps are
tracked by `docs/dev/V2_REWRITE.md`; human learner review remains open.
An enforcing SELinux system does not by itself mean
that the student's processes run in a confined SELinux domain.

Primary references: [Lima templates](https://lima-vm.io/docs/templates/),
[Fedora glibc-static](https://packages.fedoraproject.org/pkgs/glibc/glibc-static/),
and [Fedora libseccomp-static](https://packages.fedoraproject.org/pkgs/libseccomp/libseccomp-static/).
