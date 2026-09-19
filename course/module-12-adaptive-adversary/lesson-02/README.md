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

## Exercise 2 - Interpret incomplete evidence without an answer hint

The introductory oracle names `next_probe`; that teaches bounded dispatch, not
independent diagnosis. Now inspect four fixed local records derived from the
control/effect distinction in Module 10. No program here runs a probe or contacts
a target. Before execution, predict a verdict and a missing observation for each
row. All cases have the same three-observation budget. Case labels are teaching
ground truth, not input to the classifier's decision.

```bash
sed -n '1,180p' review_evidence.py
python3 -m json.tool evidence-cases.json
python3 review_evidence.py evidence-cases.json
```

### Line by line

- `EXPECTED` pairs a useful operation with two intended denials. A denial-only
  record cannot establish that useful work survived.
- `review` rejects an exceeded budget, duplicate observations, and unknown check
  names. Its decision reads observations, never the case label.
- A contrary observed effect produces `observed_failure`. Missing or `unknown`
  effects produce `inconclusive`, even when no failure was seen.
- Complete matching observations produce `passed_observations`; the claim stays
  scoped to those observations. The code never labels a system universally secure.
- Sorting makes the evidence summary stable for comparison and replay.

Expected statuses, in order: `passed_observations`, `observed_failure`,
`inconclusive`, `inconclusive`. The third case illustrates a missed seeded failure;
the fourth shows that uncertainty is also possible for a hardened case.

Intentional error and repair: on a copy of the reviewer, treat missing observations
as passed. Predict which row becomes falsely reassuring, run it, then restore
`inconclusive`. Do not change the input to obtain the desired verdict.

Faded exercise: replace one observation with `unknown` in a workspace copy of
the JSON. Explain the smallest additional observation needed to resolve it before
running the reviewer. Independent checkpoint: provide an evidence matrix for a
new three-check case and explain both the verdict and its limits. Case labels and
configured controls alone are never proof of an observed effect.
