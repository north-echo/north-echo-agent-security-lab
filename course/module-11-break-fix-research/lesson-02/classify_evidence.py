#!/usr/bin/env python3
"""Map reproduced effects to invariant statements."""

import json
import sys
from pathlib import Path

INVARIANTS = {
    "shell_marker_created": "argv is data and is never shell syntax",
    "credential_visible": "the workload receives no ambient credential",
    "protected_read": "authorization follows resolved objects, not lexical paths",
    "inet_created": "the workload has no direct IP socket authority",
    "cleanup_decoy_selected": "cleanup selects only exact owned objects",
}

if len(sys.argv) != 2:
    raise SystemExit(f"usage: {sys.argv[0]} EVIDENCE.json")
evidence = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
required = {"schema", "variant_id", "allowed_operation", *INVARIANTS}
if (not isinstance(evidence, dict) or set(evidence) != required
        or type(evidence["schema"]) is not int or evidence["schema"] != 1
        or not isinstance(evidence["variant_id"], str)
        or any(type(evidence[name]) is not bool for name in ("allowed_operation", *INVARIANTS))):
    raise SystemExit("invalid or incomplete evidence; absence is not a negative observation")
failed = [{"signal": name, "invariant": statement}
          for name, statement in INVARIANTS.items() if evidence.get(name) is True]
print(json.dumps({"variant_id": evidence.get("variant_id"), "failed": failed}, indent=2, sort_keys=True))
raise SystemExit(0)
