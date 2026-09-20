# Module 04 - Build a minimal tool-using agent

Build a small deterministic agent loop with `read_file`, `write_file`, and argv-based command execution over synthetic tasks. Begin deliberately over-authorized, inventory inherited authority, then define and verify a narrow tool contract.

No AI service, network call, or API credential is used. A checked-in JSON task acts as the local scripted policy so every decision is reproducible and inspectable.

Play in order: `04.01`, `04.02`, `04.03`, then `module-04`.

Outcomes:

- execute a deterministic sequence of named tools and emit one complete JSON record per action;
- preserve argv boundaries without shell reparsing and record nonzero tool results;
- inventory the launcher's environment, descriptors, and working directory without logging secret values;
- remove synthetic ambient environment authority before launching a child;
- distinguish an action request, an execution result, and evidence that the result actually occurred.

## Learning route and limits

Prerequisites: B0/B1 and Modules 01-03. Continue as your ordinary account inside the disposable Linux VM. The guided lessons introduce their new syntax and interfaces before the independent lab combines them.

04.01 connects each requested action to a result and an independently observed effect, including aggregate failure status. 04.02 preserves argument boundaries and distinguishes child status from runner status. 04.03 applies environment hygiene at the child boundary.

A JSON request, a runner's trace, and an independently observed effect are three different forms of evidence. JSON syntax does not authorize an action. This module is not a production schema validator, path sandbox, resource manager, durable audit store, or model safety policy.

Before moving on, demonstrate both useful allowed work and the intended restriction, and explain the difference in your own words. A failed compiler command or missing input is not a security success. Use the independent lab's practice feedback to revisit a specific lesson; passing checks does not replace understanding or make the combined program production-ready.
