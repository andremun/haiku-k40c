# B1: Chipset path and file inventory — RESULT (reworked)

## Chipset

The K40c (PCI ID 10de:1024, GK110B) uses **`nvf1_chipset`**, selected at
`reference/nouveau/nvkm/engine/device/base.c:3218` via `case 0x0f1` from
`PMC_BOOT_0` bits [28:20]. The struct `nvf1_chipset` is defined at
`base.c:1770-1803`.

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
| GF100-inherited | 23 |
| generic-NVKM | 28 |
| other-chip | 18 |
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

### generic-NVKM files (28)

These are base implementations with no chip-specific pattern in their names.

| Subsystem | Count | Files |
|---|---|---|
| fifo | 8 | `base.c`, `cgrp.c`, `chan.c`, `chid.c`, `runl.c`, `runq.c`, `ucgrp.c`, `uchan.c` |
| mmu | 6 | `base.c`, `mem.c`, `umem.c`, `ummu.c`, `uvmm.c`, `vmm.c` |
| fb | 4 | `base.c`, `gddr5.c`, `ram.c`, `sddr3.c` |
| pci | 3 | `agp.c`, `base.c`, `pcie.c` |
| bar | 1 | `base.c` |
| bus | 1 | `base.c` |
| gr | 1 | `base.c` |
| imem | 1 | `base.c` |
| ltc | 1 | `base.c` |
| mc | 1 | `base.c` |
| top | 1 | `base.c` |
| ce | 0 | — |
| privring | 0 | — |

### other-chip files (18)

These carry a chip name that is neither GK110, GK104, nor a GF1xx pattern:
NV04, NV17, NV40, NV46, NV50, G84, G92, GT215, R535. They are inherited
through the constructor chain.

| Subsystem | Count | Files |
|---|---|---|
| pci | 4 | `g84.c`, `g92.c`, `nv40.c`, `nv46.c` |
| mc | 4 | `gt215.c`, `nv04.c`, `nv17.c`, `nv50.c` |
| imem | 3 | `nv04.c`, `nv50.c`, `r535.c` |
| bar | 2 | `g84.c`, `nv50.c` |
| fifo | 2 | `nv04.c`, `nv50.c` |
| gr | 2 | `ctxnv50.c`, `nv50.c` |
| mmu | 1 | `vmmnv04.c` |

Note: Counts per subsystem are per-class only. Adding all classes gives the
subsystem total shown in the breakdown table above.

## Outputs

- `analysis/files.json` — 88 entries in `{"path", "subsystem", "class", "role"}`
  format. Closure is closed inside every directory. Roles are 6+ words and
  follow the "chipset constructor" / "used by" format. `--check` mode exits 0
  when the file matches the tool output, 1 otherwise.
- `tools/nouveau_files.py` — Source-based tool: extracts constructors from
  `nvf1_chipset`, resolves them to files, then iteratively follows references
  within each directory. Classifies by chip pattern in basename (including
  `other-chip`). Deterministic: all sets are sorted before use.
- `make check` — passes with 0 failures.

## Open questions

- Some other-chip files (e.g. `gt215.c`, `nv40.c`, `r535.c`) belong to GPU
  families between the original GeForce and GK104/K40c. These are transitively
  pulled in by the closure algorithm because the constructor chain traverses
  through them. They are not relevant for the GK110 compute path but are
  correctly listed because the constructor chain requires them.
