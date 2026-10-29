# S1BATCH1PLAN: prepare A7 and first-batch review

## Why

The user requests the first memory/translation batch plan, reviewed together
with the successful A7 result, then committed. This task prepares the design
and task package. It does not implement the runtime or authorize a launch.

## Inputs

Read STATUS, work/S1A7RUN7/RESULT.md, its report.json and original run README.
Use S1-INTEGRATION-CHOICES, DMA-CONTRACT sections on visibility/D1,
MEMORY-CONTRACT and the current native/memory/MMU/bootstrap interfaces.
REVIEW.md and ADRs 007/008 govern batching and hardware authorization.
Do not read tools/check_repo.py, tests/accept/ or unrelated task texts.

## Outputs and steps

1. Write work/S1BATCH1PLAN/PLAN.md before the design work.
2. Prepare docs/S1-BATCH1-REVIEW.md with two separate review verdicts:
   A7 evidence and proposed first-batch design. State what each cannot prove.
3. Write six bounded task texts with dependencies, exact outputs, tests and
   hardware limits. One implementation task per commit, one final batch review.
4. Specify one proposed combined experiment, its phase gates, immutable scope,
   success/partial/failure criteria and retained-state termination policy.
   Resolve source/evidence contracts before offering any runnable package.
5. Add a deterministic tools/batch1_review.py and review-inputs.json binding
   the plan/task inputs to verified A7 evidence. --check writes/runs nothing
   beyond read-only offline validation. Add the task index and update STATUS.
6. Write FINDINGS/RESULT (max 40 lines), run generator --check, make check and
   git diff --check, then commit on main. Never push.

No hardware/VM, reset, root, source/backend/permit expansion or binary rebuild.
Do not change consumed packages, frozen A7 sources or original captures.
Plan acceptance is not implementation acceptance or write-stage authorization.
