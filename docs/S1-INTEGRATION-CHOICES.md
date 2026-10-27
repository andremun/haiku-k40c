# S1 integration choices (host design, 2026-10-27)

These are SOURCE_ONLY candidate choices for GK110B. They resolve software design
questions; they do not verify the card, authorize writes, or implement a native
submission path. The v6.12 source pin differs from the Linux 6.8 capture.
All source paths below are relative to `reference/nouveau/`.

## Memory and page mode

The selected device table uses `gk104_mmu_new` and `gf100_bar_new`
(`nvkm/engine/device/base.c:1770-1805`). Use GK104's 128 KiB big-page mode,
with 4 KiB small-page mappings for S1 buffers. GK110 FB defaults to page shift 17
(`nvkm/subdev/fb/gk110.c:55-65`); VMM dispatch chooses geometry from that FB
setting (`nvkm/subdev/mmu/vmmgf100.c:401-416`). Program and verify the matching
FB mode before translation: shift 17 clears bit 0 of 0x100c80
(`nvkm/subdev/fb/gf100.c:66-77`). A model setting alone is insufficient.
Do not mix the alternate 64 KiB-mode directory geometry with the existing model.

For mode 17 the SPT has 32768 eight-byte entries, LPT 1024, and PGD 8192;
one PDE spans 128 MiB (`nvkm/subdev/mmu/vmmgk104.c:39-51`). The existing
PageTable encoder models this 40-bit GPU VA geometry. Initially use only 4 KiB
pages, uncompressed kind 0, no overlapping large mappings. Initialize absent
SPTEs and PDEs, and preserve the selected invalid-LPTE semantics
(`vmmgk104.c:25-36`). Host encoder round trips are not GPU translation evidence.

Choose owned VRAM for page directories/tables, channel instances, GPFIFO,
pushbuffer and runlist storage. Bootstrap through the locked physical slow
window, then publish and read back every referenced structure. Use BAR1 for
USERD as selected by `nvkm/engine/fifo/gk104.c:114-119,745-749`; its physical
allocation and BAR virtual address are different fields. This choice reduces
S1 host DMA targets but still needs the pre-POST host flush page.

Reserve a bounded arena only after VRAM ownership is established independently.
Do not pick a physical address from the trace or assume firmware-reserved memory
is free. Each resource ledger entry must record owner, placement, CPU view,
GPA, device IOVA, physical VRAM, GPU VA, BAR VA, extent, alignment, publication,
and pin state as applicable. Missing address-domain proof stops setup.

Preserve the two FB MMU debug allocations selected by GK110's oneinit: by default
128 KiB each with at least 4 KiB alignment (`nvkm/subdev/fb/gf100.c:44-64`;
`gk110.c:55-65`). No evidence establishes that they are GR-only or safe to omit.
Keep them separate from the host flush page. The selected source does not supply
GM200's debug-buffer register programming; do not import a newer-chip sequence.
Their physical necessity on this minimal path remains UNKNOWN.

## BAR and invalidation

Use distinct owned BAR contexts, with VMM ranges bounded by discovered aperture
sizes. BAR2 bootstrap precedes fast instance access; do not recursively depend on
that fast path to construct its own tables (`nvkm/subdev/bar/gf100.c:80-146`).
BAR1 context enable is 0x001704, BAR2 is 0x001714; both encode physical instance
address >>12 with enable bit, not a GPU VA (`gf100.c:46-77`). No aperture size or
captured context pointer is a constant for Haiku.

After writing/publishing tables and instance bytes, request a BAR flush and
check it with a bounded host deadline and poll count. The source uses
`nvkm_msec(..., 2000, ...)`, a 2000 ms bound, not 2 ms
(`nvkm/subdev/bar/g84.c:29-40`). A shorter test timeout is a software policy,
not the source value. BAR context waits call this flush twice
(`bar/gf100.c:38-44`). CPU ordering, BAR completion and TLB invalidation are
separate obligations.

Serialize the complete invalidation transaction with a global MMU lock
(`nvkm/subdev/mmu/vmmgf100.c:181-234`):

1. Check free slots at 0x100c80 mask 0x00ff0000 with deadline/poll limits.
2. For this owned PDB, encode (physical PDB >>12)<<4 plus target (VRAM=0,
   HOST=2, NCOH=3), and write 0x100cb8. Reject overflow or misalignment first.
3. Request PAGE_ALL with 0x80000001 at 0x100cbc. BAR contexts additionally
   use HUB_ONLY (type bit 2), as selected by engref[BAR]. Do not use ALL_PDB
   to avoid specifying the owned context.
4. Wait for 0x100c80 bit 0x00008000. Failure at any point prevents channel
   binding and retains potentially referenced storage.

