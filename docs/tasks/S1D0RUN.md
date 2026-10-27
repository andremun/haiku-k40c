# Macro task S1D0RUN: observe one physical mapping stage

Read docs/STATUS.md, docs/D0-STAGE-REVIEW.md, work/S1D0PACKAGE/RESULT.md,
docs/DMA-CONTRACT.md (D0) and ADR 006/008. Check the concrete package and
self-review. General hardware approval is already supplied by ADR 008.

Prerequisite: the human-started R5 kernel journal stream must exist and remain
live. Never run root or bypass the missing baseline. Check no QEMU guest is
running. Do not stop another guest without asking.

Write work/S1D0RUN/PLAN.md. Run tools/haiku/d0_stage.py --check and the closed
D0 launcher --check before the physical launcher. Run the physical stage once.
Preserve all raw evidence and record exact sources, artifacts and command.
After a launcher-reported stop, report and ask before another guest run.
Do not modify and retry, including after a parser false alarm.

A pass proves structural mapping coverage at its recorded cutoff only. Keep
publication denied. It does not close Q7, verify payload, or satisfy S1.
Study the result before defining the next source-backed physical transaction.

Update findings, status and the review document. Write RESULT.md (max 40 lines),
run make check, and commit this task separately. Never push.
