# Module 05 - Filesystem confinement, path resolution, and Landlock (scaffold)

Planned outcome: break string-prefix path validation with traversal and symlinks, move to descriptor-relative resolution and `openat2`, then apply Landlock while testing the pre-opened-descriptor limit.

Independent lab properties will cover allowed reads/writes, traversal, symlink escape, descriptor inheritance, child confinement, and cleanup with randomized protected paths.
