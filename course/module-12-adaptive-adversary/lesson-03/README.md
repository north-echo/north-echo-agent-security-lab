# 12.03 - Package a calibrated candidate experiment

## Outcomes and prerequisites

Complete 12.01-12.02. You will package known local code, inputs, and observations; verify their recorded bytes; detect a missing or changed input before replay; and repeat the experiment from a relocated directory.

## Concepts before commands

**Reproducibility** requires the inputs and procedure, not just the conclusion. A result without the code and scenario may be impossible to interpret later.

A **checksum** describes bytes. Comparing a file to its recorded SHA-256 detects a mismatch, but an attacker who can replace both file and inventory can make them agree. This package is not signed, and matching hashes do not establish authorship, trustworthy behavior, or the truth of a claim.

Only replay the known course sources you have just read. Never execute an unknown downloaded “experiment” because its self-supplied manifest verifies. Even an exact argv list can launch harmful code.

## Prepare and read both programs

From the course root:

```bash
./lab-start 12.03
cd .student/12.03
pwd
ls -l package_experiment.py verify_package.py
cat package_experiment.py
cat verify_package.py
```

Use `nano` with the exact filename to navigate. The input runner and oracle remain the known synthetic programs from 12.01-12.02, not a new probing tool.

### The packager

<!-- source: course/module-12-adaptive-adversary/lesson-03/package_experiment.py format=code -->
```python
#!/usr/bin/env python3
"""Bundle explicit local inputs and sources for replay from a clean directory."""
import hashlib
import json
from pathlib import Path
import sys


def main():
    if len(sys.argv) != 6:
        raise SystemExit("usage: package_experiment.py RESULT SPEC RUNNER CANDIDATE_ID DIRECTORY")
    result_path, spec_path, runner = map(Path, sys.argv[1:4])
    result = json.loads(result_path.read_text())
    spec = json.loads(spec_path.read_text())
    if (not isinstance(spec, dict) or set(spec) != {"oracle_command", "budget", "run_id"}
            or type(spec["budget"]) is not int or not 1 <= spec["budget"] <= 8
            or not isinstance(spec["run_id"], str)
            or not isinstance(result, dict)):
        raise SystemExit("invalid spec or result shape")
    command = spec["oracle_command"]
    if (not isinstance(command, list) or len(command) != 3
            or any(not isinstance(item, str) or not item for item in command)):
        raise SystemExit("packaging supports only the explicit local Python oracle plus scenario interface")
    oracle, scenario = map(Path, command[1:])
    trace = result.get("trace", [])
    if (type(result.get("schema")) is not int or result.get("schema") != 1
            or result.get("status") not in ("observed", "not_observed")
            or not isinstance(trace, list) or not isinstance(result.get("claim"), str)
            or type(result.get("actions_used")) is not int
            or result.get("run_id") != spec["run_id"]
            or result.get("actions_used") != len(trace) or not 1 <= len(trace) <= spec["budget"]):
        raise SystemExit("invalid result, run identity, or budget")
    files = {"runner.py": runner.read_bytes(), "oracle.py": oracle.read_bytes(),
             "scenario.json": scenario.read_bytes(), "expected.json": result_path.read_bytes()}
    portable = dict(spec, oracle_command=["python3", "oracle.py", "scenario.json"])
    files["spec.json"] = (json.dumps(portable, indent=2, sort_keys=True) + "\n").encode()
    package = {"schema": 2, "candidate_id": sys.argv[4], "run_id": spec["run_id"],
               "hypothesis": "The recorded local scenario permits the reported observation within this budget.",
               "result_status": result["status"], "claim": result["claim"],
               "limits": ["synthetic local oracle", "single run", "bounded probe set", "non-discovery is not proof"],
               "replay": ["python3", "runner.py", "spec.json", "result.json"],
               "sha256": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}
    output = Path(sys.argv[5])
    output.mkdir()  # Never overwrite an existing experiment or student work.
    for name, data in files.items():
        (output / name).write_bytes(data)
    (output / "package.json").write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
```
<!-- /source -->

