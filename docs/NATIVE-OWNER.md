# Native owner and DMA contract (S1NATIVE)

The separate `generic/k40c_owner/v1` module owns startup and allocation state.
The legacy driver owns only a client reference and an exclusive lease. No GPU
operation is exposed. Publication remains denied. This is an implemented source
contract with host tests and native link evidence, not native load/reload proof.

## Lifetime selected from Haiku

KNOWN / SOURCE_ONLY: `headers/os/drivers/module.h:17-28` declares the module
interface and B_KEEP_LOADED. In the pinned kernel,
[module.cpp:356-363,2216-2221](https://github.com/haiku/haiku/blob/49a0af9585d80e42240af63ab66e31e9873f59b8/src/system/kernel/module.cpp#L356)
adds a permanent reference after successful initialization of a KEEP_LOADED
module. `put_module` at lines 2262-2275 therefore cannot ordinarily reduce its
reference count to zero. The initialized state and image remain resident.

This differs from the legacy driver lifetime:
[legacy_drivers.cpp:463-476](https://github.com/haiku/haiku/blob/49a0af9585d80e42240af63ab66e31e9873f59b8/src/system/kernel/device_manager/legacy_drivers.cpp#L463)
calls uninit_driver and unloads the driver's add-on. A driver static alone is
insufficient for the per-boot latch or retained allocations.

The sparse reference checkout omits these two kernel files. They were read from
the exact pinned commit into /tmp. `work/S1NATIVE/source-hashes.log` records their
SHA-256 values. The module file matches the cross-source checkout byte for byte.
The kernel used for linking is the previously exported matching hrev60207 kernel.
This source check alone does not establish runtime behavior. The later
S1OWNERTEST result below supplies the bounded cardless lifetime observation.

## Implementation

`HaikuOwnerModule.*` exports a versioned kernel-only C interface and modules[].
B_MODULE_INIT constructs the owner in aligned resident storage exactly once.
Repeated initialization and every uninitialization request are rejected. There
is no destructor, reset-to-Fresh, recovery override, or forced-free API. The
module does not allocate resources during initialization.

`NativeOwner.*` contains the startup latch, NativePool, memory adapter and opaque
allocation handles. It stores no driver-owned provider, object, or callback.
Consequently a driver unload cannot leave a dangling provider vtable in a pool
record. All operations use one nonblocking atomic guard: concurrent/reentrant
entry returns Busy. Exclusive lease IDs and allocation IDs increase monotonically.
Stale leases or handles fail; neither type is a device address.

`OwnerClient.*` acquires the module by its fixed name, checks ABI version and
required operations, then acquires a lease. On close it detaches before releasing
the module reference. Busy detach keeps both reference and lease. A driver must
drain and serialize its own calls before uninit_driver. A client that loses its
lease without detaching leaves the owner busy until the guest ends. There is no
automatic lease takeover. This deliberately trades recovery convenience for
preservation of possibly referenced state.

Before startup, bounded host read/write and cleanup are allowed. Partial native
allocation or failed release retains a record; failed detach cleanup quarantines
it. Quarantine blocks further allocation. Once startup is attempted, all owned
storage is conservatively retained and quarantined on detach. The current API
cannot prove which resources are unreferenced, so it exposes no retirement or
recovery shortcut. Diagnostics expose extent/GPA/status only, never CPU pointers
or verified IOVAs. Retained storage survives client recreation in the owner.

The freestanding `runtime/BootState.h` holds the same one-shot type used by the
host controller. Only the controller and owner can transition it. Beginning
consumes the latch. Finishing records caller-reported Complete or Failed.
Detach during Running records Failed. No transition returns to Fresh, even when
all allocations were freed. These state markers grant no write permission and
are not independent hardware-readiness evidence.

S1OWNERTEST now loads this owner with a dedicated cardless client probe.
`results/20261027-owner-reload/` records the successful 52.57-second hrev60207 run.
Client lease 1 consumes the software latch and detaches allocation token 2 into
quarantine. After real uninit/reload, lease 2 observes token 2, Failed state,
one owned record and one quarantine record. Startup and allocation are refused.
Host pattern readback, aligned GPA, clean release and denied publication also pass.

This is KNOWN Haiku OS evidence for the tested lifetime path. It does not test
failed delete_area recovery, arbitrary concurrent clients, physical DMA or GPU
references. Identity/memory probes remain isolated tests. Future production
integration must acquire this module rather than create another latch or pool
inside an unloadable driver. The lifetime result supplies no DMA/readiness proof.

## DMA proof required before a provider exists

KNOWN from `tools/haiku/card_run.py:90-110`: the closed B5 command requests Q35,
KVM, fixed RAM and only the approved VFIO device. It requests no explicit guest
IOMMU device. This is a statement about requested configuration. It is not proof
of live DMA translation, identity mapping, or visibility.

GPA-to-device-IOVA equality remains UNKNOWN. ABI v1 has no provider installation
operation and always denies publication. B_32_BIT_CONTIGUOUS and get_memory_map
establish host storage/GPA mechanics only. The KEEP_LOADED flag establishes
neither DMA mapping nor cache visibility.

A later provider must supply checkable evidence for all of these obligations:

1. Bind the mapping contract to the current guest instance, launch configuration,
   approved device, VFIO isolation and guest translation configuration. Reject
   stale evidence after RAM-slot, device, IOMMU, migration or lifecycle changes.
2. Establish the actual device aperture and translation for the entire owned
   extent. Validate alignment, width, overflow and permissions. A plausible GPA
   value or CPU readback does not establish an IOVA.
3. Own a nonzero mapping token whose implementation and state live as long as
   every reference, including quarantine. A failed partial map must expose its
   cleanup token. No provider callback may point into an unloadable client.
4. Specify CPU memory type and device cache/coherency target. Implement and check
   the required ordering, cache/bus visibility and mapping invalidation protocol.
   A compiler fence alone is insufficient. Do not invent a flush instruction or
   infer visibility from a cardless byte-copy test.
5. Validate the contract with a separately reviewed, authorized physical stage
   using owned memory and fault baselines. Record exactly which address/visibility
   property the experiment establishes. No such stage ran in this task.
6. Unmap only after independently established quiescence. Remove device mappings
   before releasing native areas. Retain partial mappings/areas on uncertainty
   and preserve fault evidence. Do not reset or retry automatically.

No native provider was added. Source proof may narrow the candidate contract,
but physical verification and A7 permission remain separate gates.

## Reproduce host/native checks

```sh
make -s -C tests ../build/tests/test_native_owner ../build/tests/test_prestart
build/tests/test_native_owner
build/tests/test_prestart
HAIKU_CROSS="$HOME/haiku-cross" KCFLAGS='-Werror -Isrc' \
  bash tools/haiku/build-driver.sh k40_owner_module \
  src/os/HaikuBackend.c src/os/HaikuMemory.cpp src/os/NativeOwner.cpp \
  src/os/HaikuOwnerModule.cpp src/os/OwnerClient.cpp
make check
```

The build compiles against real Haiku headers with freestanding C++, no RTTI or
exceptions, and links with --no-undefined against matching kernel.so. It exports
the module table without a dynamic global constructor. It is not installed or
loaded by these commands. No VM, PCI/BAR access, reset or root step is involved.
