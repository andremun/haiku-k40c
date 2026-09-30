# K40c / GK110 Haiku Compute Driver

## 1. Project objective

Develop a minimal, native Haiku kernel driver for the NVIDIA Tesla K40c, based on the GK110 architecture, with the initial objective of GPU compute rather than display.

The driver is **not** intended initially to provide:

- display output;
- framebuffer graphics;
- X11/Wayland integration;
- OpenGL;
- Vulkan;
- CUDA compatibility;
- video encode/decode;
- power management;
- dynamic reclocking;
- thermal management;
- multi-GPU scheduling;
- general NVIDIA hardware support.

The initial target is considerably narrower:

> Detect a Tesla K40c, initialise the GK110 GPU sufficiently to create a GPU virtual address space and compute context, submit a minimal command stream to the GK110 compute engine, execute a known computation, and retrieve the result.

The eventual driver should be Haiku-native rather than a direct port of Linux Nouveau's architecture.

The Linux Nouveau driver is to be treated primarily as a source of validated GK110 hardware knowledge. Linux-specific infrastructure such as DRM, TTM, GEM, NVIF, Linux PCI APIs, Linux DMA APIs, and the NVKM object hierarchy should not be reproduced unless a specific hardware dependency makes this unavoidable.

---

# 2. Target hardware

## 2.1 Development machine

The development and validation target is a Dell Precision T7610:

- 2 × Intel Xeon E5-2620 v2
- 64 GB DDR3 ECC Registered RAM
- 2 × NVIDIA Tesla K40c
- 1 × NVIDIA Quadro K600 used as the display GPU
- 1300 W PSU
- SATA SSD available for Haiku installation
- additional SAS storage retained for Ubuntu/scientific workloads

The K40c is a GK110-generation Tesla card. The Quadro K600 is also Kepler but is not the target GPU.

The K600 should remain the display adapter during development where practical. The K40c should initially be treated as a compute-only PCI device.

## 2.2 Development topology

Use the same physical T7610 for both environments:

```text
                    Dell Precision T7610
                           |
             +-------------+-------------+
             |                           |
          Ubuntu                       Haiku
             |                           |
       development                    target
       environment                   driver
             |                           |
      +------+-------+                K40c
      |              |
   K40c #1        K40c #2
      |
  Nouveau / other
  reference setup

Display:
    Quadro K600
```

The ability to boot Ubuntu and Haiku on the same physical machine is valuable because PCI configuration, BAR layout, firmware state, memory configuration, and hardware behaviour can be compared directly.

Initially develop against one K40c only.

Do not attempt multi-K40 operation until a single K40c can execute a verified compute workload.

---

# 3. Fundamental design principle

Do not attempt:

```text
Linux Nouveau
       |
       +--> Haiku
```

Instead use:

```text
                 NVIDIA GK110 hardware
                         |
          +--------------+--------------+
          |                             |
     Linux Nouveau                Haiku driver
          |                             |
   validated hardware            native implementation
   knowledge and algorithms      using Haiku APIs
```

Nouveau's current GK110 device description shows that GK110 uses, among other components:

- `gk110_fb`
- `gk104_mc`
- `gk104_mmu`
- `gk110_fifo`
- `gk110_gr`
- `gk104_ce`
- GK110-specific GR firmware

The current Nouveau source therefore provides a particularly useful dependency map for the hardware.

The Haiku implementation should retain the hardware knowledge but discard the Linux-specific architecture.

---

# 4. Initial functional target

The first complete driver milestone should be:

```text
PCI detection
    |
    v
GK110 identification
    |
    v
BAR mapping
    |
    v
basic MMIO access
    |
    v
GPU reset / initialisation
    |
    v
memory controller / framebuffer initialisation
    |
    v
VRAM detection
    |
    v
GPU instance memory
    |
    v
GPU virtual memory / MMU
    |
    v
one GPU virtual address space
    |
    v
FIFO/PBDMA initialisation
    |
    v
one GPU channel
    |
    v
one GPFIFO
    |
    v
GR/compute engine initialisation
    |
    v
FECS / GPCCS firmware
    |
    v
KEPLER_COMPUTE_B class
    |
    v
minimal command stream
    |
    v
GPU execution
    |
    v
completion detection
    |
    v
read result
```

A successful test should demonstrate actual GPU execution, not merely successful driver attachment.

---

# 5. Explicit non-goals for Phase 1

Do not implement the following during initial development:

```text
Display
KMS
DRM
GEM
TTM
dma-buf
OpenGL
Vulkan
CUDA runtime
CUDA ABI compatibility
OpenCL runtime
NVENC
NVDEC
I2C
GPIO
thermal management
voltage management
reclocking
dynamic power management
audio
multi-GPU scheduling
hotplug
suspend/resume
user-space GPU virtualisation
```

These may become later projects.

---

# 6. Nouveau source tree to investigate

Use a current Linux kernel source tree containing Nouveau.

The main source hierarchy of interest is:

```text
drivers/gpu/drm/nouveau/nvkm/
|
+-- engine/
|   |
|   +-- device/
|   |   +-- base.c
|   |   +-- pci.c
|   |
|   +-- fifo/
|   |   +-- base.c
|   |   +-- gf100.c
|   |   +-- gk104.c
|   |   +-- gk110.c
|   |   +-- chan.c
|   |   +-- chid.c
|   |   +-- runl.c
|   |   +-- runq.c
|   |
|   +-- gr/
|       +-- gf100.c
|       +-- gk104.c
|       +-- gk110.c
|       +-- ctxgf100.c
|       +-- ctxgf100.h
|
+-- subdev/
    |
    +-- fb/
    |   +-- gf100.c
    |   +-- gk110.c
    |   +-- ramgk104.c
    |
    +-- mmu/
        +-- base.c
        +-- gf100.c
        +-- gk104.c
        +-- vmm.c
        +-- vmmgf100.c
        +-- vmmgk104.c
```

