# Roadmap

## Completed

- v0.1 - platform lifecycle, Modules 01-03, Gate A (arm64). Record: `validation/RESULTS.md`
- v0.2 - Modules 04-06. Record: `validation/tranche-01/RESULTS.md`
- v0.3 - Modules 07-09. Record: `validation/tranche-02/RESULTS.md`
- v0.4 - Modules 10-12. Record: `validation/tranche-03/RESULTS.md`
- v1.0 - cold capstone, field manual, release workflow, Gate D. Record: `validation/gate-d/RESULTS.md`
- v1.0.1 - runtime-containment framing, continuous x86-64 and arm64 CI, release hygiene, and Landlock filesystem-right coverage through ABI 9 when exposed by build headers
- v1.0.2 - pinned plain-mode Lima appliance, idempotent provisioning, shared CI prerequisites, checksum-verified course installation, readiness probing, and SSH-based evidence export

## Post-1.0.2

- Debian 12 baseline run on x86-64 with a recorded validation entry.
- Module 12 depth: attestation-driven probe selection and true-negative versus false-negative comparison. See `docs/dev/SPEC_v1.0.1.md` section 5.
- Landlock ABI 4 network rules as an optional Module 08 exercise on kernels supporting that ABI.
