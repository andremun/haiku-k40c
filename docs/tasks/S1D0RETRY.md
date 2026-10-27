# S1D0RETRY: one approved physical D0 retry

Read docs/STATUS.md, work/S1D0THREAD/RESULT.md, docs/D0-TASK-PROOF.md,
docs/D0-STAGE-REVIEW.md, ADR 006/008 and the original D0 task limits.
The user said “Go ahead” on 2026-10-28 after the failed D0 report. That authorizes
the checked observer correction and one retry. No new general approval is needed.

Write work/S1D0RETRY/PLAN.md. Check the final task/source pins and stage suite.
Verify R5 remains live with the same full filter and a real baseline control.
Run d0_run.py --check, then d0_run.py once. Its output folder is fresh and ends
in d0-mapping-retry-01. Guest artifacts and approved GPU effects remain unchanged.

Preserve all raw records, proof metadata and topology/extent cutoff evidence.
A stop consumes this go-ahead. Report and ask before any further guest run.
Do not modify and retry. Never claim a mapping observation proves payload,
coherency, native POST or S1. Keep publication denied.

Write findings, RESULT.md (max 40 lines), status and the batch review outcome.
Run make check and commit this task separately. Never push. If D0 passes, the
next task prepares native POST integration and the reviewed A7 package. A7 needs
an explicit per-run yes. Do not build D1 or more visibility machinery before A7.
