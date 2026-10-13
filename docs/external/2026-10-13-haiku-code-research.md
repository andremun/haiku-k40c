# Haiku code that can help the K40c project

Research date: 2026-10-13

## Assessment

Existing Haiku code can bridge much of the operating-system integration gap. I did not find a ready-made solution for K40c initialization, FIFO setup, or GR context generation in the sources inspected.

The findings below are based on upstream source inspection and project release information. They are not hardware-tested results, and do not demonstrate that the proposed Haiku driver can initialize or submit work to the K40c.

## Current NVIDIA work on Haiku

X547 maintains an experimental NVIDIA port combining the NVIDIA open kernel driver with Mesa NVK and Zink. Published experimental releases include v0.0.2.

The port targets Turing and newer GPUs. NVIDIA documents the same hardware boundary for its open kernel modules. The Kepler K40c therefore cannot use this port as a direct replacement for the driver being developed. Its useful role is as an operating-system integration reference.

Sources:

- [Haiku NVIDIA port](https://github.com/X547/nvidia-haiku)
- [Experimental releases](https://github.com/X547/nvidia-haiku/releases)
- [NVIDIA supported GPU generations](https://github.com/NVIDIA/open-gpu-kernel-modules#compatible-gpus)
- [Port submodule configuration](https://github.com/X547/nvidia-haiku/blob/master/.gitmodules)

The submodule configuration identifies the NVIDIA adaptation fork and branch. Its OS adaptation merits further inspection for memory, synchronization and driver-lifecycle patterns. This research does not certify those individual implementations as suitable for the K40c.

## Useful Haiku interfaces and implementations

| Project gap | Existing code | Application and limits |
|---|---|---|
| PCI discovery, ownership and configuration | `headers/os/drivers/PCI.h` | Enumeration, configuration access, reservation, capabilities, power-state operations, and MSI/MSI-X interfaces are available. Verify their behavior in the chosen guest and build. |
| BAR mapping, including addresses above 4 GB | NVIDIA kernel `driver.c` | Demonstrates register mapping and reconstruction of a 64-bit framebuffer BAR from paired registers. Review its address-domain assumptions before adapting it. |
| Resident host buffers and physical segments | `OS.h` and `KernelExport.h` | Locked/contiguous areas, memory locking, physical-segment lookup, and physical-memory mapping provide the foundation for a real buffer backend. They do not allocate GPU VRAM. |
| Timing, publication ordering and interrupts | `KernelExport.h` | Exposes `spin()`, memory barriers, timers, and interrupt-handler installation/removal. CPU ordering alone must not be assumed to complete posted GPU writes. |
| Device lifecycle and cleanup | Radeon HD `device.cpp` | First-open initialization, locking, reference counting, final-close cleanup, and checked user/kernel transfers are useful structural examples. GPU quiescence must precede release of DMA-accessible resources. |
| ROM acquisition and validation | Radeon HD `radeon_hd.cpp` | ROM mapping, copying, PCI image handling and validation provide surrounding infrastructure. AMD AtomBIOS execution semantics do not apply to NVIDIA. |

Direct source links:

- [PCI interface](https://github.com/haiku/haiku/blob/master/headers/os/drivers/PCI.h)
- [Kernel interfaces](https://github.com/haiku/haiku/blob/master/headers/os/drivers/KernelExport.h)
- [Area allocation definitions](https://github.com/haiku/haiku/blob/master/headers/os/kernel/OS.h)
- [NVIDIA kernel driver](https://github.com/haiku/haiku/blob/master/src/add-ons/kernel/drivers/graphics/nvidia/driver.c)
- [Radeon HD device lifecycle](https://github.com/haiku/haiku/blob/master/src/add-ons/kernel/drivers/graphics/radeon_hd/device.cpp)
- [Radeon HD ROM acquisition](https://github.com/haiku/haiku/blob/master/src/add-ons/kernel/drivers/graphics/radeon_hd/radeon_hd.cpp)

These links follow upstream `master` and may change. Pin reviewed revisions before implementation, and check interfaces against the project toolchain and Haiku image.

## Implications for memory and submission

The operating-system memory gap is smaller than the review package suggests. Haiku defines `B_FULL_LOCK`, `B_CONTIGUOUS`, and variants restricting physical allocation below 4 GB. Its existing NVIDIA driver uses contiguous allocation and `get_memory_map()` for a command buffer.

The remaining work is to establish the allocation policy, lifetime, alignment, address domain, and visibility protocol for each K40c object. Physical-segment lookup alone does not prove a complete DMA mapping. The PCI interface also exposes `ram_address()`; inspect its implementation and platform behavior before equating CPU physical and PCI bus addresses.

Keep these quantities distinct:

- CPU virtual addresses.
- Guest physical and device DMA/bus addresses.
- GPU virtual addresses.
- VRAM physical addresses.
- CPU-visible BAR aperture addresses.

The reviewed project models currently manipulate CPU vectors. A real backend must allocate GPU-visible objects and publish their contents. Define host-memory and VRAM operations separately, then connect the page-table and GPFIFO encoders to them.

Sources: [allocation definitions](https://github.com/haiku/haiku/blob/master/headers/os/kernel/OS.h), [NVIDIA allocation example](https://github.com/haiku/haiku/blob/master/src/add-ons/kernel/drivers/graphics/nvidia/driver.c), [PCI address interface](https://github.com/haiku/haiku/blob/master/headers/os/drivers/PCI.h).

## Initialization remains unresolved

The older Haiku NVIDIA driver contains cold-start work, but its documentation records limitations for GeForce 6/7-era cards. This does not establish a reusable GK110B initialization path.

The newer Turing port likewise does not demonstrate that its initialization machinery transfers to Kepler. Existing Haiku code supplies execution and supervision mechanisms, but the K40c still needs a chip-specific initialization procedure derived from the relevant Nouveau path.

The earlier E4 review therefore remains applicable: reconstruct conditions, read-modify-write operations, copying, delays, polling, helper effects and board-control operations. A flat replay of apparent debug-log writes is insufficient evidence of a sound procedure.

Source: [legacy NVIDIA driver notes](https://github.com/haiku/haiku/blob/master/src/add-ons/kernel/drivers/graphics/nvidia/UPDATE.html).

## Recommended development sequence

1. **Build a thin Haiku backend.** Implement PCI ownership, checked BAR mapping, allocation, timing, logging and cleanup using existing Haiku patterns. Validate against the exact project headers and kernel image.
2. **Separate GPU-memory interfaces.** Distinguish host-buffer allocation, VRAM allocation, GPU address-space mapping, and publication of page-table/RAMFC bytes. Connect the existing host encoders through these interfaces.
3. **Inspect the newer NVIDIA ports OS adaptation.** Use it as a reference for memory, synchronization and lifecycle integration. Retain Nouveau as the K40c hardware reference.
4. **Treat E4 as a dedicated initialization task.** Preserve state-dependent semantics and independently verify readiness. Existing Haiku infrastructure does not remove this dependency.
5. **Keep the first S1 experiment focused.** Use a source-verified FIFO-local command, deliberate interrupt masking, bounded polling of progress and relevant faults, and verified quiescence before cleanup.

## Effect on feasibility

The research increases confidence in the Haiku integration portion: the necessary OS mechanisms and useful driver examples already exist.

It does not yet increase confidence in blind boot-script replay or prove S1 without GR. The best opportunity is to reuse established OS mechanisms and concentrate new engineering on K40c initialization, GPU-visible memory, channel submission and safe teardown.

## Research limits

- No driver was built or installed during this research.
- No GPU, PCI, BAR, reset, passthrough or VM operation was performed.
- Source availability is not proof of compatibility with the project snapshot.
- No complete Haiku Kepler initialization or compute implementation was identified in the inspected sources; this is a scoped research result, not proof that none exists anywhere.
