# Firmware Analysis (GK110 GR engine)

## Goal

Load the two built-in firmware arrays (FECS, GPCCS) onto the K40c GR engine so that the GPU can execute compute shaders — the S3 milestone. The driver loads four blobs (data + code for each Falcon), writes register `0x000260` around the uploads, applies context register lists, and starts the HUB ucode. Five steps in total.

## What Nouveau does

1. **Firmware selection** — `gf100_gr_nofw` (`nvkm/engine/gr/gf100.c:2561`) sets `gr->firmware = false` and returns 0; this is the default path because `NvGrUseFW` is false.
2. **Constructor table** — `gk110b_gr_fwif` (`nvkm/engine/gr/gk110b.c:143`) has two entries (`gf100_gr_load`, `gf100_gr_nofw`) both pointing to `&gk110b_gr`; without the option `gf100_gr_nofw` is taken.
3. **FECS data array** — `gk110_grhub_data` is a `uint32_t[]` of 193 words (772 bytes) defined in `nvkm/engine/gr/fuc/hubgk110.fuc3.h:2`; it is loaded into the HUB Falcon's data RAM.
4. **FECS code array** — `gk110_grhub_code` is a `uint32_t[]` of 768 words (3072 bytes) defined in `nvkm/engine/gr/fuc/hubgk110.fuc3.h:209`; it is loaded into the HUB Falcon's instruction RAM.
5. **GPCCS data array** — `gk110_grgpc_data` is a `uint32_t[]` of 27 words (108 bytes) defined in `nvkm/engine/gr/fuc/gpcgk110.fuc3.h:2`; it is loaded into each GPC Falcon's data RAM.
6. **GPCCS code array** — `gk110_grgpc_code` is a `uint32_t[]` of 448 words (1792 bytes) defined in `nvkm/engine/gr/fuc/gpcgk110.fuc3.h:44`; it is loaded into each GPC Falcon's instruction RAM.
7. **FECS ucode struct** — `gk110_gr_fecs_ucode` (`nvkm/engine/gr/gk110.c:321`) binds `gk110_grhub_code` and `gk110_grhub_data` into a `struct gf100_gr_ucode`.
8. **GPCCS ucode struct** — `gk110_gr_gpccs_ucode` (`nvkm/engine/gr/gk110.c:331`) binds `gk110_grgpc_code` and `gk110_grgpc_data` into a `struct gf100_gr_ucode`.
9. **Master control register — clear** — `nvkm_mc_unk260(device, 0)` (`nvkm/engine/gr/gf100.c:1842`) writes 0 to register `0x000260` before the microcode upload.
10. **Load FECS data** — `nvkm_falcon_load_dmem(&gr->fecs.falcon, gr->func->fecs.ucode->data.data, 0x0, gr->func->fecs.ucode->data.size, 0)` (`nvkm/engine/gr/gf100.c:1843`) loads the HUB data blob at offset 0.
11. **Load FECS code** — `nvkm_falcon_load_imem(&gr->fecs.falcon, gr->func->fecs.ucode->code.data, 0x0, gr->func->fecs.ucode->code.size, 0, 0, false)` (`nvkm/engine/gr/gf100.c:1846`) loads the HUB code blob.
12. **Load GPCCS data** — `nvkm_falcon_load_dmem(&gr->gpccs.falcon, gr->func->gpccs.ucode->data.data, 0x0, gr->func->gpccs.ucode->data.size, 0)` (`nvkm/engine/gr/gf100.c:1851`) loads the GPC data blobs.
13. **Load GPCCS code** — `nvkm_falcon_load_imem(&gr->gpccs.falcon, gr->func->gpccs.ucode->code.data, 0x0, gr->func->gpccs.ucode->code.size, 0, 0, false)` (`nvkm/engine/gr/gf100.c:1854`) loads the GPC code blobs.
14. **Master control register — set** — `nvkm_mc_unk260(device, 1)` (`nvkm/engine/gr/gf100.c:1857`) writes 1 to register `0x000260` after the uploads.
15. **HUB context registers** — `gf100_gr_init_csdata(gr, grctx->hub, 0x409000, 0, 0)` (`nvkm/engine/gr/gf100.c:1860`) applies the HUB register list; the arguments are the context data base address and two offsets (both zero).
16. **GPC 0 context registers** — `gf100_gr_init_csdata(gr, grctx->gpc_0, ctx_base_0x41a, 0, sub_0x418)` (`nvkm/engine/gr/gf100.c:1861`) applies the GPC 0 register list; context data base is at offset 0x041a000, with sub-offset 0x0418000.
17. **GPC 1 context registers** — `gf100_gr_init_csdata(gr, grctx->gpc_1, ctx_base_0x41a, 0, sub_0x418)` (`nvkm/engine/gr/gf100.c:1862`) applies the GPC 1 register list; context data base is at offset 0x041a000, with sub-offset 0x0418000.
18. **TPC context registers** — `gf100_gr_init_csdata(gr, grctx->tpc, ctx_base_0x41a, 4, sub_0x419)` (`nvkm/engine/gr/gf100.c:1863`) applies the TPC register list; context data base is at offset 0x041a000, with sub-offset 0x0419800.
19. **PPC context registers** — `gf100_gr_init_csdata(gr, grctx->ppc, ctx_base_0x41a, 8, sub_0x41b)` (`nvkm/engine/gr/gf100.c:1864`) applies the PPC register list; context data base is at offset 0x041a000, with sub-offset 0x041be00.
20. **Clear HUB control** — `nvkm_wr32(device, 0x40910c, 0x00000000)` (`nvkm/engine/gr/gf100.c:1867`) writes 0 to the HUB control register.
21. **Start HUB ucode** — `nvkm_wr32(device, 0x409100, 0x00000002)` (`nvkm/engine/gr/gf100.c:1868`) writes 2 to the HUB start register.
22. **Wait for HUB ready** — `nvkm_msec(device, 2000, ...)` (`nvkm/engine/gr/gf100.c:1869`) waits up to 2000 ms while polling `nvkm_rd32(device, 0x409800)` for the ready bit (`nvkm/engine/gr/gf100.c:1870`).
23. **Read context size** — `gr->size = nvkm_rd32(device, 0x409804)` (`nvkm/engine/gr/gf100.c:1877`) reads the GR context size from hardware.
24. **Falcon reset** — `gf100_gr_fecs_reset` (`nvkm/engine/gr/gf100.c:2466`) writes 0x00000070 to register `0x409614`, delays 10 µs, sets bits 0x700 of `0x409614`, and reads back.
25. **External firmware path** — `gf100_gr_load` (`nvkm/engine/gr/gf100.c:2595`) returns `-EINVAL` when `NvGrUseFW` is false (`nvkm/engine/gr/gf100.c:2599`), falling through to `gf100_gr_nofw`. It requests files `fuc409c`–`fuc41ad` from `nvkm/engine/gr/gf100.c:2602`–`2605` when the option is true.

