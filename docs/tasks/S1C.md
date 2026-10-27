# Task S1C: Correct the S1 board evidence and work roles

## Why

The VGA explanation incorrectly attributes card MMIO accesses to QEMU legacy
port routing. The S1 plan still assigns work to the retired local agent.
This task corrects those documents. It grants no hardware permission.

## Inputs

- `AGENTS.md`, `REVIEW.md`, and `docs/STATUS.md`.
- `docs/BOARD-OPERATIONS.md` and `docs/S1-PLAN.md`.
- `reference/nouveau/nvkm/engine/disp/vga.c:27-52`.
- `reference/nouveau/nvkm/subdev/bios/init.c:1623-1656`.
- `reference/linux-run-debug/mmiotrace.txt.xz`, lines 45579-45598 and 46468-46469.

## Facts and definitions

KNOWN means the source or capture directly states the fact.
TRACE_VERIFIED requires a matching capture. Necessity remains UNKNOWN.
Codex implements host tasks. Claude Code reviews. The user decides board
policy, outside review, and every card stage.

## Outputs

- Correct the VGA explanation and decision 4 in `docs/BOARD-OPERATIONS.md`.
- Update the next steps and track roles in `docs/S1-PLAN.md`.
- Record consulted Nouveau files in `docs/licensing.md`.
- Write `work/S1C/PLAN.md`, `FINDINGS.md`, and `RESULT.md`.
- Update `docs/STATUS.md` for the handoff.

## Procedure

1. Check the pinned source and the specified capture lines.
2. Correct the documents without choosing board policy.
3. Run `make check` and inspect the diff.
4. Commit the task for Claude Code review. Do not push or merge.

## Check

`make check` must pass. Review the source citations and current work roles.
Do not change code, generated data, acceptance checks, or hardware state.
