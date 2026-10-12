# Task C4b Result

Four design documents written, each verified by `make check` with 0 failures.

## Outputs

1. `docs/07-firmware-analysis.md` (2026-10-12) — FECS/GPCCS firmware arrays,
   external firmware files, load sequences. 4 built-in firmware arrays, 4
   external files, 17 load-sequence calls.

2. `docs/04-mmu-design.md` (2026-10-12) — MMU init, kind table, VMM address
   space, PTE/PDE encoding, instance-block PDB/limit, BAR setup. 17 Nouveau
   citations, 11 Haiku design steps, 4 Haiku interfaces.

3. `docs/05-fifo-design.md` (2026-10-12) — FIFO init, PBDMA init, run queues,
   channel bind/start, RAMFC write, USERD setup, MC init. 28 Nouveau
   citations, 14 Haiku design steps, 5 Haiku interfaces.

4. `docs/06-gr-design.md` (2026-10-12) — GR engine init with firmware load,
   FECS reset, 10 init hooks, GR context generation, ZBC clear path. 17
   Nouveau citations, 21 Haiku design steps, 5 Haiku interfaces.

## Commits

- `c22f561` C4b: GR engine design document (docs/06-gr-design.md)
- Previous commits for 04-mmu-design.md, 05-fifo-design.md, 07-firmware-analysis.md

## Not known (from all four documents)

### MMU (04-mmu-design.md)
- MMU read/write scratch buffer size and purpose
- MMU TLB flush register after page-table updates
- Kind lookup table mapping to hardware compression formats

### FIFO (05-fifo-design.md)
- Purpose of 7 of 15 RAMFC words (only USERD address, CB address, channel ID are clear)
- PBDMA run queue status register bit-field layout (bits 13–15)
- Which PBDMA units exist on GK110B and the enable mask
- GPC runlist group entry layout

### GR (06-gr-design.md)
- Whether GR MMIO tables contain drawing-only writes that are harmless but wasted
- Exact GR context image buffer layout and on-card meaning of sub-buffers
- Whether graphics-only hooks (zcull, ROP) are truly optional for compute

### Firmware (07-firmware-analysis.md)
- What the FECS and GPCCS microcode does beyond loading data into Falcon memory
- Whether the firmware load sequence can be simplified for compute-only use
- Exact size of each firmware array (sizeof values)

## Open questions for C5 (reference run)

Before S3 work can start, the compute shader must run on the K40c under Linux
with Nouveau and Mesa (task C5). If it does not run there, there is no
reference for the GR engine init sequence and the project stops at S2.
