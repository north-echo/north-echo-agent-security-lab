# 10.01 - Order the complete runtime by dependency

## Goal

Turn the earlier controls into a launch dependency graph, trigger an invalid order, and prove the repaired plan satisfies every dependency.

## Exercise 1 - Read the plan validator

```bash
sed -n '1,240p' check_order.py
python3 -m json.tool broken-plan.json
python3 -m json.tool repaired-plan.json
```

### Source, block by block

- `REQUIRED` names every phase that changes the security result. A plan cannot silently omit teardown or broker readiness.
- `BEFORE` contains dependency edges, not a preferred cosmetic order. The cgroup precedes descendants; namespace creation precedes capability removal; Landlock setup precedes a filter that does not allow Landlock syscalls; every restriction precedes workload `exec`; collection follows workload exit.
- `main` accepts only a JSON string array, rejects duplicate, missing, and unknown steps, maps each step to its position, and reports every reversed edge.
- The exit status is nonzero whenever an effective dependency is violated, so the check can gate a launcher build.

## Exercise 2 - Trigger the ordering failure

```bash
python3 check_order.py broken-plan.json; test "$?" -eq 1
```

Expected output includes `apply_landlock must precede apply_seccomp`. The deliberate mistake installs seccomp first. A useful workload policy may deny the Landlock setup syscalls; applying that filter first can make the filesystem control impossible to install. A list containing both controls is not proof of composition.

## Exercise 3 - Repair and challenge the graph

```bash
python3 check_order.py repaired-plan.json
cp repaired-plan.json challenge-plan.json
python3 - <<'PY'
import json
from pathlib import Path
p = Path("challenge-plan.json")
steps = json.loads(p.read_text())
steps.remove("enter_cgroup")
steps.insert(3, "enter_cgroup")
p.write_text(json.dumps(steps) + "\n")
PY
python3 check_order.py challenge-plan.json; test "$?" -eq 1
rm challenge-plan.json
```

### Line by line

- The repaired plan moves Landlock before seccomp and returns `ok: true`.
- The small Python edit deliberately moves cgroup entry after namespace creation. The validator rejects it because processes created during namespace setup would otherwise exist before accounting is attached.
- Removing the temporary challenge leaves only shipped lesson files.

The broker starts before the isolated child because the child has no inherited IP network and must find a ready filesystem socket. The user namespace is entered before dropping capabilities because mapping root in a new user namespace creates namespace-scoped capabilities that must then be removed. Collection is last because `--collect` is a lifecycle guarantee, not a workload restriction.

## Checkpoint and troubleshooting

```bash
test "$(python3 check_order.py repaired-plan.json)" = '{"ok": true, "violations": []}'
```

- If JSON parsing fails, restore an array of quoted step names; ordering is evaluated only after shape validation.
- If a step appears harmless to move, identify what it creates, what syscalls it needs, and which later phase removes that authority.
- Checkpoint: explain why `apply_landlock` before `apply_seccomp` and `enter_namespaces` before `drop_privilege` are dependencies rather than style choices.
