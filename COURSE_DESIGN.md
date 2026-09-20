# Course design

North Echo uses concept explanation, guided practice, repetition with changed
inputs, and independent practicals. The beginner-first rewrite draws teaching-structure
lessons from the user's successful RH124/RH134 experience without copying course
content. Explanation length follows the material and its prerequisites, not a
fixed brevity target. AI is not part of the required student's execution path.

Every guided lesson follows this loop:

1. Understand the purpose and prerequisite concepts; locate and read the actual supplied files.
2. Predict the result, then run an exact command or edit/compile a small program, with local explanations of syntax and save/run steps.
3. Observe a runtime or kernel-visible fact and compare it with the prediction.
4. Read the security explanation immediately after the observation.
5. Trigger an intentional failure or incomplete control.
6. Correct it with an interface already in view.
7. Verify resulting state rather than trusting command intent.

Line-by-line commentary is intentionally local: it follows the block it explains instead of becoming a detached glossary. It explains mechanics and security meaning without turning an independent practical into a solution transcript.

"Read this program" must include how to access that file in the VM. Reading,
editing, and executing are distinct actions. An independent practical withholds
the implementation, not basic workspace or editor instructions.

Technical claims need primary-source support, version qualifications, and
honest boundaries on what an experiment establishes. Sources support self-contained
teaching; they do not replace it. Distinguish API guarantees from our chosen
policy and from tested observations. The B0/B1 review is retained in
`docs/dev/BEGINNER_SOURCE_REVIEW.md`; the Fedora companion and numbered-module
claim/evidence map are in `docs/SOURCE_TRUTH.md`. These are scoped technical
reviews, not formal verification or proof of human learning.

End labs state functional and security properties but omit complete solutions. Graders rotate synthetic details, observe from outside the submitted program, and report the failed property. Practice diagnostics identify relevant lessons. Exam diagnostics name only the property.

AI may be used as a tutor or debugger if the learner chooses. It is never required to start, complete, or grade a lesson. The learning objective is for the student's keyboard time to build Linux/security intuition, not to operate a coding-agent workflow.

Boundary Atlas is a destination, not a prerequisite. Modules 11-12 introduce synthetic evidence, hardened counterparts, and careful interpretation of non-discovery after the learner has direct experience with the mechanisms. Module 12 distinguishes introductory hinted dispatch from independent interpretation of incomplete offline observations.

The [learning path](docs/LEARNING_PATH.md) supplies an entry diagnostic, a faded task
for each module, cumulative checkpoints, and a human-scored reasoning rubric.
The capstone uses independently limited ordered jobs, failure recovery, and
per-job collection; its kernel assertions reuse Module 10, but its batch protocol
requires transfer. Automated execution does not establish teaching effectiveness.
Use the [learner pilot protocol](docs/dev/LEARNER_PILOT.md) before making claims
about novice completion, retention, or course duration.
