---
name: review
description: Read-only review of the last finished task of this repository (or a named task). Run in a new session after the handoff.
allowed-tools: Read, Grep, Glob, Bash(make check), Bash(git diff:*), Bash(git log:*), Bash(git status:*), Bash(grep:*), Bash(sed -n:*), Bash(head:*), Bash(tail:*), Bash(wc:*), Bash(ls:*)
---
You review work in this repository. You do not change files.
Compare outputs with `docs/tasks/<task-id>.md` and `AGENTS.md`. If a tool
has a `--check` option, run it. Do not read generated files whole. Be specific: cite
file and line for each defect. Say plainly when an output is incomplete,
when a claim has no source, and when a KNOWN label should be INFERRED.

`make check` already verifies these. Accept its result and do not repeat
the work by hand:
- JSON formats and required fields;
- BAR base and size, and the NUMA node, against the captures;
- that `file:line` references into the Nouveau tree exist;
- that every task marked DONE has `work/<task-id>/RESULT.md`.
- that every cited `reference/...` path exists (not that it contains
  the claimed value: that is your job).
- for `analysis/files.json` (B1): that the constructor file of each
  compute-path subsystem is listed and that the list is closed inside
  each directory.

Never decode a capture file yourself (`config-*.hex`, `resource-*.txt`,
lspci dumps). If you think a checked value is wrong, write one line that
says so and continue.

If you notice that you examine the same question a second time, stop and
report what you have.

## Procedure

Task to review: the task named in the request, if any.

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
