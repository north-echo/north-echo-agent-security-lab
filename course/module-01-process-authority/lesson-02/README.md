# 01.02 - Environment inheritance is authority

Goal: observe a child receiving data it never requested, then launch it with an explicit environment.

## Exercise 1 - Observe the leak

The workspace `FIXTURE.txt` contains a randomized synthetic user. Export a fake token derived from it:

```bash
export DEMO_AGENT_TOKEN="fake-$(awk -F= '/fixture_id/{print $2}' FIXTURE.txt)"
python3 show-env.py
```

Expected pattern:

```text
DEMO_AGENT_TOKEN=fake-...
```

The child did not open a credential store. The parent handed the value across `execve` in `envp`.

Confirm at the syscall boundary:

```bash
strace -f -e trace=execve python3 show-env.py 2>&1 | head -20
```

Expected pattern: `execve` reports an environment count. `strace -v -s 200` can show more; do not use that option around real secrets.

## Exercise 2 - Make the intentional mistake

Run the starter launcher:

```bash
sed -n '1,160p' launch-insecure.py
python3 launch-insecure.py
```

Expected: the token is still printed. Passing `env=os.environ.copy()` feels explicit but preserves every inherited variable.

Fix the launcher by replacing the copied environment with only:

```python
child_env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
```

Run it again. Expected: `DEMO_AGENT_TOKEN=<absent>`.

## Exercise 3 - Verify, do not assume

```bash
python3 launch-insecure.py | grep -F 'DEMO_AGENT_TOKEN=<absent>'
```

Expected: one matching line and exit status 0. The control is an allowlisted environment constructed at the authority-transfer point, not a promise that children will ignore secrets.