The exact current source should always be checked rather than assuming that filenames or function boundaries remain unchanged.

The Linux Nouveau GK110 device descriptor is particularly useful because it identifies the inheritance relationships explicitly. For example, GK110 uses `gk104_mmu_new`, `gk110_fifo_new`, `gk110_gr_new`, and `gk110_fb_new`.

---

# 7. Source classification

Every source file encountered should be classified into one of four categories.

## A. Hardware algorithm — REIMPLEMENT

The source contains information about:

- register programming;
- GPU initialisation;
- page-table formats;
- FIFO programming;
- PBDMA configuration;
- GR configuration;
- firmware loading;
- command submission;
- GPU state transitions.

These are the most valuable sources.

The implementation should be translated into a Haiku-native design rather than copied structurally.

## B. Hardware data — EXTRACT

Examples:

- register offsets;
- bit fields;
- engine class IDs;
- GK110 topology;
- page-table descriptors;
- context tables;
- firmware metadata;
- MMIO sequences.

These should be extracted into clean Haiku-specific definitions.

## C. Linux infrastructure — DISCARD/REPLACE

Examples:

- Linux PCI APIs;
- Linux DMA APIs;
- Linux memory management;
- DRM;
- TTM;
- GEM;
- NVIF;
- Linux locking;
- Linux workqueues;
- Linux interrupt infrastructure;
- Linux kernel object lifetime management.

Replace these with Haiku mechanisms.

## D. Unnecessary subsystem — IGNORE

Examples:

- display;
- I2C;
- GPIO;
- thermal;
- voltage;
- reclocking;
- NVDEC;
- NVENC;
- audio;
- DRM KMS.

---

# 8. Minimum hardware dependency graph

The intended dependency graph is:

```text
                    +------------------+
                    | Haiku PCI driver |
                    +---------+--------+
                              |
                              v
                    +------------------+
                    | K40Device        |
                    | GK110 detection  |
                    +---------+--------+
                              |
               +--------------+--------------+
               |              |              |
               v              v              v
          +---------+    +---------+    +---------+
          | MMIO    |    | FB/VRAM |    | MC      |
          +----+----+    +----+----+    +----+----+
               |              |              |
               +--------------+--------------+
                              |
                              v
                       +-------------+
                       | GPU memory  |
                       +------+------+
                              |
                              v
                       +-------------+
                       | GK104 MMU   |
                       | / VMM       |
                       +------+------+
                              |
                              v
                     +----------------+
                     | GPU VA space   |
                     +-------+--------+
                             |
                +------------+------------+
                |                         |
                v                         v
          +-----------+             +-----------+
          | FIFO      |             | GR        |
          | GK110     |             | GK110     |
          +-----+-----+             +-----+-----+
                |                         |
                |                         |
                +------------+------------+
                             |
                             v
                    +------------------+
                    | GPFIFO/channel   |
                    +---------+--------+
                              |
                              v
                    +------------------+
                    | Compute class    |
                    | KEPLER_COMPUTE_B |
                    +---------+--------+
                              |
                              v
                         GPU execution
```

---

# 9. Phase 0 — establish the Ubuntu reference environment

Before writing Haiku code, establish a reproducible Ubuntu environment that can inspect and exercise the K40c.

The Ubuntu environment is the laboratory.

It should provide:

1. hardware identification;
2. PCI configuration inspection;
3. BAR inspection;
4. Nouveau source;
5. Nouveau kernel logs;
6. register inspection where safe;
7. firmware inspection;
8. GPU execution tests;
9. automated source analysis;
10. build/test automation.

---

# 10. Ubuntu tools

## 10.1 Essential system tools

Install and use:

```bash
build-essential
gcc
g++
clang
lld
cmake
ninja-build
meson
git
git-lfs
pkg-config
python3
python3-dev
python3-venv
```

For source analysis:

```bash
ripgrep
fd-find
jq
ctags
clangd
bear
ccache
```

Useful additional tools:

```bash
gdb
strace
ltrace
perf
valgrind
bpftrace
```

Not all of these will be directly applicable to kernel code, but they are useful for automating the surrounding development environment.

---

# 11. PCI and hardware inspection

Use:

```bash
lspci -nn
lspci -vv
lspci -xxxx
```

Identify the K40c explicitly:

```bash
lspci -nn | grep -i nvidia
```

Record:

- vendor ID;
- device ID;
- subsystem ID;
- revision;
- BAR addresses;
- BAR sizes;
- PCI command/status registers;
- interrupt configuration;
- PCI capabilities;
- PCIe link state.

Save the output in version-controlled reference files.

Example:

```text
reference/
    pci/
        k40c-lspci-nn.txt
        k40c-lspci-vv.txt
        k40c-lspci-xxxx.txt
```

The reference files are part of the development dataset.

---

# 12. PCI configuration capture

Use `setpci` for controlled PCI configuration-space inspection.

Examples:

```bash
setpci -s <BDF> COMMAND
setpci -s <BDF> STATUS
```

Do not write arbitrary PCI configuration values during initial investigation.

Any command that modifies PCI state must be documented and tested on a disposable boot configuration.

---

# 13. Kernel/Nouveau reference environment

Obtain a clean Linux kernel source tree.

Suggested workflow:

```bash
git clone https://github.com/torvalds/linux.git linux
cd linux
git log -- drivers/gpu/drm/nouveau
```

Then maintain a known commit/tag used as the reference.

