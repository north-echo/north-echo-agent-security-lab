# Module 04 Linux acceptance record

- Source: checkpoint `08d1712` plus the working-tree changes that implement Module 04
- Environment: Ubuntu 24.04.4 LTS arm64, kernel 6.8.0-134-generic, ordinary `lima` user
- Scope: three guided lessons, independent lab, practice/exam grading, replay, reset, cleanup, tests, and course attestation

## Result

Module 04 passed its acceptance run.

- Lesson 04.01 produced the required deterministic ordered action trace; removing a trace operation reproduced the intended failure, and restoring it passed the checkpoint.
- Lesson 04.02 preserved structured argv, propagated tool failure status, and did not invoke a shell; the deliberate `shell=True` variant created the synthetic marker and altered argv as expected, and the repair passed.
- Lesson 04.03 showed that inherited environment variables are ambient authority; the unsafe run exposed a synthetic secret, while the repaired environment did not.
- The untouched lab starter failed in both practice and exam modes.
- A completed solution passed all 9 externally graded properties in both practice and exam modes.
- Replay generated a fresh fixture and removed the prior solution.
- Module reset dry-run named only owned paths. The real reset removed all Module 04 student work and fixtures while preserving pass metadata.
- No owned runtime resource remained. No real credential, external API, or external target was used.

Raw command transcripts are stored beside this file. Synthetic canaries/secrets and host-specific repository paths are redacted from the committed evidence.

## Known boundaries

The agent policy is a deterministic local teaching fixture, not an AI model. Module 04 intentionally demonstrates ambient authority before later modules add confinement. It does not claim pathname, syscall, resource, or network isolation; those controls are taught in Modules 05-09.

## Acceptance disposition

All Module 04 requirements in `docs/dev/MODULE_ACCEPTANCE_TEMPLATE.md` are satisfied. Tranche 1 remains incomplete until Modules 05 and 06 pass the same gate.
