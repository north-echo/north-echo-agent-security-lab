# Course design

North Echo borrows the useful rhythm of an RHCSA/RH199 lab course: exact commands, immediate observation, a short explanation at the point it matters, repetition, and an independent practical. It minimizes lectures and does not make AI part of the student's execution path.

Every guided lesson follows this loop:

1. Run an exact command or compile a small program.
2. Read a line-by-line explanation of the command, its important flags, and its shell syntax.
3. Predict and observe a kernel-visible fact.
4. Read the security explanation immediately after the observation.
5. Trigger an intentional failure or incomplete control.
6. Correct it with an interface already in view.
7. Verify resulting state rather than trusting command intent.

Line-by-line commentary is intentionally local: it follows the block it explains instead of becoming a detached glossary. It explains mechanics and security meaning without turning an independent practical into a solution transcript.

End labs state functional and security properties but omit complete solutions. Graders rotate synthetic details, observe from outside the submitted program, and report the failed property. Practice diagnostics identify relevant lessons. Exam diagnostics name only the property.

AI may be used as a tutor or debugger if the learner chooses. It is never required to start, complete, or grade a lesson. The learning objective is for the student's keyboard time to build Linux/security intuition, not to operate a coding-agent workflow.

Boundary Atlas is a destination, not a prerequisite. Modules 11-12 will introduce non-agent probes, seeded weaknesses, hardened counterparts, and careful interpretation of non-discovery only after the learner has direct experience with the mechanisms.
