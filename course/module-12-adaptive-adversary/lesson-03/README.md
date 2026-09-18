# 12.03 - Package a calibrated candidate experiment

## Goal

Turn a bounded result into a replayable experiment candidate without expanding its claim beyond the evidence.

```bash
sed -n '1,180p' package_experiment.py
python3 ../../course/module-12-adaptive-adversary/lesson-02/adaptive_runner.py \
  ../../course/module-12-adaptive-adversary/lesson-02/network-spec.json result.json
python3 package_experiment.py result.json candidate-12 package.json
python3 -m json.tool package.json
```

### Line by line

- The packager accepts only a schema-1 observed/not-observed result.
- It preserves the trace and claim, adds a falsifiable bounded hypothesis, lists four interpretation limits, and supplies structured replay argv.
- `candidate_id` labels this package; it is not a vulnerability identifier or publication claim.

Intentional mistake: remove the `non-discovery is not proof` limit. The package then invites an inference its evidence cannot support. Restore all limits and verify:

```bash
grep -F 'non-discovery is not proof' package.json
python3 package_experiment.py result.json candidate-12 second.json
cmp package.json second.json
rm result.json package.json second.json
```

## Checkpoint and troubleshooting

- Package the raw trace, not a prose-only summary.
- A promising observation remains a candidate until independently reproduced under a broader protocol.
- Checkpoint: distinguish the package hypothesis, observed result, and stated limits.
