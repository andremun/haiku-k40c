# Review: batch-1 result and channel/scheduler/NOP design

2026-10-30. Prepared for Claude review. This is a design package.
No batch-2 runtime or launch approval exists.

## Two requested verdicts

1. ACCEPT or REWORK batch-1 result bf67465 within its recorded scope.
2. ACCEPT or REWORK this second-batch design and its six implementation tasks.

The result is [S1-BATCH1-RUN-REVIEW.md](S1-BATCH1-RUN-REVIEW.md).
Reproduce it with `python3 tools/batch1_result.py --check`.
A7 POST/readiness and the finite BAR1 initial/remap/restore path passed under Haiku.
R5 selected logs were unchanged. Host bus mastering was off after exit.
These are KNOWN / HARDWARE_VERIFIED on 04:00.0 within the capture's scope.
They do not establish channel translation, PBDMA fetch or safe live reuse.
The post-POST flush-register readback was zero. Q7 and Q11 remain open.
The consumed marker and raw capture remain unchanged.

## Target and hypothesis

Proposed stage: `S1_CHANNEL_NOP`, a design label with no CLI yet.
One fresh combined launch runs unchanged A7, repeats the memory gates, then tests
one standalone channel on the discovered GR-associated runlist without GR setup.
The hypothesis is that this channel can consume one host NOP and detach cleanly.
GR-independent scheduling is UNKNOWN. Linux's full-stack trace does not prove it.

Use owned VRAM for all command payloads and scheduling structures.
Keep the arm-only host flush page and its fresh structural witness unchanged.
No generic host DMA visibility provider is enabled. Q7 stays open for that provider.
A positive device-consumption observation can establish only this VRAM channel path.
An unsupported mandatory ordering or address contract blocks the runnable package.

S1 PASS requires all of the following in one approved run:

- Fresh A7 and memory prerequisite gates pass under their existing evidence rules.
- The native owner establishes a distinct channel address space and owned resources.
- Empty GP_GET/GP_PUT baselines are recorded before the single notification.
- After one GPFIFO entry and one host NOP, GP_GET advances to the new GP_PUT.
- Payload GET diagnostics and complete selected raw fault snapshots support the result.
- Bounded stop/preempt/remove/unbind and owned mapping closure pass.
- The guest/tracer terminate and the host bus-master check passes.

The channel contract must fix the payload-GET interpretation before implementation.
GP_GET proves entry consumption under the project's S1 criterion, not compute completion.
Do not present a stationary pointer, CPU echo or BAR1 witness as channel progress.
Any missing gate prevents S1 PASS, even if earlier progress is recorded.

## Source facts and implementation consequences

All new hardware mechanics below are KNOWN in pinned source, verification SOURCE_ONLY.
Source paths are relative to reference/nouveau unless otherwise stated.
The v6.12 source differs from the Linux 6.8 capture. Keep that distinction visible.

| Fact / source | Consequence |
|---|---|
| device/base.c:1777-1805 selects GK110 FIFO and GK104 MMU for GK110B | Follow the inherited function tables, not a newer-chip recipe. |
| fifo/gk110.c:35-58,107-128 selects GK104 RAMFC/USERD and conditional group preempt | Choose a software-only group; do not emit a hardware group record. |
| fifo/gk104.c:40-79 accesses channel registers starting at 0x800000 | The current 8 MiB BAR0 view is insufficient. Validate a new bounded view against PCI resources. |
| fifo/gk104.c:82-118 encodes RAMFC, physical USERD and 0x200-byte channel stride | Keep physical USERD, channel GPU VA and BAR VA distinct. Encode every RAMFC field from owned metadata. |
| fifo/base.c:306-320; gk104.c:801-805 allocates USERD for every channel ID and maps it in BAR1 | Default to source-sized storage: 4096 slots times 0x200 bytes. Do not shrink backing silently. |
| fifo/gk104.c:745-749 writes BAR1 USERD base to 0x2254 | The BAR1 context must be active for USERD. The batch-1 mapper ends disabled. |
| mmu/vmmgf100.c:337-367 joins a physical PDB and VA limit into the instance | A separate channel PDB/SPT/instance is required. BAR1 test tables do not prove channel translation. |
| mmu/vmmgf100.c:188-233 selects PDB and adds HUB_ONLY only for a BAR reference | Channel invalidation must not reuse the BAR-only invalidate type blindly. |
| fifo/gf100.c:927-936 discovers PBDMA enables by writing all ones, reading and restoring | Discovery belongs to the write inventory. Validate density and routing, never assume mask 7. |
| fifo/gk104.c:389-393,756-800 associates PBDMAs and TOP runlists | Derive the selected runlist and queue association from current topology. Never assume runlist 0. |
| nouveau_chan.c:302-307 sets devm to BIT(0), independently of runlist/runq | Source the RAMFC device mask separately. It is not the TOP engine or PBDMA mask. |
| fifo/gf100.c:351-359; gk104.c:379-386,735-753 initializes queues and enables interrupts | Specify a polling-only interrupt deviation. Do not copy INTREN or write-all status clears. |
| fifo/gk104.c:410-457 uses BIT(runlist), address/count commit and channel-only entries | Preserve unrelated runlist-block bits. Retain active and empty list backing. |
| nouveau_dma.c:74-94 orders entry writes before GP_PUT; :100-119 reads GP_GET | Use separate publication and single-notification phases. No doorbell is added for this chip. |
| nouveau_chan.c:447-450; nouveau_dma.c:41-69 records payload GET low/high | Distinguish GP_GET 0x88 from payload GET 0x44/0x60. Log stable samples with explicit semantics. |
| open-gpu-doc/classes/host/cla16f.h:42-75,150-165,196-201 defines class, USERD, NOP and packet fields | Host method 0x08 uses the existing two-word packet 0x20010002, 0. GPFIFO length is separate. |
| fifo/chan.c:135-192; gf100.c:42-46,370-373 defines standalone preempt/removal | Complete bounded removal before unbind. A preempt request alone is insufficient. |
| fifo/gk104.c:190-267,288-294 reports engine/context and queue state | Retain raw status. Recovery-only idle checks do not establish generic quiescence. |
| fifo/runl.c:86-100 places the queue-idle loop in a conditional recovery path | A new finite teardown contract needs review. Do not claim source proves arbitrary safe freeing. |

