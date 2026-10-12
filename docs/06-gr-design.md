# GR Design (GK110 Graphics/Compute Engine)

## Goal

Start the GR engine of the GK110B and give one channel a GR context, so
that a compute job can run: milestone S3. In Nouveau's order: prepare
the engine once (`oneinit`), run `gf100_gr_init` (register tables, the
init hooks, exception enables), load and start the two microcode
programs at the end of it, and generate the context image for the
channel. Whether a compute-only driver may leave out the hooks for
drawing units is open; this design runs them all.

## What Nouveau does

1. **GR constructor** — `gk110b_gr_new` (`nvkm/engine/gr/gk110b.c:150`)
   calls `gf100_gr_new_(gk110b_gr_fwif, device, type, inst, pgr)`. The
   list `gk110b_gr_fwif` (`nvkm/engine/gr/gk110b.c:143`) leads to the
   function table `gk110b_gr` (`docs/07-firmware-analysis.md`).
2. **Function table** — `gk110b_gr` (`nvkm/engine/gr/gk110b.c:105`)
   defines `.oneinit_tiles`, `.oneinit_sm_id`, `.init`, `.init_gpc_mmu`,
   `.init_vsc_stream_master`, `.init_zcull`, `.init_num_active_ltcs`,
   `.init_rop_active_fbps`, `.init_fecs_exceptions`, `.init_sked_hww_esr`,
   `.init_419cc0`, `.init_419eb4`, `.init_ppc_exceptions`,
   `.init_tex_hww_esr`, `.init_shader_exceptions`, `.init_rop_exceptions`,
   `.init_exception2`, `.init_400054`, `.mmio`, `.fecs`, `.gpccs`,
   `.rops`, `.ppc_nr`, `.grctx`, `.trap_mp` members.
3. **MMIO tables** — `gk110b_gr_pack_mmio` (`nvkm/engine/gr/gk110b.c:87`)
   returns a list of register-write tables that
   `gf100_gr_init` applies through `gf100_gr_mmio` before calling init
   hooks.
4. **FECS firmware** — `gk110_gr_fecs_ucode`
   (`nvkm/engine/gr/gk110.c:321`) provides the FECS microcode table
   containing `gk110_grhub_code` and `gk110_grhub_data` arrays compiled
   from `fuc/hubgk110.fuc3.h`.
5. **GPCCS firmware** — `gk110_gr_gpccs_ucode`
   (`nvkm/engine/gr/gk110.c:331`) provides the GPCCS microcode table
   containing `gk110_grgpc_code` and `gk110_grgpc_data` arrays compiled
   from `fuc/gpcgk110.fuc3.h`.
6. **FECS reset** — `gf100_gr_fecs_reset`
   (`nvkm/engine/gr/gf100.c:2466`) writes 0x00000070 to register
   `0x409614` to assert FECS reset, delays 10 µs, sets bits 0x700 of
   `0x409614`, and reads back.
7. **Main init, in this order** — `gf100_gr_init`
   (`nvkm/engine/gr/gf100.c:2342`): `init_gpc_mmu` (line 2349); the
   register tables of `mmio` through `gf100_gr_mmio` (line 2360);
   `init_vsc_stream_master` (2374); `init_zcull` (2375);
   `init_num_active_ltcs` (2376); `init_rop_active_fbps` (2378); direct
   writes that enable interrupts and exceptions; `init_fecs_exceptions`
   (2392); `init_sked_hww_esr` (2411); `init_419cc0` (2417);
   `init_419eb4` (2419); `init_ppc_exceptions` (2424); for each GPC and
   TPC `init_tex_hww_esr` (2435) and `init_shader_exceptions` (2439);
   `init_rop_exceptions` (2445); `init_exception2` (2452);
   `init_400054` (2455); `gf100_gr_zbc_init` (2457); and last
   `gf100_gr_init_ctxctl` (2462), which loads and starts the microcode
   (`docs/07-firmware-analysis.md`). The hooks that the table of the
   GK110B does not set (`init_r405a14`, `init_bios` and others) are
   skipped by their `if`. Between the hooks the function writes about
   twenty registers itself; they are in `hardware/registers/gr.yaml`
   with function `gf100_gr_init`.
8. **Init GPC MMU** — `gf100_gr_init_gpc_mmu`
   (`nvkm/engine/gr/gf100.c:2264`) reads the FB MMU page-directory
   address and writes it to GR MMU forwarding registers `0x418880`
   through `0x4188b8`.
9. **Init PPC exceptions** — `gk104_gr_init_ppc_exceptions`
   (`nvkm/engine/gr/gk104.c:415`) loops over enabled GPC/PPC pairs and
   writes 0xc0000000 to PPC register `0x038`.
