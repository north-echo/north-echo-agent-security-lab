# Module 06 - Constrain syscalls with seccomp

Measure a real workload before writing policy, observe the operational difference between errno and kill actions, then launch a static child under a native-architecture default-deny libseccomp filter.

Play in order: `06.01`, `06.02`, `06.03`, then `module-06`.

Outcomes:

- collect and interpret a syscall profile without treating one trace as universal truth;
- compare `SCMP_ACT_ERRNO` and `SCMP_ACT_KILL_PROCESS` using an observable denied call;
- reproduce an alternate-interface bypass against a narrow blacklist;
- construct a native-architecture default-deny filter and prove it is active before `exec`;
- preserve a stated workload while denying socket, socket-pair, ptrace, and an unlisted syscall;
- explain why syscall filtering is not pathname authorization, resource accounting, or network destination policy.

Prerequisites: Modules 01-05, Linux, `strace`, a C compiler with static libc development files, and libseccomp headers/library discoverable through `pkg-config`. All probes are local and unprivileged.

## Learning route and limits

Prerequisites: Modules 01-05. Continue as your ordinary account inside the disposable Linux VM. The guided lessons introduce their new syntax and interfaces before the independent lab combines them.

06.01 establishes a functional baseline and the limits of one trace. 06.02 compares failure actions and an incomplete one-call rule. 06.03 constructs a native default-deny policy, then checks useful work and denied calls.

A small list is not automatically sound: it can omit required startup work or allow unnecessary operations. Explain why Seccomp: 2 proves less than a correct rule set. The independent lab deliberately uses a tiny static workload and errno-based denial; it does not promise arbitrary-program compatibility.

Before moving on, demonstrate both useful allowed work and the intended restriction, and explain the difference in your own words. A failed compiler command or missing input is not a security success. Use the independent lab's practice feedback to revisit a specific lesson; passing checks does not replace understanding or make the combined program production-ready.
