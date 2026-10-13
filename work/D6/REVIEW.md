# Review D6, first session (scaffold, 2026-10-13): REWORK of the tool

Kept: `tests/ref_qmd.cpp` and the entry in `tests/Makefile` (10 checks,
all pass). The words that it prints are correct.

Not kept: `tools/qmd_compare.py` and its two output files. The tool had
173 typed lines like `("QMD_RESERVED_B", 208, 204)` in place of code
that reads the header. 60 of the 155 rows had wrong bits (the header
says `MW(207:204)` for that field). The session then corrected one row
for each run of `make check`, which cannot end.

What to do: the task text now says it. The tool opens
`reference/mesa/src/gallium/drivers/nouveau/nvc0/cla0c0qmd.h` when it
runs and takes the bits from the `#define NVA0C0_QMDV00_06_` lines. No
table in the tool. `make check` reports a typed table as a failure.

## Second session (2026-10-13): ACCEPT

26 minutes. The tool reads the header when it runs, has no table, and
its 155 rows are equal to the reviewer's computation. Result: with the
parameters of the reference job, `src/compute/LaunchDesc.cpp` builds the
same descriptor, field by field, that Mesa sent to the K40c. This is the
first driver code verified against the card. The session did not read
the checker.
