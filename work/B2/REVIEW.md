# B2: review (2026-10-08, commit 036da4d) — REWORK (small)

Reviewer: Claude (Anthropic), at the user's request. A `/review` session
of the local model (2026-10-07, 112 minutes) gave ACCEPT with no defects.
It reported the `--check` option as present and did not run it.

## Accepted

- The graph: 447 nodes (369 functions, 78 tables) and 708 edges from the
  four roots. `gf100_gr_init`, `gf100_fb_init` and `gk104_fifo_init` are
  reached through their tables (`gk110b_gr`, `gk110_fb`, `gk110_fifo`).
  No node belongs to a later chip.
- The table handling (array tables, field values) is the right fix.

## Defects

| File | Problem | Evidence | Severity |
|---|---|---|---|
| `tools/callgraph.py` | The output is not the same on every run. `work/B2/RESULT.md` says "deterministic". | `python3 tools/callgraph.py --check` exits 1 on the committed files, three times of three. A run without `--check` changes 4 lines in `analysis/callgraph.json` and `analysis/callgraph.md`: the node and edge sets are equal, the order differs. | Medium |
| `analysis/callgraph.md` | The task asks, for each of fb, mmu, fifo and gr, which calls are only for other chips, or a statement that a graph of names cannot tell. The file has neither. | No line of the file has "other chip" or "cannot tell". The graph has nodes from `nv04.c`, `nv50.c` and `gf108.c` files: say for each subsystem whether the GK110B path uses them or the graph only reaches them by name. | Medium |

## What the rework needs

1. Find the place where the order depends on a set or a dictionary of
   sets, and sort it. Do not change the nodes or the edges.
2. `make check` now runs `tools/callgraph.py --check` twice. It must pass.
3. Add the section on other-chip calls to `analysis/callgraph.md` (the tool writes it).
4. Correct "deterministic" in `work/B2/RESULT.md` only after step 2 passes.
5. Handoff, stop. This is a short task.
