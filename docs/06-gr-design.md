# GR Design (GK110 Graphics/Compute Engine)

## Goal

Initialize the GK110 GR engine for compute — the S3 milestone (GR
ready). Five steps: load the FECS and GPCCS firmware blobs, run the
init hooks that set up MMU forwarding and exceptions, generate a GR
context image for one channel, and write the launch descriptor to the
FIFO ring. The compute-only driver may skip three graphics-only hooks
(zcull, two ROP hooks).

## What Nouveau does

1. **GR constructor** — `gk110b_gr_new` (`nvkm/engine/gr/gk110b.c:150`)
   calls `gf117_gr_new(&gk110b_gr, device, type, inst)` to create the GR
   engine with the GK110B function table.
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
7. **Main init** — `gf100_gr_init` (`nvkm/engine/gr/gf100.c:2342`)
   calls `gf100_gr_init_exception2` (register `0x40011c`, `0x400134`),
   `gf100_gr_init_400054` (register `0x400054`),
   `gf100_gr_init_tex_hww_esr` (TPC register `0x224`),
   `gf100_gr_init_shader_exceptions` (TPC registers `0x644`, `0x64c`),
   `gf100_gr_init_rop_exceptions` (ROP registers `0x144`, `0x070`,
   `0x204`, `0x208`), `gf100_gr_init_419cc0` (GPC/TPC register
   `0x48c`), `gk104_gr_init_sked_hww_esr` (register `0x407020`),
   `gf100_gr_init_fecs_exceptions` (register `0x409c24`),
   `gk110_gr_init_419eb4` (register `0x419eb4`),
   `gk104_gr_init_ppc_exceptions` (PPC register `0x038`),
   `gf100_gr_init_num_active_ltcs` (registers `0x100800`, `0x08ac`),
   `gf100_gr_init_gpc_mmu` (GR MMU registers `0x418880`–`0x4188b8`),
   then applies the mmio tables and calls the per-chip init hooks in
   table order.
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

1. **Allocate the GR engine structure** — Create a `GrEngine` class
   holding the function-table entries and firmware pointers. The
   constructor stores the `gk110b_gr` function table layout.
2. **Load FECS firmware** — Write the `gk110_grhub_code` and
   `gk110_grhub_data` arrays (from `gk110_gr_fecs_ucode` at
   line 321 of gk110.c) into the BAR-mapped MMIO region, replacing the
   firmware load path. Use `RegisterIO::write32()` for the code section
   and `RegisterIO::write32()` for the data section.
3. **Load GPCCS firmware** — Write the `gk110_grgpc_code` and
   `gk110_grgpc_data` arrays (from `gk110_gr_gpccs_ucode` at
   line 331 of gk110.c) into the GPC MMIO region, replacing the
   firmware load path.
4. **Reset FECS** — Write 0x00000070 to register `0x409614`, delay 10 µs
   using `snooze()`, set bits 0x700 of `0x409614`, and read back,
   replacing `gf100_gr_fecs_reset` at line 2466 of gf100.c.
5. **Run exception init** — Write 0xffffffff to registers `0x40011c` and
   `0x400134` to enable all exception reporting, replacing
   `gf100_gr_init_exception2` at line 2192 of gf100.c.
6. **Write 400054 constant** — Write 0x34ce3464 to register `0x400054`,
   replacing `gf100_gr_init_400054` at line 2186 of gf100.c.
7. **Enable TEX HWW** — Write 0xc0000000 to TPC register `0x224`,
   replacing `gf100_gr_init_tex_hww_esr` at line 2223 of gf100.c.
8. **Enable shader exceptions** — Write to TPC registers `0x644` and
   `0x64c`, replacing `gf100_gr_init_shader_exceptions` at line 2215 of
   gf100.c.
9. **Enable FECS exceptions** — Write 0x000e0000 or 0x000e0001 to
   register `0x409c24`, replacing `gf100_gr_init_fecs_exceptions` at
   line 2257 of gf100.c.
10. **Enable scheduler HWW** — Write 0x40000000 to register `0x407020`,
    replacing `gk104_gr_init_sked_hww_esr` at line 391 of gk104.c.
11. **Bit-toggle 419eb4** — Apply the bit-toggle sequence on register
    `0x419eb4` (set bits 0x1000–0x8000 then clear), replacing
    `gk110_gr_init_419eb4` at line 339 of gk110.c.
12. **Set PPC exceptions** — Loop over PPC pairs and write 0xc0000000
    to PPC register `0x038`, replacing
    `gk104_gr_init_ppc_exceptions` at line 415 of gk104.c.
