# C3e Plan: GR engine subsystem model

## Structure
70 members: 26 main table, 44 nested (fecs.ucode 4, gpccs.ucode 4, grctx 34, zbc 2).
Decisions file: `analysis/hwmodel/decisions/gr.json`. Work in 5 parts.

## Part 1 (this session start)
Members: `zbc.clear_color`, `zbc.clear_depth`, `fecs.ucode.code.data`, `fecs.ucode.code.size`,
`fecs.ucode.data.data`, `fecs.ucode.data.size`, `gpccs.ucode.code.data`, `gpccs.ucode.code.size`,
`gpccs.ucode.data.data`, `gpccs.ucode.data.size`.
10 members. 6 functions (zbc, fecs.reset, gpccs.ucode members), 4 values (sizes).
Values need no evidence. Functions: read source, write what/certainty/evidence.

## Part 2
Hooks: `init_gpc_mmu`…`init_400054` (12 hooks), `trap_mp`, `fecs.reset`, `rops`.
15 functions.

## Part 3
Main table remaining: `init`, `oneinit_tiles`, `oneinit_sm_id`, `mmio`, `ppc_nr`.
5 members.

## Part 4
grctx functions: `main`, `unkn`, `hub`, `gpc_0`, `gpc_1`, `zcull`, `tpc`, `ppc`,
`icmd`, `mthd`, `bundle`, `pagepool`, `attrib_cb_size`, `attrib_cb`, `attrib`,
`patch_ltc`, `sm_id`, `tpc_nr`, `rop_mapping`, `alpha_beta_tables`, `dist_skip_table`,
`gpc_tpc_nr`, `r418800`, `r419eb0`, `r419f78`. 25 functions.

## Part 5
grctx values: `bundle_size`, `bundle_min_gpm_fifo_depth`, `bundle_token_limit`,
`pagepool_size`, `attrib_nr_max`, `attrib_nr`, `alpha_nr_max`, `alpha_nr`. 8 values.

## After each part
Run `python3 tools/hwmodel.py && make check`, commit ("C3e: part N"), update NOTES.md.