Do not continuously change the reference kernel while implementing the Haiku driver.

Maintain:

```text
reference/linux-kernel/
reference/nouveau/
reference/firmware/
```

with an explicit version/commit record.

---

# 14. Nouveau source extraction

Create an automated extraction script that collects only the GK110 dependency tree.

For example:

```text
tools/
    extract_nouveau_gk110.py
```

The script should:

1. locate GK110 source files;
2. follow local `#include` dependencies;
3. follow function references;
4. identify inherited implementations;
5. generate a dependency report;
6. copy or index relevant source;
7. produce a machine-readable dependency graph.

The output should distinguish:

```text
GK110-specific
GK104-inherited
GF100-inherited
generic NVKM
Linux-only
```

This classification should be generated before attempting translation.

---

# 15. Automated source analysis

Use `clangd` and LLVM tooling to build an indexed representation of Nouveau.

Generate `compile_commands.json` for the relevant kernel/Nouveau build if practical.

Useful automated analyses:

```text
find all functions referenced by gk110_gr
find all functions referenced by gk110_fifo
find all register constants referenced by GK110 paths
find all structures required by gk110_gr
find all firmware symbols
find all GK110-specific macros
find all GK104/GF100 inherited dependencies
find all Linux-specific APIs
```

The coding agent should not be expected to discover these relationships repeatedly.

Generate a static report:

```text
reports/
    gk110-functions.md
    gk110-registers.md
    gk110-fifo-dependencies.md
    gk110-gr-dependencies.md
    gk110-mmu-dependencies.md
    linux-api-dependencies.md
```

---

# 16. Register and hardware investigation

The driver development process should build a hardware register database.

Create:

```text
hardware/
    registers/
        mc.yaml
        fb.yaml
        mmu.yaml
        fifo.yaml
        pbdma.yaml
        gr.yaml
        compute.yaml
```

Each register entry should eventually contain:

```yaml
name:
address:
width:
reset_value:
readable:
writable:
fields:
  - name:
    shift:
    width:
    description:
source:
notes:
```

Do not allow the coding agent to invent register definitions.

Every register used in the driver should have a traceable source.

Possible sources include:

- Nouveau;
- NVIDIA public documentation;
- Linux Nouveau headers;
- reverse-engineering documentation;
- observed hardware behaviour.

---

# 17. Firmware investigation

GK110 GR initialisation uses FECS and GPCCS firmware.

The current Nouveau GK110 GR implementation explicitly references:

```text
gk110_gr_fecs_ucode
gk110_gr_gpccs_ucode
```

and exposes the `KEPLER_COMPUTE_B` class.

The development process must establish:

1. exact firmware files;
2. firmware format;
3. firmware version;
4. loading mechanism;
5. required alignment;
6. destination memory;
7. boot/init sequence;
8. licensing/distribution status.

Do not embed firmware into the Haiku driver until its licensing/distribution status has been established.

Create:

```text
firmware/
    README.md
    manifest.yaml
```

The manifest should record:

```text
filename
source
version
hash
license
distribution status
required engine
```

---

# 18. Important firmware experiment

Before attempting the full Haiku implementation, determine whether GK110 GR can be brought up using the exact firmware and sequence employed by Nouveau.

The Ubuntu environment should be used to answer:

```text
What firmware is required?
Where is it loaded?
What registers control Falcon boot?
What constitutes successful FECS boot?
What constitutes successful GPCCS boot?
How is failure detected?
```

This should be a separate reverse-engineering task.

---

# 19. Haiku driver architecture

The eventual driver should use Haiku's device-driver architecture rather than attempting to reproduce Linux's.

Haiku's device manager uses device nodes and driver entry points such as:

- `supports_device()`;
- `register_device()`;
- `init_driver()`;
- `uninit_driver()`;
- `register_child_devices()`.

Drivers can expose devices through `/dev`.

The Haiku driver should therefore have a thin OS-facing layer:

```text
Haiku device manager
        |
        v
k40c driver
        |
        +-- K40Device
        |
        +-- MMIO
        +-- PCI
        +-- interrupts
        +-- memory
        +-- MMU
        +-- FIFO
        +-- GR
```

---

# 20. Proposed Haiku source tree

Initial implementation:

```text
src/add-ons/kernel/drivers/gpu/k40c/

    k40c.cpp
    k40c.h

    pci.cpp
    pci.h

    mmio.cpp
    mmio.h

    interrupt.cpp
    interrupt.h

    mc.cpp
    mc.h

    fb.cpp
    fb.h

    vram.cpp
    vram.h

    memory.cpp
    memory.h

    instmem.cpp
    instmem.h

    mmu.cpp
    mmu.h

    page_table.cpp
    page_table.h

    fifo.cpp
    fifo.h

    channel.cpp
    channel.h

    gpfifo.cpp
    gpfifo.h

    pbdma.cpp
    pbdma.h

    gr.cpp
    gr.h

    gr_gk110.cpp
    gr_gk110.h

    gr_context.cpp
    gr_context.h

    firmware.cpp
    firmware.h

    debug.cpp
    debug.h

    tests.cpp
```

The exact Haiku source location may need adjustment to current Haiku driver conventions.

---

# 21. Driver layers

Keep the implementation divided into three layers.

## Layer 1 — Haiku OS integration

```text
k40c.cpp
pci.cpp
interrupt.cpp
memory.cpp
```

Responsibilities:

- device discovery;
- resource acquisition;
- DMA-capable memory;
- interrupts;
- locking;
- kernel threads;
- device node;
- user/kernel boundary.

No GK110-specific algorithms should be placed here.

## Layer 2 — GPU abstraction