The source describes the last status as possibly queued. Treat it as that
protocol's completion condition, not independent proof of translation or DMA
quiescence. Physical publication/translation tests must still establish that a
mapping and its invalidation took effect. No native invalidator is supplied here.

## Routing and channel choice

Choose one standalone channel with a software-only group (`hw=false`), no
hardware group entry, and no GR context. This matches the optional group path
in `nvkm/engine/fifo/chan.c:386-405` with GK110's non-forced group table;
`cgrp.c:222-235` records the mode. Runlist emission includes a group record only
for hardware groups (`nv50.c:285-318`). Therefore the candidate uses channel-ID
preemption (`gk110.c:36-46`, `gf100.c:42-46`). If the mode changes, both runlist
encoding and preemption must change; never infer mode from having one channel.

Discover TOP after POST with the selected GK104 parser. It reads 64 bounded
entries at 0x022700; DATA/ENUM/ENGINE_TYPE and continuation bits establish engine,
runlist and fault association (`nvkm/subdev/top/gk104.c:31-117`). Reject incomplete,
unknown or conflicting routing instead of assigning runlist 0 by convention.
For S1 select the discovered GR-associated runlist as the scheduling candidate,
without initializing GR. The normal constructor adds the software engine there
(`nvkm/engine/fifo/gk104.c:756-800`). This does not prove that GR can be omitted.

Discover the PBDMA association through 0x002390 + index*4 masks
(`gk104.c:389-393,764-775`). The source discovers PBDMA count by write-all/readback
and restoring 0x000204 (`gf100.c:927-936`): it is a write-stage operation, not a
read-only B5 survey. Reject sparse/unsupported masks rather than assuming that a
popcount proves dense indices. Validate runlist ID, engine IDs, runq membership,
RAMFC device mask and channel ID together before publication. Exact live values
are UNKNOWN. Preserve unrelated enable bits; no discovery write is authorized here.

Do not reuse normal FIFO/PBDMA init wholesale: it enables interrupts
(`gk104.c:379-386,745-752`). Polling needs an explicit reviewed interrupt policy,
complete raw fault snapshots, and a write allow-list. Masked interrupts do not
mean faults are absent. GR-independent scheduling remains an experiment, not a
consequence of selecting the host NOP method.

## Teardown and release proof

A successful GET transition alone is insufficient. Keep all referenced resources
pinned until a bounded teardown succeeds:

1. Prevent new PUT and scheduling; stop the channel using the selected hook
   (`nvkm/engine/fifo/gk104.c:40-46`). Preserve initial faults before clearing any.
2. Under the runlist lock, preempt the chosen standalone channel and wait until
   0x002634 bit 0x00100000 clears (`gf100.c:370-373`; `chan.c:135-158`).
3. Remove the channel, publish an owned list without it, and wait for runlist
   pending to clear (`chan.c:162-192`; `gk104.c:420-447`). Retain both old and new
   lists until references are known to have moved.
4. Check each selected PBDMA idle condition (0x003080 + index*4, mask 0x0000e000;
   `gk104.c:288-294`) and relevant engine busy/context-switch/current IDs
   (`gk104.c:190-267`). Stop if any state is unknown or still refers to the channel.
5. Unbind the channel (`gk104.c:58-63`), detach its PDB, publish/invalidate the
   affected mappings, and take final raw fault snapshots before retiring pins.

These are conservative release obligations, not a proven complete hardware
quiescence predicate. In particular the source's recovery-only idle loop is
conditional on runlist preemption (`runl.c:86-100`); do not claim it proves this
standalone path safe. Any timeout, incomplete snapshot, uncertain write, or stale
reference quarantines every affected allocation. No automatic engine/GPU reset,
forced free, or retry is a recovery policy. User-directed recovery must establish
quiescence before freeing memory. The host flush-page reference must also be
removed safely; if that cannot be proven it survives until the guest is stopped.

## Remaining gates

This task closes source choices for mode, context invalidation, discovered
routing and group semantics. Implementation and card evidence remain open:
verified DMA/visibility, persistent native owner, physical I2C transport,
whole-program preflight, VRAM arena ownership, readiness/fault coverage,
translation tests, scheduling without GR, and complete teardown evidence.
The next host work must close those implementations and preflight coverage;
A7 still needs review and the user's explicit go-ahead. No write-stage run is
ready for approval from these documents alone.

S1DMACONTRACT now records the candidate host DMA address chain and exact additional
source identities in docs/DMA-CONTRACT.md. It leaves live mapping/coherency and
payload visibility open. Neither proposed D0/D1 experiment is a runnable stage.
