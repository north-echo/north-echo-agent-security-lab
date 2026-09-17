# Module 07 cgroup cleanup foundation

The safety foundation was exercised on the Ubuntu 24.04.4 LTS arm64 disposable VM before Module 07 lesson authoring began.

- A target-scoped transient user service was registered before launch.
- The live service carried the exact workspace-bound description.
- Its effective cgroup was beneath `user-501.slice/user@501.service/app.slice`.
- Effective `MemoryMax=67108864` and `TasksMax=16` values were observed through systemd and cgroup v2.
- Cleanup dry-run validated the same ownership state without mutation.
- Real cleanup stopped only the registered service, confirmed it inactive, confirmed its cgroup was removed, and then removed the runtime registry.
- Target reset removed the disposable workspace and fixture.

Automated tests reject unrelated or ambiguous unit names, forged descriptions, and cgroups outside the delegated user manager. Direct cgroup-path registry entries fail closed; the owning transient unit is the cleanup authority.

This record covers the cleanup foundation only. It does not mark Module 07 playable or satisfy the module acceptance gate.