## Resource, ownership and mapping contract

Keep A7's one reservation, permanent owner and startup-once latch.
Extend the resident memory owner for channel work under a distinct signed authority.
Use its same append-only arena and locks. A second arena could overlap live objects.
No client supplies a raw register writer, address, callback or proof Boolean.
Do not turn the old memory permit into permission for scheduler writes.

The completed batch-1 test disables BAR1 and retains its objects.
A new owner-controlled phase must validate that closure, prepare USERD mappings,
invalidate and explicitly re-enable the owned BAR1 context before FIFO setup.
Do not change the old witness into a context-left-enabled result.
Reuse retained BAR table backing only through a checked owner transition.
Changes to memory code and this transition receive the final implementation review.
A7 phase implementation bytes remain frozen to run7. Key/nonce changes remain allowed.

Required ledger roles include existing debug/test/BAR objects, channel directory,
small-page table, instance/RAMFC, full USERD backing, GPFIFO, pushbuffer,
active runlist and empty runlist. Record physical placement, CPU view, channel VA,
BAR VA, extent/alignment, owner/epoch, write generation and every active reference.
Check arena capacity before any write. Never borrow batch-1 DataA/DataB as commands.

Channel VA must differ from physical placement and BAR VA by construction.
Map only reviewed payload extents into the channel VMM. Keep all unmapped entries
initialized with the selected format. Guard alignment, extent, width and overlaps.
Use the existing gk104 format, 128 KiB page mode and 4 KiB SPT pages.
A CPU BAR mapping cannot substitute for channel-PDB attachment.

Discover PCI BAR resources again. Add only the BAR0 pages needed for the selected
channel registers. Any selected channel ID needs inactive/unbound baseline evidence.
BAR1 gains a bounded explicitly UC writable USERD view for GP_PUT, with polling reads.
This differs from batch 1's read-only 8 KiB CPU view and must appear in the inventory.
Map source-sized USERD storage into BAR1, while limiting CPU access to the selected slot.
BAR2 remains excluded. Effective UC/PAT/MTRR behavior remains unmeasured.
CPU ordering, GPU BAR flush, readback and channel-PDB invalidation stay separate.

## Six implementation tasks

| Order | Task | Output |
|---|---|---|
| 1 | [S1CHANCONTRACT](tasks/S1CHANCONTRACT.md) | Source/trace decisions, interrupt policy, address roles, authority, progress and closure predicates |
| 2 | [S1CHANMEM](tasks/S1CHANMEM.md) | Owned role extensions, channel table/RAMFC images, source-sized USERD and BAR1 handoff |
| 3 | [S1CHANSCHED](tasks/S1CHANSCHED.md) | Bounded discovery, polling-only FIFO/PBDMA setup and standalone channel/runlist controls |
| 4 | [S1CHANCLOSE](tasks/S1CHANCLOSE.md) | Stop/preempt/remove/unbind, fault capture and conservative retention controller |
| 5 | [S1CHANSUBMIT](tasks/S1CHANSUBMIT.md) | Exact NOP, single PUT, bounded progress checks and native one-shot composition |
| 6 | [S1CHANPACKAGE](tasks/S1CHANPACKAGE.md) | Immutable combined package, exact cardless rehearsal, evidence validator and review inventory |