```text
mc.cpp
fb.cpp
vram.cpp
mmu.cpp
fifo.cpp
channel.cpp
gpfifo.cpp
gr.cpp
```

Responsibilities:

- GPU resources;
- memory;
- GPU virtual memory;
- command submission;
- engine state.

## Layer 3 — GK110 implementation

```text
gr_gk110.cpp
gr_context.cpp
firmware.cpp
```

Responsibilities:

- GK110-specific registers;
- GK110 context;
- FECS/GPCCS;
- compute engine;
- GK110-specific command classes.

---

# 22. Milestone 1 — PCI detection

Goal:

```text
Haiku boots
    |
    v
K40c detected
    |
    v
driver attaches
    |
    v
driver prints:
    vendor
    device
    subsystem
    revision
    BARs
```

No GPU initialisation.

Success criterion:

```text
K40c is correctly identified and the driver does not destabilise Haiku.
```

The Quadro K600 must remain usable as the display adapter.

---

# 23. Milestone 2 — MMIO

Implement:

```text
read32(offset)
write32(offset, value)
```

with bounds checking and tracing.

Initial test:

```text
read known identification registers
read BOOT0
read PMC/MC state
```

Do not perform speculative writes.

Provide a debug mode:

```text
k40c.debug.mmio=1
```

or equivalent mechanism.

The driver should log:

```text
register
old value
new value
reason
```

for all nontrivial writes during development.

---

# 24. Milestone 3 — PCI/BAR resource management

Map only the resources actually required.

Determine experimentally:

```text
BAR0
BAR1
other BARs
```

and document their roles.

Do not map every BAR simply because it exists.

The driver should expose:

```text
bar0_base
bar0_size
bar1_base
bar1_size
```

in a diagnostic structure.

---

# 25. Milestone 4 — MC and basic GPU initialisation

Implement the minimum memory-controller state required for:

- stable MMIO;
- VRAM access;
- engine reset;
- later MMU initialisation.

Use Nouveau's GK104/GK110 inheritance as the hardware reference.

Do not port the complete NVKM `mc` subsystem.

---

# 26. Milestone 5 — VRAM detection

Implement:

```text
detect_vram()
```

Expected K40c configuration:

```text
12 GB GDDR5
```

Do not hard-code 12 GB.

The driver should discover and report actual VRAM size.

Initial diagnostic test:

```text
allocate VRAM buffer
write pattern
read pattern
verify
```

This may initially be CPU-side access if the architecture permits it.

---

# 27. Milestone 6 — Instance memory

Implement the minimum GPU-visible instance memory needed by:

- MMU;
- FIFO;
- channel;
- GPFIFO;
- GR context.

Do not reproduce all Nouveau instance-memory abstractions.

Use a simple allocator initially.

Example:

```text
InstanceMemoryAllocator
    allocate(size, alignment)
    free(handle)
    physical_address(handle)
```

---

# 28. Milestone 7 — GK104/GK110 MMU

The GK110 device description uses the GK104 MMU implementation.

The relevant Nouveau dependency chain is approximately:

```text
vmmgk104
    |
    +--> vmmgf100
    |
    +--> gf100
    |
    +--> gk104
```

Do not port this hierarchy literally.

Implement:

```text
K40MMU
    create_address_space()
    allocate_page_table()
    map()
    unmap()
    flush()
    destroy_address_space()
```

The implementation must reproduce the GK104/GK110 hardware page-table format.

---

# 29. GPU virtual-address test

Before FIFO/GR:

```text
allocate VRAM
    |
map at GPU virtual address X
    |
verify page-table state
    |
flush MMU
    |
verify mapping using a simple GPU operation if possible
```

This is an important checkpoint.

Do not proceed to complex GR debugging if GPU virtual memory itself has not been validated.

---

# 30. Milestone 8 — FIFO/PBDMA

The GK110 FIFO implementation is a key source.

The current Nouveau source has a GK110-specific FIFO implementation with substantial inheritance from GK104/GF100. The GK110 implementation configures channel/runlist/PBDMA-related infrastructure rather than introducing an entirely new FIFO architecture.

For the initial driver simplify aggressively:

```text
one FIFO
one channel
one runlist
one GPFIFO
one compute engine
```

Avoid:

```text
multiple clients
multiple users
scheduler
preemption
channel groups
dynamic scheduling
```

unless hardware bring-up requires them.

---

# 31. Milestone 9 — GPFIFO

Implement a minimal GPFIFO.

Conceptually:

```text
CPU
 |
 | writes command entries
 v
GPU-visible GPFIFO
 |
 v
FIFO/PBDMA
 |
 v
GPU engine
```

The driver should be able to:

```text
create_gpfifo()
submit_gpfifo()
kick_channel()
wait_for_completion()
```

Initially use polling if interrupts complicate bring-up.

Interrupt-driven completion can be added after basic execution works.

---

# 32. Milestone 10 — GR / compute engine

The GK110 GR source is the most important high-level source after MMU/FIFO.

The current Nouveau GK110 implementation inherits many operations from GF100/GK104 but defines GK110-specific MMIO, firmware, context and initialisation information. It explicitly includes:

```text
KEPLER_B
KEPLER_COMPUTE_B
```

as supported software classes.

The driver must reproduce only the compute-relevant portion.

---

# 33. FECS and GPCCS

Treat the GR microcontrollers as a separate subsystem:

```text
GR
 |
 +-- FECS
 |
 +-- GPCCS
 |
 +-- GR context
 |
 +-- compute engine
```

Implement explicit diagnostics:

```text
fecs_load()
fecs_boot()
fecs_status()

gpccs_load()
gpccs_boot()
gpccs_status()
```