13. **Set active LTC count** — Read register `0x100800` for the number
    of active LTCs and broadcast to GPC register `0x08ac`, replacing
    `gf100_gr_init_num_active_ltcs` at line 2280 of gf100.c.
14. **Set GPC MMU forwarding** — Read the FB MMU page-directory address
    and write it to GR MMU registers `0x418880`–`0x4188b8`, replacing
    `gf100_gr_init_gpc_mmu` at line 2264 of gf100.c.
15. **Oneinit SM enumeration** — Compute the SM ID array from GPC–TPC
    pairings, replacing `gf100_gr_oneinit_sm_id` at line 1895 of
    gf100.c.
16. **Oneinit tile mapping** — Compute the tile-to-GPC mapping using
    prime-factor distribution, replacing
    `gf100_gr_oneinit_tiles` at line 1913 of gf100.c.
17. **Apply MMIO tables** — Apply the register-write tables from
    `gk110b_gr_pack_mmio` at line 87 of gk110b.c through
    `gf100_gr_mmio`, replacing the mmio step of `gf100_gr_init` at
    line 2342 of gf100.c.
18. **Skip graphics-only hooks** — Leave out `init_zcull`
    (`gf117_gr_init_zcull` at line 124 of gf117.c),
    `init_rop_active_fbps` (`gk104_gr_init_rop_active_fbps` at line
    406 of gk104.c), and `init_rop_exceptions`
    (`gf100_gr_init_rop_exceptions` at line 2201 of gf100.c), which
    configure drawing units not needed for compute.
19. **Generate GR context image** — Call the grctx functions in order:
    `.hub` → `.gpc_0` → `.zcull` → `.gpc_1` → `.tpc` → `.ppc` →
    `.pagepool` → `.bundle` → `.attrib` → `.unkn`, replacing
    `gf100_grctx_generate_main` at line 1342 of ctxgf100.c. The context
    image is a buffer of register writes applied by the GR engine during
    channel switch.
20. **ZBC clear values** — Write the colour clear registers via
    `gf100_gr_zbc_clear_color` at line 49 of gf100.c (registers
    `0x405804`–`0x405810`, `0x405814`, `0x405820`, `0x405824`) and the
    depth clear registers via `gf100_gr_zbc_clear_depth` at line 100 of
    gf100.c (registers `0x405818`, `0x40581c`, `0x405820`, `0x405824`).
21. **Write LTC patch** — Generate LTC patch entries for the channel
    context via `gk104_grctx_generate_patch_ltc` at line 864 of
    ctxgk104.c, configuring LTC cache behavior.

## Haiku interfaces

1. `` `malloc()` `` — `os/SupportDefs.h` (via `<stdlib.h>`): allocates
   the GR engine structure, GR context image buffer, and ZBC data
   structures; replaces `kzalloc`/`kmalloc` from Nouveau.
2. `` `free()` `` — `os/SupportDefs.h` (via `<stdlib.h>`): frees GR
   engine structures, context image buffers, and ZBC data; replaces
   `kfree`.
3. `` `snooze()` `` — `os/kernel/OS.h`: sleeps for a given number of
   microseconds; replaces `nvkm_msec(device, 2000, ...)` timeouts and
   the 10 µs delay after FECS reset.
4. `` `memset()` `` — `os/SupportDefs.h` (via `<string.h>`): zeroes the
   GR context image buffer and ZBC clear tables; replaces `memset` from
   Nouveau.
5. `` `memcpy()` `` — `os/SupportDefs.h` (via `<string.h>`): copies the
   firmware blobs (`gk110_grhub_code`, `gk110_grhub_data`,
   `gk110_grgpc_code`, `gk110_grgpc_data`) into the BAR-mapped MMIO
   region.

## Host tests

`tests/test_pagetable.cpp` covers page-table encoding used by GR MMU
setup (step 14 of the Haiku design): PTE/PDE encoding and the
address-space geometry. `tests/test_pushbuffer.cpp` covers the push-buffer
encoding used to build the command buffers that the GR engine executes
(step 20). No `tests/` file covers the GR engine init sequence (steps
2–17), the GR context generation (step 19), or the ZBC clear path
(steps 20–21). A GR init test would need `MockMMIO` to capture the
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
- Whether the two graphics-only hooks
  (`init_zcull` at `nvkm/engine/gr/gf117.c:124` and
  `init_rop_active_fbps` at `nvkm/engine/gr/gk104.c:406`) are truly
  optional for compute or if the GPU hardware requires those units to
  be configured even when only compute shaders run. The source classifies
  them as graphics-only but does not provide evidence beyond the
  function name.
