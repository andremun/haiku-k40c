# Plan B5: Minimum chain to one computation

## Steps
1. **Subsystems**: Parse `nvf1_chipset` from `base.c` (31 members). Assign status: bar/fb/imem/mmu/mc/fifo/gr needed; disp/mspdec/msppp/msvld not-needed; others reasoned.
2. **GR hooks**: Parse `gk110b_gr` from `gk110b.c` (18 init/oneinit hooks). Look up function definition lines in callgraph. Classify use (compute/graphics-only/both). init_zcull = graphics-only.
3. **Firmware**: Two built-in headers: `fuc/hubgk110.fuc3.h` (fecs) and `fuc/gpcgk110.fuc3.h` (gpccs).
4. **Steps**: Build 10+ ordered steps from PCI mapping to compute launch. Functions: gf100_fb_init, gk110_fb_new, gk104_mc_new, gk104_mmu_new, nv50_instmem_new, gk110_fifo_new, gk104_fifo_init, gk110b_gr_new, gf100_gr_init, nve4_screen_compute_setup, nve4_launch_grid.
5. Registers for each step = union of mmio_accesses.json entries for its nouveau functions.
6. Run `make check` after building the complete tool.

## Checks
- `make check` passes (check_repo.py validates format, required functions, subsystem status, gr_hooks).
- `tools/min_chain.py --check` exits 0 (idempotent generation).
