
# Native NVIDIA Tesla K40c (GK110) Compute Driver for Haiku

## 1. Objective and Scope

The project is to develop a native Haiku kernel driver for the NVIDIA Tesla K40c, based on the GK110 Kepler GPU architecture, with **compute functionality as the primary objective**.

The driver is intended initially for the Dell Precision T7610 development machine:

- 2 × Intel Xeon E5-2620 v2
- 64 GB DDR3 ECC Registered RAM
- 2 × NVIDIA Tesla K40c, 12 GB VRAM each
- 1 × NVIDIA Quadro K600 used as the display GPU
- 1300 W PSU
- Ubuntu 22.04 currently available as the development/reference OS
- Haiku x86_64 will eventually be the target OS

The first usable driver should not attempt to reproduce the complete Linux NVIDIA/Nouveau graphics stack. The intended progression is:

**PCI discovery → MMIO access → GPU identification → VRAM management → GPU virtual memory/MMU → FIFO/channel submission → Kepler compute engine → deterministic GPU computation.**

Display, OpenGL, Vulkan, CUDA compatibility, power management, reclocking, multi-GPU support and sophisticated user-space APIs are later extensions.

The first important milestone is therefore not "run CUDA on Haiku". It is:

> Initialise one K40c sufficiently to submit a controlled compute command sequence, execute it on the GPU, and retrieve/verify the result from the host.

The implementation should be Haiku-native. Linux Nouveau should primarily serve as a source of hardware knowledge, register definitions, firmware information, algorithms and a behavioural reference rather than as a Linux driver mechanically ported into Haiku.

Nouveau is particularly valuable because its current source contains explicit Kepler/GK110 implementations for the relevant FIFO, GR and MMU infrastructure.

---

## 2. Design Constraints and Non-Goals

### 2.1 Fundamental constraints

The driver must:

1. Target GK110/Kepler specifically at first.
2. Work with the Tesla K40c's compute-oriented configuration.
3. Use Haiku's native PCI, memory, interrupt, threading, locking and device-driver facilities.
4. Avoid dependencies on Linux kernel APIs.
5. Keep hardware-specific register programming separate from Haiku operating-system integration.
6. Make every GPU initialisation stage independently testable and observable.
7. Fail safely when a hardware stage cannot be initialised.
8. Provide extensive diagnostic logging during development.

The coding agent must not assume that a Linux subsystem such as DRM, TTM, GEM, `dma_fence`, Linux workqueues or Linux interrupt APIs can simply be reproduced wholesale.

### 2.2 Explicit non-goals for the first implementation

Do not initially implement:

- display/KMS;
- X11/Wayland integration;
- OpenGL;
- Vulkan;
- CUDA compatibility;
- CUDA PTX compilation;
- power management;
- automatic reclocking;
- thermal management;
- SLI;
- SR-IOV/virtual functions;
- multiple simultaneous GPUs;
- sophisticated GPU scheduling;
- production-quality user-space compute APIs.

These can be considered only after a stable single-GPU compute path exists.

---

## 3. Reference Hardware and Initial Hardware Investigation

The Ubuntu system should remain the primary **reference and development environment** before attempting the Haiku implementation.

The first stage is to establish an authoritative hardware record for the exact K40c installed in the T7610.

Record:

- PCI domain/bus/device/function;
- PCI vendor/device ID;
- subsystem vendor/device ID;
- revision;
- BAR addresses and sizes;
- PCI capabilities;
- interrupt configuration;
- PCIe link characteristics;
- available VRAM;
- VBIOS information;
- GPU identification registers;
- relevant firmware versions;
- behaviour with Nouveau;
- behaviour with the proprietary NVIDIA driver, if useful for observation;
- topology of the two K40c cards and K600.

Use Ubuntu tools including:

```text
lspci
setpci
lshw
dmidecode
dmesg
journalctl
udevadm
cat /proc/iomem
cat /proc/interrupts
```

`pciutils` is available directly in Ubuntu 22.04; the Jammy package provides the `lspci`/PCI inspection infrastructure.

The two K40c cards should initially be treated independently. Develop and test against **one card only**, with the second card reserved for later experiments or recovery.

The Quadro K600 should remain the display device during development. This avoids making the K40c driver responsible for display initialisation.

---

## 4. Nouveau/GK110 Source Map

The principal hardware reference is the Linux Nouveau implementation.

The coding agent should obtain a fixed Linux kernel/Nouveau source revision and work from that snapshot rather than repeatedly analysing an uncontrolled moving target.

The relevant dependency structure is approximately:

