# gr: Hardware Model

## Purpose
The GR engine runs the compute job on the GK110B (GR is the engine name in Nouveau; it also does 3D drawing). Two controllers inside it, FECS for the hub and GPCCS for each GPC, run the microcode of task C2. gf100_gr_init starts the engine: it sets up MMU forwarding, applies the register tables in mmio, calls the init hooks of the function table in order and enables exception reporting. For each channel a context image (grctx) is generated from tables of register writes and from the grctx functions. The zbc members keep the table of clear values. For milestone S3 the Haiku driver has to reproduce init with its hooks, the microcode load, and the generation of one context image; which hooks a compute-only driver may leave out (zcull and the two ROP hooks set up drawing units) is not established.

## Nouveau files

- Constructor: **gk110b_gr_new** (`nvkm/engine/gr/gk110b.c:150`)
- Function table: **gk110b_gr** (`nvkm/engine/gr/gk110b.c:105`)

## Members

| Member | Function | Role | Needed | Registers |
|--------|----------|------|--------|-----------|
| oneinit_tiles | gf100_gr_oneinit_tiles | init | True | 0 |
| oneinit_sm_id | gf100_gr_oneinit_sm_id | init | True | 0 |
| init | gf100_gr_init | init | True | 25 |
| init_gpc_mmu | gf100_gr_init_gpc_mmu | init | True | 9 |
| init_vsc_stream_master | gk104_gr_init_vsc_stream_master | init | True | 1 |
| init_zcull | gf117_gr_init_zcull | init | True | 5 |
| init_num_active_ltcs | gf100_gr_init_num_active_ltcs | init | True | 2 |
| init_rop_active_fbps | gk104_gr_init_rop_active_fbps | init | True | 3 |
| init_fecs_exceptions | gf100_gr_init_fecs_exceptions | init | True | 1 |
| init_sked_hww_esr | gk104_gr_init_sked_hww_esr | init | True | 1 |
| init_419cc0 | gf100_gr_init_419cc0 | init | True | 2 |
| init_419eb4 | gk110_gr_init_419eb4 | init | True | 8 |
| init_ppc_exceptions | gk104_gr_init_ppc_exceptions | init | True | 1 |
| init_tex_hww_esr | gf100_gr_init_tex_hww_esr | init | True | 1 |
| init_shader_exceptions | gf100_gr_init_shader_exceptions | init | True | 2 |
| init_rop_exceptions | gf100_gr_init_rop_exceptions | init | True | 4 |
| init_exception2 | gf100_gr_init_exception2 | init | True | 2 |
| init_400054 | gf100_gr_init_400054 | init | True | 1 |
| trap_mp | gf100_gr_trap_mp | interrupt | False | 4 |
| mmio | gk110b_gr_pack_mmio | data | True | 0 |
| fecs.ucode | gk110_gr_fecs_ucode | data | True | 0 |
| code.data | gk110_grhub_code | data | True | 0 |
| code.size | sizeof | data | True | 0 |
| data.data | gk110_grhub_data | data | True | 0 |
| data.size | sizeof | data | True | 0 |
| fecs.reset | gf100_gr_fecs_reset | init | True | 3 |
| gpccs.ucode | gk110_gr_gpccs_ucode | data | True | 0 |
| code.data | gk110_grgpc_code | data | True | 0 |
| code.size | sizeof | data | True | 0 |
| data.data | gk110_grgpc_data | data | True | 0 |
| data.size | sizeof | data | True | 0 |
| rops | gf100_gr_rops | runtime | True | 1 |
| ppc_nr | 2 | data | False | 0 |
| grctx | gk110b_grctx | data | True | 0 |
| main | gf100_grctx_generate_main | runtime | True | 2 |
| unkn | gk104_grctx_generate_unkn | runtime | True | 6 |
| hub | gk110_grctx_pack_hub | data | True | 0 |
| gpc_0 | gk110_grctx_pack_gpc_0 | data | True | 0 |
| gpc_1 | gk110_grctx_pack_gpc_1 | data | True | 0 |
| zcull | gf100_grctx_pack_zcull | data | True | 0 |
| tpc | gk110b_grctx_pack_tpc | data | True | 0 |
| ppc | gk110_grctx_pack_ppc | data | True | 0 |
| icmd | gk110_grctx_pack_icmd | data | True | 0 |
| mthd | gk110_grctx_pack_mthd | data | True | 0 |
| bundle | gk104_grctx_generate_bundle | runtime | True | 0 |
| bundle_size | 0x3000 | data | False | 0 |
| bundle_min_gpm_fifo_depth | 0x180 | data | False | 0 |
| bundle_token_limit | 0x600 | data | False | 0 |
| pagepool | gk104_grctx_generate_pagepool | runtime | True | 0 |
| pagepool_size | 0x8000 | data | False | 0 |
| attrib_cb_size | gf100_grctx_generate_attrib_cb_size | runtime | True | 0 |
| attrib_cb | gf100_grctx_generate_attrib_cb | runtime | True | 0 |
| attrib | gf117_grctx_generate_attrib | runtime | True | 0 |
| attrib_nr_max | 0x324 | data | False | 0 |
| attrib_nr | 0x218 | data | False | 0 |
| alpha_nr_max | 0x7ff | data | False | 0 |
| alpha_nr | 0x648 | data | False | 0 |
| patch_ltc | gk104_grctx_generate_patch_ltc | runtime | True | 2 |
| sm_id | gf100_grctx_generate_sm_id | runtime | True | 4 |
| tpc_nr | gf100_grctx_generate_tpc_nr | runtime | True | 2 |
| rop_mapping | gf117_grctx_generate_rop_mapping | runtime | True | 7 |
| alpha_beta_tables | gk104_grctx_generate_alpha_beta_tables | runtime | True | 2 |
| dist_skip_table | gf117_grctx_generate_dist_skip_table | runtime | True | 1 |
| gpc_tpc_nr | gk104_grctx_generate_gpc_tpc_nr | runtime | True | 1 |
| r418800 | gk104_grctx_generate_r418800 | runtime | True | 2 |
| r419eb0 | gk110_grctx_generate_r419eb0 | runtime | True | 1 |
| r419f78 | gk110_grctx_generate_r419f78 | runtime | True | 1 |
| zbc | gf100_gr_zbc | data | True | 0 |
| clear_color | gf100_gr_zbc_clear_color | runtime | True | 7 |
| clear_depth | gf100_gr_zbc_clear_depth | runtime | True | 4 |

