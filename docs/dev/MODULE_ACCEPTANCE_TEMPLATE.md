# Playable module acceptance template

Copy this checklist into the validation record for every new module. A scaffold becomes **playable** only when every applicable box is supported by repository evidence and a Linux run.

## Learning design

- [ ] The module states observable learning outcomes and prerequisites.
- [ ] It contains at least three substantive guided lessons and one independent lab.
- [ ] Each independent-lab property uses only commands, APIs, and reasoning practiced in the guided lessons.
- [ ] The module introduces one conceptual layer at a time and names cross-layer assumptions.
- [ ] AI is optional and is not required to start, solve, or grade the work.

## Guided lessons

- [ ] Every action block has exact commands or a complete, small source listing.
- [ ] Every meaningful line, flag, operator, variable, and security-sensitive call is explained immediately after the block.
- [ ] Expected output is described as a stable pattern, with variable fields identified.
- [ ] The explanation states what the observation proves and what it does not prove.
- [ ] Every lesson includes an intentional mistake, bypass, or incomplete control.
- [ ] The learner repairs the failure using an interface already introduced.
- [ ] A checkpoint verifies effective kernel or runtime state.
- [ ] Troubleshooting covers realistic failures without recommending unsafe host changes.

## Independent lab and grading

- [ ] The lab states its functional contract, input/output interface, and security properties without giving a complete solution.
- [ ] The starter implementation is useful enough to run but fails meaningful security properties.
- [ ] Start fixtures randomize synthetic names, paths, ports, IDs, and canaries where relevant.
- [ ] Every grading run creates fresh evaluation details independent of the start fixture.
- [ ] The grader observes behavior or effective state rather than matching source text.
- [ ] The grader covers functional success, intended denials, and at least one bypass variant.
- [ ] Security properties that cannot be observed reliably by the external grader on the supported baseline are explicitly identified, justified, and validated through source review or a targeted higher-kernel run.
- [ ] Practice output names failed properties and relevant lesson references.
- [ ] Exam output names failed properties but suppresses repair-oriented hints.
- [ ] Attempt count, last result, mode, and pass state persist; student source and generated secrets do not.

## Lifecycle and safety

- [ ] `lab-start`, resume, `lab-status`, and `lab-grade` work for the new targets.
- [ ] Lesson, module, and `--all` reset scopes remove all disposable artifacts for the new targets.
- [ ] Reset followed by start rotates fixture details while preserving the learning objective.
- [ ] Every process, mount, cgroup, namespace helper, service, network object, and temporary path that can outlive a foreground command is registered.
- [ ] Cleanup validates exact ownership and containment before mutation and fails closed on ambiguity.
- [ ] `--dry-run` follows the same validation path and accurately describes the intended cleanup.
- [ ] Adversarial tests prove the cleanup code rejects external paths, unrelated PIDs, and unowned host resources.
- [ ] No exercise needs a real credential, external target, host firewall change, or broad privilege.

## Documentation

- [ ] The canonical lesson README files are complete.
- [ ] The field-manual chapter contains the complete guided commands and source, line-by-line teaching, expected observations, security meaning, failure/repair, troubleshooting, checkpoints, and independent-lab contract.
- [ ] The manual and canonical files agree on names, paths, commands, flags, expected behavior, and prerequisites.
- [ ] Optional references are clearly optional and do not carry required teaching.
- [ ] Setup, status output, and the prerequisites matrix name any new package, kernel feature, or privilege requirement.

## Verification evidence

- [ ] Automated platform tests cover target discovery, replay, reset scopes, status, state retention, and failure behavior.
- [ ] Grader tests cover the starter failure, an acceptable implementation, and relevant bypasses.
- [ ] Course attestation passes after an intentional review of the manifest diff.
- [ ] Guided lessons and the independent lab were run on a supported disposable Linux VM.
- [ ] Distribution, kernel, architecture, package versions, commands, outcomes, and skips are recorded.
- [ ] Cleanup leaves no owned process, mount, cgroup, service, network object, or temporary artifact behind.
- [ ] The validation record contains no real secret, unrelated host data, or retained student solution.

## Release decision

- [ ] All applicable checks above pass.
- [ ] Known limitations are precise and do not invalidate a learning objective or safety property.
- [ ] `README.md`, `ROADMAP.md`, `docs/dev/HANDOFF.md`, and the field manual reflect the same completion state.
- [ ] The module status changes from **Scaffold** to **Playable** only now.
