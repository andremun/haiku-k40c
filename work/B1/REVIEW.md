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

# Second review (2026-10-07, commit f433fd3) — REWORK

Reviewer: Claude (Anthropic), at the user's request.

## Accepted

- The file list: 88 files, closed inside each directory. Do not change it.
- The tool finds the files from the source. The hand-written table is gone.

## Defects

| File | Problem | Evidence | Severity |
|---|---|---|---|
| `tools/nouveau_files.py` | The output differs between runs. `work/B1/RESULT.md` does not say so, and the first version of the tool claimed the opposite. | Two runs changed `role` in about 30 entries (`nvkm_cgrp_ref` became `nvkm_cgrp_new`, `gk104_runl_pending` became `gk104_runl_allow`). The tool iterates over Python sets, and their order changes between runs. | High |
| `analysis/files.json` | `role` is a symbol name and the subsystem ("gk104_runl_pending — fifo"). It does not say what the file provides. This was a defect in the first review. The result lists it under "Open questions" and leaves it. | Every entry. | High |
| `analysis/files.json` | 54 of 88 files are `generic-NVKM`, with files that carry a chip name among them (`gf108.c`, `gt215.c`, `nv50.c`, `r535.c`). | `classify()` in the tool. The class list had no place for other chips: `other-chip` is new in `docs/PHASES.md`. | Medium |
| `work/B1/RESULT.md` | Still calls 0x0f1 a PCI ID (first review). It is the chipset field of PMC_BOOT_0. | Line 5. | Low |
| `work/B1/RESULT.md` | Says the chipset is selected at `base.c:1770`. Line 1770 is the start of the `nvf1_chipset` table. The selection (`case 0x0f1`) is at `reference/nouveau/nvkm/engine/device/base.c:3218`. | Lines 5-6. | Low |
| Session | The session started task B2 after the B1 handoff. `AGENTS.md`: one task, handoff, stop. | `work/B2/PLAN.md`. | Process |

## What the rework needs

`docs/PHASES.md`, task B1, has the exact rules. `make check` verifies
the first three.

1. Make the tool give the same output on every run (sort every set) and
   add `--check`.
2. Generate `role` in the required form.
3. Generate `class` from the chip name in the file name, with `other-chip`.
4. Correct the two statements in `work/B1/RESULT.md` and update its
   class counts.
5. `make check`, handoff, stop.