One task per commit on main, make check before each commit, no push.
No intermediate card experiment. Build teardown before enabling native submission.
Host source work can proceed as authorized. Mandatory unresolved gates block native execution.
The final implementation/package requires a new Claude verdict and explicit one-run user yes.

## Proposed single-run gates

| Gate | Condition |
|---|---|
| G0 | Exact artifacts/kernel/ROM, exclusive fixed card, one guest, live R5/observer, reset-valid fault baseline |
| G1 | Frozen fresh A7 and fresh structural witness pass; 0x100c10 readback remains observation only |
| G2 | Repeat physical/BAR1 memory witnesses and owned disable with retained ledger; current broker attestation |
| G3 | Distinct scheduler grant, complete contract/layout validation, safe BAR0 expansion and USERD/BAR1 handoff |
| G4 | PBDMA discovery, TOP-derived routing, clean raw faults and polling-only setup, all before channel start |
| G5 | Fully staged/read-back channel PDB/SPT/RAMFC, USERD, ring, packet and runlists; empty pointer baseline |
| G6 | Bind/start and commit the owned channel list; one GP_PUT update only; bounded GP_GET advance and payload diagnostics |
| G7 | Stop/preempt/remove/wait, queue/engine observations, unbind, owned PDB/BAR closure and final faults |
| G8 | Retention recorded, owned guest/tracer exit, R5 delta and bus-master check; combined verdict |

Contract work must fix bind/start/commit ordering from the selected lifecycle,
including its locks, rather than treat the gate table as a register replay.
Use software host deadlines and independent poll limits even if a clock stalls.
The immutable package must budget boot, A7, memory, every bounded queue/flush wait,
USERD initialization, buffered output and closure within the existing 600 seconds.
No deadline increase, partial evidence fallback or automatic retry is planned.

## Interrupts, faults and closure

Keep host-facing interrupts masked. Derive and test exact INTREN zero writes,
readback and ownership from source. Record every omitted Linux initialization write.
A7 masks do not establish all PBDMA/FIFO leaf masks. Check them explicitly.
Capture raw MC/FIFO/MMU/private-ring, selected PBDMA/HCE and engine/runlist/channel
state before and after each consequential phase. Masked status is insufficient.
Unexpected nonzero baseline, a new fault, missing coverage or journal overflow stops.
Preserve status before any reviewed acknowledgement. Never clear a fault to get PASS.
No interrupt service handler, recovery engine reset or generic fault-clear helper is added.

Block further PUT, stop the channel, preempt its software-only group member,
publish/wait an owned empty runlist, observe source-backed queue/engine state,
and unbind before detaching the channel PDB and closing the owned BAR1 mapping.
The contract must settle ordering and precise predicates before native implementation.
Idle IDs can contain stale numbers. Do not demand arbitrary zero values or ignore busy references.
Preserve primary and cleanup failures independently. Continue only reviewed safe cleanup.
An unexplained state or timeout fails closure and quarantines all possible references.

Retain allocations and mappings until guest/VFIO termination on success and failure.
Distinguish observed scheduler detach from generic DMA quiescence and safe live reuse.
The old S1Experiment release Boolean cannot be set merely because memory was retained.
Use an explicit finite closure result instead, with reviewed guest-end retention semantics.
No successful S1 label follows GET progress if scheduler detach or host closure fails.
The review must accept this finite teardown scope before the final package is offered.

## Exclusions and review package requirements

No GR/CE initialization, object binding, shaders, Falcon firmware, compute,
semaphores, host command payload DMA, BAR2, power/fan changes or arbitrary probes.
No inherited all-engines enable or interrupt enable from the old FIFO design.
No root, other card, manual reset, binding change, Linux --gpu or consumed-package reuse.
D1 is not reintroduced. Q11 echo is not a gate. Unknown GR-free behavior remains the experiment.

Final review must include exact commands and all artifact hashes, complete driver
and inherited A7 writes, BAR CPU mappings, resource ledger, address expressions,
per-phase authority, interrupt deviations, omission reasons, time/poll budgets,
raw fault criteria, closure and evidence claims. Every operation needs a pinned source.
Rehearse the identical complete guest job/binaries cardless before offering the package.
No-card refusal must occur before any grant. Verify final-name loads and real open status.
Preserve replay/one-shot/retention behavior on repeated loads.
One future approval covers one whole combined launch. ADR 006 applies after any stop.

## Current boundaries and reproduction

The plan does not establish S1 success or prepare S2/S3 as successful milestones.
On actual S1 success, record its finite evidence first, then prepare S2 and S3 separately.
Reproduce the plan binding with `python3 tools/batch2_review.py --check`.
The generated review-inputs records source spans, exact inputs, task dependencies
and the batch-1 capture hashes. No VM or card is accessed by that command.
