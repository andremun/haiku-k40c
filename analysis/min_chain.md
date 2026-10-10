# Minimum Chain to One Compute Job (GK110 / K40c)

## Steps: PCI mapping to compute launch

1. **bar (known)** — Map PCI BAR regions. `gf100_bar_new` at `nvkm/subdev/bar/gf100.c:192`.
   No MMIO accesses recorded in B3 analysis; BAR mapping is a resource allocation step.

2. **fb (known)** — Initialize framebuffer layer. `gk110_fb_new` at `nvkm/subdev/fb/gk110.c:69`,
   then `gf100_fb_init` at `nvkm/subdev/fb/gf100.c:87`. No MMIO accesses in B3 for gf100_fb_init
   itself; page init has 2 accesses.

3. **mc (known)** — Configure memory controller. `gk104_mc_new` at `nvkm/subdev/mc/gk104.c:63`.
   No MMIO accesses in B3; MC setup is largely register-less at init time.

4. **imem (known)** — Initialize instantiated memory. `nv50_instmem_new` at `nvkm/subdev/instmem/nv50.c:436`.
   No MMIO accesses in B3; this is a memory allocation infrastructure step.

5. **mmu (known)** — Set up memory management unit. `gk104_mmu_new` at `nvkm/subdev/mmu/gk104.c:38`.
   No MMIO accesses in B3; MMU setup is configuration-only at init.

6. **fifo (known)** — Initialize FIFO engine. `gk110_fifo_new` at `nvkm/engine/fifo/gk110.c:128`,
   then `gk104_fifo_init` at `nvkm/engine/fifo/gk104.c:744` with 3 MMIO accesses
   (registers 0x002254, 0x002100, 0x002140).

7. **gr (known)** — Initialize graphics/compute engine. `gk110b_gr_new` at
   `nvkm/engine/gr/gk110b.c:150`, then `gf100_gr_init` at `nvkm/engine/gr/gf100.c:2342`
   with 25 MMIO accesses including `0x400500`, `0x400100` and others across the GR register space.

8. **mesa (known)** — Set up compute context. `nve4_screen_compute_setup` at
   `reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:44`. No MMIO accesses
   in B3; this is a user-space driver function that prepares the push buffer.

9. **mesa (known)** — Launch compute grid. `nve4_launch_grid` at
   `reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:785`. No MMIO accesses
   in B3; this function builds the command buffer and triggers GPU execution.

10. **channel (partly-known)** — Create channel and submit command buffer.
    `gf100_fifo_init_pbdmas` at `nvkm/engine/fifo/gf100.c:873` with 9 MMIO accesses.
    Channel creation and command buffer submission are only partially traced in the B2 call graph.

## GR hooks classification

| Hook | Function | Use | Reason |
|---|---|---|---|
| init | gf100_gr_init | compute | Generic GR init used by both graphics and compute pipelines |
| init_gpc_mmu | gf100_gr_init_gpc_mmu | compute | GPC MMU init configures address translation for compute |
| init_vsc_stream_master | gk104_gr_init_vsc_stream_master | both | VSC stream routing supports both graphics and compute vertex streams |
| init_zcull | gf117_gr_init_zcull | graphics-only | Depth culling unit is specific to rasterization graphics pipeline |
| init_num_active_ltcs | gf100_gr_init_num_active_ltcs | both | LTC count init is shared by graphics and compute workloads |
| init_rop_active_fbps | gk104_gr_init_rop_active_fbps | graphics-only | ROP framebuffer config is for graphics rendering only |
| init_fecs_exceptions | gf100_gr_init_fecs_exceptions | both | FEC exception handling shared between graphics and compute |
| init_sked_hww_esr | gk104_gr_init_sked_hww_esr | both | Scheduler error service routine supports both paths |
| init_419cc0 | gf100_gr_init_419cc0 | both | Register 0x419cc0 init used by both graphics and compute engines |
| init_419eb4 | gk110_gr_init_419eb4 | compute | GK110-specific register used for compute pipeline configuration |
| init_ppc_exceptions | gk104_gr_init_ppc_exceptions | both | PPC exception handling supports both graphics and compute recovery |
| init_tex_hww_esr | gf100_gr_init_tex_hww_esr | both | Texture error service used by compute and graphics |
| init_shader_exceptions | gf100_gr_init_shader_exceptions | both | Shader exception handling needed for both shader and compute execution |
| init_rop_exceptions | gf100_gr_init_rop_exceptions | graphics-only | ROP exceptions are specific to raster operations in graphics |
| init_exception2 | gf100_gr_init_exception2 | both | Exception group 2 handling shared across compute and graphics |
| init_400054 | gf100_gr_init_400054 | both | Register 0x400054 init used by both graphics and compute pipelines |
| oneinit_sm_id | gf100_gr_oneinit_sm_id | both | SM identity config for both graphics and compute execution |
| oneinit_tiles | gf100_gr_oneinit_tiles | both | Memory tiling init for both graphics and compute workloads |

Four hooks are graphics-only: init_zcull (depth culling), init_rop_active_fbps (ROP
framebuffer configuration), init_rop_exceptions (ROP-specific error handling), and they
are not needed for pure compute workloads. The remaining 14 hooks are needed for compute
or shared between graphics and compute.

## Firmware

Two firmware blobs are built-in to the Nouveau source tree:

- **fecs** (Falcon EXEC context scheduler): header `nvkm/engine/gr/fuc/hubgk110.fuc3.h`.
  Compiled into the Nouveau driver as part of the GR firmware interface.
- **gpccs** (GPC compute context scheduler): header `nvkm/engine/gr/fuc/gpcgk110.fuc3.h`.
  Compiled into the Nouveau driver for GK110 GPC scheduling.

Both are loaded from the driver source, not from external firmware files or VBIOS.

## Not known yet

- **Channel creation and command buffer submission**: The B2 call graph traces from the
  chipset constructor through init functions, but does not include the full user-space
  path from Mesa `nvc0_screen_compute_new` through channel creation to actual command
  buffer submission. The channel subsystem step is marked partly-known.
- **Shader code upload**: The path from Mesa user-space to GPU memory for the actual
  compute shader binary (SASS code) is not traced in the B2 call graph.
- **Completion handling**: How the driver detects when the compute job has finished
  (interrupt handling, sync objects) is not in scope for the minimum chain.