The driver must report exact Falcon status when initialisation fails.

Do not return simply:

```text
GR init failed
```

Instead report:

```text
FECS:
    firmware loaded: yes/no
    boot requested: yes/no
    status: ...
    error: ...

GPCCS:
    firmware loaded: yes/no
    boot requested: yes/no
    status: ...
    error: ...
```

---

# 34. GR context

GK110 requires the appropriate GR context setup.

The implementation should initially support only:

```text
one context
one channel
one compute workload
```

Do not build a general context-management framework until this works.

Use Nouveau's:

```text
ctxgf100.*
gk110 context data
```

as hardware references.

---

# 35. Compute class

Bind:

```text
KEPLER_COMPUTE_B
```

This is a critical milestone because it establishes that the driver is talking to the compute-capable GK110 engine rather than merely initialising the GPU.

Nouveau's current GK110 GR implementation explicitly registers this class.

---

# 36. First GPU execution test

Do not begin with CUDA.

The first execution test should be a tiny GPU command sequence with a deterministic result.

For example:

```text
input:
    GPU-visible buffer

operation:
    simple compute/write operation

output:
    GPU-visible buffer

expected:
    exact known byte pattern
```

The test should have:

```text
CPU setup
GPU submission
GPU execution
completion detection
CPU verification
```

Example conceptual result:

```text
input[0] = 7

GPU:
    output[0] = 42

CPU:
    assert(output[0] == 42)
```

The exact command sequence should be derived from Nouveau and validated experimentally, not invented by the coding agent.

---

# 37. First major success criterion

The first meaningful success criterion is:

```text
K40c
  |
  +-- detected
  +-- initialised
  +-- VRAM available
  +-- MMU active
  +-- FIFO active
  +-- compute channel active
  +-- GR active
  +-- KEPLER_COMPUTE_B active
  +-- command submitted
  +-- GPU executes
  +-- result verified
```

At that point the project has demonstrated a native Haiku GK110 compute driver.

Everything beyond this is expansion.

---

# 38. Ubuntu automated-development environment

The Ubuntu machine should be treated as the primary development host before Haiku transfer.

Recommended repository:

```text
k40c-haiku/
|
+-- agent/
+-- docs/
+-- hardware/
+-- reference/
+-- nouveau/
+-- firmware/
+-- src/
+-- tests/
+-- tools/
+-- scripts/
+-- reports/
```

---

# 39. Suggested automated tooling

## Source retrieval

```text
git
git worktree
git submodule
git-lfs
```

Maintain fixed reference commits.

## Search

```text
rg
fd
ctags
clangd
```

The coding agent should use `rg` heavily rather than loading entire Linux source files into context.

## C/C++ analysis

```text
clang
clangd
clang-format
clang-tidy
bear
```

Use Clang tooling to identify:

- call graphs;
- structures;
- macros;
- type dependencies;
- unused code;
- suspicious casts.

## Build acceleration

```text
ccache
ninja
```

## Debugging

```text
gdb
kgdb, where practical
serial console
Haiku debugger
```

## Hardware inspection

```text
lspci
setpci
dmesg
journalctl
```

Use any direct MMIO/register utility only with great caution.

## Kernel tracing

Use Linux Nouveau's logging/debug facilities as a reference for expected state transitions.

Haiku has built-in kernel tracing/debugging facilities; `dprintf()`/`TRACE()` and the `traced` command are specifically recommended in Haiku driver-development guidance.

---

# 40. Use Ubuntu Nouveau as an oracle

Where possible, run the same operation through Nouveau on Ubuntu and record:

```text
register writes
register reads
engine initialisation order
firmware loading
MMU setup
FIFO setup
GR setup
```

The goal is to establish:

```text
Known-good Linux operation
            |
            v
expected hardware state
            |
            v
Haiku implementation
```

This is substantially safer than deriving the entire sequence from static source alone.

---

# 41. Register-trace methodology

Develop a register-tracing framework before serious Haiku development.

Conceptually:

```text
trace event:
    timestamp
    engine
    register
    read/write
    value
    reason
```

Store traces as:

```text
traces/
    linux/
        boot.txt
        fifo.txt
        gr.txt
        compute.txt

    haiku/
        boot.txt
        fifo.txt
        gr.txt
        compute.txt
```

Then create a comparison tool:

```text
tools/compare_register_traces.py
```

Output:

```text
sequence mismatch:
    expected:
        0x....
    actual:
        0x....

missing write:
    register:
        0x....

unexpected write:
    register:
        0x....
```

This could become one of the most valuable tools in the project.

---

# 42. Automated hardware-state snapshots

Create a standard diagnostic command:

```text
k40dump
```

or equivalent.

It should eventually capture:

```text
PCI state
BARs
MC state
FB state
MMU state
FIFO state
PBDMA state
GR state
FECS state
GPCCS state
interrupt state
```

Output:

```text
snapshots/
    k40c-YYYYMMDD-HHMMSS/
        pci.txt
        mc.txt
        fb.txt
        mmu.txt
        fifo.txt
        gr.txt
        fecs.txt
        gpccs.txt
```

This is particularly useful when the GPU hangs.

---

# 43. GPU hang diagnostics

GPU hangs are likely to be one of the hardest parts.

The driver must have a dedicated diagnostic path.

On timeout:

```text
submit()
    |
    v
wait()
    |
    v
timeout
    |
    +--> dump FIFO
    +--> dump PBDMA
    +--> dump GR
    +--> dump MMU fault
    +--> dump FECS
    +--> dump GPCCS
    +--> dump channel
    +--> dump GPFIFO
```

Never simply reset the GPU and discard the evidence.

---

# 44. Unit tests before GPU tests

