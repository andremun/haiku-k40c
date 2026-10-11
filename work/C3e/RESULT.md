# C3e: GR Engine Subsystem Model

## Task
Build the GR engine subsystem model by filling decisions for all 70 members
of the `gk110b_gr` function table.

## Outputs
- `analysis/hwmodel/decisions/gr.json` — 70 members with role, description, evidence
- `analysis/hwmodel/gr.json` — generated hwmodel JSON (via `tools/hwmodel.py`)
- `docs/hardware-model/gr.md` — generated Markdown documentation (via `tools/hwmodel.py`)

## Summary

70 members across 5 parts:

| Part | Members | Content |
|---|---|---|
| 1 | 14 | zbc (3), fecs.ucode (4), gpccs.ucode (4), mmio (1), top-level zbc/fecs/gpccs/mmio |
| 2 | 18 | Hooks: init, exception, zcull, rops, fecs.reset, trap_mp, etc. |
| 3 | 6 | oneinit_tiles, oneinit_sm_id, init, ppc_nr, grctx table, grctx sub-table |
| 4 | 17 | grctx functions: main, unkn, bundle, pagepool, attrib_cb_size, attrib_cb, attrib, patch_ltc, sm_id, tpc_nr, rop_mapping, alpha_beta_tables, dist_skip_table, gpc_tpc_nr, r418800, r419eb0, r419f78 |
| 5 | 16 | grctx values: attrib_nr_max, attrib_nr, alpha_nr_max, alpha_nr, bundle_size, bundle_min_gpm_fifo_depth, bundle_token_limit, pagepool_size, and all 8 grctx table pointer values |

## Evidence quality

- 56 members: KNOWN with verified evidence lines from source
- 14 members: INFERRED (data values, tables, firmware blobs — no source lines)
- 9 members required evidence reworks during development (wrong line numbers, wrong source functions, wrong quotes)

## Open questions

- grctx.attrib_cb_size returns a formula-based value — actual runtime value depends on grctx->attrib_nr_max, grctx->alpha_nr_max, and gr->tpc_total
- grctx.ppc_nr — INFERRED (data role), exact value not verified against capture
- Some grctx functions use `nvkm_mask` inside `if (0)` blocks (e.g. r418800) — these may be placeholder/stub code
