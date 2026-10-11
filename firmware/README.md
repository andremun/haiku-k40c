# Firmware Manifest

## Which code

The GK110 GR (graphics/compute) engine requires two small programs to be
loaded onto its built-in Falcon controllers before any rendering or compute
can proceed:

| Array | File | Engine | Kind | Words | Size |
|---|---|---|---|---|---|
| `gk110_grhub_data` | `nvkm/engine/gr/fuc/hubgk110.fuc3.h:2` | fecs | data | 193 | 772 B |
| `gk110_grhub_code` | `nvkm/engine/gr/fuc/hubgk110.fuc3.h:209` | fecs | code | 768 | 3072 B |
| `gk110_grgpc_data` | `nvkm/engine/gr/fuc/gpcgk110.fuc3.h:2` | gpccs | data | 27 | 108 B |
| `gk110_grgpc_code` | `nvkm/engine/gr/fuc/gpcgk110.fuc3.h:44` | gpccs | code | 448 | 1792 B |

The two `.fuc3` assembly sources that generate these arrays are
`nvkm/engine/gr/fuc/hubgk110.fuc3` and `nvkm/engine/gr/fuc/gpcgk110.fuc3`,
with copyright:

    Copyright 2013 Red Hat Inc.
    Authors: Ben Skeggs <bskeggs@redhat.com>

License: MIT (SPDX identifier in `hubgk110.fuc3.h:1` and `gpcgk110.fuc3.h:1`).

This is **Nouveau's own code, not NVIDIA's firmware**. The Nouveau
developers wrote it in Falcon assembly (the `.fuc3` files, copyright Red
Hat, author Ben Skeggs) as a replacement for NVIDIA's microcode, and the
headers hold the assembled result. It is MIT-licensed like the rest of
Nouveau. The Haiku driver must load these same arrays.

## How Nouveau chooses

The firmware loading path is selected by the `gf100_gr_fwif` table in
`nvkm/engine/gr/gf100.c:2613`, which has two entries:

1. `gf100_gr_load` — tried first, and used only when the `NvGrUseFW`
   option is set to true. This function (at `gf100.c:2595`) calls `gf100_gr_load_fw`
   four times to load external firmware files:
   `fuc409c` (FECs instruction), `fuc409d` (FECs data), `fuc41ac`
   (GPCCS instruction), `fuc41ad` (GPCCS data).

2. `gf100_gr_nofw` — **the default path**: taken when `NvGrUseFW` is
   false, and false is the default when the option is not set. This function
   (at `gf100.c:2561`) simply sets `gr->firmware = false` and returns
   success, meaning the driver uses the built-in arrays instead.

For GK110, the `gk110b_gr_fwif` table in
`nvkm/engine/gr/gk110b.c:143` uses the same two entries, pointing to
`gk110b_gr`. Without the option, `gf100_gr_load` fails, `gf100_gr_nofw`
is taken and the built-in arrays are used. This is the path that the
Haiku driver reproduces.

The `gf100_gr_load` function checks the `NvGrUseFW` option first
(`gf100.c:2599`):

```c
if (!nvkm_boolopt(device->cfgopt, "NvGrUseFW", false))
    return -EINVAL;
```

If the option is false it returns `-EINVAL`, falling through to the
`gf100_gr_nofw` handler.

## How it is loaded

Once the firmware is selected (built-in arrays), the GR engine is
initialised by `gf100_gr_init_ctxctl_int` at
`nvkm/engine/gr/gf100.c:1831`, which performs these 17 steps:

1. **Line 1842** `nvkm_mc_unk260(device, 0)` — write 0 to master
   control register `0x000260` (`nvkm/subdev/mc/gf100.c:64`).
2. **Line 1843** `nvkm_falcon_load_dmem()` — load FECS data memory from
   `gk110_grhub_data` into the Falcon's data RAM.
3. **Line 1846** `nvkm_falcon_load_imem()` — load FECS instruction
   memory from `gk110_grhub_code` into the Falcon's instruction RAM.
