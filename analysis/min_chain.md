# Minimum Chain to One Compute Job (GK110 / K40c)

## Subsystem classification

**Needed** (11): bar, fb, fifo, gr, imem, ltc, mc, mmu, privring, timer, top
**Optional** (16): bios, bus, ce, clk, devinit, dma, fuse, gpio, i2c, iccsense, mxm, pci, pmu, sw, therm, volt
**Not needed** (4): disp, mspdec, msppp, msvld

## Steps: PCI mapping to compute launch

1. **bar (partly-known)** — Map PCI BAR regions and read VBIOS for GPU identification
   Functions: gf100_bar_new at `nouveau/nvkm/subdev/bar/gf100.c:192.
   Notes: Only the constructor gf100_bar_new is traced; init function not in call graph.

2. **fb (known)** — Initialize framebuffer layer including memory layout and page tables
   Functions: gk110_fb_new at `nouveau/nvkm/subdev/fb/gk110.c:69, gf100_fb_init at `nouveau/nvkm/subdev/fb/gf100.c:87.

3. **mc (partly-known)** — Master control provides engine enable bits and interrupt configuration
   Functions: gk104_mc_new at `nouveau/nvkm/subdev/mc/gk104.c:63.
   Notes: Only the constructor gk104_mc_new is traced; init function not in call graph.

4. **imem (partly-known)** — Instance memory provides GPU objects such as page tables and RAMFC structures
   Functions: nv50_instmem_new at `nouveau/nvkm/subdev/instmem/nv50.c:436.
   Notes: Only the constructor nv50_instmem_new is traced; init function not in call graph.

5. **mmu (known)** — Set up memory management unit for address translation
   Functions: gk104_mmu_new at `nouveau/nvkm/subdev/mmu/gk104.c:38, nvkm_mmu_init at `nouveau/nvkm/subdev/mmu/base.c:389.

6. **top (partly-known)** — Device topology table lists engines and their runlists for FIFO access
   Notes: Topology initialized early; gk104_fifo_init reads device->top at fifo/gk104.c:764.

7. **fifo (known)** — Initialize FIFO engine for command submission and context switching
   Functions: gk110_fifo_new at `nouveau/nvkm/engine/fifo/gk110.c:128, gk104_fifo_init at `nouveau/nvkm/engine/fifo/gk104.c:744.
   Registers: 3 MMIO accesses (0x002254, 0x002100, 0x002140).

8. **ltc (partly-known)** — LTC layer provides zbc color and depth configuration for the GR engine
   Notes: LTC initialized before GR; called from gr/gf100.c:94 for zbc color configuration.

9. **timer (partly-known)** — Timer subdev provides polling delays for GR firmware initialization waits
   Notes: Timer used by every nvkm_msec call at gr/gf100.c:758 during GR init.

10. **privring (partly-known)** — PRI ring provides the register bus to GR units for interrupt and error handling
   Notes: Privring initialized before GR; register bus to engines at privring/gf100.c.

11. **gr (known)** — Initialize graphics and compute engine with firmware and exception handlers
   Functions: gk110b_gr_new at `nouveau/nvkm/engine/gr/gk110b.c:150, gf100_gr_init at `nouveau/nvkm/engine/gr/gf100.c:2342, gf100_gr_init_ctxctl_int at `nouveau/nvkm/engine/gr/gf100.c:1831.
   Registers: 29 MMIO accesses (0x40910c, 0x409100, 0x409800, 0x409804, 0x400500... ).

12. **channel (partly-known)** — Create channel address space with RAMFC write and runlist commit
   Functions: gk104_chan_ramfc_write at `nouveau/nvkm/engine/fifo/gk104.c:82, gk104_runl_commit at `nouveau/nvkm/engine/fifo/gk104.c:430.
   Registers: 2 MMIO accesses (0x002270, 0x002274).
   Notes: Channel creation traced; full command buffer submission not fully traced.

13. **channel (partly-known)** — Create GR context for the channel including GPU object generation
   Functions: gf100_gr_chan_new at `nouveau/nvkm/engine/gr/gf100.c:377, gf100_grctx_generate at `nouveau/nvkm/engine/gr/ctxgf100.c:1436.
   Registers: 13 MMIO accesses (0x404170, 0x404170, 0x404170, 0x404170, 0x40802c... ).
   Notes: GR context creation traced via grep; not in B2 call graph.

