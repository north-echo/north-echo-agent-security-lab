# Module 05 - Confine filesystem access

Turn a directory name into an enforced filesystem boundary. First break lexical path checks with traversal and symlinks. Then anchor lookup to a directory descriptor with `openat2(2)` and add Landlock so an entire child process is restricted. Finally confront Landlock's important pre-opened-file-descriptor limit.

Play in order: `05.01`, `05.02`, `05.03`, then `module-05`.

Outcomes:

- distinguish a pathname string from the kernel object reached during lookup;
- reproduce traversal, prefix-collision, and symlink escapes against a naive broker;
- use `openat2` with `RESOLVE_BENEATH`, `RESOLVE_NO_MAGICLINKS`, and `RESOLVE_NO_SYMLINKS` for descriptor-relative lookup;
- query the Landlock ABI, select supported rights, add a path-beneath rule, set `no_new_privs`, and restrict a child before `exec`;
- demonstrate that Landlock does not revoke already-open descriptors and remove that inherited authority before launch.

Prerequisites: Modules 01-04, Linux, a C compiler, Linux UAPI headers containing `openat2.h` and `landlock.h`, and a kernel with `openat2` and Landlock. The lessons require no root privilege, mount, network access, or host policy change.

Cross-layer boundary: `openat2` protects individual brokered lookups. Landlock restricts future filesystem operations by the launched process. Neither one closes an already-open descriptor; descriptor hygiene from Module 01 remains necessary.

## Learning route and limits

Prerequisites: Modules 01-04. Continue as your ordinary account inside the disposable Linux VM. The guided lessons introduce their new syntax and interfaces before the independent lab combines them.

05.01 distinguishes path spelling, component ancestry, and lookup results. 05.02 practices descriptor-relative reads and writes. 05.03 restricts a launched child and revisits authority already held in descriptors.

Keep two questions separate: did the broker resolve this request safely, and is the entire child restricted when it opens files itself? The first is an openat2 question; the second is a Landlock question. Record the running ABI and build headers rather than relying on the distro name.

Before moving on, demonstrate both useful allowed work and the intended restriction, and explain the difference in your own words. A failed compiler command or missing input is not a security success. Use the independent lab's practice feedback to revisit a specific lesson; passing checks does not replace understanding or make the combined program production-ready.
