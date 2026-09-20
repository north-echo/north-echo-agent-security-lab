# Module 02 - Linux namespaces

Namespaces change which kernel objects a process sees. They do not automatically remove capabilities, filter syscalls, limit resources, or make a complete sandbox.

Play in order: `02.01`, `02.02`, `02.03`, then `module-02`.

## Learning route and limits

Prerequisites: Module 01. Continue as your ordinary account inside the disposable Linux VM. The guided lessons introduce their new syntax and interfaces before the independent lab combines them.

02.01 introduces namespace handles and identity maps. 02.02 changes a child hostname while preserving the parent's and practices argument forwarding through a shell. 02.03 shows why changing PID numbering without replacing procfs creates contradictory observations.

Ask which namespace of which type, not merely whether a process is in a container. Explain why inside UID 0 is not global root, why PID 1 is namespace-relative, and why a fresh PID namespace needs a matching procfs view. Here the parent environment is the VM, not the Mac.

Before moving on, demonstrate both useful allowed work and the intended restriction, and explain the difference in your own words. A failed compiler command or missing input is not a security success. Use the independent lab's practice feedback to revisit a specific lesson; passing checks does not replace understanding or make the combined program production-ready.