## Haiku driver design

1. **Define firmware arrays** — Include `gk110_grhub_data`, `gk110_grhub_code`, `gk110_grgpc_data`, `gk110_grgpc_code` from the built-in firmware in `firmware/manifest.yaml`. These are MIT-licensed (Red Hat, Ben Skeggs), same as the Haiku driver.
2. **Wrap arrays in ucode structs** — Create a `struct Gk110Firmware` holding pointers and sizes for FECS data/code and GPCCS data/code, mirroring the `gf100_gr_ucode` structure.
3. **Write 0 to register `0x000260`** — Before uploads, write 0 to this register using the `RegisterIO` abstraction (`RegisterIO::write32()`). This replaces `nvkm_mc_unk260(device, 0)` at line 1842.
4. **Load FECS data memory** — Copy 193 words (772 bytes) of `gk110_grhub_data` to the HUB Falcon's data RAM. Use a memory copy loop or `memcpy` to the BAR-mapped region.
5. **Load FECS instruction memory** — Copy 768 words (3072 bytes) of `gk110_grhub_code` to the HUB Falcon's instruction RAM.
6. **Load GPCCS data memory** — Copy 27 words (108 bytes) of `gk110_grgpc_data` to each GPC Falcon's data RAM.
7. **Load GPCCS instruction memory** — Copy 448 words (1792 bytes) of `gk110_grgpc_code` to each GPC Falcon's instruction RAM.
8. **Write 1 to register `0x000260`** — After uploads, write 1 to this register. This replaces `nvkm_mc_unk260(device, 1)` at line 1857.
9. **Apply context register lists** — Call `gf100_gr_init_csdata` equivalents for HUB, GPC 0, GPC 1, TPC, and PPC, using the register lists defined in `grctx->hub`, `grctx->gpc_0`, `grctx->gpc_1`, `grctx->tpc`, `grctx->ppc` from `docs/hardware-model/gr.md`. Each list is a table of register writes.
10. **Clear HUB control register** — Write 0 to register `0x40910c` using `RegisterIO::write32()`, replacing line 1867.
11. **Start HUB ucode** — Write 2 to register `0x409100` using `RegisterIO::write32()`, replacing line 1868.
12. **Poll for HUB ready** — Loop reading register `0x409800` with `RegisterIO::read32()`, checking bit 31 (0x80000000), with a timeout of 2000 ms using `snooze()`.
13. **Read GR context size** — Read register `0x409804` to get the context size, replacing line 1877.
14. **Reset FECS Falcon** — Write 0x00000070 to register `0x409614`, delay 10 µs, set bits 0x700 of `0x409614`, and read back. This uses `RegisterIO::write32()`, `snooze()`, and `RegisterIO::read32()`.
15. **Leave out the external firmware path** — `gf100_gr_load` is not needed because the Haiku driver always uses the built-in arrays; `request_firmware` and `release_firmware` are D-ignore per `analysis/linux_deps.md`.

