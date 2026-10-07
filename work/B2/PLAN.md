# B2: Call graph — PLAN

## Objective
Build a call graph from the four chipset constructors (fb, mmu, fifo, gr) through
their init paths. Output JSON (`analysis/callgraph.json`) and markdown
(`analysis/callgraph.md`).

## Scope
Only files listed in `analysis/files.json`. Four roots:
- `gk110_fb_new` → `gk110_fb` table → functions/tables it names
- `gk104_mmu_new` → `gk104_mmu` table → functions/tables it names
- `gk110_fifo_new` → `gk110_fifo` table → functions/tables it names
- `gk110b_gr_new` → `gk110b_gr` table → functions/tables it names

## Approach
1. Read all `.c` files in the four scope directories.
2. Extract **function definitions** (`name(args) {`) and **table definitions**
   (`name = {` or `name[] = {` or `const struct … name = {`). Record
   `(name, file, line_number)`.
3. For each function body, find every identifier that is also a node name → edge.
4. For each table body (lines between `name = {` and closing `}`), find every
   identifier after `.` that is a node name → edge.
5. Nodes get optional `"kind"`: `"function"` or `"table"`.
6. Sort all sets before use for determinism.

## Outputs
- `tools/callgraph.py` — the tool (with `--check` mode)
- `analysis/callgraph.json` — graph JSON
- `analysis/callgraph.md` — readable per-subsystem paths

## Verification
`make check` validates: every node's `file:line` defines that name; the four
roots are nodes; every edge joins two nodes; caller body uses callee; every node
is reached from a root; `gf100_gr_init`, `gf100_fb_init`, `gk104_fifo_init` are
nodes.
