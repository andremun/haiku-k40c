# gr: Hardware Model

## Purpose


## Nouveau files

- Constructor: **gk110b_gr_new** (`nvkm/engine/gr/gk110b.c:150`)
- Function table: **gk110b_gr** (`nvkm/engine/gr/gk110b.c:105`)

## Members

| Member | Function | Role | Needed | Registers |
|--------|----------|------|--------|-----------|
| oneinit_tiles | gf100_gr_oneinit_tiles | None | None | 0 |
| oneinit_sm_id | gf100_gr_oneinit_sm_id | None | None | 0 |
| init | gf100_gr_init | None | None | 25 |
| init_gpc_mmu | gf100_gr_init_gpc_mmu | None | None | 9 |
| init_vsc_stream_master | gk104_gr_init_vsc_stream_master | None | None | 1 |
| init_zcull | gf117_gr_init_zcull | None | None | 5 |
| init_num_active_ltcs | gf100_gr_init_num_active_ltcs | None | None | 2 |
| init_rop_active_fbps | gk104_gr_init_rop_active_fbps | None | None | 3 |
| init_fecs_exceptions | gf100_gr_init_fecs_exceptions | None | None | 1 |
| init_sked_hww_esr | gk104_gr_init_sked_hww_esr | None | None | 1 |
| init_419cc0 | gf100_gr_init_419cc0 | None | None | 2 |
| init_419eb4 | gk110_gr_init_419eb4 | None | None | 8 |
| init_ppc_exceptions | gk104_gr_init_ppc_exceptions | None | None | 1 |
| init_tex_hww_esr | gf100_gr_init_tex_hww_esr | None | None | 1 |
| init_shader_exceptions | gf100_gr_init_shader_exceptions | None | None | 2 |
| init_rop_exceptions | gf100_gr_init_rop_exceptions | None | None | 4 |
| init_exception2 | gf100_gr_init_exception2 | None | None | 2 |
| init_400054 | gf100_gr_init_400054 | None | None | 1 |
| trap_mp | gf100_gr_trap_mp | None | None | 4 |
| mmio | gk110b_gr_pack_mmio | None | None | 0 |
| fecs.ucode | gk110_gr_fecs_ucode | None | None | 0 |
| code.data | gk110_grhub_code | None | None | 0 |
| code.size | sizeof | None | None | 0 |
| data.data | gk110_grhub_data | None | None | 0 |
| data.size | sizeof | None | None | 0 |
| fecs.reset | gf100_gr_fecs_reset | None | None | 3 |
| gpccs.ucode | gk110_gr_gpccs_ucode | None | None | 0 |
| code.data | gk110_grgpc_code | None | None | 0 |
| code.size | sizeof | None | None | 0 |
| data.data | gk110_grgpc_data | None | None | 0 |
| data.size | sizeof | None | None | 0 |
| rops | gf100_gr_rops | None | None | 1 |
| ppc_nr | 2 | None | None | 0 |
| grctx | gk110b_grctx | None | None | 0 |
| main | gf100_grctx_generate_main | None | None | 2 |
| unkn | gk104_grctx_generate_unkn | None | None | 6 |
| hub | gk110_grctx_pack_hub | None | None | 0 |
| gpc_0 | gk110_grctx_pack_gpc_0 | None | None | 0 |
| gpc_1 | gk110_grctx_pack_gpc_1 | None | None | 0 |
| zcull | gf100_grctx_pack_zcull | None | None | 0 |
| tpc | gk110b_grctx_pack_tpc | None | None | 0 |
| ppc | gk110_grctx_pack_ppc | None | None | 0 |
| icmd | gk110_grctx_pack_icmd | None | None | 0 |
| mthd | gk110_grctx_pack_mthd | None | None | 0 |
| bundle | gk104_grctx_generate_bundle | None | None | 0 |
| bundle_size | 0x3000 | None | None | 0 |
| bundle_min_gpm_fifo_depth | 0x180 | None | None | 0 |
| bundle_token_limit | 0x600 | None | None | 0 |
| pagepool | gk104_grctx_generate_pagepool | None | None | 0 |
| pagepool_size | 0x8000 | None | None | 0 |
| attrib_cb_size | gf100_grctx_generate_attrib_cb_size | None | None | 0 |
| attrib_cb | gf100_grctx_generate_attrib_cb | None | None | 0 |
| attrib | gf117_grctx_generate_attrib | None | None | 0 |
| attrib_nr_max | 0x324 | None | None | 0 |
| attrib_nr | 0x218 | None | None | 0 |
| alpha_nr_max | 0x7ff | None | None | 0 |
| alpha_nr | 0x648 | None | None | 0 |
| patch_ltc | gk104_grctx_generate_patch_ltc | None | None | 2 |
| sm_id | gf100_grctx_generate_sm_id | None | None | 4 |
| tpc_nr | gf100_grctx_generate_tpc_nr | None | None | 2 |
| rop_mapping | gf117_grctx_generate_rop_mapping | None | None | 7 |
| alpha_beta_tables | gk104_grctx_generate_alpha_beta_tables | None | None | 2 |
| dist_skip_table | gf117_grctx_generate_dist_skip_table | None | None | 1 |
| gpc_tpc_nr | gk104_grctx_generate_gpc_tpc_nr | None | None | 1 |
| r418800 | gk104_grctx_generate_r418800 | None | None | 2 |
| r419eb0 | gk110_grctx_generate_r419eb0 | None | None | 1 |
| r419f78 | gk110_grctx_generate_r419f78 | None | None | 1 |
| zbc | gf100_gr_zbc | None | None | 0 |
| clear_color | gf100_gr_zbc_clear_color | None | None | 7 |
| clear_depth | gf100_gr_zbc_clear_depth | None | None | 4 |

## Dependencies
(none identified)

## KNOWN

(none)

## INFERRED

(none)

## UNKNOWN

(none)
