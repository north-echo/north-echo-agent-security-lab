# B0/B1 depth and source review

## Scope and review method

Reviewed 2026-09-19 against the supplied pilot's actual code and interfaces.
This record covers six guided lessons and two practical contracts, not a
claim-level audit of the entire twelve-module track. It supplements, rather
than replaces, Linux execution evidence and a future learner walkthrough.

The user's B0.02 feedback exposed a concrete omission: a source listing appeared
without instructions for finding and reading that file inside the VM. The
review therefore checked connective instructions as well as technical claims.

For each unit: inspect the canonical file; locate the primary reference for
the substantive claim; read the relevant section; compare wording with the
actual example and grader; state assumptions/limits; exercise observations.
Do not treat a bibliography, matching keywords, or passing tests as proof that
the prose teaches effectively. No reference text or course exercise is copied.

## Source versions

- Ubuntu Noble's published GNU Bash manual identifies package 5.2.21-2ubuntu4;
  the validation guest reports Bash 5.2.21. Built-in `help pwd` and `help cd`
  were also read there. GNU website fetches timed out, so the reviewed shell
  source is the upstream manual distributed by Ubuntu, not a third-party blog.
- Ubuntu Noble's GNU `ls` and `cat` manual pages cover the inspected commands;
  the guest has coreutils 9.4.
- Python references are the maintained **3.12** documentation, which currently
  identifies 3.12.14. The guest has **3.12.3**. Relevant behavior is checked on
  that guest; documentation patch versions are not claimed to be identical.
- The nano reference explicitly documents **7.2**, matching the guest.
- The Linux baseline is Ubuntu 24.04.5 LTS, aarch64, kernel 6.8.0-139-generic.
  No Windows, macOS exercise, or new x86-64 equivalence claim is made.

## Claim-to-source map

D = documented interface; C = North Echo example/policy choice;
O = observation requiring the supplied code and recorded execution baseline.
These distinctions are also explained in the learner manual.

