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

# Third review (2026-10-08, after a 2-hour rework session with no commit)

Reviewer: Claude (Anthropic). The session changed `tools/callgraph.py`
and stopped at the time limit. Its changes are in the working tree.

## Findings

- The order problem is fixed by the uncommitted change (the sorted
  `todo.extend` in `build_graph`). Three runs with different
  `PYTHONHASHSEED` values give the same two output files.
- `--check` still fails, and it would fail for a correct tool. The cause
  is in `main()`: `if existing != graph`. `existing` comes from
  `json.load`, so its edges are lists. `graph["edges"]` holds tuples. A
  list is never equal to a tuple in Python, so the comparison is always
  unequal. Evidence: `json.loads(json.dumps(graph)) == existing` is True.
- `--check` compares only the JSON file. The task asks for both files.
- The other-chip section of `analysis/callgraph.md` is still missing.

## What the rework needs

1. In `--check`, compare the text that the tool would write with the
   text of each file (`analysis/callgraph.json` and
   `analysis/callgraph.md`). Build the text once, in one function, and
   use it for both writing and checking.
2. Add the other-chip section to `analysis/callgraph.md`.
3. Run the tool, then `make check`. Correct `work/B2/RESULT.md`.
4. Handoff, stop. Do not look for other causes: the two above are the
   whole problem.

# Resolution (2026-10-08): fixed by the scaffold, B2 accepted

A third rework session (75 minutes) ended with no change. The user's rule
of 2026-10-08 applies: when an attempt fails with negligible, diagnosed
errors, the scaffold fixes them and passes the task. Claude made these
changes to `tools/callgraph.py`:

- `render()` builds the text of both output files once. `--check`
  compares that text with the files. The old comparison of a loaded JSON
  object with the graph in memory could never succeed.
- A section "Code for other chips" in `analysis/callgraph.md`: nodes per
  subsystem and file class, and the statement that a graph of names
  cannot tell which nodes the card runs.
- The scan reads only the files of `analysis/files.json`. Two nodes came
  from other files (`hdr` in `gr/gm200.c`, `ramxlat` in `fb/gddr3.c`).

Result: 446 nodes and 704 edges (was 447 and 708). `--check` passes
with three hash seeds. `make check` passes.

History note: the agent's own fix of the output order (the sorted
`todo.extend` in `build_graph`) and its regenerated outputs entered the
repository in commit d66d3ec, whose message names only the B6 checker.
That commit swept in the agent's uncommitted work by mistake of the
scaffold. The graph, the table handling and the order fix are the
agent's work.