```text
GK110 device description
        │
        ├── PCI / BAR / MMIO
        │
        ├── MC / hardware units
        │
        ├── FB / VRAM
        │
        ├── INSTMEM
        │
        ├── BAR
        │
        ├── MMU / VMM
        │       │
        │       └── page tables / GPU virtual addresses
        │
        ├── FIFO
        │       │
        │       ├── channels
        │       ├── runlists
        │       ├── PBDMA
        │       └── interrupts
        │
        └── GR
                │
                ├── GPC/TPC configuration
                ├── context
                ├── firmware/Falcon components
                └── compute classes
```

The source should be classified into three categories.

### A. Hardware knowledge to preserve

These are the most valuable parts of Nouveau:

- register offsets;
- register bit definitions;
- GK110-specific constants;
- engine topology;
- FIFO/channel structures;
- MMU/page-table formats;
- GR/GPC/TPC configuration;
- firmware names and loading requirements;
- command/class identifiers;
- hardware sequencing;
- known workarounds;
- error and fault interpretation.

### B. Algorithms to reimplement

These can be translated conceptually:

- GPU memory allocation;
- GPU virtual-address mapping;
- page-table construction;
- channel creation;
- GPFIFO construction;
- runlist submission;
- interrupt handling;
- engine initialisation;
- compute context creation.

### C. Linux-specific infrastructure to discard

Do not port these directly:

- Linux DRM;
- Linux device model;
- Linux PCI interfaces;
- Linux DMA APIs;
- Linux VM/allocator infrastructure;
- TTM/GEM;
- Linux scheduler primitives;
- Linux workqueues;
- Linux locking abstractions;
- Linux `dma_fence`;
- Linux userspace interfaces.

Current Nouveau source demonstrates that newer GPU generations continue to reuse substantial Kepler-era FIFO infrastructure, including `gk110_chan_*` and related functions. This is useful evidence that the GK110 implementation should be analysed as a set of reusable hardware mechanisms rather than as an isolated driver file.

The source tree to investigate first is therefore:

```text
drivers/gpu/drm/nouveau/nvkm/
    engine/
        device/
        fifo/
        gr/
        ce/
    subdev/
        pci/
        bus/
        mc/
        fb/
        mmu/
        instmem/
        bar/
        bios/
        i2c/
        gpio/
        therm/
        clk/
        pmu/
    core/
    falcon/
```

Priority is:

```text
device
pci
bus
mc
fb
instmem
bar
mmu
fifo
gr
falcon
```

with display, thermal, clock and power-management components deferred.

---

## 5. Ubuntu Pre-Haiku Development Environment

A substantial amount of work should be completed under Ubuntu before booting Haiku.

The Ubuntu environment should contain:

```text
gcc / g++
clang / clangd
make / cmake
git
gdb
lldb
objdump
readelf
nm
addr2line
hexdump
xxd
strings
grep / ripgrep
sed / awk
python3
ctags or universal-ctags
cscope
bear
pciutils
binutils
```

Clang/clangd are available in the Ubuntu 22.04 package ecosystem and are useful for source navigation and static analysis.

The agent should also create a reproducible source-analysis environment containing:

```text
Linux kernel source
Nouveau source
Haiku source
Haiku headers
driver-development notes
generated register database
generated dependency graph
test programs
captured logs
```

The development repository should have at least:

```text
k40c-haiku/
    docs/
    nouveau-reference/
    hardware/
    analysis/
    registers/
    firmware/
    host-tests/
    haiku-driver/
    traces/
    tools/
    experiments/
```

The `nouveau-reference` directory should be treated as immutable reference material. Changes should occur in the Haiku implementation, not by modifying the reference source.

---

## 6. Automated Source and Hardware Analysis

This is an important opportunity for the coding agent.

Before writing substantial driver code, automate extraction of information from Nouveau.

The analysis tooling should generate:

### 6.1 Register database

Extract:

```text
register address
register name
bit fields
mask
reset/initial value where known
read/write semantics where documented
GK110-specific source references
```

Represent it in a machine-readable format such as JSON/YAML and optionally generate C++ constants.

### 6.2 Dependency graph

For each GK110 function, identify:

```text
function
source file
called functions
hardware registers accessed
subsystems required
Linux-only dependencies
Haiku replacement required
```

This should produce a graph such as:

```text
k40c_probe
   |
   +-- pci_init
   +-- mmio_init
   +-- mc_init
   +-- fb_init
   +-- instmem_init
   +-- bar_init
   +-- mmu_init
   +-- fifo_init
   +-- gr_init
   +-- channel_create
   +-- gpfifo_submit
```

### 6.3 Register-access extraction

Automatically identify every MMIO access in the GK110 implementation:

```text
nvkm_rd32(...)
nvkm_wr32(...)
nvkm_mask(...)
```

and associate each access with:

