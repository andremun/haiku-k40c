# Plan D6 (second start): qmd_compare.py tool

## Steps

1. **Parse the header**: Open `cla0c0qmd.h`, extract lines starting with `#define NVA0C0_QMDV00_06_`.
   - MW lines → field dict: `name -> "HI:LO" text`
   - Non-MW lines → named values dict: `name -> int value`
   - Print counts for verification.

2. **Read words + reference**: Run `build/tests/ref_qmd --words`, read the 64 hex words.
   Read `analysis/linux_run_shader.json` "qmd" array.
   For each reference entry: resolve name→HI:LO, substitute index `(i)` in the text,
   evaluate HI and LO, extract bits from our words, compare with reference value.
   Handle named values (TRUE/FALSE, hex, etc.).

3. **Write output files**: `analysis/qmd_compare.json` and `analysis/qmd_compare.md`.
   Support `--check` mode (write nothing, exit 0 if files match).

## Checks
- Step 1 prints ~113 fields, ~76 named values.
- Step 2 computes all 155 reference fields.
- Step 3 writes both files; `--check` passes twice.