10. **Init 419eb4** — `gk110_gr_init_419eb4`
    (`nvkm/engine/gr/gk110.c:339`) applies `nvkm_mask` on register
    `0x419eb4` to set bits 0x1000–0x8000 then clears them for a
    bit-toggle sequence.
11. **Oneinit SM ID** — `gf100_gr_oneinit_sm_id`
    (`nvkm/engine/gr/gf100.c:1895`) enumerates all valid GPC–TPC pairs
    into the SM array and returns the total SM count.
12. **Oneinit tiles** — `gf100_gr_oneinit_tiles`
    (`nvkm/engine/gr/gf100.c:1913`) computes the tile-to-GPC mapping
    using a prime-factor distribution algorithm and sorts GPCs by TPC
    count.
13. **GR context** — `gk110b_grctx`
    (`nvkm/engine/gr/ctxgk110b.c:73`) defines the GR context function
    table: `.main`, `.unkn`, `.hub`, `.gpc_0`, `.gpc_1`, `.zcull`,
    `.tpc`, `.ppc`, `.icmd`, `.mthd`, `.bundle`, `.pagepool`,
    `.attrib_cb_size`, `.attrib_cb`, `.attrib`, `.patch_ltc`,
    `.sm_id`, `.tpc_nr`, `.rop_mapping`, `.alpha_beta_tables`,
    `.dist_skip_table`, `.gpc_tpc_nr`, `.r418800`, `.r419eb0`,
    `.r419f78`.
14. **Context main** — `gf100_grctx_generate_main`
    (`nvkm/engine/gr/ctxgf100.c:1342`) generates the GR context image by
    calling `.hub`, `.gpc_0`, `.zcull`, `.gpc_1`, `.tpc`, `.ppc`, then
    `.pagepool`, `.bundle`, `.attrib`, and `.unkn`.
15. **Context unkn** — `gk104_grctx_generate_unkn`
    (`nvkm/engine/gr/ctxgk104.c:894`) writes mask operations on registers
    `0x418c6c`, `0x41980c`, `0x41be08`, `0x4064c0`, `0x405800` and
    `0x419c00` for unknown GR context setup.
16. **ZBC clear** — `gf100_gr_zbc_clear_color`
    (`nvkm/engine/gr/gf100.c:49`) writes four colour data registers
    (`0x405804`–`0x405810`), the format register (`0x405814`), selects
    the ZBC entry (`0x405820`), and triggers a colour write via
    `0x405824` set to TRIGGER | WRITE | COLOR.
17. **ZBC depth** — `gf100_gr_zbc_clear_depth`
    (`nvkm/engine/gr/gf100.c:100`) writes the depth data register
    (`0x405818`), the format register (`0x40581c`), selects the ZBC
    entry (`0x405820`), and triggers a depth write via `0x405824` set to
    TRIGGER | WRITE | DEPTH.

## Haiku driver design

The first version of this section listed the steps in a different order
from Nouveau, started the microcode before the engine was set up, and
left out three hooks as "graphics-only". The scaffold rewrote it to
follow `gf100_gr_init` line by line. Nothing here has run on the card.

1. **Once, before the first start** — reproduce `gf100_gr_oneinit`
   (`nvkm/engine/gr/gf100.c:1989`): read the unit
   counts (`rops` reads register `0x409604`), compute the tile map
   (`gf100_gr_oneinit_tiles`, line 1913) and the SM list
   (`gf100_gr_oneinit_sm_id`, line 1895). Nouveau also calls
   `nvkm_pmu_pgob(device->pmu, false)` here (line 2006): see "Not known".
2. **Start of init** — clear bits `0x00010001` of register `0x400500`
   and run `init_gpc_mmu` (step 8 of the section above).
3. **Register tables** — apply the tables of `gk110b_gr_pack_mmio`
   (`nvkm/engine/gr/gk110b.c:87`) as `gf100_gr_mmio` does. The tables
   have to be extracted from the Nouveau source as data (design
   category B, extract); this is not done yet.
4. **Init hooks in Nouveau's order** — every hook of step 7 above, each
   as a small function on `RegisterIO` with the register writes that
   `docs/hardware-model/gr.md` lists for it, and the direct writes of
   `gf100_gr_init` between them. All hooks are run, also `init_zcull`
   and the two ROP hooks.
5. **Clear-value table** — `gf100_gr_zbc_init` (line 2457), which uses
   the two `zbc` members and the `ltc` subsystem
   (`docs/hardware-model/ltc.md`).
