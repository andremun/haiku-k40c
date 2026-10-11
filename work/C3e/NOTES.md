# C3e notes

Start: tools/hwmodel.py lists gr; analysis/hwmodel/gr.json is generated (70 members) with no decisions yet.

## Part 1 (2026-10-12)
14 members decided: zbc (3), fecs.ucode (4), gpccs.ucode (4), mmio (1).
- `zbc` (table, INFERRED): container for ZBC clear functions
- `zbc.clear_color` (function, runtime, KNOWN): writes 7 registers to set a clear colour value and trigger it (TRIGGER|WRITE|COLOR)
- `zbc.clear_depth` (function, runtime, KNOWN): writes 4 registers to set a clear depth value and trigger it (TRIGGER|WRITE|DEPTH)
- `fecs.ucode` (table, INFERRED): FECS firmware container
- `fecs.ucode.code.data` / `.size` / `data.data` / `.size` (values, INFERRED): FECS hub firmware blob
- `gpccs.ucode` (table, INFERRED): GPCCS firmware container
- `gpccs.ucode.code.data` / `.size` / `data.data` / `.size` (values, INFERRED): GPCCS GPC firmware blob
- `mmio` (table, INFERRED): init function pointers packed into GR context image for register setup
All 56 remaining members have no decisions yet (expected). `make check` passes for the 14 decided members.

## Part 2 (2026-10-12)
18 members: hooks and runtime functions. All evidence lines verified against source.
`make check` passes for all 32 members.

## Part 3 (2026-10-12)
6 members: oneinit_tiles, oneinit_sm_id, init, ppc_nr, grctx table, grctx sub-table.
`make check` passes for all 38 members.

## Part 4 (2026-10-12)
17 grctx function members added. Initial batch had 6 evidence failures.
`make check` passes for all 55 members.

## Part 5 (2026-10-12)
16 grctx value/pointer entries + 3 grctx function fixes (attrib_cb, attrib, attrib_cb_size).
`make check` passes for all 71 members.

## Final cleanup (2026-10-12)
Fixed 9 remaining evidence failures (attrib_cb_size, patch_ltc, rop_mapping, alpha_beta_tables, dist_skip_table, gpc_tpc_nr, r418800, r419eb0, r419f78).
Root causes: wrong line numbers (pointing to comments/closing braces), wrong source functions, wrong quotes.
All 70 members now pass `make check`. Task complete.

