# Phases and tasks

Order follows `docs/design/design.md` section 50 and the specification
section 10. Phases A-D run on Ubuntu without touching the GPUs. Each task
is one session. A task is done only when its outputs exist, its checks
pass (`make check`) and `docs/STATUS.md` is updated.

Paths to Nouveau files in any output are relative to `reference/nouveau/`
(for example `nvkm/engine/gr/gk110.c`). Line numbers are 1-based.

## Phase A: Ubuntu reference data

### A1. Hardware record
- Inputs: `reference/pci/*`, `docs/OPEN_QUESTIONS.md` (Q1).
- Outputs: `hardware/record.json`, `hardware/record.md`.
- `record.json` is a list, one object per K40c:
  `{"pci_address", "pci_id", "subsystem_id", "revision",
  "bars": [{"index", "base", "size", "flags"}], "numa_node", "vbios",
  "vram_mib", "link": {"speed", "width"},
  "nouveau_chipset": {"value", "status", "evidence"}}`.
  Hex values as strings (`"0xe6000000"`). `status` is KNOWN, INFERRED or
  UNKNOWN.
- Check: `make check` validates the format.

### A2. Root captures
- Inputs: `reference/pci/root/lspci-vvv-*.txt` (the two K40c files). Read
  `reference/pci/README.md` first.
- Outputs: add three fields to each object in `hardware/record.json`, and
  one section per card to `hardware/record.md` with the source line of
  each value. Do not change the A1 fields.
  - `"pci_capabilities"`: every `Capabilities: [...]` line of the capture,
    in order: `[{"offset": "0x60", "name": "Power Management", "version": 3}]`.
    `version` is the number after `version` or `v`; `null` if none.
  - `"interrupt"`: `{"pin": "A", "irq": 66, "msi": {"offset": "0x68",
    "enabled": true, "count": 1, "max_count": 1, "is_64bit": true,
    "maskable": false}}`, from the `Interrupt:` and `MSI:` lines.
  - `"link_capability"`: `{"speed": "8GT/s", "width": 16, "aspm": "not
    supported"}` from `LnkCap`. The existing `"link"` field stays as the
    current state; check that `LnkSta` agrees with it and say so in
    `record.md`.
- Check: `make check` compares the capability offsets and the IRQ with the
  capture, and requires the three fields when A2 is marked DONE.
- This task is only the three fields above. Write `work/A2/PLAN.md` and
  `work/A2/RESULT.md` for it (replace older files of that name).

## Phase B: Nouveau dependency extraction

### B1. Chipset path and file inventory
- Find the chipset entry for this card in `nvkm/engine/device/base.c`.
  For each subdevice and engine on the compute path (bar, bus, fb, imem,
  ltc, mc, mmu, pci, privring, top, fifo, gr, ce, and what they need),
  follow the constructor to every file that implements it, including the
  inherited gk104, gf100 and nv50 code.
- Outputs: `tools/nouveau_files.py`, `analysis/files.json`: a list of
  `{"path", "subsystem", "class", "role"}` where `class` is one of
  `GK110-specific`, `GK104-inherited`, `GF100-inherited`,
  `generic-NVKM`, `Linux-only`.
- Check: every path exists. Every constructor named in the chipset entry
  for the listed subdevices has its file listed. `make check` also
  requires the list to be closed inside each directory: when a listed
  file uses a function or table that another file of the same directory
  defines, that file is listed too. Example: `gr/gk110b.c` only calls
  `gf100_gr_new_()`, so `gr/gf100.c` and the files that it uses belong to
  the list. For the 13 subsystems above that is about 88 files.
- The tool must find the files by reading the source (constructor, then
  the functions and tables that each file uses). A table of names written
  by hand in the tool is not accepted.
- Subsystems that are not on the compute path (disp, mspdec, msppp,
  msvld, sw, ...) may be left out. A subsystem that is listed must be
  closed. Files in other directories that the path needs (for example
  `nvkm/core/`, `nvkm/falcon/`) are your decision: list them and say why
  in `role`.
- `class` comes from what the file is, not only from its name: a
  `base.c`, `chan.c` or `vmm.c` that all chips share is `generic-NVKM`.
  `role` says what the file does on this card's path in a few words.

