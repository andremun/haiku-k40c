# C2: ordered S1 integration recipe and remaining gates

2026-10-16. This is a reviewed-input checklist/design, not a register replay
or an approved hardware experiment. SOURCE_ONLY entries below are tied to the
pinned v6.12 source; TRACE_VERIFIED means the named access is also observed in
the Linux capture, whose kernel was 6.8. That mismatch must remain visible.

`analysis/load_trace.json/.md` name load-phase anchors and domain runs. Those
runs are chronology, not causal source attribution for every register access.
Linux initializes the full stack, including GR. It is not a trace of minimal S1.
Captured addresses belong to that run and must never be reused by Haiku.

| Order / integration step | Domain and ownership | Wait / error test | Rollback and gate |
|---|---|---|---|
| 0. Environment/identity | Approved guest, PCI identity/config/BAR resources; map a bounded read-only BAR0 area | Verify identity, width, mapping bounds and stable safe register reads; no arbitrary survey | Unmap and release PCI module. Host reset scope/recovery and hardware permission remain user steps |
| 1. Host flush-page prerequisite | Owned pinned host page with verified device IOVA, distinct from CPU/GPA/GPU VA | Resolve guest IOMMU configuration; ensure address encoding fits; baseline faults before writes | Keep page alive across POST and all hardware references; quarantine on uncertain quiescence. Do not assume Haiku ram_address alone proves VFIO DMA |
| 2. Selected preinit + VBIOS program | MC/bus/private-ring/I2C/GPIO/timer/FB prerequisites and validated ROM tables | Validate complete reachable bytecode/helper set first; bounded waits; each board target needs explicit decision | Fail before first write if preflight/board policy missing. Do not equate script marker with readiness |
| 3. Independent bring-up ladder | Reserved VRAM scratch and physical PRAMIN window, under one global selector/data lock | Stable identity/timer, raw bus/private-ring faults, address-dependent patterns and complements at owned locations; test aliases | No full-VRAM readiness claim. Do not free/restore unknown firmware-owned memory. A7 requires separate review |
| 4. Instance memory/bootstrap | Allocate owned channel/PGD/table/runlist/USERD/pushbuffer storage; physical VRAM via slow window | Upload/read back zeroes and encoded bytes; verify address domain, alignment and extent | Release only unreferenced allocations; retain all possibly referenced storage on any later failure |
| 5. BAR/MMU mapping | Program owned page tables and BAR contexts; select 4 KiB/128 KiB geometry and scratch dependencies | Publish table bytes, BAR flush, context-specific TLB invalidation; validate mappings independently of the host vector model | Mapping failures prevent channel binding. Full scratch/BAR2 recipe and page-size mode remain required integration work |
| 6. FIFO/PBDMA routing | TOP-selected runlist/engine association, discovered PBDMA mask, stage-specific interrupt masking | Validate routing, channel/runlist ownership and relevant raw faults. Keep IRQs masked for a polling-only test | Do not copy in-tree interrupt enabling without a handler. Do not infer GR-independent scheduling from class selection |
| 7. Channel/RAMFC/USERD | Owned instance block, GPU VA and physical references explicitly distinguished | Fill every context-dependent word from owned addresses/masks; publish/read back; bind and enable, checking status | Stop/preempt/remove/unbind before freeing. Remaining opaque words need exact source provenance and rationale |
| 8. Runlist publication | Owned aligned VRAM or NCOH list with reviewed target, runlist ID and entry count | Write runlist address then commit count/ID; bound pending poll and preserve fault snapshots | Failed commit may be active; do not free the list. Existing simulation primitive tests encoding/order only |
| 9. One host NOP | Exact two-word packet, one GPFIFO entry, owned published memory | Empty baseline ring, publish before PUT; observe new GET equal new PUT before deadline with no relevant fault | Failed PUT may have reached hardware. Retain references until teardown is proven |
| 10. Teardown | Channel disable, preempt, list without channel, pending/idle checks, unbind | Check channel/PBDMA/engine-switch state and final raw faults; preserve logs before acknowledging | Only then retire pins/release storage and host flush page. Failed quiescence enters quarantine/recovery, never implicit free |

