# B2 REWORK: Determinism + other-chip section — PLAN

## Defects to fix (from work/B2/REVIEW.md)

1. **Non-deterministic output**: `scope_dirs()` returns a `set()` and the
   BFS adjacency dict has unsorted sets. This makes JSON node order vary
   between runs. Fix: sort every set before iteration.

2. **Missing "other chip" section**: `analysis/callgraph.md` must report,
   for each subsystem (fb, mmu, fifo, gr), which calls go to other-chip
   files (nv04, nv50, gf108, etc.). The tool writes this.

3. **RESULT.md says "deterministic"**: correct it only after `--check`
   passes twice.

## Steps

1. Fix `callgraph.py`:
   a. `scope_dirs()`: convert set to sorted list.
   b. BFS `todo`: use sorted list from set.
   c. Write "other chip" section in markdown generation.
2. Regenerate `analysis/callgraph.json` and `analysis/callgraph.md`.
3. Run `make check` — fix any failures.
4. Update `work/B2/RESULT.md`.
5. Handoff.
