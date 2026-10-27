# DMA publication contract: source and evidence closure

S1DMACONTRACT narrows the candidate address path. It does not close Q7 or enable
publication. GPA-as-IOVA is INFERRED for ordinary mapped RAM under the saved
no-explicit-vIOMMU configuration. No live mapping or payload visibility was
measured. NativeOwner still has no provider installation operation. The existing
HaikuMemory default denies publication.

## Source identities and limits

KNOWN from work/S1DMACONTRACT/host-inventory.log: the inspected host runs Linux
6.8.0-138-generic, package linux-hwe-6.8 6.8.0-138.138~22.04.1. Its installed QEMU
reports 6.2.0, Ubuntu package 1:6.2+dfsg-2ubuntu6.31. The recorded binary SHA-256
is 55862c768c21fa7d3e72ca1b24797d8ab5b406eb5ef4c9ab9c2280f4e0b8f330.
The installed package verification returned success. These are current inventory
facts, not the identity of the executable used in the earlier B5 run. That run
recorded the command name and arguments but no QEMU binary hash/version.

The exact Ubuntu QEMU source was reconstructed from its official
[DSC](https://security.ubuntu.com/ubuntu/pool/main/q/qemu/qemu_6.2+dfsg-2ubuntu6.31.dsc),
orig archive and Debian patch archive. Both archive sizes and SHA-256 values match
the DSC. dpkg-source applied the package patch series in /tmp/k40-dma-sources/.
The DSC signature was not checked. HTTPS origin and recorded content hashes give
retrieval/reproducibility evidence, not an independent build attestation.

The additional Haiku sources use the existing pin
49a0af9585d80e42240af63ab66e31e9873f59b8. Linux VFIO source uses the upstream v6.8
baseline. It is explicitly not the exact Ubuntu -138 kernel source. Distribution
deltas and the effective live domain configuration remain UNKNOWN.
All additional URLs/content hashes are in work/S1DMACONTRACT/evidence.json.
No reference/ content changed. The aliases below name these exact files:

| Alias | Source |
|---|---|
| Q-common | Patched Ubuntu hw/vfio/common.c |
| Q-vfio-pci | Patched Ubuntu hw/vfio/pci.c |
| Q-pci | Patched Ubuntu hw/pci/pci.c |
| Q-trace | Patched Ubuntu hw/vfio/trace-events |
| H-vm | Pinned Haiku src/system/kernel/vm/vm.cpp |
| H-area | Pinned Haiku src/system/kernel/vm/VMArea.cpp and headers/private/kernel/vm/VMArea.h |
| H-paging | Pinned Haiku src/system/kernel/arch/x86/paging/64bit/X86PagingMethod64Bit.h |
| L-type1 | Linux v6.8 drivers/vfio/vfio_iommu_type1.c |

Source facts below are KNOWN / SOURCE_ONLY. Conditional conclusions are INFERRED.
No source fact is marked HARDWARE_VERIFIED merely because the code exists.

## Candidate address chain

| Boundary | What source establishes | What remains unverified |
|---|---|---|
| Guest kernel CPU pointer -> GPA | Haiku walks the current/kernel translation map and combines contiguous physical entries. H-vm:5360-5445. The driver requires one extent covering the rounded allocation. src/os/HaikuBackend.c:52-76. | This provides guest physical addresses, not host physical addresses or device IOVAs. |
| GPA storage ownership | B_32_BIT_CONTIGUOUS becomes contiguous wiring with an upper physical restriction at 4 GiB when needed. H-vm:1638-1649. The adapter validates the complete extent below 4 GiB and retains its area token. | Allocation alone does not give a VFIO mapping, device aperture or visibility. |
| PCI DMA address space -> QEMU guest memory | VFIO selects pci_device_iommu_address_space for the assigned device. Q-vfio-pci:2856-2862. Without a selected IOMMU function, Q-pci:2705-2753 returns address_space_memory. | The saved options request no explicit guest IOMMU. The realized per-device address space was not captured. |
| QEMU RAM section -> VFIO IOVA/HVA | Q-common:922-925 rounds the section address-space offset to a host page. Q-common:1073-1096 derives the RAM host pointer and calls vfio_dma_map with that IOVA and extent. | Each relevant section must actually map, cover the full allocation, and remain mapped. Device RAM, holes, IOMMU regions and discard listeners have different handling. |
| VFIO userspace request -> host IOMMU | Q-common:493-523 passes separate vaddr, iova, size and device READ/WRITE permissions to VFIO_IOMMU_MAP_DMA. L-type1:1560-1600 checks alignment/overflow. L-type1:613-650,1464-1486 pins/translates QEMU virtual pages. L-type1:1430-1451 installs IOVA -> host PFN mappings. | Actual ioctl success, backend type, domain/aperture and lifetime are not in B5 evidence. Upstream kernel behavior is not a runtime domain capture. |
| GPU requester -> owned bytes | The host IOMMU is the candidate translator from device IOVA to host physical memory. CPU KVM translation is a separate path to the same guest RAM backing. | No physical transfer to or from the owned page was verified. |

INFERRED: for ordinary RAM in the global guest address space, the mapping IOVA
has the same numerical value as GPA. It is not numerically the host physical
address or QEMU host virtual pointer. Neither guest DMA32 allocation nor the lack
of an explicit vIOMMU option proves that equality for a particular allocation.
Do not install an identity mapper on this inference.

KNOWN from the saved B5 launch: Q35, 4096 MiB, one requested VFIO device
0000:04:00.0, and no explicit guest IOMMU device. Saved host checks recorded
vfio-pci and a one-device group. These are saved observations, not current checks.
The launch memory size does not mean every number below 4 GiB is RAM. Only mapped
RAM intervals may satisfy the contract. The serial PCI command value was 0x0007.
Bus mastering was already enabled before the identity probe. Who enabled it is
INFERRED to be firmware/Haiku, not verified. It grants no DMA test permission.

## Aperture, ownership and invalidation

The first mapping role is the pre-POST host flush page, not a general GPU buffer.
GK110 selects the GF100 flush hook (reference/nouveau/nvkm/subdev/fb/gk110.c:55-65).
Nouveau allocates a zeroed page and dma_map_page(..., DMA_BIDIRECTIONAL) in
reference/nouveau/nvkm/subdev/fb/base.c:281-289. It programs the returned DMA
address shifted by eight in fb/gf100.c:81-84. It does not program a CPU pointer
or substitute a Linux physical address for a DMA address.

KNOWN / SOURCE_ONLY: the existing helper encodes a 32-bit value after shifting
by eight (src/runtime/PreStart.cpp:115-118). That supplies a 40-bit encoding
limit, not proof of the card's complete DMA aperture. Require 4 KiB alignment and
a complete page. Validate the full mapped extent, not just the encoded base,
against all constraints: allocation, host IOVA windows/page sizes, permissions,
register encoding and the selected role. Reject overflow, holes and partial
coverage. Keep GPA, IOVA, HVA, host PA, VRAM and GPU VA distinct in diagnostics.

Haiku owns/pins guest pages. QEMU owns the RAM backing and VFIO mapping lifecycle.
A guest provider cannot create a host VFIO mapping by calling get_memory_map.
It needs evidence tied to the actual host mapping owner and current launch.
Guest RAM-slot changes, discard, vIOMMU changes, device reassignment, migration,
restore, or a new guest invalidate prior evidence. Preserve backing and mappings
while any device reference may exist. Guest owner residency alone cannot control
the host mapping lifetime.

Q-common:1198-1234 handles mapping removal. Host IOMMU mapping removal is distinct
from GPU PDB/TLB invalidation and BAR publication. The pre-POST page is addressed
through its DMA target, not through a constructed GPU VMM. Neither a GPU TLB flush
nor clearing a software token removes host mappings. Removing a mapping also does
not independently prove that a requester has stopped issuing transactions.

## CPU and device visibility

KNOWN / SOURCE_ONLY: H-area.cpp:26-35 starts memory_type at zero. H-area.h:239-248
returns/sets that field. H-paging:167-183 maps default/write-back selection to no
additional cache-control bits. This supports a normal cached-RAM candidate. It
does not capture the effective guest PAT/MTRR state, KVM memory attributes or host
RAM type. The live effective memory type remains UNKNOWN.

L-type1:1437-1439 requests IOMMU_CACHE. That request is not universal proof that
non-snooping transactions are blocked. L-type1:2270-2279 conditionally enables
that domain feature when the IOMMU supports it. L-type1:2623-2638,2665-2668 reports
VFIO_DMA_CC_IOMMU for the domains. No result of that query was captured for this
QEMU container. Do not turn IOMMU_CACHE in source into a live coherency claim.

The pinned Haiku headers/private/kernel/arch/x86/64/atomic.h:10-27 implement
read/write/full barriers with lfence/sfence/mfence and compiler memory clobbers.
These are ordering primitives. They do not prove a mapping, flush a GPU cache,
confirm a DMA transfer or establish host/device coherency by themselves.
Do not add wbinvd, clflush or an invented cache operation as a substitute.

A future publication operation must establish effective CPU memory type, the
host domain's snoop/coherency behavior and the device transaction/cache target.
It must then specify CPU-store ordering before device notification and device
completion ordering before CPU reads. Streaming/noncoherent ownership transitions
need actual supported sync operations, not a fence-only implementation. None is
provided here. GPU cache handling, CPU ordering and bus/MMIO posting are separate.

BAR flush is also separate. The selected source writes 0x070000 and polls bit 1
clear with a 2000 ms bound (reference/nouveau/nvkm/subdev/bar/g84.c:29-40).
That status is not a self-checking payload observation. The consulted source does
not define a host-page byte result which could verify a round trip. Treat the
flush-page transaction's data-level effects as UNKNOWN. Do not invent a sentinel
that the device is expected to change.

## Bounded provider interface proposal

This is a design contract, not a new API implementation or permission token.
The existing DmaProvider remains unchanged and no native instance is installed.
Its bool verified field is insufficient as a production evidence handoff by itself.
A future implementation must validate evidence inside a resident owner.

| Operation | Required inputs/output and failure rule |
|---|---|
| Attest mapping | Exclusive owner lease; guest/launch and device identities; GPA extent; alignment, direction and role. Return a resident nonzero mapping token and separately typed IOVA only after complete coverage/permissions are validated. Partial ownership must return a retention token on failure. |
| Bind evidence | Bind token to host mapping generation, VM/RAM/device configuration, memory-type/coherency profile and physical validation scope. A caller-supplied JSON document, hash, Boolean or plausible address does not authenticate a current host mapping. A trusted host/guest handoff remains to be designed. |
| Publish for device | Validate token, CPU subextent, role, ownership direction and current evidence generation. Apply the supported visibility protocol before granting a device reference. Deny unknown profiles. |
| Observe from device | Require bounded device completion and the matching visibility protocol before exposing returned data. A CPU readback of its own stores is insufficient. |
| Retire | Require source-backed removal of device references and independent quiescence. Keep host mapping/backing until removal completes. Preserve original errors and quarantine on any uncertainty. No forced release, reset or retry. |

Every operation needs a deadline, stalled-clock/poll bound and serialized state.
Providers, evidence and cleanup tokens must outlive driver detach and quarantine.
The immutable owner latch still gates physical startup. Simulation completion is
not a physical startup state or a provider proof. ABI v1 gets no new operation
from this proposal.

## Smallest separate verification design

There is no justified self-checking pre-POST payload test in the consulted source.
The smallest useful first stage is therefore D0 mapping observation. It can narrow
the address contract without pretending to close payload visibility. D1 is a
separate conditional physical transaction experiment. Neither stage is implemented. ADR 008 now records the user's hardware approval
for planned S1 stages once concrete implementations and prerequisites are ready.
Neither belongs in the closed B5 identity launcher.

### D0: observe the host mapping for one owned guest page

Use a new reviewed fixed stage/launcher. Permit only 0000:04:00.0 and repeat the
existing VFIO binding, one-device group and access checks. Ask before stopping an
existing guest. Keep one guest, disposable overlay, incremental evidence and the
independent 600 s watchdog. Freeze RAM topology, migration and device assignment.
Record exact executable/package/source hashes, kernel identity, launch instance
and realized device/DMA address-space topology. Do not assume historical B5's
configuration is a current mapping attestation.

Capture host IOMMU/VFIO error baselines before and after the run, plus the guest
identity and PCI command reads. New faults stop the stage. Missing required host
logs close the gate. Do not read unsourced GPU fault registers or clear any status.

A native client of the permanent owner allocates and zeros one 4 KiB-aligned logical page
below 4 GiB, reports its full guest physical extent and opaque token, and performs
only CPU pattern/readback tests. It does not publish, enable bus mastering or
program any GPU address. Existing identity reads may remain the only GPU reads.
The allocator may reserve more backing than the logical page. Retain the entire
area/token. QEMU maps ordinary guest RAM sections, not just that allocation. The
proposal bounds the driver operations but does not limit device DMA reachability
to the test page. Record the actual mapped intervals and permissions in the stage
review. The native ABI currently lacks the evidence handoff, so that needs separate review.

Launch the exact QEMU binary as an owned child under a bounded host observer of
VFIO ioctls. strace is installed and is a candidate observer, not a validated stage
tool. Capture successful SET_IOMMU and MAP_DMA calls, their complete arguments and
return values, then relevant UNMAP_DMA calls through guest termination. Handle
interrupted/restarted/incomplete records explicitly. Distinguish containers and
track full interval lifetimes. The syscall observer needs no host root or live
/dev/mem/BAR inspection. Required fault logs are a separate input.
Do not attach to unrelated processes or reuse another guest's container.

Q-trace:102 and Q-common:1078 emit the RAM event before the mapping ioctl at
Q-common:1095. That event is not success evidence. MAP_DMA itself can internally
retry EBUSY after an unmap (Q-common:513-516). The observer must capture actual
ioctl returns and lifetime transitions. It must not invent success from one event.
Stop without a modified retry if the launcher reports a failure.

Accept only the reviewed Type1/Type1v2 backend. Reject no-IOMMU mode and all
unsupported backends. Success requires exactly one approved assignment and complete successful READ/WRITE
mapping coverage of the owned guest extent in the correct container/address space,
with no invalidation before inspection. A hole, permission mismatch, unknown
backend, missing event, unmatched unmap or topology change fails. No negative DMA
probe is allowed. CPU readback and successful maps establish no physical payload
visibility. Keep publication denied. This stage could supply runtime address-map
evidence, not HARDWARE_VERIFIED transfer or cache coherency.

### D1: conditional flush-target experiment

Only after D0 evidence and a reviewed memory-type/coherency contract exist, prepare
a separate first-write experiment. Its candidate effects are programming the owned
flush target at 0x100c10 and requesting/polling the selected BAR flush protocol.
The exact preinit requirements, read/write allow-list and complete raw fault
baseline must be closed before a runnable package exists. Do not assume that a
naked BAR flush is safe before the selected preinit sequence. If prerequisites
require more writes, revise the stage scope explicitly before asking permission.

Use a zeroed, owned, pinned page with a source-validated IOVA. Retain it across
all references and failures. Bound polls by both count and monotonic time within
the guest deadline. Preserve guest fault/status baselines and host IOMMU/VFIO fault
logs before and after the run. Any unavailable required baseline closes the gate.
Do not clear faults to obtain a passing baseline or probe an unmapped address.

Readback of the encoded target, BAR completion and unchanged fault baselines would
only establish those observations for that run. Absence of faults is not a payload
proof. Since no defined host-byte response is known, this experiment alone cannot
mark bidirectional payload visibility verified. A separately sourced engine/test
protocol with known data semantics is still needed before a general provider or
broader DMA claim. Do not make POST depend on an unsupported circular proof.

On failure or uncertain quiescence retain the page and evidence. Do not restore an
unknown old target, free while a target may refer to it, manually reset, or retry.
Normal guest termination must follow the reviewed VFIO mapping/backing teardown
order. It is not a new proof of hardware quiescence by itself.

The user approved planned S1 hardware work under ADR 008 after this source audit.
That approval covers D0 and necessary first-write stages once their implementation,
exact register scope, review and prerequisites are ready. Do not repeat the general
approval request. It does not authorize guessing missing protocols or bypassing
review/stop rules. This document remains a design, not a runnable package.
There is no current need for a root-readable fact to
complete this source audit. Future physical baseline collection may need a user
step, which must then name the exact read-only command in docs/REQUESTS.md.

## Reproduce the evidence inventory

Run python3 tools/dma_contract.py --check for repository/source-pin metadata.
This compares exact JSON text without network access or writes. To additionally
verify all fetched files, use --check --verify-external --external-root DIR.
Pins alone do not verify an external cache or a live mapping. make check runs the
repository-only comparison. The output always denies production eligibility.

For the additional sources, download each URL in evidence.json to its recorded
relative path under DIR. The five qemu-ubuntu/* entries are reconstructed instead:
place the DSC and its two archives in DIR, verify the recorded hashes and sizes,
and run dpkg-source --no-check -x DIR/qemu-ubuntu.dsc DIR/qemu-ubuntu. Validate the
patched file hashes with --verify-external afterward. Do not modify reference/.

Q7 remains OPEN. Address identity is a conditional source inference, not a verified
mapping. Effective coherency, trusted evidence handoff, physical payload semantics,
quiescence and provider publication remain explicit gates.
