# B5 Result: Minimum chain to one compute job

## Outputs

- `tools/min_chain.py` — Tool that parses subsystems, GR hooks, firmware, and steps from
  Nouveau source and the B2/B3 analysis. Produces `analysis/min_chain.json`.
- `analysis/min_chain.json` — Structured JSON with 4 sections:
  - `subsystems`: 31 entries, one per member of `nvf1_chipset`. 7 needed (bar, fb, imem,
    mmu, mc, fifo, gr), 4 not-needed (disp, mspdec, msppp, msvld), 20 optional.
  - `steps`: 10 ordered steps from PCI BAR mapping to compute launch. Functions include
    gf100_bar_new, gk110_fb_new, gk104_mc_new, nv50_instmem_new, gk104_mmu_new,
    gk110_fifo_new, gk104_fifo_init, gk110b_gr_new, gf100_gr_init,
    nve4_screen_compute_setup, nve4_launch_grid, gf100_fifo_init_pbdmas.
    Registers from B3 MMIO analysis included where applicable.
  - `gr_hooks`: 18 entries from `gk110b_gr`. 3 graphics-only (init_zcull,
    init_rop_active_fbps, init_rop_exceptions), 12 both, 3 compute.
  - `firmware`: 2 built-in headers (fecs: hubgk110.fuc3.h, gpccs: gpcgk110.fuc3.h).
- `analysis/min_chain.md` — 70-line markdown document describing the chain.

## Checks

- `make check` passes with 0 failures.
- `tools/min_chain.py --check` exits 0 (idempotent generation).

## Decisions

- 7 subsystems are needed for any compute job: bar (PCI mapping), fb (framebuffer),
  imem (instantiated memory), mmu (address translation), mc (memory controller),
  fifo (command submission), gr (compute engine).
- 4 subsystems are not-needed: disp, mspdec, msppp, msvld (display and video decode).
- 18 other subsystems are optional (bios, bus, clk, devinit, fuse, gpio, i2c, iccsense,
  privring, therm, timer, top, volt, ce, dma, mxm, pmu, sw).
- 3 GR hooks are graphics-only: init_zcull (depth culling), init_rop_active_fbps (ROP
  framebuffer config), init_rop_exceptions (ROP error handling).
- Step 10 (channel) is partly-known: channel creation and command buffer submission are
  only partially traced in the B2 call graph.
- 4 functions not in the call graph (gf100_bar_new, gk104_mc_new, nv50_instmem_new,
  gf100_fifo_init_pbdmas) were resolved by grepping source directly.

## Open questions

- Channel creation and command buffer submission details are not fully traced (partly-known
  step 10). This is expected since B2 call graph starts from chipset constructors, not
  user-space Mesa functions.
- Shader code upload path from user-space to GPU is not in scope for the minimum chain.
- Completion/interrupt handling path is not included.