### Source, line by line

- Five arguments identify the existing result, spec, runner, local candidate label, and new destination.
- Spec/result checks require the known schema, matching run identity, and a trace count within budget. They do not independently authenticate or remeasure observations.
- The command must have the local Python-oracle-plus-scenario shape. The packager does not discover arbitrary program dependencies or prove the supplied executable trustworthy.
- The files mapping reads the known sources, scenario, and expected result as bytes.
- A portable spec names the copied files relative to the package directory; it does not preserve a workstation-specific absolute repository path.
- SHA-256 is calculated over each packaged file's exact bytes.
- The package records hypothesis, claim, limits, and a replay argv. These are review metadata, not a certification or publication.
- `mkdir()` refuses an existing destination. Writing occurs only inside this newly created directory.
- An interrupted write can leave an incomplete directory. Verification must reject missing content; do not overwrite the directory to disguise that failure.

The packager assumes small trusted local inputs. It is neither a dependency manager nor a general safe archive extractor.

### The non-executing verifier

<!-- source: course/module-12-adaptive-adversary/lesson-03/verify_package.py format=code -->
```python
#!/usr/bin/env python3
"""Check the fixed local package inventory without executing packaged code."""
import hashlib
import json
from pathlib import Path
import re
import sys

FILES = {"runner.py", "oracle.py", "scenario.json", "expected.json", "spec.json"}


def verify(root):
    manifest = root / "package.json"
    if root.is_symlink() or manifest.is_symlink() or not manifest.is_file():
        raise ValueError("expected an ordinary package directory and manifest")
    package = json.loads(manifest.read_text())
    hashes = package.get("sha256") if isinstance(package, dict) else None
    if not isinstance(hashes, dict) or set(hashes) != FILES:
        raise ValueError("unexpected package inventory")
    for name in sorted(FILES):
        digest = hashes[name]
        path = root / name
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("invalid digest")
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"missing or non-regular package file: {name}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"checksum mismatch: {name}")
    print("PACKAGE BYTES MATCH RECORDED INVENTORY; AUTHENTICITY IS NOT ESTABLISHED")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_package.py DIRECTORY")
    try:
        verify(Path(sys.argv[1]))
    except (OSError, ValueError) as error:
        raise SystemExit(f"package verification failed: {error}")
```
<!-- /source -->

### Source, line by line

- `FILES` is an exact allowlist, not a set of arbitrary paths taken from a manifest.
- The directory/manifest leaf checks refuse symbolic links and missing regular input.
- Parsing requires a mapping with exactly the five expected hash entries.
- Each hash must be a lowercase 64-character hexadecimal string.
- Each expected file must be a regular non-symlink leaf; its bytes are hashed and compared.
- The success message states the limit: matching inventory does not establish authenticity.
- Exceptions produce nonzero status and a diagnostic. No packaged program is imported or executed.

This verifier does not claim race-free behavior against a concurrent same-account mutator, validate every metadata field, or inventory unrelated extra files. Keep the prepared directory under your control.

## Exercise 1 - Produce and package known evidence

```bash
NE_RUNNER=../../course/module-12-adaptive-adversary/lesson-02/adaptive_runner.py
NE_SPEC=../../course/module-12-adaptive-adversary/lesson-02/network-spec.json
python3 "$NE_RUNNER" "$NE_SPEC" result.json
python3 package_experiment.py result.json "$NE_SPEC" "$NE_RUNNER" candidate-12 package
python3 -m json.tool package/package.json
python3 verify_package.py package
```

The two variables name sources you already read. Quoting keeps each pathname one argument. `candidate-12` is merely your local label, not a vulnerability identifier.

Predict the five hashed files and compare with the printed inventory. The manifest is not included in its own hash list. The original result is copied as `expected.json`; a later replay will create a separate `result.json`.

## Exercise 2 - Deliberately remove an input, then repair it

