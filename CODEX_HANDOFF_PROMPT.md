# Prompt for the new Linux-backed Codex task

Copy the text below into the first task created for this repository on the disposable Linux VM.

---

Continue building the North Echo Agent Security Lab from this repository. Do not regenerate it from scratch. Read `AGENTS.md` and `HANDOFF.md` first, then follow their required reading order and acceptance gates.

Your first gate is to validate the existing v0.1 platform and fully authored Modules 01-03 on this Linux VM. Run the non-destructive preflight, automated tests, course attestation, and the complete matrix in `docs/LINUX_VALIDATION.md`. Fix real portability, safety, lesson, or grader defects with focused regression tests. Record the exact distribution, kernel, architecture, tool versions, results, and limitations. Do not claim Linux validation for anything that did not actually run.

After Gate A passes, build the full course in the three tranches defined in `ROADMAP.md`: Modules 04-06, Modules 07-09, then Modules 10-12 and the cold capstone. Finish every module against `docs/MODULE_ACCEPTANCE_TEMPLATE.md` before calling it playable, and finish each tranche gate before starting the next tranche.

The course must remain hands-on and independent of AI. Guided lessons need exact commands, complete small code listings, immediate line-by-line explanations, expected output patterns, intentional mistakes, repairs, checkpoints, and troubleshooting. Independent labs must use only practiced skills and must not reveal complete solutions. Practice graders should report failed security properties with useful references; exam graders should reduce hints. Maintain randomized synthetic fixtures, external evaluation fixtures, metadata-only history, safe lesson/module/all reset scopes, and fail-closed registered cleanup.

Never cut corners on the field manual. Treat the manual as a first-class implementation surface and keep it synchronized with every lesson, code sample, fixture, grader, expected observation, and troubleshooting path. Optional man pages may deepen a lesson but may not replace local explanations.

Run only in this disposable VM, use only synthetic local data and services, and never use personal, employer, cloud, or production credentials or any external target. Ask for direction only if a required choice would materially change the curriculum or safety boundary; otherwise continue through the current acceptance gate and leave the repository in a tested, reviewable state.

---
