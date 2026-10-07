# B1: Chipset path and file inventory — RESULT (reworked)

## Chipset

The K40c (PCI ID 0x0f1) uses **`nvf1_chipset`** (GK110B), selected at
`reference/nouveau/nvkm/engine/device/base.c:1770` via `case 0x0f1` from
`PMC_BOOT_0` bits [28:20].

The struct is defined at `base.c:1770-1803` and contains **31 constructor
entries** — 22 subdevices and 9 engines.

## Tool

`tools/nouveau_files.py` was rewritten to derive the file list from source
code instead of a hand-written map. It:

1. Extracts constructor names from `nvf1_chipset` in `base.c`.
2. Finds the file that defines each constructor using the same scan patterns
   as `check_repo.py`.
3. Iteratively follows every function/table reference within each directory
   until the list is closed (closure).

## File inventory — 88 entries

### Classification summary

| Class | Count |
|---|---|
| GK110-specific | 6 |
| GK104-inherited | 13 |
| GF100-inherited | 15 |
| generic-NVKM | 54 |
| Linux-only | 0 |

### Subsystem breakdown (compute-path subsystems)

| Subsystem | Count |
|---|---|
| fifo | 13 |
| gr | 20 |
| mmu | 12 |
| fb | 10 |
| pci | 9 |
| mc | 7 |
| imem | 4 |
| bar | 4 |
| ltc | 3 |
| top | 2 |
| bus | 2 |
| ce | 1 |
| privring | 1 |

### GK110-specific files (6)

| Subsystem | File | Role |
|---|---|---|
| fifo | `nvkm/engine/fifo/gk110.c` | `gk110_fifo_new` |
| gr | `nvkm/engine/gr/ctxgk110.c` | `gk110_grctx` |
| gr | `nvkm/engine/gr/ctxgk110b.c` | `gk110b_grctx` |
| gr | `nvkm/engine/gr/gk110.c` | `gk110_gr_init_gpc_unk_1` |
| gr | `nvkm/engine/gr/gk110b.c` | `gk110b_gr_new` |
| fb | `nvkm/subdev/fb/gk110.c` | `gk110_fb_new` |

### GK104-inherited files (13)

| Subsystem | File | Role |
|---|---|---|
| ce | `nvkm/engine/ce/gk104.c` | `gk104_ce_new` |
| fifo | `nvkm/engine/fifo/gk104.c` | `gk104_runl_pending` |
| gr | `nvkm/engine/gr/ctxgk104.c` | `gk104_grctx` |
| gr | `nvkm/engine/gr/gk104.c` | `gk104_gr_init_sked_hww_esr` |
| fb | `nvkm/subdev/fb/gk104.c` | `gk104_fb_clkgate_blcg_init_main_0` |
| fb | `nvkm/subdev/fb/ramgk104.c` | `gk104_ram_new` |
| ltc | `nvkm/subdev/ltc/gk104.c` | `gk104_ltc_new` |
| mc | `nvkm/subdev/mc/gk104.c` | `gk104_mc_new` |
| mmu | `nvkm/subdev/mmu/gk104.c` | `gk104_mmu_new` |
| mmu | `nvkm/subdev/mmu/vmmgk104.c` | `gk104_vmm_new` |
| pci | `nvkm/subdev/pci/gk104.c` | `gk104_pci_new` |
| privring | `nvkm/subdev/privring/gk104.c` | `gk104_privring_new` |
| top | `nvkm/subdev/top/gk104.c` | `gk104_top_new` |

### GF100-inherited files (15)

| Subsystem | File | Role |
|---|---|---|
| fifo | `nvkm/engine/fifo/gf100.c` | `gf100_fifo_intr_mmu_fault_unit` |
| gr | `nvkm/engine/gr/ctxgf100.c` | `gf100_grctx` |
| gr | `nvkm/engine/gr/ctxgf119.c` | `gf119_grctx` |
| gr | `nvkm/engine/gr/gf100.c` | `gf100_gr_init_fecs_exceptions` |
| gr | `nvkm/engine/gr/gf119.c` | `gf119_gr_init_prop_0` |
| bar | `nvkm/subdev/bar/gf100.c` | `gf100_bar_new` |
| bus | `nvkm/subdev/bus/gf100.c` | `gf100_bus_new` |
| fb | `nvkm/subdev/fb/gf100.c` | `gf100_fb_init_page` |
| fb | `nvkm/subdev/fb/ramgf100.c` | `gf100_ram_new` |
| ltc | `nvkm/subdev/ltc/gf100.c` | `gf100_ltc_zbc_clear_color` |
| mc | `nvkm/subdev/mc/gf100.c` | `gf100_mc_unk260` |
| mmu | `nvkm/subdev/mmu/gf100.c` | `gf100_mmu_kind` |
| mmu | `nvkm/subdev/mmu/memgf100.c` | `gf100_mem_map` |
| mmu | `nvkm/subdev/mmu/vmmgf100.c` | `gf100_vmm_aper` |
| pci | `nvkm/subdev/pci/gf100.c` | `gf100_pcie_set_cap_speed` |

### generic-NVKM files (54)

These cover NV04, NV17, NV40, NV41, NV46, NV50, G84, G92, GF104, GF108,
GT215, and base implementations across all compute-path subsystems.

| Subsystem | Count | Files |
|---|---|---|
| fifo | 10 | `base.c`, `cgrp.c`, `chan.c`, `chid.c`, `nv04.c`, `nv50.c`, `runl.c`, `runq.c`, `ucgrp.c`, `uchan.c` |
| gr | 10 | `base.c`, `ctxgf104.c`, `ctxgf108.c`, `ctxgf110.c`, `ctxgf117.c`, `ctxnv50.c`, `gf104.c`, `gf108.c`, `gf117.c`, `nv50.c` |
| mmu | 7 | `base.c`, `mem.c`, `umem.c`, `ummu.c`, `uvmm.c`, `vmm.c`, `vmmnv04.c` |
| pci | 7 | `agp.c`, `base.c`, `g84.c`, `g92.c`, `nv40.c`, `nv46.c`, `pcie.c` |
| fb | 5 | `base.c`, `gddr5.c`, `ram.c`, `ramgf108.c`, `sddr3.c` |
| mc | 5 | `base.c`, `gt215.c`, `nv04.c`, `nv17.c`, `nv50.c` |
| imem | 4 | `base.c`, `nv04.c`, `nv50.c`, `r535.c` |
| bar | 3 | `base.c`, `g84.c`, `nv50.c` |
| ltc | 1 | `base.c` |
| top | 1 | `base.c` |
| bus | 1 | `base.c` |
| ce | 0 | — |
| privring | 0 | — |

Note: Counts per subsystem are generic-NVKM only. Adding chip-specific files
gives the subsystem total shown in the breakdown table above.

## Outputs

- `analysis/files.json` — 88 entries in `{"path", "subsystem", "class", "role"}`
  format. Closure is closed inside every directory.
- `tools/nouveau_files.py` — Source-based tool: extracts constructors from
  `nvf1_chipset`, resolves them to files, then iteratively follows references
  within each directory. Classifies by chip pattern in basename.
- `make check` — passes with 0 failures.

## Open questions

- Some generic-NVKM files (e.g. `gt215.c`, `gf104.c`, `gf108.c`) belong to
  GPU families between GF100 and GK104. These are not relevant for the
  GK110/K40c compute path but are transitively pulled in by closure.
- The `role` field shows the defining function/table name. It does not
  describe the file's purpose in natural language.
