---
description: Review the last finished task (or the task you name)
agent: review
---
Task to review: $ARGUMENTS

If no task is named above, review the LAST ROW of the task log in
`docs/STATUS.md`. That is the task that was just finished. Do not review
"Current task": it has not started, and it has no outputs.

Steps, in this order. Do not add steps.

1. Run `make check`. Report its result. Everything it verifies is settled
   (see the list in your instructions). Do not verify it again.
2. Read `docs/tasks/<task-id>.md` and list its outputs. For
   each output: does the file exist? If none exist, say so in one line
   and stop.
3. Read the outputs and `work/<task-id>/RESULT.md`. Check only:
   - every field or section that the task file asks for is present;
   - each KNOWN label has a source that says exactly that (open the cited
     file and line); otherwise it is INFERRED;
   - the outputs agree with each other (for example `.json` and `.md`);
   - `docs/STATUS.md` and the task log match what exists, and the work is
     committed (`git status --short`).
4. Report a table: file, problem, evidence, severity. Then one line:
   ACCEPT or REWORK. If you find no defect, say ACCEPT. Do not search for
   more.

Do not edit files. Do not plan or start the next task.
