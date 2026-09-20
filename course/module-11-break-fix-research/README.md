# Module 11 - Compare and repair a small containment model

Complete Modules 01-10 first. Work through `11.01`, `11.02`, `11.03`, then `module-11`.

The earlier modules attempted operations under Linux controls. This chapter changes scale: you inspect a deliberately small, fixed local model to practice evidence classification, complete repair, preservation, and replay. It is not an external vulnerability-discovery exercise and does not reproduce arbitrary vulnerabilities.

By the end you should be able to:

- distinguish configuration choices, actual local effects, modeled decisions, and unobserved properties;
- generate and replay a seeded combination without treating its name as a diagnosis;
- classify every supplied observation and reject missing evidence;
- repair all known model choices while preserving the allowed operation and opaque identity;
- test idempotence and explain what a successful model comparison does **not** establish.

The harness uses a constant shell marker fixture, one explicitly fake variable, generated sibling files, an unconnected socket, and string-only cleanup candidates. It never interprets arbitrary plan text, contacts a target, or deletes a cleanup candidate. The broker-only branch skips socket creation; it does not install kernel confinement. The resolved-path branch is not race-free, and cleanup selection is not real resource collection. Keep those limitations beside every conclusion.

Estimated work: three guided sessions plus an independent repair lab. Save short evidence notes as you go; a passing JSON comparison is not a substitute for explaining the observation.