Hardware-independent tests should be executable on Ubuntu before the Haiku port.

Examples:

```text
page-table encoding
GPU virtual-address calculations
alignment
bit-field packing
register encoding
FIFO entry encoding
command packet construction
firmware-header parsing
context-table generation
```

These can be compiled as ordinary host-side C++ tests.

Suggested:

```text
tests/
    test_registers.cpp
    test_mmu.cpp
    test_page_tables.cpp
    test_fifo.cpp
    test_commands.cpp
    test_firmware.cpp
```

This allows the coding agent to make substantial progress without booting Haiku.

---

# 45. Hardware-independent emulation layer

Build a minimal MMIO abstraction:

```cpp
class RegisterIO {
public:
    virtual uint32 read32(uint32 offset) = 0;
    virtual void write32(uint32 offset, uint32 value) = 0;
};
```

Then provide:

```text
RealMMIO
MockMMIO
TraceMMIO
```

This allows:

```text
driver algorithm
      |
      +--> real K40
      |
      +--> mock register space
      |
      +--> recorded Nouveau trace
```

The coding agent can therefore test large portions of the driver without touching hardware.

---

# 46. Recorded-hardware replay

An especially useful extension is:

```text
Nouveau trace
      |
      v
recorded register state
      |
      v
MockMMIO
      |
      v
Haiku-independent driver logic
```

This will permit regression testing of the extracted algorithms.

---

# 47. Static safety rules for the coding agent

The coding agent must not:

1. invent register addresses;
2. invent bit-field definitions;
3. invent firmware formats;
4. assume Linux memory semantics apply to Haiku;
5. copy Linux locking code blindly;
6. introduce CUDA dependencies;
7. introduce DRM dependencies;
8. initialise display hardware;
9. silently ignore MMU faults;
10. silently recover from GPU hangs without producing diagnostics.

Every hardware-specific constant should have a provenance comment.

Example:

```cpp
// GK110 register.
// Source: Nouveau nvkm/.../gk110.c
// Verified against Ubuntu K40c register trace.
constexpr uint32 REG_FOO = 0x123456;
```

---

# 48. Source provenance

Maintain:

```text
docs/register-provenance.md
```

Every significant hardware constant should have:

```text
symbol
value
GPU generation
source file
source commit
interpretation
verification status
```

Use statuses:

```text
SOURCE_ONLY
TRACE_VERIFIED
HARDWARE_VERIFIED
HAIKU_VERIFIED
```

Do not mark hardware behaviour as verified merely because Nouveau uses it.

---

# 49. Licensing

Before copying code from Nouveau into the Haiku repository, perform a licensing audit.

Distinguish:

```text
concept / hardware knowledge
        vs.
copyrighted source implementation
```

Prefer:

```text
study source
extract algorithm
reimplement independently
```

rather than wholesale copying Linux Nouveau source into a Haiku kernel driver.

Create:

```text
docs/licensing.md
```

containing:

- source files consulted;
- licenses;
- firmware licenses;
- copied material, if any;
- independently reimplemented material.

This should be completed before upstream distribution.

---

# 50. Phase ordering

Recommended development order:

```text
PHASE A
Ubuntu environment
    |
    v
PHASE B
Nouveau dependency extraction
    |
    v
PHASE C
GK110 register/hardware database
    |
    v
PHASE D
Host-side algorithms/tests
    |
    v
PHASE E
Haiku PCI skeleton
    |
    v
PHASE F
MMIO
    |
    v
PHASE G
MC + FB + VRAM
    |
    v
PHASE H
MMU
    |
    v
PHASE I
FIFO/PBDMA
    |
    v
PHASE J
GR/Falcon
    |
    v
PHASE K
GPFIFO + compute submission
    |
    v
PHASE L
first GPU computation
    |
    v
PHASE M
interrupts + robust synchronisation
    |
    v
PHASE N
user-space API
```

---

# 51. What should happen before booting Haiku

Do as much as possible on Ubuntu first.

The following should exist before serious Haiku implementation begins:

```text
[ ] K40c PCI identity recorded
[ ] BAR configuration recorded
[ ] Nouveau source snapshot recorded
[ ] GK110 dependency graph generated
[ ] GK110/GK104/GF100 inheritance classified
[ ] relevant firmware identified
[ ] firmware provenance documented
[ ] register database started
[ ] MMU algorithms understood
[ ] FIFO architecture understood
[ ] GR architecture understood
[ ] FECS/GPCCS boot sequence documented
[ ] KEPLER_COMPUTE_B identified
[ ] first command sequence understood
[ ] host-side register/packet tests implemented
[ ] trace infrastructure implemented
[ ] GPU hang diagnostic strategy defined
```

The purpose is to reduce the amount of simultaneous uncertainty when the first Haiku kernel driver is loaded.

---

# 52. First Haiku boot

The first Haiku driver should do almost nothing.

Expected behaviour:

```text
Haiku boot
    |
    v
PCI enumeration
    |
    v
K40c recognised
    |
    v
driver attaches
    |
    v
log PCI/BAR information
    |
    v
driver exits cleanly
```

Do not initialise the GPU at this stage.

This establishes that the Haiku device-manager integration works.

---

# 53. Second Haiku stage

Add:

```text
BAR mapping
MMIO read
```

Test only safe identification registers.

Then:

```text
Haiku
    |
    v
K40c
    |
    v
read BOOT0
    |
    v
confirm GK110
```

Only after this works should writes begin.

---

# 54. Third Haiku stage

Add:

```text
MC
FB
VRAM
```

Success:

```text
K40c
    |
    v
driver reports approximately 12 GB VRAM
    |
    v
VRAM allocation
    |
    v
known-pattern test
```

