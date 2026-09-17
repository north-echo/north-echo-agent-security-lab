# 07.02 - Bound memory and observe OOM

## Goal

Apply a memory ceiling to an entire transient service and observe a synthetic allocator crossing it without risking the VM.

`memory_hog.py` converts one argument to a count, retains one-megabyte `bytearray` blocks so pages stay charged, prints bounded progress every eight blocks, and sleeps only after allocation completes.

```bash
python3 memory_hog.py 16
set +e
systemd-run --user --wait --pipe --collect --quiet \
  --property=MemoryMax=33554432 --property=MemorySwapMax=0 \
  -- python3 "$PWD/memory_hog.py" 96
status=$?
set -e
printf 'bounded_status=%s\n' "$status"
```

### Line by line

- The 16 MiB baseline should complete normally.
- `MemoryMax=33554432` is an exact 32 MiB cgroup ceiling; `MemorySwapMax=0` prevents the exercise from shifting pressure into swap.
- The 96 MiB request is synthetic and bounded. The kernel kills the charged process tree before it reaches that size.
- `set +e` permits observation of the expected failure; the saved nonzero status is restored to visible evidence before fail-fast mode returns.
- `--collect` removes the failed unit and its cgroup after systemd reports memory peak and service result.

Intentional failure: run the 96 MiB request without `MemoryMax`. It completes and proves observation alone is not enforcement. Restore both memory properties.

## Checkpoint and troubleshooting

```bash
! systemd-run --user --wait --pipe --collect --quiet --property=MemoryMax=33554432 --property=MemorySwapMax=0 -- python3 "$PWD/memory_hog.py" 96
```

- A nonzero result is expected; do not increase the allocation or change host overcommit settings.
- `memory.max` bounds charged memory, while OOM outcome can vary with interpreter startup and kernel accounting. The stable property is containment below the configured ceiling.
