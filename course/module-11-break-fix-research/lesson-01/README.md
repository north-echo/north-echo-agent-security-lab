# 11.01 - Reproduce a seeded weakness without an agent

## Goal

Generate a repeatable unknown variant, use a deterministic harness to reproduce its effects, and separate configuration clues from behavioral evidence.

## Exercise 1 - Read the complete generator and harness

```bash
sed -n '1,200p' make_variant.py
sed -n '1,300p' variant_harness.py
```

### Line by line

- `make_variant.py` starts from five hardened controls, uses only an explicit integer seed, and weakens two through four randomly selected controls. The seed makes research replayable; it is not security randomness.
- The workload contains one allowed synthetic read and a literal shell-looking argument. Variant identity is opaque evidence metadata.
- `variant_harness.py` creates a new private directory, allowed file, protected sibling, symlink, and marker.
- Execution mode passes the same literal through either `shell=True` or an argv array. Environment mode launches `/usr/bin/env` with inherited or minimal variables.
- Filesystem mode compares lexical spelling or the resolved target. Network mode creates, but never connects, an IPv4 socket. Cleanup mode selects candidate names but never deletes them.
- The evidence contains observed effects, not the control labels, and preserves allowed-operation success.

## Exercise 2 - Trigger and replay the variant

```bash
python3 make_variant.py 1101 variant.json
NORTH_ECHO_FAKE_CREDENTIAL=FAKE-LESSON-11.01 \
  python3 variant_harness.py variant.json evidence.json run-a
python3 -m json.tool variant.json
python3 -m json.tool evidence.json
```

At least two adverse evidence fields are true. `allowed_operation` remains true. The intentional mistake is to call the changed configuration itself proof: a `direct` field is suspicious, but `inet_created:true` is the reproduced effect.

Replay the exact seed and compare:

```bash
python3 make_variant.py 1101 replay.json
cmp variant.json replay.json
```

The byte-identical plan makes the observation reproducible. A different seed may select a different weakness set without changing the research method.

## Exercise 3 - Prove the harness is bounded

```bash
test ! -e run-a/not-a-workspace
test -e run-a/protected.txt
find run-a -maxdepth 2 -type f -o -type l | sort
rm run-a/allowed/data.txt run-a/allowed/link.txt run-a/protected.txt
test ! -e run-a/shell-marker || rm run-a/shell-marker
rmdir run-a/allowed run-a
rm variant.json replay.json evidence.json
```

The protected file still exists because the reproducer reads but never modifies it. Cleanup evidence is only a selected-name list inside the harness; no service or host object is removed.

## Checkpoint and troubleshooting

- If `run-a` exists, remove only the exact files listed above before replaying; the harness refuses to reuse a directory.
- If no credential is visible in an inherited variant, confirm the explicitly fake variable prefixes the harness command.
- Do not replace the synthetic literal with a command affecting anything outside the generated directory.
- Checkpoint: identify one field that is configuration and one field that is reproduced evidence.