---

# 55. Fourth Haiku stage

Add:

```text
instance memory
MMU
GPU VA
```

Success:

```text
GPU virtual address
        |
        v
mapped physical VRAM
        |
        v
verified GPU access
```

---

# 56. Fifth Haiku stage

Add:

```text
FIFO
PBDMA
channel
GPFIFO
```

Initially:

```text
one channel
one GPFIFO
one runlist
```

Do not implement a scheduler.

---

# 57. Sixth Haiku stage

Add:

```text
GR
FECS
GPCCS
GK110 context
KEPLER_COMPUTE_B
```

Success criterion:

```text
GR reports operational
```

not merely:

```text
GR registers were written
```

---

# 58. Seventh Haiku stage

Submit the first compute command.

The first result should be tiny and deterministic.

Example:

```text
GPU buffer:
    [7]

compute:
    output = input + 35

expected:
    [42]
```

The exact GPU command sequence must be determined from the GK110 hardware documentation/Nouveau implementation and verified on the K40c.

---

# 59. Eighth Haiku stage — interrupts

Only after polling-based execution works should interrupts be introduced.

Implement:

```text
GPU interrupt
    |
    v
channel completion
    |
    v
waiter wakeup
```

Retain polling as a debugging fallback.

---

# 60. Ninth stage — user-space interface

Only after kernel-level execution is stable should a user-space API be designed.

Possible initial API:

```text
/dev/gpu/k40c0
```

with operations conceptually equivalent to:

```text
GET_INFO
ALLOC
FREE
MAP
UNMAP
SUBMIT
WAIT
```

Do not design a CUDA-compatible API.

The first API should expose the minimum functionality required to demonstrate native Haiku GPU compute.

---

# 61. Later compute interface options

Once raw GPU execution works, investigate:

```text
Option A:
native Haiku compute API

Option B:
OpenCL implementation

Option C:
Vulkan compute

Option D:
CUDA compatibility layer
```

These are separate projects.

The recommended architectural boundary is:

```text
                user-space API
                     |
                     v
             Haiku GPU runtime
                     |
                     v
               K40c driver
                     |
                     v
                 GK110
```

The K40c kernel driver should not know about CUDA source code, CUDA libraries, or CUDA application semantics.

---

# 62. Possible use of existing open-source projects

Investigate, but do not automatically depend on:

```text
Nouveau
Mesa
NVK
envytools
Linux GPU tools
OpenCL implementations
Vulkan implementations
```

For the first driver, Nouveau is the primary hardware reference.

Mesa/NVK should only become relevant once a functional native GPU driver exists.

---

# 63. Role of an AI coding agent

The coding agent should be assigned tasks in bounded units.

Good tasks:

```text
extract GK110 register definitions
build dependency graph
translate a register table
implement page-table encoding
write host-side tests
write Haiku wrapper
generate diagnostic code
compare register traces
analyse compiler errors
analyse static-analysis warnings
generate documentation
```

Poor tasks:

```text
"Port Nouveau to Haiku."
"Make the K40 work."
"Implement CUDA."
"Fix the GPU hang."
```

The latter tasks contain too much hidden state.

---

# 64. Recommended agent workflow

For each subsystem:

```text
1. Give agent source files.
2. Ask for hardware dependency analysis.
3. Ask for a written algorithm.
4. Review algorithm.
5. Ask for host-side implementation.
6. Run tests.
7. Port to Haiku.
8. Boot hardware.
9. Capture trace.
10. Compare against Ubuntu.
11. Fix one discrepancy.
12. Record result.
```

Do not allow the agent to modify several GPU subsystems simultaneously.

---

# 65. Suggested agent milestones

The coding agent should produce these artifacts sequentially:

```text
01-gk110-hardware-map.md
02-nouveau-dependency-map.md
03-register-database.md
04-mmu-design.md
05-fifo-design.md
06-gr-design.md
07-firmware-analysis.md
08-haiku-driver-design.md
09-host-test-suite.md
10-haiku-pci-driver.md
11-haiku-mmio-driver.md
12-haiku-memory-driver.md
13-haiku-mmu-driver.md
14-haiku-fifo-driver.md
15-haiku-gr-driver.md
16-haiku-compute-test.md
```

Each document should be reviewed before the next implementation stage.

---

# 66. Success criteria by level

## Level 0

```text
K40c detected by Haiku.
```

## Level 1

```text
BARs mapped.
MMIO works.
```

## Level 2

```text
VRAM detected.
VRAM allocation works.
```

## Level 3

```text
GPU virtual memory works.
```

## Level 4

```text
FIFO/channel/GPFIFO works.
```

## Level 5

```text
GR/FECS/GPCCS initialisation works.
```

## Level 6

```text
KEPLER_COMPUTE_B command executes.
```

## Level 7

```text
GPU computation produces a verified result.
```

## Level 8

```text
Interrupt-driven execution works reliably.
```

## Level 9

```text
A stable Haiku user-space compute API exists.
```

## Level 10

```text
Higher-level compute runtime can use the driver.
```

---

# 67. Failure policy

At every stage:

```text
failure
   |
   +--> capture diagnostic state
   |
   +--> save logs
   |
   +--> save register snapshot
   |
   +--> identify last successful operation
   |
   +--> reproduce
   |
   +--> isolate subsystem
```

Do not respond to failures by adding arbitrary register writes.

GPU programming should remain evidence-driven.

---

# 68. Multi-GPU support

Do not implement initially.

Once one K40c works:

```text
K40c #1
    |
    v
stable driver
    |
    v
K40c #2
```

The second card should initially be treated as an independent instance:

```text
/dev/gpu/k40c0
/dev/gpu/k40c1
```

