# B1 Rework: Chipset path and file inventory

## Problem
The first attempt only listed the 31 constructor files. The check finds 89
files used by those files but not listed. The tool uses a hand-written
CONSTRUCTOR_MAP instead of reading the source.

## Steps

1. Rewrite `tools/nouveau_files.py`:
   a. Parse `nvf1_chipset` from `base.c` to get constructor function names.
   b. For each constructor, find the file that defines it by scanning all `.c`
      files in the Nouveau tree.
   c. **Iterative closure**: for every file found, scan for function/table
      references whose definition lives in the same directory. Add those files.
      Repeat until no new files are found.
   d. Classify each file by basename rules (GK110-specific, GK104-inherited,
      GF100-inherited, generic-NVKM). Files outside compute-path dirs are
      generic-NVKM with a reason in `role`.
   e. Scope: bar, bus, fb, imem, ltc, mc, mmu, pci, privring, top, fifo, gr, ce.
      Subsystems not in this list may appear if pulled in by closure.

2. Run the tool: `python3 tools/nouveau_files.py`.
3. Run `make check`. If it still fails, iterate the closure (some files pull
   in more files).

## Outputs
- `tools/nouveau_files.py` (rewritten)
- `analysis/files.json` (updated)
- `work/B1/RESULT.md` (updated with counts)
- `make check` passes.