```bash
mv package/scenario.json package/scenario.saved
NE_MISSING_STATUS=0
python3 verify_package.py package > missing.out 2> missing.err || NE_MISSING_STATUS=$?
test "$NE_MISSING_STATUS" -ne 0
cat missing.err
mv package/scenario.saved package/scenario.json
python3 verify_package.py package
```

Verification must fail before any replay command is run. Restore the **same** saved file, then verify again. A metadata summary cannot replace a missing scenario.

Now change only the scenario's formatting, retaining the same JSON meaning:

```bash
cp package/scenario.json original-scenario.json
python3 - <<'PY'
from pathlib import Path

path = Path("package/scenario.json")
path.write_bytes(path.read_bytes() + b"\n")
PY
NE_CHANGED_STATUS=0
python3 verify_package.py package > changed.out 2> changed.err || NE_CHANGED_STATUS=$?
test "$NE_CHANGED_STATUS" -ne 0
cat changed.err
cp original-scenario.json package/scenario.json
python3 verify_package.py package
```

The checksum changes even though JSON parsing would yield the same object. It identifies bytes, not semantic equivalence. Repair by restoring the recorded source, not by silently changing the hash to fit an unexplained modification.

## Exercise 3 - Relocate and replay

```bash
mv package relocated-package
python3 verify_package.py relocated-package
(
  cd relocated-package
  python3 runner.py spec.json result.json
  cmp expected.json result.json
)
python3 package_experiment.py result.json "$NE_SPEC" "$NE_RUNNER" candidate-12 second-package
cmp relocated-package/package.json second-package/package.json
NE_EXISTING_STATUS=0
python3 package_experiment.py result.json "$NE_SPEC" "$NE_RUNNER" candidate-12 second-package \
  > existing.out 2> existing.err || NE_EXISTING_STATUS=$?
test "$NE_EXISTING_STATUS" -ne 0
python3 verify_package.py second-package
```

The parentheses create a subshell; its directory change does not move your outer lesson shell. Replay uses only the copied runner, oracle, scenario, and spec. The Python runtime remains an environmental dependency; this is source portability, not a bootable or hermetic environment.

The second package has identical metadata for identical inputs. Repeating into its existing directory fails without overwriting it. Byte-identical results are possible because this tiny oracle omits timestamps and real-world variability; do not demand that property from every legitimate experiment.

## Checkpoint and independent explanation

```bash
python3 - <<'PY'
import json
from pathlib import Path

root = Path("relocated-package")
package = json.loads((root / "package.json").read_text())
assert package["candidate_id"] == "candidate-12"
assert package["replay"] == ["python3", "runner.py", "spec.json", "result.json"]
assert json.loads((root / "spec.json").read_text())["oracle_command"] == [
    "python3", "oracle.py", "scenario.json"]
assert (root / "expected.json").read_bytes() == (root / "result.json").read_bytes()
assert "non-discovery is not proof" in package["limits"]
assert "checksum mismatch" in Path("changed.err").read_text()
assert "missing or non-regular" in Path("missing.err").read_text()
print("PORTABLE REPLAY AND NON-EXECUTING INTEGRITY CHECKS: PASS")
PY
```

Write `review-notes.md` separating hypothesis, observed result, interpretation, limits, and proposed next **review** question. Explain why a forged result could still be packaged and why matching hashes do not authorize running unfamiliar code. No external submission is required.

If replay fails, compare the interpreter version and verified inputs before changing the expected result. If a package already exists, use a new exact destination or reset the lesson after saving your notes. Do not remove files by a broad prefix.

Save any package you want to keep, return with `cd ../..`, then use `./lab-reset 12.03` to discard the prepared workspace. The course reset removes generated local files after ownership checks; this exercise creates no background service.

## Source truth

Python's [hashlib documentation](https://docs.python.org/3.14/library/hashlib.html) defines the byte digest used here. [JSON documentation](https://docs.python.org/3.14/library/json.html) explains serialization, which is distinct from byte identity and from the truth of evidence. Package format and claim limits are course-defined.
