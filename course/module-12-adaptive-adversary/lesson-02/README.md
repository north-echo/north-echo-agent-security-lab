# 12.02 - Adapt within an action budget

## Goal

Use one inventory observation to choose one focused probe, preserve an auditable trace, and discover the same network weakness in two actions.

```bash
sed -n '1,260p' adaptive_runner.py
python3 adaptive_runner.py network-spec.json result.json
python3 -m json.tool result.json
```

### Line by line

- The runner validates the exact spec, structured oracle command, integer budget, and run identity.
- Action one is always `inventory`. Its `next_probe` value must be in the fixed allowlist.
- If budget remains, action two invokes that probe with exact argv and a timeout; no shell or generated exploit is used.
- Finding, calibrated claim, budget use, and the complete observations are written together.

Expected status is `observed`, actions used is 2, and finding probe is `network`.

Intentional failure and repair:

```bash
python3 -c 'import json;p=json.load(open("network-spec.json"));p["budget"]=1;open("short.json","w").write(json.dumps(p))'
python3 adaptive_runner.py short.json short-result.json
grep 'not established' short-result.json
python3 adaptive_runner.py network-spec.json result.json
rm short.json short-result.json result.json
```

Budget one cannot run the focused probe; the repair restores budget two rather than overstating inventory evidence.

## Checkpoint and troubleshooting

- If the oracle path fails, preserve the three argv elements in `oracle_command`; do not join them into a shell string.
- Checkpoint: show which observation caused action two and which field proves the budget was respected.