4. **Line 1851** `nvkm_falcon_load_dmem()` — load GPCCS data memory from
   `gk110_grgpc_data`.
5. **Line 1854** `nvkm_falcon_load_imem()` — load GPCCS instruction
   memory from `gk110_grgpc_code`.
6. **Line 1857** `nvkm_mc_unk260(device, 1)` — write 1 to the same
   register, after both uploads.
7. **Line 1860** `gf100_gr_init_csdata(gr, grctx->hub, ...)` — set up
   HUB context register data.
8. **Line 1861** `gf100_gr_init_csdata(gr, grctx->gpc_0, ...)` — GPC 0.
9. **Line 1862** `gf100_gr_init_csdata(gr, grctx->gpc_1, ...)` — GPC 1.
10. **Line 1863** `gf100_gr_init_csdata(gr, grctx->tpc, ...)` — TPC.
11. **Line 1864** `gf100_gr_init_csdata(gr, grctx->ppc, ...)` — PPC.
12. **Line 1867** `nvkm_wr32(device, 0x40910c, 0x00000000)` — clear HUB
    control register.
13. **Line 1868** `nvkm_wr32(device, 0x409100, 0x00000002)` — start the
    HUB ucode running.
14. **Line 1869** `nvkm_msec(device, 2000, ...)` — wait up to 2 s for
    the HUB to signal it is ready.
15. **Line 1870** `nvkm_rd32(device, 0x409800)` — poll the HUB status
    register.
16. **Line 1873** `gf100_gr_ctxctl_debug(gr)` — if the HUB did not
    become ready, debug the context control registers.
17. **Line 1877** `nvkm_rd32(device, 0x409804)` — read the GR context
    size from the hardware.

The HUB ucode initialises the GPCs, so the GPC Falcon controllers are
configured by the HUB ucode itself; the driver only loads the code into
their instruction/data memory.

## What the Haiku driver must do

The Haiku driver must:

1. **Load `gk110_grhub_data`** (193 words, 772 bytes) into the HUB
   Falcon's data memory at offset 0.
2. **Load `gk110_grhub_code`** (768 words, 3072 bytes) into the HUB
   Falcon's instruction memory at offset 0.
3. **Load `gk110_grgpc_data`** (27 words, 108 bytes) into each GPC
   Falcon's data memory at offset 0.
4. **Load `gk110_grgpc_code`** (448 words, 1792 bytes) into each GPC
   Falcon's instruction memory at offset 0.
5. **Write 0 to register `0x000260` before the uploads** (step 1 above).
6. **Write 1 to register `0x000260` after the uploads** (step 6 above).
7. **Initialize context register lists** for HUB, GPC 0, GPC 1, TPC,
   and PPC.
8. **Start the HUB ucode** and wait for it to signal readiness.
9. **Read the GR context size** from the hardware.

The built-in firmware arrays are generated by this project's tool and
may be distributed as part of the Haiku driver (they are MIT-licensed,
same as Haiku). The external firmware files (`fuc409c`–`fuc41ad`) are
NVIDIA's proprietary microcode, extracted from NVIDIA's driver. They are
not in the Linux source, this project marks them `do-not-distribute`,
and the Haiku driver does not need them: it uses the built-in arrays.

## Not known

- What register `0x000260` does. `nvkm_mc_unk260` writes 0 to it before
  the uploads and 1 after them (`nvkm/subdev/mc/gf100.c:64`); envytools
  has no name for it. MC is the master control, not a memory controller.
- What the FECS and GPCCS ucode programs do after they start — the
  assembly source is available but not analysed in detail.
- The exact layout and meaning of the HUB and GPC context register lists
  that `gf100_gr_init_csdata` programs.
- How the HUB ucode configures individual GPC Falcons after it starts.
- Whether the built-in arrays are always identical to the external
  firmware files, or if there are chipset-specific differences.
