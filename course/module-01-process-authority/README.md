# Module 01 - Processes, syscalls, and inherited authority

You will trace a command from process creation to kernel-visible effects, then remove two authorities that commonly cross `execve(2)` by accident: environment data and open file descriptors.

Play in order: `01.01`, `01.02`, `01.03`, then `module-01`.

## Learning route and limits

Prerequisites: B0 and B1. Continue as your ordinary account inside the disposable Linux VM. The guided lessons introduce their new syntax and interfaces before the independent lab combines them.

01.01 connects source, executable, process, and syscall. 01.02 traces an environment value and practices a constructed C environment. 01.03 traces an already-open reference and practices closing unknown extra descriptors.

Replacing program code does not automatically discard its environment or open descriptors. Explain the difference between a filename and a descriptor, and between fork and exec. Neither environment hygiene nor descriptor closure restricts every future file open.

Before moving on, demonstrate both useful allowed work and the intended restriction, and explain the difference in your own words. A failed compiler command or missing input is not a security success. Use the independent lab's practice feedback to revisit a specific lesson; passing checks does not replace understanding or make the combined program production-ready.
