# v2.0.0-beta.1 candidate and release acceptance

Learner-review beta, not stable certification or evidence of novice comprehension.
All exercises used synthetic local fixtures in disposable VMs. The original
learner VM was not changed. No student solutions or generated canaries are retained.

## Final candidate

Archive: `north-echo-beta-final-b-20260920.tgz`.
SHA256: `3e5d05b81646b336cbf4c84927904c514c8a9867581b9224ff33ee8c5440828c`.
This working-tree snapshot precedes documentation-only acceptance updates and
the release commit. CI and actual-release installation must check the tagged source.

| Environment | Strict tests | Preflight | Other gates |
| --- | --- | --- | --- |
| Fedora 44 ARM64, 6.19.10-300.fc44.aarch64, Python 3.14.3, SELinux enforcing | 132 passed, 0 skips, 37.528s | 33 passed, 0 failed | integrity, manual sync, warning-clean Landlock compile, empty managed runtime: pass |
| Ubuntu 24.04.5 ARM64, 6.8.0-139-generic, Python 3.12.3 | 132 passed, 0 skips, 36.009s | 33 passed, 0 failed | integrity, manual sync, warning-clean Landlock compile, empty managed runtime: pass |

Fedora image URL:
`https://download.fedoraproject.org/pub/fedora/linux/releases/44/Cloud/aarch64/images/Fedora-Cloud-Base-Generic-44-1.7.aarch64.qcow2`.
Image SHA256: `55c60a3b80d3616a08705afd0459e75fe9f03c54aba7a46e4002a41a72fa0d5b`.
Lima 2.2.0, 4 CPUs, 6 GiB RAM, 30 GiB disk; plain mode, no host mounts or
SSH-agent forwarding. Fedora runtime Landlock ABI 7; Ubuntu runtime ABI 4.
Installed packages remain repository-resolved, not frozen by the image digest.

macOS control-plane check: 132 discovered, 92 passed, 40 expected Linux-only
skips, 37.793s. This is not a kernel-validation claim. Both Lima templates pass
`limactl validate` on Lima 2.2.0.

Tests replay documented command blocks and independent preparation, evaluate
reference implementations, and reject broken controls. They do not simulate a
novice learning independently. Earlier tranche hashes/counts remain in their own
`*-rewrite-20260919` records, not silently upgraded to this candidate.

## Corrections during final acceptance

- An earlier candidate transfer omitted the managed directories. Its test suite
  passed, but the old `test -z "$(find ...)"` could mistake a failed search for
  empty state. Both installers and CI now require real nonsymlink directories
  and check search success separately. A regression covers missing directories,
  nonempty state, and a deliberately failing search. The final archive includes
  the directories, and the corrected runtime gate passed on both guests.
- The first 132-test run caught a stale assertion for removed duplicate manual
  headings. It now checks the actual canonical independent-lab titles; both
  complete suites were rerun, producing the results above.

## PDF candidate QA

271 Letter pages, linked contents/bookmarks, 307 link annotations. All pages
rendered and reviewed as contact sheets; B0.02, a C-heavy lesson, and capstone
also reviewed at reading resolution. No clipping, overlap, unreadable glyphs,
or broken tables observed. Text/geometry/navigation checker reports no problems.
The approved B0.02 source is preserved. The final release-built PDF must receive
the same automated check and representative rendered comparison.

## Remaining publication gates at this checkpoint

- Commit/push, Ubuntu x86-64 and ARM64 CI against the release commit.
- Tag-bound source/manual/PDF/history/checksum artifacts and prerelease publication.
- Fresh installation of the actual published archive; marker/work preservation
  on restart; intentionally failing readiness with nonzero start; restoration;
  plain-mode evidence copy with equal guest/host digest.

Post-publication observations belong in a follow-up record, because they cannot
exist inside the source archive before that archive is published. Do not move
the release tag to add that evidence. Fedora x86-64 and human learner outcomes
remain unvalidated regardless of these mechanical results.