### B2. Call graph
- Outputs: `tools/callgraph.py`, `analysis/callgraph.json`
  (`{"nodes": [{"name", "file", "line"}], "edges": [["caller", "callee"]]}`,
  `line` = line of the function definition), plus a readable
  `analysis/callgraph.md`.
- Scope: from the chipset constructors down through the init paths of fb,
  mmu, fifo and gr.
- Check: each node's `file:line` defines that function.

### B3. MMIO access extraction
- Outputs: `tools/extract_mmio.py`,
  `registers/mmio_accesses.json`: a list of
  `{"file", "line", "function", "op", "reg", "reg_value", "value",
  "mask", "subsystem"}`. `op` is `rd32`, `wr32` or `mask`. `reg_value` is
  the integer value when `reg` is a constant, else `null`.
- Scope: every `nvkm_rd32`, `nvkm_wr32`, `nvkm_mask` in the files of
  `analysis/files.json`.
- Check: each `file:line` contains the call. Report the count per file
  and compare it with `grep -c` in `RESULT.md`.

### B4. Linux dependency map
- Outputs: `tools/linux_deps.py`, `analysis/linux_deps.json`: a list of
  `{"file", "line", "symbol", "category", "haiku_api", "note"}`.
  `category` uses the design document section 7: `A-reimplement`,
  `B-extract`, `C-replace`, `D-ignore`.
- Check: `haiku_api` names exist in `reference/haiku/headers`.

### B5. Minimum chain to one computation
- Outputs: `analysis/min_chain.json` (ordered steps
  `{"step", "subsystem", "functions", "registers", "firmware", "status",
  "notes"}`) and `analysis/min_chain.md`.
- Must say which parts of the GR path are needed for compute and which
  are graphics-only, and which firmware is needed and where it comes from.

## Phase C: hardware database and firmware

### C1. Register database
- Outputs: `tools/build_regdb.py`, `hardware/registers/<subsystem>.yaml`
  (mc, fb, mmu, fifo, pbdma, gr, compute). Entry format: design document
  section 16 (`name, address, width, reset_value, readable, writable,
  fields[name, shift, width, description], source, notes`), plus
  `status` (SOURCE_ONLY, TRACE_VERIFIED, HARDWARE_VERIFIED, HAIKU_VERIFIED).
- Names come from envytools `rnndb`. Addresses are absolute.
- Check: every entry has `name`, `address`, `source`, `status`.

### C2. Firmware
- Outputs: `firmware/README.md`, `firmware/manifest.yaml`
  (`filename, source, version, hash, license, distribution status,
  required engine`).
- Covers the FECS and GPCCS microcode for this chipset and how Nouveau
  builds and loads it.

### C3. Subsystem hardware model
- Outputs: `docs/hardware-model/<name>.md` for pci, bars, mmio, mc,
  fb-vram, instmem, bar, mmu, fifo, channel, gpfifo, runlist, pbdma, gr,
  falcon-firmware. Each has: purpose, Nouveau files, registers,
  dependencies, and sections `KNOWN`, `INFERRED`, `UNKNOWN`.
- Check: files exist, have the three sections, cite existing files.

### C4. Design documents
- Outputs: `docs/04-mmu-design.md`, `docs/05-fifo-design.md`,
  `docs/06-gr-design.md`, `docs/07-firmware-analysis.md`,
  `docs/register-provenance.md` (design document sections 48 and 65).

## Phase D: host-side algorithms and tests

Plain C++17 built with `g++` on Ubuntu. `tests/Makefile` builds and runs
the tests. `make check` runs them.

### D1. Register access abstraction
- `RegisterIO` with `MockMMIO` and `TraceMMIO` (design document section
  45), with tests.

### D2. GK104 page-table encoding
- Page directory and page table entry encoding and a map/unmap model,
  from B2/C3, with tests against values derived from the source.

### D3. GPFIFO and push-buffer encoding
- GPFIFO entry and method encoding, with tests.

### D4. Register-trace comparison tool
- `tools/compare_register_traces.py` (design document section 41), with
  tests on synthetic traces.

## Gate: end of phase D

The user reviews phases A-D before any Haiku work. Phases E-N (Haiku PCI
skeleton, MMIO, MC/FB/VRAM, MMU, FIFO/PBDMA, GR/Falcon, GPFIFO and
submission, first computation, interrupts, user-space API) are planned
at the gate. They need a Haiku boot and GPU access, so the user runs them.
