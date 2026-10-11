# Task C1 Result: Register database

## Outputs
- `tools/build_regdb.py` — generates all YAML files + README.md, supports `--check`
- 14 YAML files in `hardware/registers/`: bar, bus, ce, fb, fifo, gr, imem, ltc, mc, mmu, pbdma, pci, privring, top
- `hardware/registers/README.md` — summary table + "Not named" sections for mc, fb, fifo, pbdma

## Summary
- 462 distinct registers across 14 groups
- 253 named (found in envytools rnndb), 209 unnamed
- 52 registers with no computable address (variable expressions)
- All status: SOURCE_ONLY

## Bugs found during dev
1. `calc_address` did macro argument substitution: replaced param names with 0 directly
   instead of first substituting `(param)` → `(arg)` then replacing remaining vars with 0.
   Fixed by matching `check_repo.py`'s `c1_address()` exactly.
2. Source list had duplicates when B3 had multiple entries on the same file:line.
   Fixed by deduplicating with `set()` before sorting.
3. `write_readme` was missing `return lines`, returning None instead of the list.
4. README.md in directory confused `--check` file comparison. Fixed by filtering `.yaml` suffix.

## Open questions
- None.