14. **mesa (known)** — Set up compute context including TLS textures and command buffer preparation
   Functions: nve4_screen_compute_setup at `mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:44.

15. **mesa (known)** — Launch compute grid with QMD descriptor and GPU execution parameters
   Functions: nve4_launch_grid at `mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:785.

16. **channel (unknown)** — Wait for the job to complete by polling the channel status register
   Notes: Job completion polling not traced in B2 call graph; needs FIFO status register.

17. **host (unknown)** — Read back the result buffer from GPU memory through the PCI BAR mapping
   Notes: Result buffer read-back not traced; requires BAR0 access to GPU memory.

## GR hooks classification

| Hook | Function | Use | Reason |
|---|---|---|---|
| init | gf100_gr_init | both | gf100_gr_init calls all other hooks and is shared between graphics and compute pipelines |
| init_400054 | gf100_gr_init_400054 | both | Register 0x400054 initialization is used by both graphics and compute pipelines |
| init_419cc0 | gf100_gr_init_419cc0 | both | Register 0x419cc0 initialization is used by both graphics and compute engines |
| init_419eb4 | gk110_gr_init_419eb4 | compute | Register 0x419eb4 is GK110-specific and used for compute pipeline configuration |
| init_exception2 | gf100_gr_init_exception2 | both | Exception group 2 handling is shared across compute and graphics execution paths |
| init_fecs_exceptions | gf100_gr_init_fecs_exceptions | both | FEC exception handling is shared between graphics and compute error paths |
| init_gpc_mmu | gf100_gr_init_gpc_mmu | compute | GPC MMU initialization configures address translation for compute |
| init_num_active_ltcs | gf100_gr_init_num_active_ltcs | both | LTC count initialization is shared by both graphics and compute workloads |
| init_ppc_exceptions | gk104_gr_init_ppc_exceptions | both | PPC exception handling supports both graphics and compute error recovery |
| init_rop_active_fbps | gk104_gr_init_rop_active_fbps | graphics-only | ROP active framebuffer configuration is for graphics rendering only |
| init_rop_exceptions | gf100_gr_init_rop_exceptions | graphics-only | ROP exceptions are specific to raster operations in graphics pipeline |
| init_shader_exceptions | gf100_gr_init_shader_exceptions | both | Shader exception handling is needed for both graphics shader and compute execution |
| init_sked_hww_esr | gk104_gr_init_sked_hww_esr | both | Scheduler hardware warning error service routine reports error conditions for both graphics and compute paths |
| init_tex_hww_esr | gf100_gr_init_tex_hww_esr | both | Texture hardware warning error service reports errors for both graphics and compute execution paths |
| init_vsc_stream_master | gk104_gr_init_vsc_stream_master | both | VSC stream master setup supports both graphics and compute vertex stream routing |
| init_zcull | gf117_gr_init_zcull | graphics-only | Depth culling unit is specific to rasterization graphics pipeline only |
| oneinit_sm_id | gf100_gr_oneinit_sm_id | both | Streaming multiprocessor ID setup configures SM identity for both paths |
| oneinit_tiles | gf100_gr_oneinit_tiles | both | Tile initialization configures memory tiling for both graphics and compute workloads |

3 hooks are graphics-only:
- **init_rop_active_fbps** (gk104_gr_init_rop_active_fbps): ROP active framebuffer configuration is for graphics rendering only
- **init_rop_exceptions** (gf100_gr_init_rop_exceptions): ROP exceptions are specific to raster operations in graphics pipeline
- **init_zcull** (gf117_gr_init_zcull): Depth culling unit is specific to rasterization graphics pipeline only

2 hooks are compute-specific:
- **init_419eb4** (gk110_gr_init_419eb4): Register 0x419eb4 is GK110-specific and used for compute pipeline configuration
- **init_gpc_mmu** (gf100_gr_init_gpc_mmu): GPC MMU initialization configures address translation for compute