## Haiku interfaces

1. `` `RegisterIO::read32()` `` — `src/hw/RegisterIO.h`: reads a 32-bit value from a register offset; used for polling `0x409800`, reading `0x409804`, and reading back after FECS reset.
2. `` `RegisterIO::write32()` `` — `src/hw/RegisterIO.h`: writes a 32-bit value to a register offset; used for all register writes (0x000260, 0x40910c, 0x409100, 0x409614).
3. `` `snooze()` `` — `os/kernel/OS.h`: sleeps for a given number of microseconds; replaces `nvkm_msec(device, 2000, ...)` and the 10 µs delay after FECS reset.
4. `` `memcpy()` `` — `os/SupportDefs.h`: copies firmware blobs into the BAR-mapped MMIO region for Falcon data/code memory loads.
5. `` `dprintf()` `` — `os/kernel/debug.h`: prints debug messages when firmware loading fails or the HUB times out waiting for ready.

## Host tests

No host tests for firmware loading exist yet. The firmware arrays are validated by the manifest tool: `tools/fw_manifest.py` reads the source headers and checks sizes, hashes, and line ranges. The register write sequences for the firmware load are verified by `tests/test_registerio.cpp` when the firmware init function is written against the `RegisterIO` interface (MockMMIO captures the log, TraceMMIO replays it). The context register list application can be tested similarly once the pack functions are written.

## Not known

- What register `0x000260` does. `nvkm_mc_unk260` writes 0 to it before the uploads and 1 after (`nvkm/subdev/mc/gf100.c:64`); envytools has no name for it. MC is the master control subdevice; the purpose of the 0→1 toggle is unknown (C3e review).
- What the FECS and GPCCS ucode programs do after they start — the assembly source (`hubgk110.fuc3`, `gpcgk110.fuc3`) is available but not analysed in detail.
- The exact layout and meaning of the HUB, GPC, TPC, and PPC context register lists that `gf100_gr_init_csdata` programs.
- How the HUB ucode configures individual GPC Falcons after it starts; the GR model notes the HUB initialises the GPCs but does not describe the mechanism.
- Whether the built-in arrays are always identical to the external firmware files (`fuc409c`–`fuc41ad`), or if there are chipset-specific differences.
