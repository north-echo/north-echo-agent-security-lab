# 12.03 - Package a calibrated candidate experiment

## Goal

Turn a bounded result into a portable experiment directory, replay it without
the repository, and keep its claim within the evidence.

```bash
sed -n '1,180p' package_experiment.py
RUNNER=../../course/module-12-adaptive-adversary/lesson-02/adaptive_runner.py
SPEC=../../course/module-12-adaptive-adversary/lesson-02/network-spec.json
python3 "$RUNNER" "$SPEC" result.json
python3 package_experiment.py result.json "$SPEC" "$RUNNER" candidate-12 package
python3 -m json.tool package/package.json
(cd package && python3 runner.py spec.json result.json && cmp expected.json result.json)
```

### Line by line

- `RUNNER` and `SPEC` name the actual source and inputs that produced the result.
  Quotes keep each pathname one argument.
- The packager checks result shape, run identity, and action budget. It supports
  exactly the lesson's local Python oracle plus scenario interface; it does not
  guess dependencies for arbitrary commands.
- The result, runner, oracle, and scenario are copied; the spec uses relative
  paths inside the package. A SHA-256 inventory records their exact bytes.
- `mkdir` refuses an existing directory, so packaging never replaces student work.
- The subshell enters only the new package, runs its own copies, and compares the
  replay against the original result. No repository path is needed for replay.
- `candidate_id` is a local label, not a vulnerability identifier or publication claim.

Intentional mistake: rename `package/scenario.json` to `package/scenario.saved`.
Replay fails because the package is incomplete. Restore the filename and replay
successfully. A JSON summary alone is not a reproducible experiment.

Now prove packaging is deterministic and clean the exact generated artifacts:

```bash
grep -F 'non-discovery is not proof' package/package.json
python3 package_experiment.py result.json "$SPEC" "$RUNNER" candidate-12 second
cmp package/package.json second/package.json
rm package/runner.py package/oracle.py package/scenario.json package/spec.json package/expected.json package/result.json package/package.json
rm second/runner.py second/oracle.py second/scenario.json second/spec.json second/expected.json second/package.json
rmdir package second
rm result.json
```

## Checkpoint and troubleshooting

- Package the raw trace, not a prose-only summary.
- A promising observation remains a candidate until independently reproduced under a broader protocol.
- Checkpoint: distinguish the package hypothesis, observed result, and stated limits.
- Independent checkpoint: move a completed package to another directory and replay
  it there; explain why hashing the report alone would not identify its inputs.
