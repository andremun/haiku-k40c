# B2 memory ownership and publication boundary

2026-10-16. `src/memory/Memory.h/.cpp`, HOST_ONLY.

This is the freestanding layer between host encoders and a future physical
backend. GuestPhysical, DeviceIova, VramPhysical and GpuVirtual are distinct
non-converting types. A backend must supply and verify the appropriate device
address; a CPU pointer or captured physical literal never establishes one.
A GPU virtual mapping is a separate operation, not an IOVA cast. No translation
or IOMMU identity is assumed by this layer.

A Buffer owns a nonzero backend token. Failed partial allocations are released
or transferred to quarantine. Writes (including failed partial writes) invalidate
publication; bounds checks use subtraction to avoid overflow. publish must
complete the actual backend upload/cache/bus visibility protocol, not only a
compiler fence. Submission pinning requires publication and a verified physical
address in the appropriate domain. While pinned, reads, writes and release are
refused. Only independently verified quiescence permits retirement.

Backend must outlive buffers. Destruction of a pinned allocation transfers its
ownership to backend quarantine, never release. Release failures are also
quarantined. Recovery retains storage until a reviewed quiescence/reset procedure
can release it. Quarantine is a backend obligation, not an implicit free.

Tests: 39 host checks plus compile-time non-conversion/non-copyability assertions.
The implementation builds with -ffreestanding -fno-exceptions -fno-rtti. This does
not prove DMA, PRAMIN uploads, GPU mappings, flushes, native allocation behavior,
or real quarantine/recovery. Those operations are deliberately injectable and
still need the Haiku/chip backend. Do not mark all of B2 hardware-ready.

## S1B2: native Haiku host adapter

`src/os/HaikuMemory.*` connects the memory interface to native host allocation.
`k40_os_allocate_dma32` uses `B_32_BIT_CONTIGUOUS`, as Haiku's nvidia driver does
(`reference/haiku/src/add-ons/kernel/drivers/graphics/nvidia/driver.c:939-957`).
Haiku defines this as contiguous storage below 4 GiB (`headers/os/kernel/OS.h:77`).
This is a conservative allocation choice, not a claim about GK110 DMA width.
The ordinary OS scratch allocator remains available for non-DMA tests.

The adapter overallocates, aligns the guest physical view, and keeps the original area for release.
The public extent excludes the unused prefix and suffix. CPU access stays bounded to that extent.
The allocator checks the full contiguous physical span and its 32-bit limit.
Neither allocation nor `get_memory_map` establishes a device IOVA.

`NativePool` stores ownership records and monotonic tokens. The caller owns its lifetime.
The pool must outlive buffers, providers, active mappings, and quarantined records.
The caller must serialize these objects and keep the pool owner loaded while it is nonempty.
Adapter recreation does not discard the pool or reuse live ownership tokens.
A later production driver must provide that persistent owner and unload discipline.

An optional `DmaProvider` supplies mapping, independent verification, publication, and unmapping.
No native identity mapper or device-visibility provider is supplied.
Without one, allocation/read/write work, but publication and submission stay denied.
A verified mapping must carry an ownership token, alignment, and a valid extent.
A failed map must expose any partial mapping token for cleanup.
The provider must outlive its mapping records. GPA-to-IOVA equality remains UNKNOWN under VFIO.
GPU virtual mappings and owned VRAM allocation remain separate MMU/VRAM integration work.

Cleanup removes the device mapping before releasing the area.
If any release step fails, the buffer blocks access, address queries, publication, and submission.
A later close may retry cleanup. Destruction transfers failed ownership to quarantine.
Quarantine never frees storage. Recovery requires external quiescence evidence.
The native adapter also blocks direct access after release begins.

Host tests exercise alignment, distinct GPA/IOVA values, missing verification, publication failures,
partial allocation/mapping, failed unmap/free, pool exhaustion, stale tokens, and quarantine recovery.
The native `k40_memory_probe` checks host allocation/readback and default-denied submission only.
It uses no PCI enumeration, BAR mapping, DMA, or GPU. A cardless pass is Haiku OS evidence only.

## S1NATIVE permanent owner

`docs/NATIVE-OWNER.md` specifies the separate KEEP_LOADED module and DMA proof
requirements. The module owns its NativePool and exports opaque handles through
a versioned kernel API. A legacy driver uses OwnerClient, detaches its lease,
then releases its module reference. Startup state and quarantine remain resident.
No external provider implementation or driver callback can be installed in v1.

The owner denies publication and conservatively retains storage after any startup
attempt. It exposes no recovery or reset shortcut. Host tests and native linking
pass; actual Haiku module load/client reload behavior remains untested. Existing
probes still use their isolated test pools and have no production lifetime claim.
