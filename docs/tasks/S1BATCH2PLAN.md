# S1BATCH2PLAN: prepare the channel/scheduler/NOP batch

## Why and inputs

Batch 1 passed the finite A7/BAR1 experiment. Prepare its result and the next
S1 design for Claude review. Read STATUS, S1BATCH1RUN/RESULT and its report,
S1-BATCH1-RUN-REVIEW, S1-BATCH1-REVIEW's second-batch boundary, and S1-PLAN's
S1 definition. Read selected channel/routing/teardown sections of
S1-INTEGRATION-CHOICES, S1-RECIPE and S1-MEMORY-CONTRACT. Follow only the
selected pinned GK110 FIFO/GK104 VMM paths and relevant current interfaces.
Do not read tools/check_repo.py, tests/accept/ or unrelated task files.

## Outputs and work

1. Write work/S1BATCH2PLAN/PLAN.md before detailed work.
2. Write docs/S1-BATCH2-REVIEW.md with separate verdicts for batch-1 evidence
   and batch-2 design. Define source gates, object domains, writes, diagnostics,
   budgets, closure, S1 acceptance and exclusions.
3. Write six bounded implementation tasks, one future commit per task.
4. Add a deterministic tools/batch2_review.py with no-write --check. Bind exact
   plan/task/source inputs to the verified batch-1 capture. Label SOURCE_ONLY
   plans separately from HARDWARE_VERIFIED observations.
5. Record findings, source consultations, STATUS and RESULT (at most 40 lines).

## Checks and boundary

Reproduce batch1_result.py --check, batch2_review.py --check and make check.
Commit on main, never push. No runtime, build package, VM or hardware change.
The next runnable package requires implementation, exact cardless rehearsal,
Claude review and a new explicit user yes. No prior approval carries forward.
