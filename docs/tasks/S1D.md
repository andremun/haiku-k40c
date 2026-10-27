# Task S1D: Incorporate the board-operation decisions

## Why

ADR 004 records the user decisions. Current S1 documents still describe them
as pending. Make those documents consistent before the policy implementation.

## Inputs

Read docs/decisions/004-board-operations-and-review.md, docs/BOARD-OPERATIONS.md,
docs/S1-PLAN.md, docs/STATUS.md, AGENTS.md, and REVIEW.md.

## Definitions

Allow applies only to the ROM and observed operations in ADR 004.
Every card stage still requires the user's go-ahead.
No further outside review is required. Host implementation review remains.

## Outputs

Incorporate ADR 004. Update docs/BOARD-OPERATIONS.md, docs/S1-PLAN.md,
and docs/STATUS.md. Write work/S1D/PLAN.md, FINDINGS.md, and RESULT.md.
Do not change code, hardware state, tests, or the user's decisions.

## Procedure

1. Incorporate the existing decision commit.
2. Replace pending-decision statements with ADR 004 references.
3. Run make check and inspect the diff.
4. Commit for review. Do not push or merge.

## Check

make check and git diff --check must pass.
The documents must preserve the ROM restriction, default denial, and card-stage gate.
