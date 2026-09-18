# Module 12 acceptance record

Status: **PASS** on Ubuntu 24.04.4 LTS arm64 with Linux 6.8.0-134-generic. Date: 2026-09-17. Source branch based on `4234b45`; final commit contains this record.

- [x] Three guided lessons cover scripted baseline, bounded adaptation, calibrated interpretation, and candidate packaging with complete local sources and failure/repair checkpoints.
- [x] Independent lab exposes only the spec/result contract; starter inventories but fails discovery.
- [x] External grader rotates five weakness classes and a no-weakness scenario.
- [x] Reference discovers every weakness within two allowlisted exact-argv actions, preserves identity, emits a complete deterministic trace, and calibrates non-discovery.
- [x] Practice/exam grading, reset, replay, cleanup, field manual, and course manifest pass.
- [x] Full Linux suite passes 40/40; course attestation and 28/28 preflight pass.

Only a synthetic local oracle was used. No network connection, real credential, external target, service, or persistent resource was created. Non-discovery is explicitly not treated as proof of security.
