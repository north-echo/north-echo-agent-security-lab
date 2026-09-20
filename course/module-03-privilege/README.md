# Module 03 - Privilege, capabilities, and no_new_privs

You will inspect the actual privilege state carried by a process, remove capability channels, and set a one-way privilege floor before `execve`.

Play in order: `03.01`, `03.02`, `03.03`, then `module-03`.

## Learning route and limits

Prerequisites: Module 02. Continue as your ordinary account inside the disposable Linux VM. The guided lessons introduce their new syntax and interfaces before the independent lab combines them.

03.01 inventories identity and all five capability sets. 03.02 contrasts partial and complete changes, then practices current-set reduction in C. 03.03 installs and observes the inherited no_new_privs restriction.

Separate current authority from the possibility of gaining privilege when executing another file. Explain why a capability-empty process can still read its own files or use inherited descriptors. Do not make setuid binaries, install file capabilities, or run this lab as global root.

Before moving on, demonstrate both useful allowed work and the intended restriction, and explain the difference in your own words. A failed compiler command or missing input is not a security success. Use the independent lab's practice feedback to revisit a specific lesson; passing checks does not replace understanding or make the combined program production-ready.
