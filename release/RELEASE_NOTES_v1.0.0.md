# North Echo Agent Security Lab v1.0.0

North Echo v1.0.0 completes the twelve-module Linux containment course and enables the cold-start graduation capstone.

## Included

- 36 guided lessons and 12 independent module labs;
- cold capstone with fresh randomized fixtures and an external multi-layer grader;
- process authority, namespaces, capabilities, Landlock, seccomp, cgroups, network mediation, credential capabilities, complete-runtime composition, break/fix research, and bounded adaptive investigation;
- practice/exam grading, integrity attestation, randomized replay, safe reset/cleanup, and metadata-only progress;
- complete Markdown and visually verified 229-page PDF field manuals;
- Ubuntu 24.04.4 LTS arm64 validation records for every module and tranche.

## Validation baseline

Linux 6.8.0-134-generic on aarch64, Python 3.12.3, GCC 13.3.0, libseccomp 2.5.5, systemd 255, and util-linux 2.39.3. The release gate requires the full automated suite, course attestation, Linux preflight, cold capstone practice/exam grading, replay rotation, and empty final runtime state.

## Safety scope

All exercises use synthetic local data, fake credentials, local processes, isolated namespaces, loopback or filesystem Unix sockets, and disposable VM resources. The release contains no production credential, external target, employer material, exploit automation, or hostile multi-user isolation claim.

## Artifacts

The release workflow produces a source archive, Git history bundle, complete Markdown manual, PDF manual, and `SHA256SUMS`. Checksums are generated after the annotated `v1.0.0` tag is created.
