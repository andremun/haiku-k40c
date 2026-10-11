# B5 Result: Minimum chain to one compute job

## Outputs

- `tools/min_chain.py` — Tool that parses subsystems, GR hooks, firmware, and steps from
  Nouveau source and the B2/B3 analysis. Produces `analysis/min_chain.json`.
- `analysis/min_chain.json` — Structured JSON with 4 sections:
  - `subsystems`: 31 entries, one per member of `nvf1_chipset`. 11 needed (bar, fb, imem,
    mmu, mc, fifo, gr, ltc, timer, privring, top), 4 not-needed (disp, mspdec, msppp, msvld),
    16 optional.
  - `steps`: 17 ordered steps from PCI BAR mapping through GR init, channel creation, Mesa
    compute setup, launch, job completion polling, and result buffer read-back. Functions include
    gf100_bar_new, gk110_fb_new, gk104_mc_new, nv50_instmem_new, gk104_mmu_new,
    gk110_fifo_new, gk104_fifo_init, gk110b_gr_new, gf100_gr_init,
    gf100_gr_init_ctxctl_int, gk104_chan_ramfc_write, gk104_runl_commit,
    gf100_gr_chan_new, gf100_grctx_generate, nve4_screen_compute_setup, nve4_launch_grid.
    Registers from B3 MMIO analysis included where applicable.
  - `gr_hooks`: 18 entries from `gk110b_gr`. 3 graphics-only (init_zcull,
    init_rop_active_fbps, init_rop_exceptions), 2 compute (init_419eb4, init_gpc_mmu),
    13 both.
  - `firmware`: 2 built-in headers (fecs: hubgk110.fuc3.h, gpccs: gpcgk110.fuc3.h).
- `analysis/min_chain.md` — 149-line markdown document describing the chain.

## Checks

- `make check` passes with 0 failures (attempt 2).
- `tools/min_chain.py --check` exits 0 (idempotent generation).

## Changes from attempt 1 (12 fixes)

1. **`top` subsystem**: changed `optional` → `needed`. Reason: device topology table lists
   engines and runlists; `gk104_fifo_init` reads `device->top` at `fifo/gk104.c:764`.
2. **`ltc` subsystem**: changed `optional` → `needed`. Reason: GR engine calls `nvkm_ltc_*`
   functions for zbc color and depth configuration at `gr/gf100.c:94` and `114`.
3. **`timer` subsystem**: changed `optional` → `needed`. Reason: every `nvkm_msec` wait call
   in GR uses the timer subdev for polling loops at `gr/gf100.c:758`.
4. **`privring` subsystem**: changed `optional` → `needed`. Reason: PRI ring provides the
   register bus to GR units for interrupt handling and hardware error reporting.
5. **Channel functions**: added 5 required functions across channel steps:
   `gf100_gr_init_ctxctl_int`, `gk104_chan_ramfc_write`, `gk104_runl_commit`,
   `gf100_gr_chan_new`, `gf100_grctx_generate`.
6. **Step depth**: changed steps 1, 3, 4 from `known` to `partly-known` — only the
   constructor is traced, the init function is not in the call graph.
7. **`mc` reason**: changed "memory controller" → "master control provides engine enable
   bits and interrupt configuration for every subdevice that the GR and FIFO engines use".
8. **`privring` reason**: changed "ring buffer" → "PRI ring provides the register bus to
   the GR units for interrupt handling and hardware error reporting".
9. **`top` reason**: changed "multi-gpu" → "device topology table lists engines and their
   runlists; `gk104_fifo_init` reads device->top to iterate runlists".
10. **HWW reason**: changed "workqueue" → "hardware warning error service routine reports
    error conditions for both graphics and compute paths".
11. **`imem` reason**: changed "instantiated memory" → "instance memory provides GPU objects
    such as page tables and RAMFC structures".
12. **GR hook `init` use**: changed `compute` → `both`. `gf100_gr_init` calls all other hooks
    and is shared between graphics and compute pipelines.

## Additional changes

- Steps 16-17 added: job completion polling (channel, unknown) and result buffer
  read-back (host, unknown).
- GR hook `init` corrected to `both` (was `compute` in attempt 1).
- Subsystem count updated from 7 to 11 needed.
- Step count expanded from 10 to 17 (added intermediate steps for top, ltc, timer,
  privring between FIFO and GR).

## Decisions

- 11 subsystems are needed for any compute job: bar, fb, imem, mmu, mc, fifo, gr,
  ltc, timer, privring, top.
- 4 subsystems are not-needed: disp, mspdec, msppp, msvld (display and video decode).
- 16 other subsystems are optional (bios, bus, clk, devinit, fuse, gpio, i2c, iccsense,
  therm, volt, ce, dma, mxm, pmu, sw, pci).
- 3 GR hooks are graphics-only: init_zcull (depth culling), init_rop_active_fbps (ROP
  framebuffer config), init_rop_exceptions (ROP error handling).
- 2 GR hooks are compute-specific: init_419eb4 (GK110 register config),
  init_gpc_mmu (GPC MMU for compute address translation).
- 13 GR hooks are shared (both graphics and compute).
- 7 steps are partly-known: only constructors traced (bar, mc, imem, top, ltc, timer,
  privring), or channel functions not in call graph.
- 2 steps are unknown: job completion polling and result buffer read-back.

## Open questions

- Channel creation and command buffer submission details are not fully traced (partly-known
  steps 12-13). This is expected since B2 call graph starts from chipset constructors, not
  user-space Mesa functions.
- Shader code upload path from user-space to GPU is not in scope for the minimum chain.
- Job completion polling mechanism (step 16) needs FIFO status register identification.
- Result buffer read-back (step 17) needs BAR0 access path confirmation.
