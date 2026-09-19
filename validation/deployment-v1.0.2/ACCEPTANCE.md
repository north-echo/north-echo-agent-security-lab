# v1.0.2 Lima deployment acceptance plan

Run this gate from macOS with Lima 2.2 or newer. The instance must be disposable and must not receive a host filesystem mount, forwarded SSH agent, real credential, or external target.

## Pinned inputs

- Ubuntu release directory: `noble/release-20260911`
- amd64 image SHA-256: `612b2c0cc1bc413a6cb8c38fd611794caf0f2b436c50013d8b3794db12ad7354`
- arm64 image SHA-256: `7b682958a67ff5de068e36de6af8b75fa645d296af5a70d6500527f6a33781db`
- Default course release: `v1.0.2`
- VM sizing: 4 CPUs, 6 GiB memory, 30 GiB disk

## Required evidence

1. `limactl validate deploy/north-echo.yaml` passes.
2. A fresh plain-mode instance reaches ready state on the pinned image.
3. The first boot passes all automated tests, course attestation, Linux preflight, the strict Module 05 compilation, and the empty-runtime check.
4. `loginctl show-user "$(id -un)" -p Linger` reports `Linger=yes`, `systemctl --user show-environment` succeeds, and `systemd-run --user --wait --pipe --collect --quiet -- true` succeeds for the ordinary Lima user.
5. Stop/start leaves the readiness marker unchanged and does not replace a synthetic file created under `~/north-echo/.student/`.
6. `limactl copy north-echo:~/north-echo-deployment-evidence.tgz .` succeeds while `plain: true` is active, and the copied archive contains only the expected synthetic validation logs and compile output.
7. A temporary copy of the template with a readiness probe that always exits nonzero causes `limactl start` to return nonzero. Delete that deliberately failed instance afterward.
8. `limactl delete -f north-echo` removes the disposable instance.

Record the tested commit, Lima version, macOS version and architecture, Ubuntu distribution/kernel/architecture, selected image URL and digest, package versions, commands, outcomes, skips, and confirmation that no real credential or host mount was used in `RESULTS.md` beside this plan.