## Dependencies
fb, ltc, mc, pmu, timer, top

## KNOWN

- **oneinit_tiles**: Computes tile-to-GPC mapping using a prime-factor distribution algorithm and sorts GPCs by TPC count (`nvkm/engine/gr/gf100.c:1913`)
- **oneinit_sm_id**: Enumerates all valid GPC-TPC pairs into the SM array and returns the total SM count (`nvkm/engine/gr/gf100.c:1895`)
- **init**: Main GR engine init: calls init_gpc_mmu, mmio setup, all sub-init hooks, then writes idle and exception registers (`nvkm/engine/gr/gf100.c:2342`)
- **init_gpc_mmu**: Reads FB MMU page-table addresses and writes them to GR MMU registers 0x418880-0x4188b8 to set up MMU forwarding (`nvkm/engine/gr/gf100.c:2264`)
- **init_vsc_stream_master**: Writes 0x00000001 to GPC register 0x3018 to enable the VSC stream master for pipeline vertex shading (`nvkm/engine/gr/gk104.c:430`)
- **init_zcull**: Computes the tile configuration from the total TPC count and writes bank and tile data to GPC registers 0x0980 to 0x3fd4 (zcull is the depth culling unit) (`nvkm/engine/gr/gf117.c:124`)
- **init_num_active_ltcs**: Reads register 0x100800 for the number of active LTCs and broadcasts it to GPC register 0x08ac (`nvkm/engine/gr/gf100.c:2280`)
- **init_rop_active_fbps**: Reads FBP count from register 0x120074 then writes it to registers 0x408850 (zrop) and 0x408958 (crop) via mask (`nvkm/engine/gr/gk104.c:406`)
- **init_fecs_exceptions**: Writes 0x000e0000 or 0x000e0001 to register 0x409c24 based on firmware presence to configure FECS exceptions (`nvkm/engine/gr/gf100.c:2257`)
- **init_sked_hww_esr**: Writes 0x40000000 to register 0x407020 to configure the scheduler hardware warning error status register (`nvkm/engine/gr/gk104.c:391`)
- **init_419cc0**: Masks bit 3 of register 0x419cc0 then loops over all GPC/TPC pairs to write 0xc0000000 to TPC register 0x48c (`nvkm/engine/gr/gf100.c:2237`)
- **init_419eb4**: Applies nvkm_mask on register 0x419eb4 to set bits 0x1000-0x8000 then clears them for a bit-toggle sequence (`nvkm/engine/gr/gk110.c:339`)
- **init_ppc_exceptions**: Loops over enabled GPC/PPC pairs and writes 0xc0000000 to PPC register 0x038 to configure PPC exception handling (`nvkm/engine/gr/gk104.c:415`)
- **init_tex_hww_esr**: Writes 0xc0000000 to TPC register 0x224 to configure the TEX hardware warning error status register (`nvkm/engine/gr/gf100.c:2223`)
- **init_shader_exceptions**: Writes to TPC registers 0x644 and 0x64c to configure shader exception masks for a GPC/TPC pair (`nvkm/engine/gr/gf100.c:2215`)
- **init_rop_exceptions**: Loops over all ROP units and writes to registers 0x144, 0x070, 0x204 and 0x208 to configure ROP exception handling (`nvkm/engine/gr/gf100.c:2201`)
- **init_exception2**: Writes 0xffffffff to registers 0x40011c and 0x400134 to enable all exception reporting in GR (`nvkm/engine/gr/gf100.c:2192`)
- **init_400054**: Writes the constant value 0x34ce3464 to register 0x400054 to configure a GR hardware setting (`nvkm/engine/gr/gf100.c:2186`)
- **trap_mp**: Reads TPC error registers 0x648 (warp) and 0x650 (global), decodes them with enum tables, logs the error, then clears 0x648 and updates 0x650 (`nvkm/engine/gr/gf100.c:1295`)
- **fecs.reset**: Writes 0x00000070 to register 0x409614 to assert FECS reset, delays 10us, sets bits 0x700 of 0x409614, then reads back (`nvkm/engine/gr/gf100.c:2466`)
- **rops**: Reads register 0x409604 and extracts bits 16:20 to return the number of active ROP units on the GPU (`nvkm/engine/gr/gf100.c:998`)
- **main**: Generates the GR context image by calling hub, gpc_0, zcull, gpc_1, tpc, ppc mmio, then pagepool, bundle, attrib, and unkn (`nvkm/engine/gr/ctxgf100.c:1342`)
- **unkn**: Writes mask operations on registers 0x418c6c, 0x41980c, 0x41be08, 0x4064c0, 0x405800 and 0x419c00 for unknown GR context setup (`nvkm/engine/gr/ctxgk104.c:894`)
- **bundle**: Generates a bundle CB with state_limit and token_limit patches based on bundle_min_gpm_fifo_depth and bundle_token_limit (`nvkm/engine/gr/ctxgk104.c:876`)
- **pagepool**: Generates a pagepool at the given address with a 0x80000000 patch to register 0x4064cc (`nvkm/engine/gr/ctxgk104.c:887`)
- **attrib_cb_size**: Returns the attrib CB size by computing 0x20 times the sum of attrib and alpha counts times TPC total (`nvkm/engine/gr/ctxgf100.c:1060`)
- **attrib_cb**: Writes the attrib CB to the given address containing method data for all registered attrib methods (`nvkm/engine/gr/ctxgf100.c:1053`)
- **attrib**: Generates attrib method entries by reading the attrib CB and populating the attrib data structures (`nvkm/engine/gr/ctxgf117.c:244`)
- **patch_ltc**: Generates LTC patch entries for the channel context to configure LTC cache behavior (`nvkm/engine/gr/ctxgk104.c:864`)
- **sm_id**: Writes the SM ID array entries to the context image for each valid GPC-TPC pairing (`nvkm/engine/gr/ctxgf100.c:1293`)
- **tpc_nr**: Writes the TPC count per GPC to the context image for each GPC in the device configuration (`nvkm/engine/gr/ctxgf100.c:1285`)
- **rop_mapping**: Generates the ROP mapping table for the context by iterating over ROP units and encoding their configuration (`nvkm/engine/gr/ctxgf117.c:198`)
- **alpha_beta_tables**: Generates alpha and beta lookup tables for the context by writing the configured table entries (`nvkm/engine/gr/ctxgk104.c:922`)
- **dist_skip_table**: Generates a distance skip table for the context based on the GPC and TPC count configuration (`nvkm/engine/gr/ctxgf117.c:188`)
- **gpc_tpc_nr**: Writes the GPC-TPC count configuration to the context image for each GPC in the system (`nvkm/engine/gr/ctxgk104.c:915`)
- **r418800**: Writes to register 0x418800 for GR context initialization with specific bit configuration (`nvkm/engine/gr/ctxgk104.c:849`)
- **r419eb0**: Writes to register 0x419eb0 for GR context setup configuring bit fields for the GK110 engine (`nvkm/engine/gr/ctxgk110.c:817`)
- **r419f78**: Writes to register 0x419f78 with FP helper invocation configuration for GR context setup (`nvkm/engine/gr/ctxgk110.c:824`)
- **clear_color**: Writes four colour data registers (0x405804-0x405810), the format register (0x405814), selects the ZBC entry (0x405820), and triggers a colour write via 0x405824 set to TRIGGER | WRITE | COLOR (`nvkm/engine/gr/gf100.c:49`)
- **clear_depth**: Writes the depth data register (0x405818), the format register (0x40581c), selects the ZBC entry (0x405820), and triggers a depth write via 0x405824 set to TRIGGER | WRITE | DEPTH (`nvkm/engine/gr/gf100.c:100`)

