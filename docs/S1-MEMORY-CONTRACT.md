# First-batch native BAR1 memory contract

S1MEMCONTRACT, 2026-10-29. SOURCE_ONLY candidate protocol, not hardware proof.
Claude accepted the plan with BAR1/gk104 only, no separate G2/D1 experiment,
observational G1 flush readback, and run7 A7 source bytes preserved.
No card run is authorized. The final implemented package still needs review/yes.

## Frozen A7 and composition

`tools/memstage/contract.py --check` compares A7 phase sources against the suite
embedded in run7's launch.json. `work/S1MEMCONTRACT/a7-freeze.json` defines that
set: A7/devinit/armed-reference/native-memory/prestart/bootstrap implementations,
original A7 client, installer and stream helper. Do not modify them for this batch.
New package keys/nonces/configuration are not changes to the A7 implementation.
The combined artifact must compile/use these exact sources, not a rewritten POST.

Reuse the original KEEP_LOADED A7 module and public ABI v2 without exporting a
new raw BAR pointer or resetting its startup latch. It remains the one PCI
reservation holder. New resident memory code may obtain and retain a reference
to that module, and create its own strictly scoped CPU mappings; it must not
reserve the card again or borrow A7's inactive execution permit.

Keep the original A7 client/job source intact as a child phase. A combined host
orchestrator controls one guest and phase-scoped HTTP services. After the original
one-open A7 child passes, a separate one-open memory client may start. This means
one open per phase, not a second startup or a second card launch. New orchestration
and the new module/API are part of the final review. They cannot change A7's grant,
ROM, allowed operations or runtime decisions. The final installer/guest job must
be rehearsed exactly, with fresh keys and no card/grants in its cardless mode.

The A7 API does not expose a general state-query or raw memory service. Therefore
the trusted host phase broker attests completion after checking the full original
A7 PASS/evidence order, current guest/kernel/artifacts, fresh mapping witness and
R5. The memory grant binds that same launch, A7 request/witness digest and the
new memory-module challenge/nonce. A client string/Boolean claiming A7 success
is never sufficient. Each phase has its own role-bound signing key/nonce; no
consumed A7 grant is reused. All belong to one reviewed immutable combined plan.

## Roles and evidence

| Object | Domain/role | Permitted claim |
|---|---|---|
| Original A7 zeroed flush page | Retained native host reference, same-run structural witness | Arm-only; no payload publication/coherency |
| Memory-stage allocations | Owned physical VRAM tokens with owner/boot generation and role | Software ownership within the selected normal heap |
| BAR0 CPU mapping | Guest PCI MMIO, physical-window bootstrap | Explicit uncached API request; bounded IO, not GPU-VA translation |
| BAR1 CPU mapping | Guest PCI resource 1, read-only test prefix | Explicit uncached API request; exact prefix/context scope |
| Instance, PGD, SPT | Owned VRAM, gk104 17/12 format | Retained candidate translation structures, not production Buffer visibility |
| Positive BAR1 witness | Same context/pages/generation and reviewed protocol | BAR1 data/mapping-update observations only |

Do not convert these to a verified general DmaProvider, host Buffer publication,
channel GPU-VA or PBDMA-fetch proof. Q7 remains open. No device is expected to
change a host-page sentinel. Q11 stays open. The original G1 read of 0x100c10
is recorded only as an observation; there is no separate D1 gate or echo test.
New memory-stage policy excludes writes to the flush-target register.

## Ownership and geometry

KNOWN / SOURCE_ONLY: GK110B selects nv50 instmem, gk104 MMU and gf100 BAR
(device/base.c:1770-1785). The normal non-mixed heap excludes the first 256 KiB
and final 1 MiB (fb/ramgf100.c:497-498,555-558). Reject mixed/unknown partition
layouts, inconsistent discovered size or sizes outside the approved profile.
The arena also excludes A7's owned scratch page. Addresses are derived at runtime,
never copied from the Linux capture. Allocation tokens are not addresses.

Reserve two zeroed, retained 128 KiB/4 KiB-aligned MMU debug objects before other
allocations: fb/gf100.c:44-64, fb/gk110.c:55-65. These are INST allocations;
core/memory.c:150-163 dispatches to instmem, instmem/nv50.c:377-390 allocates
through nvkm_ram_get, and fb/ram.c:79-82 identifies VRAM. Thus they belong in the
VRAM ledger, not extra host-DMA targets. GK110's selected gf100 init does not
program GM200's debug registers. No such register writes are added. This preserves
the selected allocation obligation without claiming their necessity is verified.

Selected geometry: gk104 128 KiB big-page mode, only 4 KiB small-page mappings
(vmmgk104.c:39-51,65-78; fb/gk110.c:64). PGD 64 KiB, SPT 256 KiB, instance
4 KiB, all at least 4 KiB-aligned. Allocate no LPT; the absent large-table half
of the PDE stays invalid. Serialize entries explicitly in bounded kernel code.
Do not use the host STL/exception AddressSpace class in the kernel.

BAR1 VMM range is bounded by its discovered aperture and the supported GPU-VA
geometry. Only the first two 4 KiB virtual pages are mapped to distinct owned
VRAM data pages. All other PDE/PTE entries remain absent. The CPU BAR1 mapping
exposes only this 8 KiB test prefix, with kernel read permission and no writes.
BAR1 is PCI resource 1; its upper address word may occupy PCI slot 2. That slot
is not the NVIDIA BAR2 aperture (PCI resource 3). BAR2/0x1714 are excluded.

## Mapping and ordering profile

