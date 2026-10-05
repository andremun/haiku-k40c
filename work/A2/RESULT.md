# Task A2 — Result

## Summary
Corrected the BAR1 upper 32-bit values in the Notes section of `hardware/record.md`.

## Changes
1. **`hardware/record.md`** — Fixed the BAR1 note:
   - GPU 0: `0x20fe0000` → `0x0000020f` (from `0x0000020fe0000000` in `resource-04_00_0.txt` line 2)
   - GPU 1: `0x21fe0000` → `0x0000021f` (from `0x0000021fe0000000` in `resource-81_00_0.txt` line 2)

2. **`docs/STATUS.md`** — Set current task to A2; added "reworked 2026-10-05, review ACCEPT" to A1 row.

## Check
`make check` — 0 failures.

## Open questions
None for this task.
