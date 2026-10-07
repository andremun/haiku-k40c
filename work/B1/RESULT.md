# B1: Chipset path and file inventory — RESULT

## Chipset

The K40c (PCI ID 0x0f1) uses **`nvf1_chipset`** (GK110B), selected at
`reference/nouveau/nvkm/engine/device/base.c:3218` via `case 0x0f1` from
`PMC_BOOT_0` bits [28:20].

The struct is defined at `base.c:1770-1803` and contains **31 constructor
entries** — 22 subdevices and 9 engines.

## File inventory

All 31 constructor functions resolve to existing source files in
`reference/nouveau/`. No files are missing.

### Classification summary

| Class | Count | Files |
|---|---|---|
| GK110-specific | 6 | `gk110.c` (fb, i2c, pmu, fifo), `gk110.c` (disp), `gk110b.c` (gr) |
| GK104-inherited | 13 | clk, gpio, ltc, mc, mmu, pci, privring, therm, top, volt, ce, mspdec, msvld |
| GF100-inherited | 8 | bar, bus, devinit, fuse, iccsense, dma (gf119), msppp, sw |
| generic-NVKM | 4 | bios (base), imem (nv50), mxm (nv50), timer (nv41) |
| Linux-only | 0 | — |

### Subdevice mapping

| Subdevice | Constructor | File | Class |
|---|---|---|---|
| bar | `gf100_bar_new` | `nvkm/subdev/bar/gf100.c` | GF100-inherited |
| bios | `nvkm_bios_new` | `nvkm/subdev/bios/base.c` | generic-NVKM |
| bus | `gf100_bus_new` | `nvkm/subdev/bus/gf100.c` | GF100-inherited |
| clk | `gk104_clk_new` | `nvkm/subdev/clk/gk104.c` | GK104-inherited |
| devinit | `gf100_devinit_new` | `nvkm/subdev/devinit/gf100.c` | GF100-inherited |
| fb | `gk110_fb_new` | `nvkm/subdev/fb/gk110.c` | GK110-specific |
| fuse | `gf100_fuse_new` | `nvkm/subdev/fuse/gf100.c` | GF100-inherited |
| gpio | `gk104_gpio_new` | `nvkm/subdev/gpio/gk104.c` | GK104-inherited |
| i2c | `gk110_i2c_new` | `nvkm/subdev/i2c/gk110.c` | GK110-specific |
| iccsense | `gf100_iccsense_new` | `nvkm/subdev/iccsense/gf100.c` | GF100-inherited |
| imem | `nv50_instmem_new` | `nvkm/subdev/instmem/nv50.c` | generic-NVKM |
| ltc | `gk104_ltc_new` | `nvkm/subdev/ltc/gk104.c` | GK104-inherited |
| mc | `gk104_mc_new` | `nvkm/subdev/mc/gk104.c` | GK104-inherited |
| mmu | `gk104_mmu_new` | `nvkm/subdev/mmu/gk104.c` | GK104-inherited |
| mxm | `nv50_mxm_new` | `nvkm/subdev/mxm/nv50.c` | generic-NVKM |
| pci | `gk104_pci_new` | `nvkm/subdev/pci/gk104.c` | GK104-inherited |
| pmu | `gk110_pmu_new` | `nvkm/subdev/pmu/gk110.c` | GK110-specific |
| privring | `gk104_privring_new` | `nvkm/subdev/privring/gk104.c` | GK104-inherited |
| therm | `gk104_therm_new` | `nvkm/subdev/therm/gk104.c` | GK104-inherited |
| timer | `nv41_timer_new` | `nvkm/subdev/timer/nv41.c` | generic-NVKM |
| top | `gk104_top_new` | `nvkm/subdev/top/gk104.c` | GK104-inherited |
| volt | `gk104_volt_new` | `nvkm/subdev/volt/gk104.c` | GK104-inherited |

### Engine mapping

| Engine | Constructor | File | Class |
|---|---|---|---|
| ce | `gk104_ce_new` | `nvkm/engine/ce/gk104.c` | GK104-inherited |
| disp | `gk110_disp_new` | `nvkm/engine/disp/gk110.c` | GK110-specific |
| dma | `gf119_dma_new` | `nvkm/engine/dma/gf119.c` | GF100-inherited |
| fifo | `gk110_fifo_new` | `nvkm/engine/fifo/gk110.c` | GK110-specific |
| gr | `gk110b_gr_new` | `nvkm/engine/gr/gk110b.c` | GK110-specific |
| mspdec | `gk104_mspdec_new` | `nvkm/engine/mspdec/gk104.c` | GK104-inherited |
| msppp | `gf100_msppp_new` | `nvkm/engine/msppp/gf100.c` | GF100-inherited |
| msvld | `gk104_msvld_new` | `nvkm/engine/msvld/gk104.c` | GK104-inherited |
| sw | `gf100_sw_new` | `nvkm/engine/sw/gf100.c` | GF100-inherited |

## Outputs

- `analysis/files.json` — 31 entries in `{"path", "subsystem", "class", "role"}` format.
- `tools/nouveau_files.py` — Reusable script that extracts constructor entries from
  `nvf1_chipset`, resolves them to source files, classifies them, and writes
  `analysis/files.json`.
- `make check` — passes with 0 failures.

## Open questions

- None for this task. All 31 files verified to exist.
