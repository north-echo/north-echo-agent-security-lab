# Foundation rewrite candidate: first Fedora regression gate

Candidate archive SHA256:
`8c06379e64d356582fded4cc38057ac920ed5a1b7c79687cf79d9b6a065ac1e0`.
This uncommitted candidate contained the B0/B1 pilot, foundation prose rewrite,
three new C bridges, six foundation regression tests, and Fedora installer tests.
Later module rewrites are not covered by this record.

In a separate candidate directory in the dedicated Fedora 44 ARM64 validation
VM, running kernel `6.19.10-300.fc44.aarch64`, SELinux enforcing:

- `python3 scripts/run_tests.py --require-no-skips`: 90 tests, all passed,
  zero skips, 16.464 seconds.
- `./scripts/attest-course`: PASS.
- `python3 scripts/build_field_manual.py --check`: synchronized.
- `./scripts/linux-preflight`: 33 required checks passed, zero failed;
  runtime Landlock ABI 7.

The added tests compile the actual C sources with warnings as errors, compare
explicit environment output, verify descriptor closure and its omitted-control
failure, and compare capability clearing with/without the operation inside an
unprivileged user namespace. They also execute the exact documented shell
examples for capability inventory, argument-boundary preservation and its
unquoted failure, and collection of a known child's status.

Host macOS: 90 tests ran, 69 passed and 21 Linux-only tests skipped, 23.474 seconds.
The first sandboxed host run was blocked from terminating its own synthetic
child process group; the approved unsandboxed rerun passed. That host result
is not Linux enforcement evidence.

Human comprehension and the complete v2 beta remain unvalidated. A final full
candidate and actual published-artifact installation gate are still required.
