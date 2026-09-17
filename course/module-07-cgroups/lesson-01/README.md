# 07.01 - Observe an effective CPU quota

## Goal

Launch a bounded transient user service, find its actual cgroup from inside the workload, and distinguish a configured percentage from the kernel's quota/period representation.

Complete `inspect_cpu.py` reads `0::PATH` from `/proc/self/cgroup`, anchors that path below `/sys/fs/cgroup`, samples `cpu.stat`, burns CPU for one second, and emits JSON. `time.monotonic()` makes elapsed time independent of wall-clock changes; the loop counter is comparative evidence, not a portable benchmark.

```bash
python3 inspect_cpu.py
systemd-run --user --wait --pipe --collect --quiet \
  --property=CPUQuota=50% -- python3 "$PWD/inspect_cpu.py"
```

### Line by line

- The first run shows the shell's inherited cgroup and commonly reports `cpu.max` as `max 100000`.
- `--user` confines management to the ordinary user's delegated manager.
- `--wait` waits for workload status, `--pipe` preserves output, and `--collect` removes the transient unit and cgroup.
- `CPUQuota=50%` becomes `50000 100000`: 50,000 microseconds of CPU time per 100,000-microsecond period.
- `--` ends systemd-run options; Python and its script remain separate argv elements.

Intentional failure: omit `CPUQuota`. The workload still succeeds, but `cpu.max` reports `max 100000`, proving no CPU ceiling was installed. Restore the property and require `50000 100000`.

## Checkpoint and troubleshooting

```bash
systemd-run --user --wait --pipe --collect --quiet --property=CPUQuota=50% -- python3 "$PWD/inspect_cpu.py" | grep -q '50000 100000'
```

- If the user manager is unavailable, use the documented VM login session; do not switch to system units or `sudo`.
- Quota throttles aggregate CPU time for the cgroup tree; it does not guarantee wall-clock latency or fair scheduling.
