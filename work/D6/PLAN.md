# Plan: D6 — Launch descriptor against the reference run

## Step 1: `tests/ref_qmd.cpp` + Makefile
- Build a `ComputeJob` matching the reference run (codeOffset=0x7f100, grid={16,1,1}, block={64,1,1}, sharedMemSize=0, localMemLow=0, numGprs=5, numBarriers=0).
- Call `buildQmd`, then `setConstantBuffer(q, 7, 0x510000, 0x800)`.
- With `--words`: print 64 words, 8 hex digits each.
- Without `--words`: check `words()[8] == 0x7f100`, print `ref_qmd: N checks, 0 failures`.
- Add `ref_qmd:compute+fifo` to `CXX_TESTS` in `tests/Makefile`.

## Step 2: `tools/qmd_compare.py`
- Run `make -s -C tests` if `build/tests/ref_qmd` missing.
- Run `build/tests/ref_qmd --words`, read header for field bit positions.
- Parse `analysis/linux_run_shader.json` `"qmd"` array.
- For each field: extract bits from our words, compare with reference.
- Write `analysis/qmd_compare.json` and `analysis/qmd_compare.md`.
- `--check` mode: compare generated files, exit 0/1.

## Step 3: `make check`, fix failures, handoff.