## Source-backed mechanics and limits

- **Host flush-page programming** (TRACE_VERIFIED access): `0x100c10` receives
  DMA address >>8 (`reference/nouveau/nvkm/subdev/fb/gf100.c:81-84`). Its allocation,
  DMA mapping and lifetime precede POST in the selected lifecycle. Buffer type
  and address provenance must be supplied by B2/B3, not copied from the trace.
- **Slow window** (SOURCE_ONLY mechanics, selector observed in trace): select
  physical VRAM window using `0x001700 = base >>16`, then access
  `0x700000 + low20` under a lock covering selection plus data. See
  `reference/nouveau/nvkm/subdev/instmem/nv50.c:57-96`. This path bootstraps before
  the fast mapping, not before memory bring-up. Window readback is not a GPU-VA
  translation test. Even a slow-window read writes the selector, so it does
  not belong to a read-only hardware stage. SOURCE_ONLY masks cover 44 physical bits; do not confuse
  that aperture format with the current model's 40-bit GPU VA range.
- **BAR flush** (TRACE_VERIFIED access): request at `0x070000`, poll busy bit
  with a host deadline (`reference/nouveau/nvkm/subdev/bar/g84.c:29-40`). This is
  distinct from a C++ compiler/CPU fence and from MMU invalidation. The caller
  must perform the appropriate CPU ordering before requesting it.
- **TLB invalidation** (SOURCE_ONLY): PDB selection/type, free-slot and queue
  status are handled in `reference/nouveau/nvkm/subdev/mmu/vmmgf100.c:181-233`.
  Implement the selected context path with the existing scratch dependency;
  a single guessed write to the invalidate register is not sufficient.
- **Runlist commit** (TRACE_VERIFIED): `0x002270` encodes target/address,
  `0x002274` encodes runlist ID/count; poll `0x002284 + id*8` pending bit.
  See `reference/nouveau/nvkm/engine/fifo/gk104.c:422-447`.
- **Preemption** (SOURCE_ONLY in the load survey; job trace also records it):
  `0x002634` is the channel preempt request, NOT runlist start. See
  `reference/nouveau/nvkm/engine/fifo/gf100.c:43-46` and the verified job sequence
  in `docs/05-fifo-design.md`. The previous S1 plan's statement was corrected.

`src/runtime/Bootstrap.*` implements only slow-window read/write, BAR flush and
runlist commit for host simulation. It validates extents/encoding, locks complete
window transactions, bounds polls even with a stalled clock and unlocks on
failure. Transfers have a software cap of 4096 words per call, not a claimed
hardware limit. Real backend calls must themselves be bounded. Partial writes
can precede failure, so rollback is caller-owned. Hardware backends are refused.

`src/runtime/S1Experiment.*` implements order/failure policy for the final
submission experiment, not the missing hardware initialization steps. Its
success predicate includes fault-free progress and verified cleanup. Neither
primitive is yet integrated into the native Haiku probe.

## Exact decisions still required before hardware implementation

1. Complete whole-program bytecode reachability and BIT-I/M/helper/preinit model;
   the observed 24-opcode inventory is insufficient for changing conditions.
2. Review GPIO/I2C/IO helper effects; identify device 0x20 or keep it denied.
3. Choose and validate host DMA/IOMMU address mapping, scratch/page-table/BAR
   layout and lifetime, MMU page-size mode and invalidation protocol.
4. Resolve TOP/runlist/PBDMA selection and GR omission experimentally, with fault
   diagnosis that distinguishes memory/routing faults from a GR dependency.
5. Define actual preempt/idle/recovery evidence before claiming quiescence.

Until those are closed, the integration recipe remains PARTIAL, with explicit
stops rather than invented register operations. Cardless testing cannot close
reset-state bring-up, DMA, physical VRAM or S1 acceptance.

The scratch-check preparation uses two write-all/read-all passes with distinct
address-derived patterns and their complements. An injected alias between
locations is detected by host tests. This is an A7 test algorithm only; the
actual scratch ownership, MMIO path, faults and memory readiness remain card
evidence that this workspace cannot supply.
