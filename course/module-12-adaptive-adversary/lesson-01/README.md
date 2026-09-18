# 12.01 - Establish a scripted baseline and its limits

## Goal

Run a fixed probe sequence before adaptation, deliberately miss a weakness outside that sequence, and report non-discovery without claiming safety.

```bash
sed -n '1,180p' local_oracle.py
sed -n '1,180p' scripted_baseline.py
python3 scripted_baseline.py local_oracle.py network-scenario.json baseline.json
python3 -m json.tool baseline.json
```

### Line by line

- The oracle accepts only five named synthetic probes plus `inventory`; it performs no network request.
- The baseline always runs argv, credential, and filesystem probes in that order using exact argv.
- The network scenario is intentionally outside that fixed set, so status is `not_observed` even though a weakness exists.
- The trace preserves every action and observation. This proves what ran, not that untested boundaries are safe.

Intentional mistake: rewrite `not_observed` as `secure`. The trace contradicts that claim because network and cleanup were never probed. Restore the calibrated status.

## Checkpoint and troubleshooting

```bash
test "$(python3 -c 'import json;print(json.load(open("baseline.json"))["status"])')" = not_observed
rm baseline.json
```

- Run from the lesson workspace so scenario paths resolve.
- Checkpoint: name the two untested surfaces and explain why the baseline remains useful for comparison.
