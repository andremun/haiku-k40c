---
description: Start the current task from docs/STATUS.md
---
Start work on the current task.

1. Read `docs/STATUS.md`. The line `Current task:` names one task ID.
   Read `docs/tasks/<ID>.md` (not the other task files). If
   `work/<ID>/REVIEW.md` or `work/<ID>/FINDINGS.md` exists, read it next.
2. Read `docs/OPEN_QUESTIONS.md` and `docs/REQUESTS.md` only for entries
   about this task.
3. If the task is blocked by an open request, say so, pick the next
   unblocked task in the same phase, and record the change in
   `docs/STATUS.md`.
4. Write `work/<task-id>/PLAN.md`: the steps, the outputs, and how you
   will check them. Keep it under 30 lines.
5. Do the task. Follow `AGENTS.md`.
6. Run `make check` and fix failures.
7. Finish with the handoff steps of `/handoff`.

$ARGUMENTS