| Unit / substantive claim | Basis and primary source section | Qualification / evidence |
| --- | --- | --- |
| B0.01: shell interprets commands; quoting keeps the sample path together; `cd` and `pwd` track location | D: [Bash](https://manpages.ubuntu.com/manpages/noble/man1/bash.1.html), QUOTING and SHELL BUILTIN COMMANDS | Ordinary paths; no claim that logical and physical paths are identical with symlinks. O: changing into `notes` changes which relative report path works. |
| B0.01-03: listing is not reading; reading source is not executing it | D: [ls](https://manpages.ubuntu.com/manpages/noble/man1/ls.1.html), `-l`; [cat](https://manpages.ubuntu.com/manpages/noble/man1/cat.1.html), DESCRIPTION; [Python invocation](https://docs.python.org/3.12/using/cmdline.html#interface-options), script argument | C: names and report contents are generated/supplied by this course. O: each named file is present and displayed before execution. |
| B0.02: current and parent PID; argument list starts with the script | D: [os.getpid/getppid](https://docs.python.org/3.12/library/os.html#os.getpid), [sys.argv](https://docs.python.org/3.12/library/sys.html#sys.argv) | O: same interactive parent is expected during our foreground runs, not a permanent identity guarantee. |
| B0.02: argument-controlled branch, output distinct from status | D: [if statements](https://docs.python.org/3.12/tutorial/controlflow.html#if-statements), [SystemExit](https://docs.python.org/3.12/library/exceptions.html#SystemExit), [print](https://docs.python.org/3.12/library/functions.html#print); Bash EXIT STATUS | C: `fail`, diagnostic wording, and status 7. O: normal run returns 0; selected failure returns 7 despite output. |
| B0.03: argument count, selected path, text output, read-error branch | D: [sys](https://docs.python.org/3.12/library/sys.html#sys.argv), [Path.read_text](https://docs.python.org/3.12/library/pathlib.html#pathlib.Path.read_text), [exception handling](https://docs.python.org/3.12/tutorial/errors.html#handling-exceptions), [OSError subclasses](https://docs.python.org/3.12/library/exceptions.html#os-exceptions) | C: required single argument and statuses 1/2. O: wrong report before repair; selected report and expected failures after it. |
| B0.03 / practical: preserve report text, including absence of final newline | D: [print](https://docs.python.org/3.12/library/functions.html#print), [TextIOWrapper](https://docs.python.org/3.12/library/io.html#io.TextIOWrapper), newline behavior | C: valid UTF-8, Unix LF or no final newline. **Not arbitrary byte preservation.** O: grader checks both report endings. |
| B0.03 / B1 edits: open, save, exit, inspect saved source | D: [nano 7.2](https://www.nano-editor.org/dist/v7/nano.html), Invoking, Editor Basics, Write-Out; active Ctrl+G help | Custom key bindings can differ. C: nano is the supplied editor, not a requirement to abandon a familiar editor. Saved-file checks are separate from runtime tests. |
| B1.01: temporary prefix for Python; process environment and key-presence test | D: Bash ENVIRONMENT; [os.environ](https://docs.python.org/3.12/library/os.html#os.environ); [mapping membership](https://docs.python.org/3.12/library/stdtypes.html#mapping-types-dict) | C: fake setting name/value. O: supplied observer reports presence, not a secret's value. Empty value still means a present key. Prefix example is for an external Python command. |
| B1.02: replacement environment, argument boundaries, wait, default streams | D: [subprocess.run/Popen](https://docs.python.org/3.12/library/subprocess.html#subprocess.run); [sys.executable](https://docs.python.org/3.12/library/sys.html#sys.executable) | C: public-style allowlist. O: usable interpreter path on this guest; full/empty/selected handoffs have different outcomes. No observer line after early failure is not an observed denial. |
| B1.03: deleting one name differs from selecting needed keys | D: [dict copying, lookup and pop](https://docs.python.org/3.12/library/stdtypes.html#mapping-types-dict) | C: required style and selected mapping. O: second private key survives the initial single-name deletion; changed-case repair is checked. |
| B1 practical: forward child output and ordinary exit result | D: [CompletedProcess.returncode](https://docs.python.org/3.12/library/subprocess.html#subprocess.CompletedProcess.returncode) and SystemExit | C: ordinary Linux codes 0-255; signal forwarding excluded. O: independent worker checks success and ordinary failure, not signal semantics. |
| B1 practical: interpreter may add a locale setting | D: [PYTHONCOERCECLOCALE](https://docs.python.org/3.12/using/cmdline.html#envvar-PYTHONCOERCECLOCALE) | No assertion that post-startup `os.environ` must contain exactly one key. The contract is about withholding unapproved parent settings. |

Repository-specific lifecycle behavior is grounded in `scripts/northecho/cli.py`,
`beginner.py`, `fixtures.py`, `state.py`, and the scoped cleanup implementation,
with replay/reset tests. The external Python/Bash docs do not certify our CLI.
The supplied trusted worker observes selected conditions; neither that worker
nor its same-user grader is a hostile-code confidentiality boundary. Selecting
an `env` argument alone does not request any user, filesystem, or network
isolation mechanism. The lessons explicitly limit their claim to this handoff.

## Depth corrections made

- Every guided program now has directory confirmation, exact filename listing,
  a read command, and a clear instruction about whether editing is required.
- B0.02 distinguishes source listing, interpreter invocation, actual program
  output, and shell-reported status. It explains imports, function calls,
  argument positions, slicing, the branch, and the intentionally chosen status.
- B0.03 explains input positions and control flow, saving versus changing an
  editor buffer, newline handling, and the directory-read error before it is
  assessed. No new practical-only failure mechanism is silently introduced.
- B1 distinguishes shell prefixes from Python keyword arguments, launcher from
  worker, selecting a mapping from deleting a key, and missing evidence from a
  negative observation. Editor access remains explicit even in faded practice.
- Independent labs retain file/editor access instructions without providing a
  completed implementation. The B1 observer example names an actual reusable
  path and states the prerequisite workspace condition.

## Technical wording corrected

The original broad text-preservation wording was narrowed to the report format
that `read_text` and the grader actually exercise. General child-status wording
was narrowed to ordinary exits: `SystemExit(child.returncode)` does not make
this launcher a signal-preserving supervisor. Neither issue was concealed by
a passing happy-path test. The intended beginner objectives remain unchanged.

## Release and learning gates

Canonical README listings and both Markdown manuals must remain synchronized.
Regression checks cover named-file access before source listings and the new
observation cases; those checks cannot assess prose adequacy or source truth.
Do not mechanically accept a lesson just because it contains a source link.
The user walkthrough is still needed to establish comprehension and pacing.
No word-count or page-count target substitutes for that evidence.