13 hooks are shared (both graphics and compute):
- **init** (gf100_gr_init): gf100_gr_init calls all other hooks and is shared between graphics and compute pipelines
- **init_400054** (gf100_gr_init_400054): Register 0x400054 initialization is used by both graphics and compute pipelines
- **init_419cc0** (gf100_gr_init_419cc0): Register 0x419cc0 initialization is used by both graphics and compute engines
- **init_exception2** (gf100_gr_init_exception2): Exception group 2 handling is shared across compute and graphics execution paths
- **init_fecs_exceptions** (gf100_gr_init_fecs_exceptions): FEC exception handling is shared between graphics and compute error paths
- **init_num_active_ltcs** (gf100_gr_init_num_active_ltcs): LTC count initialization is shared by both graphics and compute workloads
- **init_ppc_exceptions** (gk104_gr_init_ppc_exceptions): PPC exception handling supports both graphics and compute error recovery
- **init_shader_exceptions** (gf100_gr_init_shader_exceptions): Shader exception handling is needed for both graphics shader and compute execution
- **init_sked_hww_esr** (gk104_gr_init_sked_hww_esr): Scheduler hardware warning error service routine reports error conditions for both graphics and compute paths
- **init_tex_hww_esr** (gf100_gr_init_tex_hww_esr): Texture hardware warning error service reports errors for both graphics and compute execution paths
- **init_vsc_stream_master** (gk104_gr_init_vsc_stream_master): VSC stream master setup supports both graphics and compute vertex stream routing
- **oneinit_sm_id** (gf100_gr_oneinit_sm_id): Streaming multiprocessor ID setup configures SM identity for both paths
- **oneinit_tiles** (gf100_gr_oneinit_tiles): Tile initialization configures memory tiling for both graphics and compute workloads

## Firmware

- **fecs** (source: built-in): Falcon EXEC context scheduler firmware compiled into Nouveau source tree for GK110
  File: `nvkm/engine/gr/fuc/hubgk110.fuc3.h`
- **gpccs** (source: built-in): GPC compute context scheduler firmware compiled into Nouveau source tree for GK110
  File: `nvkm/engine/gr/fuc/gpcgk110.fuc3.h`

## Not known yet

- Step 1: **bar** (partly-known) — Map PCI BAR regions and read VBIOS for GPU identification
  Notes: Only the constructor gf100_bar_new is traced; init function not in call graph.
- Step 3: **mc** (partly-known) — Master control provides engine enable bits and interrupt configuration
  Notes: Only the constructor gk104_mc_new is traced; init function not in call graph.
- Step 4: **imem** (partly-known) — Instance memory provides GPU objects such as page tables and RAMFC structures
  Notes: Only the constructor nv50_instmem_new is traced; init function not in call graph.
- Step 6: **top** (partly-known) — Device topology table lists engines and their runlists for FIFO access
  Notes: Topology initialized early; gk104_fifo_init reads device->top at fifo/gk104.c:764.
- Step 8: **ltc** (partly-known) — LTC layer provides zbc color and depth configuration for the GR engine
  Notes: LTC initialized before GR; called from gr/gf100.c:94 for zbc color configuration.
- Step 9: **timer** (partly-known) — Timer subdev provides polling delays for GR firmware initialization waits
  Notes: Timer used by every nvkm_msec call at gr/gf100.c:758 during GR init.
- Step 10: **privring** (partly-known) — PRI ring provides the register bus to GR units for interrupt and error handling
  Notes: Privring initialized before GR; register bus to engines at privring/gf100.c.
- Step 12: **channel** (partly-known) — Create channel address space with RAMFC write and runlist commit
  Notes: Channel creation traced; full command buffer submission not fully traced.
- Step 13: **channel** (partly-known) — Create GR context for the channel including GPU object generation
  Notes: GR context creation traced via grep; not in B2 call graph.
- Step 16: **channel** (unknown) — Wait for the job to complete by polling the channel status register
  Notes: Job completion polling not traced in B2 call graph; needs FIFO status register.
- Step 17: **host** (unknown) — Read back the result buffer from GPU memory through the PCI BAR mapping
  Notes: Result buffer read-back not traced; requires BAR0 access to GPU memory.

