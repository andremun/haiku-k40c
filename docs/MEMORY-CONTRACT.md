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
