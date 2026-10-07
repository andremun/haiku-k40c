# B1: review (2026-10-07) — REWORK

Reviewer: Claude (Anthropic), at the user's request. The first attempt is
commit ff49f4d.

## What is correct

- The chipset entry: `nvf1_chipset`, `reference/nouveau/nvkm/engine/device/base.c:1770`,
  31 constructors (22 subdevices, 9 engines).
- Each of the 31 constructors is defined in the file that the inventory
  gives for it.

## Defects

| File | Problem | Evidence | Severity |
|---|---|---|---|
| `analysis/files.json` | Lists only the file that defines each constructor. The task says to follow the constructor "to every file that implements it, including the inherited gk104, gf100 and nv50 code". | `reference/nouveau/nvkm/engine/gr/gk110b.c:153` only calls `gf100_gr_new_()`. That file has 0 MMIO accesses and `nvkm/engine/gr/gf100.c` has 246. `nvkm/engine/fifo/gk110.c` has 1 and `nvkm/engine/fifo/gk104.c` has 45. `nvkm/subdev/mmu/gk104.c` has 0 and points to `gk104_vmm_new` (`vmmgk104.c`). | High: B2 and B3 take their scope from this file and would miss most of the code. |
| `tools/nouveau_files.py` | `CONSTRUCTOR_MAP` is a table of constructor to file written by hand. The tool reads the chipset entry and then looks each name up in that table. It cannot find an inherited file. | `tools/nouveau_files.py`, `CONSTRUCTOR_MAP`. | High |
| `analysis/files.json` | `class` comes from the file name only, so `Linux-only` can never occur and shared files have no rule. | `classify()` in the tool. | Medium |
| `analysis/files.json` | `role` repeats the constructor and the subsystem name ("gf100_bar_new — bar (bar)"). It does not say what the file does. | Every entry. | Low |
| `work/B1/RESULT.md` | Calls 0x0f1 a PCI ID. It is the chipset field of PMC_BOOT_0 (bits 28:20). The PCI ID is 10de:1024. | `hardware/record.md`. | Low |

## Why `make check` passed

It checked only that each path exists and that `class` is an allowed
value. It now also checks what the first defect describes (see
`docs/PHASES.md`, task B1). On the first attempt it reports 89 files that
are not listed.

## What the rework needs

1. Rewrite `tools/nouveau_files.py` so that it finds the files from the
   source: the constructor of each compute-path subsystem, then, again
   and again, the files that define the functions and tables that the
   files found so far use. Do not write file names into the tool.
2. Scope: bar, bus, fb, imem, ltc, mc, mmu, pci, privring, top, fifo, gr,
   ce. Leave the other subsystems out unless the path needs them. The
   closed list for these 13 has about 88 files in their own directories.
3. Decide which files outside those directories the path needs and give
   the reason in `role`.
4. Write `work/B1/RESULT.md` again with the counts per subsystem and per
   class. Replace `work/B1/PLAN.md`.
5. `make check` must pass. Then run the handoff.