- subsystem;
- initialisation phase;
- source location;
- register;
- value/mask;
- purpose if inferable.

This becomes a practical "GK110 bring-up checklist".

### 6.4 Linux dependency detector

The agent should flag references to:

```text
struct device
struct pci_dev
spinlock_t
mutex
wait_queue
dma_*
ioremap
kmalloc
vmalloc
GFP_*
work_struct
completion
atomic_*
list_head
Linux IRQ interfaces
DRM interfaces
```

Each occurrence should be classified as:

```text
replace with Haiku API
rewrite algorithm
remove
defer
```

### 6.5 Documentation generator

Generate a concise subsystem document automatically from the source analysis:

```text
PCI
MMIO
VRAM
MMU
FIFO
Channel
GPFIFO
GR
Firmware
Interrupts
```

For each subsystem, show:

```text
purpose
Nouveau files
GK110-specific files
hardware registers
dependencies
Haiku implementation status
tests
known unresolved issues
```

This tooling is valuable enough that it should be developed before the main driver.

---

## 7. Haiku Driver Architecture

The Haiku implementation should be a native kernel driver with a deliberately small architecture.

A possible initial layout is:

```text
k40c/
    k40c.cpp
    k40c.h

    pci.cpp
    mmio.cpp
    interrupt.cpp

    memory.cpp
    vram.cpp
    instmem.cpp
    bar.cpp

    mmu.cpp
    page_table.cpp

    fifo.cpp
    channel.cpp
    gpfifo.cpp

    gr.cpp
    gr_gk110.cpp

    firmware.cpp
    debug.cpp

    tests/
```

The core device object should contain only state required by the driver:

```text
PCI information
BAR mappings
MMIO base
VRAM information
GPU architecture
MMU state
FIFO state
channel state
GR state
interrupt state
diagnostic state
```

Separate:

1. **Haiku OS integration**
2. **GPU hardware abstraction**
3. **GK110-specific implementation**

For example:

```text
Haiku PCI API
      ↓
K40C PCI abstraction
      ↓
GK110 hardware description
      ↓
GK110 engine implementation
```

The driver should not expose a CUDA-like API at this stage.

A minimal private test interface is preferable: enough to allocate memory, submit a test workload and return a result.

The Haiku device-manager model should be followed rather than inventing a Linux-style registration mechanism. Haiku drivers provide standard driver/device entry points and device nodes through the Haiku device architecture.

---

## 8. Implementation Sequence

Implementation should proceed as a sequence of independently verifiable stages.

### Stage 1 — PCI discovery

Success criteria:

- Haiku identifies the K40c;
- correct PCI ID detected;
- BARs discovered;
- device node created;
- no GPU programming yet.

### Stage 2 — MMIO

Implement:

```text
BAR mapping
32-bit register read
32-bit register write
masked write
diagnostic register dump
```

Success criterion:

> Known identification/status registers return values consistent with Ubuntu/Nouveau observations.

### Stage 3 — Basic GPU state

Implement only what is required to establish:

```text
MC
FB
VRAM detection
instance memory
BAR infrastructure
```

Do not yet initialise compute.

Success criteria include:

- correct VRAM size;
- stable MMIO;
- allocation of a small GPU-visible memory region;
- CPU read/write verification.

### Stage 4 — GPU virtual memory

Implement:

```text
GPU virtual address space
page tables
page-table allocation
mapping
unmapping
GPU address translation
```

Start with one address space and a minimal mapping model.

Success criterion:

> A known physical/VRAM allocation can be mapped to a GPU virtual address and accessed correctly by a GPU command.

### Stage 5 — FIFO/channel infrastructure

Implement:

```text
FIFO initialisation
channel
channel context
GPFIFO
runlist
PBDMA configuration
interrupts
```

This is one of the most difficult stages and should be treated independently from GR.

The key objective is:

> Submit a deliberately trivial GPU command and obtain a completion indication.

### Stage 6 — Compute engine

Implement the minimum GK110 GR/compute initialisation required for compute.

Do not attempt the complete graphics pipeline.

The agent must identify precisely which parts of Nouveau's `gr/gk110` path are required for compute and which are graphics-only.

This stage may require:

- GR engine initialisation;
- GPC/TPC configuration;
- context state;
- FECS/GPCCS firmware;
- compute class registration;
- relevant Falcon microcontroller setup.

No assumption should be made that firmware is optional. The agent must determine the exact dependency from the GK110 Nouveau path.

### Stage 7 — First deterministic computation

The first GPU test should be deliberately simple.

Conceptually:

```text
host allocates buffer
        ↓
initialise known values
        ↓
map buffer into GPU VA
        ↓
create compute channel
        ↓
submit compute command
        ↓
GPU modifies buffer
        ↓
wait for completion
        ↓
CPU reads buffer
        ↓
verify exact expected result
```

