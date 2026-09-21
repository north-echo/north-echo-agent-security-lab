# Licensing

Copyright (c) 2026 North Echo contributors.

North Echo Agent Security Lab uses separate licenses for software and teaching
materials. This is a scope map, not a choice between two licenses for every file.
It applies to North Echo-owned material in this working tree from the licensing
transition after v2.0.0-beta.2, subject to the prior-permission and third-party
exceptions below. The actual license texts control.

## Software: Apache-2.0

Except where a specific notice says otherwise, the platform, graders, tests,
scripts, command-line entry points, deployment/build configuration, example
programs, starter code and machine-readable fixtures are licensed under the
Apache License, Version 2.0.

This includes software under `scripts/`, `graders/`, `tests/`, `deploy/`,
`.github/` and `course/`, and root-level `lab-*` commands. It also covers
software not explicitly listed here. The full license is in [LICENSE](LICENSE)
and at [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0).

### Embedded-code exception

North Echo-authored code examples, shell commands, configuration examples and
source listings embedded in Markdown, manuals or other teaching documents are
offered under Apache-2.0, separately from the surrounding prose. You may extract,
modify and redistribute those examples under Apache-2.0 without applying
CC BY-SA to your own software. Preserve applicable notices, including the
retained MIT notice for previously MIT-licensed material.

A fenced block is not automatically software: explanatory prose, quotations,
terminal output and tables retain their applicable content or third-party
terms. Third-party examples retain any specific license notices.

## Teaching materials: CC BY-SA 4.0

Except for the software exception and specifically identified exclusions,
North Echo-authored lesson prose, exercise instructions, diagrams, illustrations
and documentation are licensed under Creative Commons Attribution-ShareAlike
4.0 International (CC BY-SA 4.0). This includes prose in `course/`, `docs/`,
root-level Markdown documents and README files elsewhere, plus generated
Markdown and PDF manuals.

The full license is in [LICENSES/CC-BY-SA-4.0.txt](LICENSES/CC-BY-SA-4.0.txt).
The [CC BY-SA 4.0 summary](https://creativecommons.org/licenses/by-sa/4.0/)
explains attribution, indicating modifications, and licensing shared adaptations
under the same or an officially compatible license. Commercial teaching and
redistribution are allowed. Private adaptations need not be published; sharing
an adaptation invokes the applicable ShareAlike terms.

Suggested attribution, supplemented with a description of your changes:

> North Echo Agent Security Lab, North Echo contributors.
> https://github.com/north-echo/north-echo-agent-security-lab
> Teaching materials: CC BY-SA 4.0, https://creativecommons.org/licenses/by-sa/4.0/.
> Code examples: Apache-2.0. See the accompanying licensing notices.

Preserve supplied attribution and notices; do not imply endorsement of your
adaptation. A collection containing independent works does not automatically
place every work under CC BY-SA.

## Previously published MIT material

The repository through commit
`b26a9a1cd7c99a2dbd2c50710579f4be3d09c22d`, including v2.0.0-beta.2 and earlier
releases, was published under MIT. Those tags and release artifacts remain
unchanged. The original notice and complete permission text are preserved in
[LICENSES/MIT.txt](LICENSES/MIT.txt).

This transition does not revoke MIT permissions for previously published
material, including when that material remains in this tree. You may continue
to use that material under MIT. New contributions after the transition are
offered under the applicable software or teaching-material license above,
unless explicitly marked otherwise. The MIT notice retained for historical
material does not make all future contributions MIT-licensed.

Historical records already present under `validation/` and `release/` are
retained under their existing MIT terms, not retroactively relicensed. New
North Echo-authored prose there follows the teaching-material default; new
software follows the software default.

## Third-party material, names and rights

Specific third-party notices take precedence for their material. Dependencies,
operating-system images, linked documentation, quoted excerpts and third-party
marks are not relicensed by this repository. License texts themselves retain
their publishers' terms.

The RH124/RH134 guides were teaching-structure references, not licensed source
material for redistribution. This policy grants no rights to Red Hat course
content and does not authorize copying it into North Echo. Any proposed
third-party inclusion needs a compatible permission basis and retained notices.

These licenses do not grant trademark rights or permission to imply endorsement.
This project is independent, not an official Red Hat, Fedora, OpenAI or Anthropic
course. Copyright licenses apply only to rights the relevant contributor can
grant; repository history and automated checks are not a legal provenance audit.

## Distribution and contributions

Keep `LICENSE`, `NOTICE`, `LICENSING.md` and `LICENSES/` with source
distributions. The manual builder embeds the scope explanation, notices and
license texts so a separately distributed manual keeps its licensing context.
For extracted examples, retain the applicable license and attribution notices.

See [CONTRIBUTING.md](CONTRIBUTING.md) before submitting changes. No published
release is silently relabeled; the next release must describe this transition.
