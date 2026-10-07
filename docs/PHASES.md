# Phases and tasks

Order follows `docs/design/design.md` section 50 and the specification
section 10. Phases A-D run on Ubuntu without touching the GPUs. Each task
is one session. A task is done only when its outputs exist, its checks
pass (`make check`) and `docs/STATUS.md` is updated.

Paths to Nouveau files in any output are relative to `reference/nouveau/`
(for example `nvkm/engine/gr/gk110.c`). Line numbers are 1-based.

## Success milestones (set 2026-10-07)

The design documents name one goal: a verified compute job. That goal is
far away and has parts that the first plan did not list (S3 below). The
project now has three success milestones. Each one is a result on its
own, and the work may stop at any of them.

| ID | Milestone | Needs | Proof |
|---|---|---|---|
| S1 | The GPU accepts a command. A channel exists, a GPFIFO entry is submitted, and the GPU consumes it. | PCI, MMIO, MC, FB/VRAM, instance memory, MMU, FIFO/PBDMA, runlist. No GR, no firmware. | The GPFIFO GET pointer of the channel advances to PUT, read from the host, with no fault interrupt pending. |
| S2 | The GPU copies a buffer. The copy engine (class `KEPLER_DMA_COPY_A`) copies N bytes between two buffers in VRAM. | S1 and the copy engine (`nvkm/engine/ce/gk104.c`). INFERRED: no firmware and no GR context are needed (the file has no falcon or firmware code). Task C3 must confirm it. | The host reads the destination buffer and it equals the source. |
| S3 | The GPU computes. A compute shader does `output[i] = input[i] + 1`. | S1, the GR engine with FECS/GPCCS firmware and a GR context, the compute class `0xa1c0`, a launch descriptor, and a shader binary in GK110 machine code. The last two are user-space work that Nouveau's kernel driver does not contain: they are in Mesa (`reference/mesa`). Tasks B6, C5 and D5 cover them. | The host reads the output buffer and checks every element. |

S1 is the first success criterion of the project. S2 is the first real
work done by the GPU. S3 is the goal of the design documents.

Before S3 work starts on Haiku, the same job must run on this card under
Linux with Nouveau and Mesa (task C5, in a Linux guest with the card
passed through: `docs/PASSTHROUGH.md`). If it does not run there, there
is no reference for S3 and the project stops at S2.

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
  `GK110-specific`, `GK104-inherited`, `GF100-inherited`, `other-chip`,
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
- `class` follows the chip name in the file name (`make check` verifies
  it): `gk110` is `GK110-specific`; `gk104` is `GK104-inherited`;
  `gf100` to `gf119` is `GF100-inherited`; another chip name (`nv04`,
  `nv50`, `g84`, `gt215`, `r535`, ...) is `other-chip`; no chip name
  (`base.c`, `chan.c`, `vmm.c`) is `generic-NVKM`. Use `Linux-only` only
  for a file that has no hardware code, and give the reason in `role`.
- `role` is one sentence of 6 words or more that the tool generates. It
  says what the file provides and how the path reaches it. A constructor
  file says `chipset constructor <name>`. Every other file says
  `used by <path of a listed file> (<symbol>)`. Examples:
  "GR engine entry: chipset constructor gk110b_gr_new, calls gf100_gr_new_"
  and "Fermi GR implementation, used by nvkm/engine/gr/gk110b.c (gf100_gr_new_)".
  When several files or symbols qualify, take the first in sorted order.
- The tool gives the same output on every run. `tools/nouveau_files.py
  --check` writes nothing and exits 0 when `analysis/files.json` is what
  the tool generates, else 1. `make check` runs it twice. Sort every set
  before you use it: Python changes the order of a set between runs.

### B2. Call graph
- Outputs: `tools/callgraph.py`, `analysis/callgraph.json`
  (`{"nodes": [{"name", "file", "line"}], "edges": [["caller", "callee"]]}`,
  `line` = line of the function definition), plus a readable
  `analysis/callgraph.md`.
- Scope: from the chipset constructors down through the init paths of fb,
  mmu, fifo and gr. The roots are `gk110_fb_new`, `gk104_mmu_new`,
  `gk110_fifo_new` and `gk110b_gr_new`. Use only files of
  `analysis/files.json`.
- Nouveau reaches most of its code through function tables, not through
  direct calls: a constructor passes a table (`&gk110b_gr`) whose fields
  name the functions (`.init = gf100_gr_init`). A graph of direct calls
  stops at the constructors. Make each table a node (`line` = the line of
  `name = {`), with an edge from the function that uses the table to the
  table, and an edge from the table to every function or table that it
  names. A node may have an optional `"kind"`: `"function"` or `"table"`.
- An edge `[a, b]` means that the body of `a` uses the name `b`.
- `analysis/callgraph.md` lists, for each of fb, mmu, fifo and gr, the
  path from the root to the init function, and says which calls are only
  for other chips (a graph of names cannot tell: say so where you do not
  know).
- Check (`make check`): each node's `file:line` defines that function or
  table; the four roots are nodes; every edge joins two nodes and the
  caller's body uses the callee; every node is reached from a root;
  `gf100_gr_init`, `gf100_fb_init` and `gk104_fifo_init` are nodes.
- The tool gives the same output on every run (sort every set, and sort
  the lines of `callgraph.md`). `tools/callgraph.py --check` writes
  nothing and exits 0 when both output files are what the tool
  generates, else 1. `make check` runs it twice.

