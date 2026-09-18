# North Echo Agent Security Lab v1.0.1

North Echo v1.0.1 sharpens the course's runtime-containment scope, adds continuous Ubuntu 24.04 validation on x86-64 and arm64, and corrects the Module 05 Landlock ABI treatment.

## Changes

- reframes the README around runtime containment for agent workloads and explicitly distinguishes model-side security;
- discloses the AI-assisted authorship and human-directed Linux validation process;
- adds an x86-64 and arm64 GitHub Actions matrix;
- handles every filesystem right known at build time and supported by the detected Landlock ABI, including device IOCTL at ABI 5 and pathname UNIX-socket resolution at ABI 9 when the build headers expose them;
- explains that rights omitted from `handled_access_fs` remain allowed and states the best-effort, build-time-known compatibility boundary;
- moves development-process material under `docs/dev/` and replaces the build roadmap with a concise release history and post-v1.0.1 plan;
- keeps the Markdown field manual in the source tree while publishing the generated PDF as a release asset;
- makes the release builder version-aware and generates the PDF directly from the tagged Markdown source.

## Validation

The release gate requires the complete automated suite, course attestation, Linux preflight, Module 05 compilation and lesson replay, empty managed runtime state, both GitHub Actions architecture legs, and visual inspection of the regenerated PDF.

## Safety scope

All exercises use synthetic local data and disposable Linux environments. No LLM or network service is required during the exercises, and no production credential or external target is used.
