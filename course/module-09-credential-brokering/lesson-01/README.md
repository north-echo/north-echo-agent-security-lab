# 09.01 - Remove ambient credential authority

## Goal

Observe a fake credential crossing `exec` through the environment, trigger a deliberate disclosure, then prove an exact-argv launcher removes it.

## Exercise 1 - Read the complete probes

```bash
sed -n '1,200p' credential_probe.py
sed -n '1,200p' clean_launch.py
```

### Source, line by line

- `credential_probe.py` asks `os.environ` for one explicitly fake variable. It reports presence and length without revealing the value by default.
- Its `leak` mode represents an untrusted tool that can read every inherited variable; it adds the value to JSON only to make the synthetic failure observable.
- `clean_launch.py` requires structured argv, constructs a new environment containing only fixed `PATH` and `LANG`, and calls `subprocess.run` with `shell=False`.
- The child status becomes the launcher status. Failure does not trigger a retry with the inherited environment.

## Exercise 2 - Trigger ambient disclosure

Set a visibly fake lesson value and invoke the probe through a new Python process:

```bash
export NORTH_ECHO_FAKE_CREDENTIAL="FAKE-LESSON-$$-DO-NOT-USE"
python3 credential_probe.py
python3 credential_probe.py leak
```

### Line by line

- `export` places the name in the environment inherited by later `exec` calls. The value is synthetic and must never be replaced with a real credential.
- The first run should report `"present": true` and a nonzero length. This proves inheritance without disclosure.
- The intentional `leak` run prints `leaked_value`. The child needed no separate credential API or user confirmation; possession of the environment was authority.

This does not mean environment variables are always logged. It proves every launched child can read the value and may copy it elsewhere.

## Exercise 3 - Repair inheritance

Run the same exact probe through the clean launcher:

```bash
python3 clean_launch.py /usr/bin/python3 "$PWD/credential_probe.py"
python3 clean_launch.py /usr/bin/python3 "$PWD/credential_probe.py" leak
test -n "$NORTH_ECHO_FAKE_CREDENTIAL"
unset NORTH_ECHO_FAKE_CREDENTIAL
```

### Line by line

- `/usr/bin/python3` is an exact executable path and the script is a separate argv element.
- Both children should report `"present": false`; `leak` cannot print a value it did not inherit.
- The parent-side `test` proves the fake credential still existed outside the child. The observation is about the launch boundary, not accidental deletion.
- `unset` removes the synthetic value from the lesson shell when the observation is complete.

Intentional mistake: change `env=clean` to `env=os.environ.copy()`. The probe sees the value again. Restore the fixed dictionary and require both modes to report absence.

The repair also removes functionality for a tool that genuinely needs the credential. Lessons 09.02-09.03 restore only an approved operation through a broker; they do not put the credential back into the workload.

## Checkpoint and troubleshooting

```bash
export NORTH_ECHO_FAKE_CREDENTIAL=FAKE-CHECKPOINT
test "$(python3 clean_launch.py /usr/bin/python3 "$PWD/credential_probe.py")" = '{"length": 0, "present": false}'
unset NORTH_ECHO_FAKE_CREDENTIAL
```

- If the child still sees the value, confirm `env=clean` is passed to the exact `subprocess.run` call.
- Do not inspect `/proc` entries belonging to unrelated processes; this exercise needs only its own child environment.
- Checkpoint: explain why a shorter-lived environment credential remains ambient authority during its lifetime.
