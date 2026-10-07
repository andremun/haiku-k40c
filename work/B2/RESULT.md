# B2: Call graph — RESULT

## Done

Call graph tool (`tools/callgraph.py`) produces `analysis/callgraph.json`
(446 nodes, 704 edges after the scaffold fix of 2026-10-08, see `REVIEW.md`) and `analysis/callgraph.md` from the four scope
subsystems (fb, mmu, fifo, gr). `make check` passes with 0 failures.

## What the tool does

1. Reads all `.c` files listed in `analysis/files.json`.
2. Extracts **function definitions** (`name(args) {`) and **table
   definitions** (`name = {`, `name[] = {`, `const struct … name = {`)
   at file scope. Each gets a `(name, file, line, kind)` tuple.
3. For each function/table body, finds edges via five patterns:
   - Pattern 1: function calls (`name(`)
   - Pattern 2: address-of (`&name`)
   - Pattern 3: struct field names (`.name =`)
   - Pattern 4: struct field values (`.name = value`)
   - Pattern 5: function call arguments (identifiers inside `()`)
4. Filters to nodes reachable from the four roots via BFS.
5. Outputs deterministic JSON + markdown.

## Three bugs fixed during development

1. **Array table definitions not extracted**: `gk110b_gr_fwif[] = {` didn't
   match the simple form regex. Fixed by adding `(?:\[[^\]]*\])?` to the
   simple form pattern.

2. **Struct field values not extracted**: `.init = gf100_fb_init` extracted
   only the field name `init`, not the value `gf100_fb_init`. Added Pattern 4
   (`\.\w+\s*=\s*(?:&|)(\w+)\b`) to extract the value after `=`.

3. **Function call arguments not extracted**: identifiers passed as arguments
   to functions were not captured. Added Pattern 5 (parse identifiers inside
   `()`) to extract them.

## Paths from roots to required init functions

- **gk110_fb_new → gk110_fb → gf100_fb_init** (Pattern 4: `.init = gf100_fb_init`)
- **gk110_fifo_new → gk110_fifo → gk104_fifo_init** (Pattern 4: `.init = gk104_fifo_init`)
- **gk110b_gr_new → gk110b_gr_fwif → gk110b_gr → gf100_gr_init** (Pattern 5: `gk110b_gr_fwif` as argument, Pattern 4: `.init = gf100_gr_init`)
- **gk110b_gr_new → gf100_gr_new_ → gf100_gr_ → gf100_gr_chsw_load → gf100_gr → gf100_gr_init** (chained function calls)

## Open questions

- Should the tool also extract edges from `.name = &func` patterns where
  the `&` prefix is explicit? Pattern 4 handles this via `(?:&|)`.
- The GR path goes through `gk110b_gr_fwif` (an array table) which is
  itself a function argument to `gf100_gr_new_`. This double-reference
  (array → table → function) is unusual but correct — Nouveau uses
  firmware interface arrays as indirect references.
