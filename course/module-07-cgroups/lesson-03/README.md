# 07.03 - Bound process-tree growth and collect it

## Goal

Apply a PID ceiling to a process tree, observe a rejected fork, and prove collection removes the transient cgroup.

`fork_pressure.py` resolves its own cgroup, attempts a bounded number of forks, makes each child sleep briefly, reaps every created child, and prints `pids.max` plus `pids.events`. Children use `_exit` so they do not rerun parent cleanup.

```bash
systemd-run --user --wait --pipe --collect --quiet \
  --property=TasksMax=12 -- python3 "$PWD/fork_pressure.py" 64
systemctl --user list-units --all 'run-*.service'
```

### Line by line

- `TasksMax=12` writes `12` to `pids.max` for the whole service tree, including the parent.
- The loop asks for at most 64 children; `fork` fails before that when the cgroup reaches its ceiling.
- Reaping prevents zombies from obscuring the count.
- `pids.events` contains a positive `max` counter after a rejected creation.
- The listing should not contain the collected transient unit. Collection, not killing only one PID, is the cleanup property.

Intentional failure: omit `TasksMax`; all 64 bounded children can be created and `pids.max` is `max`. Restore the ceiling and require fewer than 64 children plus a positive `max` event.

## Checkpoint and troubleshooting

```bash
systemd-run --user --wait --pipe --collect --quiet --property=TasksMax=12 -- python3 "$PWD/fork_pressure.py" 64 | grep -q '"pids_max": "12"'
```

- Never substitute an unbounded fork loop. The fixed upper bound and short sleep make failure recoverable.
- A PID controller bounds task creation; it does not limit CPU or memory, so compose all required controllers.
