# B1 - Useful work with less inherited data

The delivery team wants a tool to read a report. The program that starts it
also holds a fake private setting the reader does not need. Your job is to
control that handoff while keeping the reader useful.

By the end, you should be able to predict which environment settings a child
receives, construct a small allowlist, test required and prohibited behavior,
and state what that repair does **not** isolate.

Prerequisites: locate and quote paths, edit a short Python file, distinguish
program/process, and interpret exit status. Use B0 if any are unfamiliar.
New ideas are introduced here: process environment, parent-to-child handoff,
allowlisting, and positive/negative tests. No namespaces, capabilities, C,
kernel tracing, network service, model, or API key is required.

Three guided lessons build toward one independent practical. The third gives
less help: use the earlier explanation on a changed case before asking for a
hint. The independent lab supplies requirements, not repair instructions.

**Scope:** this is environment hygiene, not a sandbox. The child still runs as
your VM user and can use that user's filesystem and other available resources.
We are not demonstrating that hostile code is contained. Use only the supplied
local workers and synthetic data inside the disposable VM.

Sequence: `b1.01`, `b1.02`, `b1.03`, then `module-b1`.
Pause after the practical to explain the boundary and record any missing steps.
If you can predict the changed case and explain the remaining authority, continue
to Module 01. This beta still needs learner review; a grade alone is not mastery.