### B3. MMIO access extraction
- Outputs: `tools/extract_mmio.py`,
  `registers/mmio_accesses.json`: a list of
  `{"file", "line", "function", "op", "reg", "reg_value", "value",
  "mask", "subsystem"}`. `op` is `rd32`, `wr32` or `mask`. `reg_value` is
  the integer value when `reg` is a constant, else `null`.
- Scope: every `nvkm_rd32`, `nvkm_wr32`, `nvkm_mask` in the files of
  `analysis/files.json` (872 calls in the 88 files). One entry for each
  call: a line with two calls (`nvkm_wr32(device, a, nvkm_rd32(device,
  b))`) gives two entries with the same `line`.
- `reg` is the register expression as it is written (`0x100c80`,
  `GPC_BCAST(0x08ac)`, `0x002a00 + (i * 4)`). `function` is the function
  that contains the line. `value` and `mask` are the argument texts, or
  `null` when the call has none (`rd32` has neither, `wr32` has no mask).
  A call that continues on the next line: join the lines before you
  split the arguments. `line` is the line of the call name.
- `subsystem` is the `subsystem` of the file in `analysis/files.json`.
- `tools/extract_mmio.py --check` writes nothing and exits 0 when the
  JSON file is what the tool generates, else 1. Sort the output by file
  and line. The tool gives the same output on every run.
- Check (`make check`): each `file:line` contains the call; the entries
  are complete (the number of entries equals the number of calls, line
  by line); `function` and `reg` agree with the source; `reg_value` is
  right for a constant; `--check` passes twice.
- `RESULT.md`: the count per subsystem and per `op`, and how many `reg`
  values are constants.

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

### B6. Compute launch path (user-space half)
- Why: the Nouveau kernel driver gives a channel and engines. The code
  that makes a compute job is in Mesa: it uploads the shader code, fills
  a launch descriptor and sends compute methods through the channel.
- Inputs: `reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c`
  (start at `nve4_launch_grid` and `nve4_screen_compute_setup`),
  `nve4_compute.xml.h`, `cla0c0qmd.h`, `qmda0c0.c`,
  `reference/mesa/src/gallium/drivers/nouveau/nv_object.xml.h`.
- Outputs: `tools/compute_launch.py`, `analysis/compute_launch.json`,
  `analysis/compute_launch.md`.
- `compute_launch.json`:
  `{"compute_class": "0xa1c0", "class_source": "file:line",
  "setup": [...], "launch": [...], "descriptor_fields": [...],
  "kernel_needs": [...]}`.
  `setup` and `launch` are the compute methods in the order that Mesa
  sends them in `nve4_screen_compute_setup` and `nve4_launch_grid`:
  `{"method": "LAUNCH_DESC_ADDRESS", "offset": "0x...", "file": "...",
  "line": 0, "value": "what Mesa writes"}`. `offset` comes from
  `nve4_compute.xml.h`. `descriptor_fields` lists the launch descriptor
  fields that `nve4_compute_setup_launch_desc` sets:
  `{"field", "file", "line"}`. `kernel_needs` lists what the job needs
  from the kernel side (channel, compute object, address space, buffers),
  each with the Mesa call that shows it.
- `compute_launch.md`: the sequence in words, which parts are for other
  chips (GM107, GP100, GV100) and not for GK110, and how the shader code
  reaches the GPU (`CODE_ADDRESS`).
- File paths are relative to `reference/mesa/`.
- Check: the class value is the one that `nv_object.xml.h` gives for
  `NVF0_COMPUTE_CLASS`; each `file:line` holds the method or field name;
  `LAUNCH_DESC_ADDRESS` and `LAUNCH` are in `launch`, in that order.

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

### C5. Reference run under Linux and the first shader binary
- This task has a user part (root, the Linux guest with the card). The
  agent prepares and analyses. See `docs/PASSTHROUGH.md`.
- User part: run `tools/guest/compute_test.c` in the Linux guest
  (Nouveau and Mesa on the K40c). It runs `output[i] = input[i] + 1` as
  a GL compute shader and prints PASS or FAIL. Run it again with
  `NV50_PROG_DEBUG=1` to print the generated GK110 code, and once under
  `mmiotrace` for the kernel side. Put the logs in `reference/linux-run/`.
- Agent part, outputs: `firmware/compute_add1.md` (the shader source,
  the Mesa version, the code words from the debug log, how to make them
  again) and `firmware/compute_add1.bin`; `docs/08-compute-launch.md`
  (what the trace shows between channel creation and the launch).
- Check: `reference/linux-run/RESULT.txt` says PASS; the binary has the
  size that the log gives.
- If the job does not run under Linux: write `escalations/ESC-NNN.md`.
  The project then stops at milestone S2.

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

### D5. Launch descriptor and compute method encoding
- A launch descriptor builder and the compute method sequence of B6 as
  push-buffer words (uses D3), with tests against values from
  `reference/mesa` and from the trace of C5.

## Gate: end of phase D

The user reviews phases A-D before any Haiku work. Phases E-N (Haiku PCI
skeleton, MMIO, MC/FB/VRAM, MMU, FIFO/PBDMA, GPFIFO and submission to
milestone S1, copy engine to S2, GR/Falcon and first computation to S3,
interrupts, user-space API) are planned at the gate. They need a Haiku
boot and GPU access. `docs/PASSTHROUGH.md` describes how a test VM can
get one K40c, so that these phases do not need a reboot into Haiku. It
is prepared and not enabled.
