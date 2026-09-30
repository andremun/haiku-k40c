---
description: Close the current task and hand off to the next session
---
Close the current task.

1. Run `make check`. If it fails, report the failures. Do not mark the
   task done.
2. Write `work/<task-id>/RESULT.md` (max 40 lines): what exists now, check
   results, what is KNOWN, INFERRED and UNKNOWN, and what the next task
   needs from this one.
3. Add new questions to `docs/OPEN_QUESTIONS.md` and new root or install
   needs to `docs/REQUESTS.md`.
4. Update `docs/STATUS.md`: current task (next one if this one is done),
   last result, one row in the task log.
5. Commit: `git add -A && git commit -m "<task-id>: <summary>"`.
6. Report in 5 lines or fewer: done or not done, and why.