Only later investigate:

```text
peer-to-peer
shared address spaces
multi-GPU scheduling
```

---

# 69. T7610-specific considerations

The T7610 provides an unusually useful development environment because it has:

```text
K600 -> display
K40c #1 -> compute
K40c #2 -> compute/reference
```

This means the target GPU does not need to provide display output.

Keep the K600 as the display device during early Haiku testing if Haiku's hardware support permits it.

Do not allow the experimental K40c driver to become the primary display driver.

The dual-socket CPU architecture is not central to the driver. The driver should not assume anything special about the two Xeon CPUs.

Likewise, 64 GB RAM is more than sufficient for the driver-development workload.

---

# 70. Performance measurement

Performance should not be an initial objective.

First measure:

```text
correctness
reliability
latency
```

Only later measure:

```text
command submission rate
GPU memory bandwidth
kernel execution rate
host-to-device bandwidth
device-to-host bandwidth
```

Do not optimise until a stable compute path exists.

---

# 71. Potential second-generation features

After the basic compute driver:

```text
GPU memory allocator
system-memory mappings
copy engine
multiple channels
multiple command queues
interrupt-driven synchronisation
GPU fences
timeouts
GPU reset
context switching
multi-process support
user-space mappings
```

Then:

```text
OpenCL
Vulkan compute
```

Potentially later:

```text
graphics
display
```

but those should be considered a separate project.

---

# 72. Potential third-generation project

If the driver becomes stable, investigate whether parts of the architecture can be generalised:

```text
GK104
GK110
GK208
```

The natural common abstraction would be:

```text
KeplerDevice
    |
    +-- MMU
    +-- FIFO
    +-- GR
    +-- Compute
```

with:

```text
GK110-specific
GK104-specific
```

implementations underneath.

Do not generalise before two devices actually require it.

---

# 73. Expected technical risks

Rank risks by subsystem rather than attempting to assign an overall project probability.

### High-risk areas

```text
GPU initialisation sequence
GR/Falcon initialisation
GR context construction
FIFO/PBDMA state
GPU MMU
GPU hang diagnosis
Haiku DMA/memory semantics
```

### Medium-risk areas

```text
PCI integration
BAR mapping
interrupts
VRAM allocation
firmware loading
command construction
```

### Lower-risk areas

```text
PCI identification
driver skeleton
MMIO wrapper
logging
host-side register encoding
documentation
test infrastructure
```

---

# 74. Immediate next steps

Before writing the Haiku driver, perform these tasks in Ubuntu.

## Step 1

Obtain a fixed Linux kernel/Nouveau source revision.

## Step 2

Identify the exact K40c PCI IDs in the T7610.

## Step 3

Capture complete PCI configuration.

## Step 4

Generate the GK110 Nouveau dependency tree.

## Step 5

Extract:

```text
GK110
GK104
GF100
```

dependencies for:

```text
FB
MMU
FIFO
GR
```

## Step 6

Build the GK110 register database.

## Step 7

Identify and document FECS/GPCCS firmware.

## Step 8

Document the GR initialisation sequence.

## Step 9

Document the FIFO/PBDMA initialisation sequence.

## Step 10

Document the MMU/page-table hierarchy.

## Step 11

Implement host-side tests for:

```text
register encoding
page-table construction
FIFO encoding
command construction
```

## Step 12

Build a register-trace comparison framework.

## Step 13

Create the minimal Haiku driver skeleton.

## Step 14

Boot Haiku and implement PCI detection.

Only after Step 14 should actual GK110 initialisation begin on Haiku.

---

# 75. Immediate coding-agent assignment

The first coding-agent task should therefore **not** be "write the driver".

Give the agent this task:

```text
Analyse the current Linux Nouveau source tree for GK110.

Produce a complete dependency analysis for implementing a
compute-only NVIDIA GK110 driver without Linux DRM/Nouveau
infrastructure.

Trace:

1. GK110 device identification
2. framebuffer/VRAM
3. memory controller
4. instance memory
5. MMU/VMM
6. FIFO
7. PBDMA
8. channel
9. GPFIFO
10. GR
11. FECS
12. GPCCS
13. KEPLER_COMPUTE_B
14. relevant firmware

For every dependency classify it as:

A = hardware algorithm that must be reimplemented
B = hardware data/register information to extract
C = Linux-specific infrastructure to replace
D = unnecessary for a compute-only driver

Produce:

- dependency graph
- source-file list
- function-level dependency list
- register list
- firmware list
- Linux API list
- proposed Haiku-native architecture
- unresolved questions
- tests required before implementation

Do not write driver code yet.
Do not assume that Linux abstractions should be reproduced.
Do not invent undocumented hardware behaviour.
Every hardware-specific claim must identify its source.
```

That analysis should become the specification for the subsequent implementation agent.

---

# 76. Definition of the project boundary

The project should be considered successful for its first phase when this statement is true:

> A native Haiku kernel driver can detect a Tesla K40c/GK110, initialise its memory and compute infrastructure, create a GPU virtual address space and compute context, submit a command stream using `KEPLER_COMPUTE_B`, execute a deterministic GPU computation, and return a verified result to the CPU, without depending on Linux Nouveau, DRM, CUDA, or a display stack.

That is a meaningful systems-engineering result in its own right.

The subsequent question is then no longer "can Haiku drive a K40c?" but rather:

```text
K40c hardware
      |
      v
native Haiku driver
      |
      v
generic Haiku GPU interface
      |
      +---- OpenCL?
      +---- Vulkan compute?
      +---- native compute API?
      |
      v
scientific / numerical applications
```

That second stage should be designed only after the first stage is operational.
