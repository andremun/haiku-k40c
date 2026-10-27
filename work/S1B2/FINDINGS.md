# S1B2 findings — 2026-10-27

## Allocation choice

KNOWN / SOURCE_ONLY: Haiku's nvidia driver uses B_32_BIT_CONTIGUOUS
(reference/haiku/src/add-ons/kernel/drivers/graphics/nvidia/driver.c:939-957).
OS.h:77 defines it as contiguous storage below 4 GiB. Use that for prospective DMA storage.
This does not establish a GK110 DMA-width limit or VFIO IOVA identity.
The ordinary B_CONTIGUOUS scratch allocator remains unchanged in purpose.

## Ownership and publication

NativePool is caller-owned and must outlive active/quarantined storage and providers.
The adapter owns the original area while exposing an aligned GPA/CPU subview.
Mapping and visibility require an explicit provider. None is supplied for hardware.
Default publication and device-address queries remain denied.
Partial allocations and mappings retain tokens until cleanup or quarantine recovery.
Cleanup unmaps before freeing. A failed area free can follow a successful unmap.
The generic Buffer previously retained its publication/address state after that failure.
It now blocks every use except close until cleanup succeeds. A regression covers this case.
Pool recreation and stale-token tests preserve ownership and reject aliasing.

## Current checks

Host memory adapter: 146 checks, zero failures.
Generic memory contract: 44 checks, zero failures.
Native C backend: 78 checks, zero failures.
All three probes link against the matching Haiku kernel, including k40_memory_probe.
No card or VM stage has run in this task yet.
No DMA/IOVA verification or GPU-VA mapping is claimed.

The new native memory probe links with the matching kernel; no extra C++ runtime is needed.
The cardless result parser now rejects any failed probe load, even if a later
reload prints PASS. The previous parser checked only for the presence of PASS.
Regression transcripts cover failure followed by PASS, missing PASS, cleanup failure,
and the harmless normal Haiku debugger-output banner.

## Source-backed pre-POST dependency

KNOWN / SOURCE_ONLY: fb/base.c:281-288 allocates and DMA-maps the flush page
in construction. fb/base.c:225-229 programs it in preinit, before scripts.
engine/device/base.c:2908-2916 calls subdevice preinit before nvkm_devinit_post.
This confirms why a CPU/GPA-only allocation cannot close the pre-POST device-address gate.
The new adapter therefore provides no default identity mapper or visibility success.
The A4 dependency research follows the selected GF100 devinit and GK110/GF119 I2C paths.
These are source facts only. No pre-start hardware operation was run.

The final adapter suite passes 146 host checks after pool-capacity tests.
make check and make vm-tools-test both exit 0. The cardless-result parser regression passes.
All three native probes link. Native runtime verification is the next step.
