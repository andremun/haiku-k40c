# C5b Notes

## Step 1: Bars & Maps ✓
Parsed PCIDEV (10de1024) → 3 BARs (0, 1, 3). MAP/UNMAP → 27 mappings.

## Step 2: Marks & Phases ✓
2 MARK lines at lines 573420 and 901168. Phases:
- load: 11–573419 (52084 r, 156004 w bar0)
- job: 573421–901167 (1648 r, 5783 w bar0)
- after: 901169–901370 (122 r, 80 w bar0)

## Step 3: Registers & Runs ✓
1086 unique job-phase BAR 0 registers (142 unnamed).
509 runs (consecutive same-domain sequences).
16 domains.

## Step 4: JSON ✓
Written to `analysis/linux_run_trace.json`.

## Step 5: Markdown ✓
Written to `analysis/linux_run_trace.md`. Fixed: registers listed as `0x......` (with prefix), not stripped.

## Step 6: --check ✓
Passes twice.

## Step 7: make check ✓
0 failures.