Use explicit `B_UNCACHED_MEMORY` in map_physical_memory's flags for new BAR0/BAR1
mappings, not a silent default or WC alternative. Haiku's pinned vm.cpp:1987-2001
makes the default UC request weak, while an explicit type is passed without
an override pointer; a failed mapping/type request stops. KernelExport.h:118,198
provides the public flag/API. The exact full running-kernel source identity is
unestablished; the linked/running kernel hash remains a mandatory package input.
Record requested type, flags, region identity, bounds and returned mapping status.
Do not label requested UC as independently measured effective PAT/MTRR/coherency.

This is a SOURCE_ONLY candidate MMIO/VRAM protocol, tested only inside the
reviewed finite experiment. It is not the unresolved cached host-RAM DMA profile.
The scoped device witness comes after the experiment, not from a caller-provided
verification flag. Mapping errors, unsupported resource types and unknown required
ordering stop before consuming structures. No clflush/wbinvd workaround is added.

Before device notification, use the x86 CPU store ordering primitive separately
from the GPU BAR flush (Haiku arch/x86/64/atomic.h:17-26). After writes through
the locked physical slow window, request/poll the sourced BAR flush, then verify
staged words. Physical-window mechanics: instmem/nv50.c:57-93; BAR flush:
bar/g84.c:29-39. Neither operation is a general payload proof.

## Ordered BAR1 experiment

1. Read safe pre-write fault state using a new read-only preflight component,
   without changing the A7 child. Its source-defined valid-at-reset subset is
   separate from the complete post-A7 memory fault snapshot. No clears to pass.
2. Run the original fresh A7 child once, with its signed current mapping witness.
   Host broker must validate its pass before signing the memory phase.
3. The new memory phase rejects an already-enabled BAR1 context. Map/register
   bounded CPU views with explicit UC, validate normal-heap ownership and take
   complete relevant fault snapshots before new writes. Unknown baseline stops.
4. Allocate/zero/retain ledger objects and test the two physical data pages using
   address-dependent patterns and complements, write-all before read-all. No
   foreign/unmapped-address negative control, no live free, no A7 scratch overlap.
5. Stage and read back zeroed PGD/SPT/instance bytes through the physical window.
   PDE/SPTE/instance fields follow vmmgf100.c:105-143,314-319,342-360. Data PTEs
   use VRAM, kind 0, no compression/volatility, and read-only access for BAR1.
6. Set/verify the selected page mode by the source-preserving RMW at 0x100c80
   (fb/gf100.c:66-77). Serialize targeted invalidation under the stage MMU lock:
   check free slots, select this PDB in VRAM, request PAGE_ALL|HUB_ONLY, and wait
   for the sourced queued condition (vmmgf100.c:180-233). Never use ALL_PDB.
7. Enable only BAR1 using the owned instance address at 0x1704
   (bar/gf100.c:52-58); perform its sourced two-flush wait (gf100.c:38-44).
   BAR1 uses gk104 MMU/VMM, the format the future channel VMM reuses. No BAR2.
8. Read both mapped pages through the read-only BAR1 prefix and compare with their
   known physical patterns. Remap VA0 from page A to page B, stage/flush/invalidate
   using the same protocol, and verify B through VA0 while VA1 still sees B.
   Restore VA0->A with the same protocol and verify A/B again. Never unmap a
   live address as a test. This witnesses this BAR1 context, not channel fetch.
9. On success, disable the known owned BAR1 context using the sourced enable-bit
   removal (gf100.c:46-49), record the raw state/final faults, and retain all
   allocations/mappings until reviewed guest/VFIO termination. No live reuse or
   claim of general hardware quiescence. If context ownership/write outcome is
   uncertain, stop writes and retain; do not restore an unknown prior pointer.

The source uses 2000 ms flush/invalidation polls. Add count bounds of 100000 and
monotonic-clock checks as software policy. Proposed memory work budget is 30 s
with bounded bulk operations (5 s each); the unchanged A7 10/15 s budgets remain.
All fit under the existing independent 600 s guest deadline, including diagnostic
drain. Bounds and record/workspace capacities must be frozen in the package.

## Fault and authority boundaries

S1MEMFAULTS must implement the catalog before the runnable package: raw MC,
FIFO aggregate/MMU-fault mask and selected privring status relevant to this path.
Read MMU fault details only for pending units, with the sourced fixed-width mask
iteration. No PBDMA-count write probe, interrupt enabling or fault acknowledgement.
A nonzero/unexplained relevant baseline or new selected fault prevents new effects.
A failed read is not a zero baseline. The fault task supplies exact registers and
valid-at-reset/after-POST distinctions with source; nothing is enabled meanwhile.

New authority has distinct request/grant magic, version, random package key,
compiled plan digest/nonce, owner challenge and serialized phase state. It binds
expected BAR resources, arena roles/extents, A7 completion/current-launch witness
and the exact approved memory plan. Layout is generated before implementation;
there is no ABI promise to external applications. Only fixed resident code derives
addresses and allowed write values. Clients supply framed signed bytes/handles,
never callbacks, register ranges, claimed verification or arbitrary GPU pointers.
No public setter can activate a physical permit or advance a phase. Wrong role,
nonce, epoch, owner, plan or phase, and replay after completion/failure are denied.
The old A7 permit remains private, inactive after its unchanged child returns.

Every allocation is retained after any device reference. Failure preserves both
primary and cleanup outcomes and stops further writes (including guessed cleanup).
A guest PASS is provisional until host R5, observer/target exit, kernel hash and
post-exit bus-master observation pass. Termination retention is not provider retire.
No intermediate card run. Final implementation needs Claude review and one yes.