For example:

```text
input[i] = i
output[i] = input[i] + 1
```

The first test should preferably avoid a sophisticated compiler/runtime.

The objective is to demonstrate that the hardware command path works.

Only after this succeeds should the project consider higher-level shader/program execution mechanisms.

---

## 9. Testing, Tracing and Failure Diagnostics

GPU bring-up must be treated as a state-machine debugging problem.

Every initialisation phase should have:

```text
entry log
important register writes
important register reads
state transition
success/failure result
```

For example:

```text
[K40C] PCI initialised
[K40C] BAR0 = ...
[K40C] GPU = GK110
[K40C] VRAM = 12288 MiB
[K40C] MMU initialised
[K40C] FIFO initialised
[K40C] channel 0 created
[K40C] GPFIFO configured
[K40C] compute engine initialised
[K40C] command submitted
[K40C] command completed
```

The driver should maintain a diagnostic dump capable of reporting:

```text
GPU identification
MC status
FIFO status
channel state
PBDMA state
runlist state
MMU state
fault registers
GR status
interrupt status
```

### Ubuntu/Nouveau trace comparison

Whenever possible, reproduce the same initialisation operation under Ubuntu and capture:

```text
register values
register writes
engine status
MMU state
FIFO state
faults
```

The Haiku implementation can then be compared against the known-working Linux/Nouveau sequence.

This should become an automated comparison tool rather than a manual process.

### GPU hang policy

A GPU hang is expected during early development.

The driver must therefore provide:

- timeout on every wait;
- diagnostic dump on timeout;
- channel reset/reinitialisation where feasible;
- ability to disable a failing stage;
- no infinite polling loops;
- no automatic repeated hardware resets without logging.

If a stage causes an unrecoverable GPU lockup, rebooting the T7610 is acceptable during early bring-up. The development process must preserve enough state to determine the last successful operation.

---

## 10. Coding-Agent Workflow, Deliverables and Next Steps

The coding agent should work incrementally. It should **not** be instructed to "implement the K40c driver" in one operation.

Each task must produce:

1. source code;
2. a short design note;
3. tests or validation procedure;
4. diagnostic output;
5. a list of unresolved assumptions;
6. references to the corresponding Nouveau implementation.

The agent must distinguish explicitly between:

```text
KNOWN
    confirmed from hardware/source

INFERRED
    strongly indicated but not directly verified

UNKNOWN
    requires experiment or additional source investigation
```

It must not silently convert inferred register meanings or command sequences into asserted facts.

### Initial coding-agent tasks

The first work package should be entirely Ubuntu-side and should **not write the Haiku driver yet**.

Task 1:

```text
Acquire and freeze the selected Nouveau/Linux source revision.
Identify all GK110/K40c-specific files.
Build the initial dependency graph.
```

Task 2:

```text
Extract all GK110-related MMIO register accesses.
Generate a machine-readable register database.
```

Task 3:

```text
Map every Linux-specific dependency in the relevant Nouveau code
to one of:

    Haiku API replacement
    independent reimplementation
    removable functionality
    deferred functionality
```

Task 4:

```text
Create a minimal GK110 hardware model/document describing:

    PCI
    BARs
    MMIO
    MC
    FB/VRAM
    instance memory
    BAR
    MMU
    FIFO
    channel
    GPFIFO
    runlist
    PBDMA
    GR
    Falcon/firmware
```

Task 5:

```text
Produce the exact minimum dependency chain required to reach:

    PCI
      → MMIO
      → VRAM
      → MMU
      → FIFO
      → channel
      → GPFIFO
      → compute engine
      → deterministic GPU operation
```

Only when that dependency chain is understood should the agent begin writing the Haiku driver.

### Definition of the first successful project milestone

The project should consider the first major milestone achieved when the following is demonstrated on the actual T7610 K40c:

```text
Haiku
  ↓
native K40c kernel driver
  ↓
GK110 initialisation
  ↓
GPU virtual memory
  ↓
GPU command submission
  ↓
Kepler compute execution
  ↓
GPU writes result
  ↓
Haiku reads and verifies result
```

That is the **minimum viable native compute driver**.

Everything above this level—CUDA compatibility, a general compute API, Vulkan/OpenGL, display support, multi-GPU support and performance optimisation—should be treated as subsequent projects rather than prerequisites for proving that the K40c can be driven natively by Haiku.

The central engineering principle is therefore:

> Reimplement the smallest GK110 hardware path necessary for compute, using Nouveau as the authoritative open hardware reference, while replacing all Linux-specific infrastructure with small, explicit Haiku-native components.