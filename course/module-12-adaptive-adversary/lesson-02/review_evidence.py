#!/usr/bin/env python3
"""Interpret fixed local observations. This program never invokes a probe."""
import json
from pathlib import Path
import sys

EXPECTED = {"allowed_work": "success", "protected_read": "denied", "direct_ip": "denied"}


def review(case):
    if (not isinstance(case, dict) or set(case) != {"case_id", "budget", "observations"}
            or not isinstance(case["case_id"], str) or not case["case_id"]
            or type(case["budget"]) is not int or not 1 <= case["budget"] <= 8
            or not isinstance(case["observations"], list)):
        raise ValueError("invalid evidence case")
    observations = case["observations"]
    if len(observations) > case["budget"]:
        raise ValueError("observation budget exceeded")
    seen = {}
    for observation in observations:
        if not isinstance(observation, dict) or set(observation) != {"check", "outcome"}:
            raise ValueError("invalid observation shape")
        name, outcome = observation["check"], observation["outcome"]
        if not isinstance(name, str) or name not in EXPECTED or name in seen:
            raise ValueError("unknown or duplicate check")
        permitted = {"success", "failure", "unknown"} if name == "allowed_work" else {"allowed", "denied", "unknown"}
        if not isinstance(outcome, str) or outcome not in permitted:
            raise ValueError("invalid observation outcome")
        seen[name] = outcome
    failures = sorted(name for name, value in seen.items()
                      if value != "unknown" and value != EXPECTED[name])
    missing = sorted(name for name in EXPECTED if name not in seen or seen[name] == "unknown")
    status = "observed_failure" if failures else "inconclusive" if missing else "passed_observations"
    return {"case_id": case["case_id"], "status": status, "failures": failures,
            "missing": missing, "claim": "limited to the supplied observations; security is not established"}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: review_evidence.py CASES.json")
    cases = json.loads(Path(sys.argv[1]).read_text())
    if not isinstance(cases, list):
        raise SystemExit("cases must be a JSON list")
    print(json.dumps([review(case) for case in cases], indent=2, sort_keys=True))