## INFERRED

- **mmio**: List of register-write tables (gk110b_gr_pack_mmio) that gf100_gr_init applies to the GR registers with gf100_gr_mmio before it calls the init hooks
- **fecs.ucode**: Table with the code and data arrays of the FECS microcode (the controller of the hub; FECS is not expanded in the source) (`nvkm/engine/gr/gk110.c:321`)
- **code.data**: Pointer to the FECS hub code firmware array (gk110_grhub_code)
- **code.size**: Size in bytes of the FECS hub code firmware array
- **data.data**: Pointer to the FECS hub data firmware array (gk110_grhub_data)
- **data.size**: Size in bytes of the FECS hub data firmware array
- **gpccs.ucode**: Table with the code and data arrays of the GPCCS microcode (the controller of each GPC; GPCCS is not expanded in the source) (`nvkm/engine/gr/gk110.c:331`)
- **code.data**: Pointer to the GPCCS GPC code firmware array (gk110_grgpc_code)
- **code.size**: Size in bytes of the GPCCS GPC code firmware array
- **data.data**: Pointer to the GPCCS GPC data firmware array (gk110_grgpc_data)
- **data.size**: Size in bytes of the GPCCS GPC data firmware array
- **ppc_nr**: Constant 2: the number of PPC units in each GPC on this chip (PPC is not expanded in the source)
- **grctx**: GR context function table defining all grctx sub-functions and their configuration values (`nvkm/engine/gr/ctxgk110b.c:73`)
- **hub**: Table of register writes (a pack) for the hub part, applied when the context image of a channel is generated
- **gpc_0**: Table of register writes (a pack) for the gpc_0 part, applied when the context image of a channel is generated
- **gpc_1**: Table of register writes (a pack) for the gpc_1 part, applied when the context image of a channel is generated
- **zcull**: Table of register writes (a pack) for the zcull part, applied when the context image of a channel is generated
- **tpc**: Table of register writes (a pack) for the tpc part, applied when the context image of a channel is generated
- **ppc**: Table of register writes (a pack) for the ppc part, applied when the context image of a channel is generated
- **icmd**: Table of register writes (a pack) for the icmd part, applied when the context image of a channel is generated
- **mthd**: Table of register writes (a pack) for the mthd part, applied when the context image of a channel is generated
- **bundle_size**: GR context bundle size constant set to 0x3000 bytes for GK110B channel context
- **bundle_min_gpm_fifo_depth**: GR context bundle minimum GPM FIFO depth constant set to 0x180 for GK110B
- **bundle_token_limit**: GR context bundle token limit constant set to 0x600 for GK110B channel context
- **pagepool_size**: GR context pagepool size constant set to 0x8000 bytes for GK110B channel context
- **attrib_nr_max**: GR context attrib method count maximum constant set to 0x324 for GK110
- **attrib_nr**: GR context attrib method count value set to 0x218 for GK110 channel context
- **alpha_nr_max**: GR context alpha method count maximum constant set to 0x7ff for GK110
- **alpha_nr**: GR context alpha method count value set to 0x648 for GK110 channel context
- **zbc**: Table of ZBC (clear colour and depth) configuration functions (`nvkm/engine/gr/gf100.c:145`)

## UNKNOWN

(none)
