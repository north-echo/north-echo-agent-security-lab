# Module 11 - Vulnerable variants and break/fix research

Analyze seeded runtime weaknesses without being told which control changed. Use a deterministic non-agent harness to reproduce effects, map observations to failed invariants, repair the plan, and compare it with a hardened counterpart.

Play in order: `11.01`, `11.02`, `11.03`, then `module-11`.

Outcomes:

- distinguish a configuration difference from evidence of security impact;
- reproduce ambient credentials, shell interpretation, symlink escape, direct IP authority, and unsafe cleanup selection using synthetic local objects;
- map observed effects to stable cross-layer invariants rather than variant labels;
- repair multiple simultaneous weaknesses while preserving the allowed operation and opaque run identity;
- prove a repair is idempotent and survives fresh randomized variants.

The harness never exploits an external target and never deletes its cleanup candidates. Every credential, path, marker, resource, and socket is synthetic and confined to the disposable workspace. Prerequisites are Modules 01, 04, 05, 08, 09, and 10.