6. **Microcode** — load and start FECS and GPCCS exactly as
   `docs/07-firmware-analysis.md` describes. In Nouveau this is the last
   step of init (line 2462), after all the register setup.
7. **Context image for a channel** — reproduce
   `gf100_grctx_generate_main` (`nvkm/engine/gr/ctxgf100.c:1342`): the
   register tables `hub`, `gpc_0`, `zcull`, `gpc_1`, `tpc`, `ppc`, then
   `pagepool`, `bundle`, `attrib` and `unkn`, and the other `grctx`
   functions of `docs/hardware-model/gr.md`. How the generated state
   becomes the image that is stored for the channel (Nouveau asks the
   FECS program to save it) was not analysed: see "Not known".
8. **Bind the context to the channel** — the engine context members of
   the FIFO (`engn.ctor`, `engn.bind` in `docs/hardware-model/fifo.md`)
   write the address of the context into the channel's instance block.
9. **Launch** — with the context bound, the compute class is bound on a
   subchannel and the job is launched with the methods of
   `analysis/compute_launch.md`; the descriptor and the launch methods
   are built by `src/compute/LaunchDesc.h`.

Left out on purpose: the interrupt and error handlers (`trap_mp` and the
exception decoding). The first driver only logs the status registers.


## Haiku interfaces

1. `` `malloc()` `` — `os/SupportDefs.h` (via `<stdlib.h>`): allocates
   the GR engine structure, GR context image buffer, and ZBC data
   structures; replaces `kzalloc`/`kmalloc` from Nouveau.
2. `` `free()` `` — `os/SupportDefs.h` (via `<stdlib.h>`): frees GR
   engine structures, context image buffers, and ZBC data; replaces
   `kfree`.
3. `` `snooze()` `` — `headers/os/kernel/OS.h`: sleeps for a given number of
   microseconds; replaces `nvkm_msec(device, 2000, ...)` timeouts and
   the 10 µs delay after FECS reset.
4. `` `memset()` `` — `os/SupportDefs.h` (via `<string.h>`): zeroes the
   GR context image buffer and ZBC clear tables; replaces `memset` from
   Nouveau.
5. `` `spin()` `` — `headers/os/drivers/KernelExport.h`: short busy
   waits in microseconds (the 10 µs of the controller reset). The
   microcode is not copied with `memcpy()`: it is sent word by word
   through registers (`docs/07-firmware-analysis.md`).

## Host tests

`tests/test_launchdesc.cpp` and `tests/accept/d5_accept.cpp` cover the
launch descriptor and the launch methods of step 9.
`tests/test_pushbuffer.cpp` covers the encoding of the methods. No file
under `tests/` covers the engine start (steps 1 to 6) or the context
image (steps 7 and 8). A GR init test would need `MockMMIO` to capture the
register access log of the full init hook sequence. A GR context
generation test would need `MockMMIO` with the register-write tables for
the grctx pack functions.

## Not known

- Whether the GR engine MMIO tables (`gk110b_gr_pack_mmio` at
  `nvkm/engine/gr/gk110b.c:87`) contain all the writes needed for
  compute, or whether some entries configure drawing-only paths that
  would be wasted but harmless on a compute-only workload.
- The exact layout of the GR context image buffer (`.bundle`, `.pagepool`,
  `.attrib`) — their sizes are constants from the grctx function table
  (`bundle_size` = 0x3000, `pagepool_size` = 0x8000 from
  `ctxgk110b.c:73`) but the on-card meaning of each sub-buffer and the
  order of register writes within each sub-buffer are not established
  beyond the function names in `nvkm/engine/gr/ctxgf100.c:1342`.
- Whether the card needs power gating switched off before GR starts.
  `gf100_gr_oneinit` calls `nvkm_pmu_pgob(device->pmu, false)`
  (`nvkm/engine/gr/gf100.c:2006`); B5 left this open
  (`work/B5/REVIEW.md`) and only a run on the card (task C5) can answer.
- How the context image is saved. The design generates the state; the
  step in which the FECS program stores it as the image of a channel
  (`gf100_gr_fecs_wfi_golden_save` and the functions near
  `nvkm/engine/gr/gf100.c:814`) was not analysed.
- Where `gf100_gr_fecs_reset` is called.
- Whether the two graphics-only hooks
  (`init_zcull` at `nvkm/engine/gr/gf117.c:124` and
  `init_rop_active_fbps` at `nvkm/engine/gr/gk104.c:406`) are truly
  optional for compute or if the GPU hardware requires those units to
  be configured even when only compute shaders run. The source classifies
  them as graphics-only but does not provide evidence beyond the
  function name.
