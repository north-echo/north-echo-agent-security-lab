# North Echo Agent Security Lab v1.0.2

North Echo v1.0.2 turns the recommended macOS setup into a pinned, disposable Lima appliance while preserving the Ubuntu 24.04 course baseline.

## Changes

- adds `deploy/north-echo.yaml` for a one-command Lima deployment on Apple Silicon or x86-64 macOS;
- pins dated Ubuntu 24.04 amd64 and arm64 cloud images by SHA-256;
- uses Lima plain mode with no host filesystem mount, dynamic port forwarding, built-in container runtime, guest agent, Rosetta, or SSH-agent forwarding;
- centralizes Ubuntu prerequisites in `deploy/ubuntu-packages.txt`, consumed by both GitHub Actions and the appliance;
- makes provisioning idempotent so ordinary VM restarts cannot reinstall over student work;
- enables lingering for the actual ordinary guest user and proves its delegated systemd user manager before declaring the appliance ready;
- downloads the tagged course archive, verifies its matching `SHA256SUMS` entry, and refuses to overwrite an incomplete existing installation;
- runs the complete tests, attestation, Linux preflight, strict Landlock compilation, and empty-runtime check during first boot;
- exports a synthetic deployment-evidence archive through `limactl copy` without adding a host mount;
- gates readiness through a probe that fails the start when validation is incomplete.

## Validation

The template was validated with Lima 2.2.0 on Apple Silicon using Apple's Virtualization framework and the pinned Ubuntu 24.04.5 arm64 image. The acceptance run covered first boot, 42 Linux tests, all 28 required preflight checks, attestation, strict Landlock compilation, correct-user lingering, empty managed runtime state, restart preservation, plain-mode evidence copy-out, and a deliberately failing probe. GitHub Actions independently passed the expanded 44-test suite on Ubuntu 24.04 x86-64 and arm64.

## Safety scope

The appliance contains only the public course and synthetic local evidence. It mounts no host directory, forwards no SSH agent, uses no production credential or external target, and is reset by deleting and recreating the VM.
