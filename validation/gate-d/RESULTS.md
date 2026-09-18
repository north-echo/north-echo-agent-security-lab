# Gate D / v1.0 acceptance record

Status: **PASS** on Ubuntu 24.04.4 LTS arm64 with Linux 6.8.0-134-generic. Date: 2026-09-17.

- [x] `./lab-start capstone --cold` creates a fresh unlabeled workspace with objective, starter, fixture metadata, and no guided solution.
- [x] External grading rotates synthetic data independently and checks the complete runtime's resources, namespaces, capabilities, Landlock, seccomp, brokered operation, credential absence, literal argv, failure propagation, validation, and teardown.
- [x] Starter fails meaningful properties; the known-good implementation passes practice and exam modes.
- [x] Capstone reset removes workspace and fixtures, preserves only progress metadata, and a new start rotates fixture identity.
- [x] Modules 01-12 remain playable; full automated suite, course attestation, Linux preflight, and final empty-state inspection pass.
- [x] Complete Markdown manual and visually inspected 229-page PDF manual are present.
- [x] Release notes and reproducible archive/bundle/checksum workflow are present; final artifacts are generated from tag `v1.0.0`.

No real credential, external target, retained student solution, or persistent owned runtime resource was used. The capstone reuses the independently validated complete-runtime properties and makes no hostile multi-user anti-cheat claim.
