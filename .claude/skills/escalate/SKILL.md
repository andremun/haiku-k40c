---
name: escalate
description: Stop the current task of this repository and write an escalation for a human decision.
---
Write `escalations/ESC-NNN.md` (next free number) with:

- Objective
- Observed behavior
- Evidence (file:line, capture files, command output)
- Approaches tried (each one, and why it failed)
- Relevant source locations
- Hypothesis (label KNOWN, INFERRED or UNKNOWN)
- Exact decision required from the user

Add a line to `docs/STATUS.md` that the task is blocked by ESC-NNN.
Commit, then stop work on this task.
