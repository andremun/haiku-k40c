# Review: A7 result and first memory/translation batch plan

2026-10-29. Status: **ACCEPT with changes (Claude Code, 2026-10-29)**.
See work/S1MEMCONTRACT/CLAUDE-REVIEW.md for the supplied review. No batch implementation or run is
claimed. The user requested this plan before implementation. Current state is
in [STATUS](STATUS.md). This file does not extend any hardware authorization.

## Two verdicts requested

1. **A7 result:** ACCEPT or REWORK of the result and its evidence scope.
2. **First-batch design:** ACCEPT or REWORK of the proposed implementation and
   experiment boundaries. Acceptance permits the planned host work, not a card
   launch. The completed implementation/package still needs its batch review
   and one explicit run approval under ADRs 007/008.

Review A7 implementation commits 0b450b1, 210e5ee and b0c24e4, then result commit
dfb7cd8. The test-dispatch correction is in b0c24e4. Review this planning commit
separately. Existing consumed markers and original captures stay unchanged.

## A7 evidence to assess

Use [the original run README](../results/20261029-a7-069cb71b/README.md),
[the generated result](../work/S1A7RUN7/report.json), and
[the task result](../work/S1A7RUN7/RESULT.md). Reproduce its offline validation
with `python3 tools/a7/result_report.py --check`.

KNOWN / HARDWARE_VERIFIED, scoped to this card under Haiku:

- POST and independent readiness passed in the single directly approved run.
- POST took 88,805 us. Deferred diagnostic output took 21,694,572 us outside
  the controller. Raw sample timing does not prove run6's exact past breakdown.
- The 537 active/38 skipped native entries match Linux after excluding its
  23 documented synthetic offset-zero REPEAT messages. Opcode bytes match ROM.
  This is instruction selection, not MMIO-value or helper-timing equivalence.
- Each intended sensor pair produced four address NACKs with clean STOP and
  continued under ADR 010. Sensor configuration/presence is not established.
- Timer, 11520 MiB size and three sampled VRAM dwords passed. This is not a
  full-page, general VRAM allocator, GPU-VA or DMA-payload test.
- Post-POST flush-register readback was zero. Re-arm completed. No initial or
  post-rearm readback was recorded. The reason for zero is UNKNOWN.
- R5 selected-class delta is empty, host bus mastering was off after exit, and
  the owned guest/tracer exited. This is not a clean-full-kernel-log claim.

Pending-zero evidence is INFERRED from guarded PASS, not a separately logged
raw value. The address witness is structural; IOVA=GPA remains INFERRED.
Q7 is open. A7 is not S1. The user directly approved the minor change; there
is no independent Claude ACCEPT to attribute to it. The old generated A7 review
entry is the frozen preparation snapshot, not current run status.

## First-batch target

Build one native memory/translation experiment after fresh A7 startup. On a
successful run, it should establish owned physical-VRAM access and the selected BAR1/gk104
VMM mapping/update path, with complete scoped fault and lifetime evidence.
It will not create a channel, start a runlist, submit a NOP or claim S1.

Proposed stage name: `S1_MEMORY_BOOTSTRAP`. This is a design label, not an existing
CLI command or approved stage. Its signed scope must include inherited A7 writes
and every new substep. It must not reuse a consumed package or broaden the A7
permit into arbitrary memory/scheduler access.

General host-RAM DMA visibility is not the first batch's promised result.
The separate D1 gate is removed by review. G1 records the post-POST flush-target
readback as an observation only. Q11 stays open; no address-echo criterion is added.
The contract task must establish a supported, scoped VRAM publication/bootstrap
protocol or stop that branch. A BAR flush, CPU echo or IOMMU coverage alone must
not set general `published`, `visible` or `mappingVerified` claims.

## Implementation tasks and commits

| Order | Task | Concrete output | Dependency |
|---|---|---|---|
| 1 | [S1MEMCONTRACT](tasks/S1MEMCONTRACT.md) | Roles, evidence scopes, dependencies, fault/ordering and retention contract; blocking decisions | This plan accepted |
| 2 | [S1MEMARENA](tasks/S1MEMARENA.md) | Native owned-VRAM arena and address ledger, with reservations and failure retention | Contract |
| 3 | [S1MEMFAULTS](tasks/S1MEMFAULTS.md) | Scoped raw fault baselines, bounded discovery and buffered phase diagnostics | Contract |
| 4 | [S1MEMUPLOAD](tasks/S1MEMUPLOAD.md) | Bounded physical-VRAM upload/readback/flush and alias tests | Arena + fault design |
| 5 | [S1MEMMMU](tasks/S1MEMMMU.md) | Freestanding table serialization, BAR contexts and targeted invalidation; scoped mapping witness | Upload + faults |
| 6 | [S1MEMPACKAGE](tasks/S1MEMPACKAGE.md) | One frozen package, host checks, exact cardless rehearsal, review/run inventory | All above |

Implement sequentially on main. Each task writes PLAN/FINDINGS/RESULT, runs
make check and has its own commit. Related work shares the final implementation
review. No intermediate card run is planned. Cardless/host results remain OS or
simulation evidence. Do not enable an operation merely to keep later tasks moving.

One permanent resource owner must hold the single card reservation and all BAR,
arena, table and host-reference lifetimes. Preserve the startup-once latch.
Completing A7 must not reset that latch or turn an A7 permit into a broader one.
New memory phases need their own reviewed authority, bound to the same launch,
owner and immutable combined plan. Phase-specific signed handoffs are permitted
only if they cannot skip gates or replay after failure. The contract task selects
and tests that composition before native implementation.

## Contract questions that must close first

- Which objects are host arm-only references, VRAM physical storage, BAR virtual
  mappings and future channel GPU-VA mappings? They must have distinct types and
  scoped evidence. No host-pointer/IOVA/VRAM/GPU-VA casts as proofs.
- Is the selected VRAM ordering/publication protocol source-supported on the
  actual CPU aperture/cache profile? Q7's general host-DMA provider stays denied.
  CPU barriers, GPU BAR flush and TLB invalidation remain separate operations.
- What does a flush-target readback mean? A7's zero is not proof of clearing or
  failed programming. Do not require an address echo unless its meaning is
  established. If no justified D1 payload test exists, record observations only.
- Which normal VRAM range is available after firmware/display reservations,
  A7 scratch and all selected FB/MMU consumers? Two MMU debug allocations from
  the selected source need an explicit placement/reference/lifetime decision.
  Do not copy another chip's debug-register sequence or a Linux trace address.
- Which non-destructive raw fault reads are valid before POST, after POST and
  before/after each new operation? Unknown mandatory coverage blocks execution.
- Which source-supported BAR-context readback/remap test witnesses the specific
  translation/invalidation path? Slow-window physical access does not test GPU VA.
  BAR-context evidence does not prove future channel-VMM translation or PBDMA fetch.

These are implementation prerequisites, not questions the reviewer must answer
by choosing an unsupported hardware assumption. Record primary-source facts,
trace evidence, inference and unresolved items separately. Escalate under AGENTS
if evidence contradicts the reference or three material attempts fail.

## One proposed physical run, after implementation review and approval

One fresh guest, disposable overlay, one signed package/launch, independent
600-second deadline, live R5 and unchanged device isolation limits. The final
review must justify shorter per-phase time/poll bounds inside that deadline.
No deadline increase or auto-retry is part of this plan.

| Gate | Required observation before proceeding |
|---|---|
| G0: preflight/reset baseline | Exact artifacts/configuration, only 04:00.0, exclusive VFIO group, live observer/R5, source-defined safe pre-write fault snapshot |
| G1: fresh A7 | Same-run witness and owned flush page; complete POST/readiness with run7 phase sources unchanged; record flush readback only as an observation; post-POST scoped fault baseline |
| G3: physical-VRAM test | Source-backed ownership ledger and aperture profile; zero/upload/readback, two-pattern and alias checks over the declared extents |
| G4: MMU/BAR bootstrap | Selected geometry and owned initialized tables/instances; slow-window bootstrap; BAR1/gk104 VMM context enable and targeted invalidation; BAR2 excluded |
| G5: scoped mapping witness | Known patterns in distinct owned physical pages, checked through the selected BAR mapping; reviewed remap/invalidation control if supported |
| G6: closure | Final faults and source-backed reference-removal observations; conservative retention through the reviewed guest/VFIO termination path |

Guest BAR1 PCI MMIO mapping is an explicit stage effect: discover its address
and aperture size, request the supported uncached mapping, restrict CPU access
to the declared test prefix and retain the mapping for the stage lifetime.
BAR1 uses the selected gk104 VMM format and context register 0x1704
(reference/nouveau/nvkm/subdev/bar/gf100.c:52-58). BAR2 mapping/context programming
is excluded unless a later S1 dependency is established and reviewed separately.
All A7 phase sources remain byte-identical to run7. Any change to them gets
its own review; new stage code cannot modify A7's allowlist, latch or grant logic.

A successful BAR1 test is limited to that aperture, context, extents, generation
and method. Do not probe an unmapped address or free/unmap live backing as a
negative control. Use safe positive controls on distinct owned pages. The
specific remap sequence must be sourced before becoming runnable.

Batch closure may deliberately retain every device-referenced allocation until
reviewed guest/VFIO termination. It does not require live allocator reuse or a
claim of general hardware quiescence. The contract must define that termination
protocol and its required observations before launch. Missing a required closure
step fails the batch; intentional retention does not become a release proof.

Failure, unexplained baseline, timeout, missing observation or uncertain write
prevents every later phase. Preserve primary and cleanup errors and quarantine
possibly referenced storage. No fallback to stale evidence, guessed values,
forced free or manual reset. A failed closure is not a batch PASS.

Only completion of all approved gates earns batch PASS. Earlier gates can have
recorded scoped results if the experiment stops, while the batch stays incomplete.
If the contract cannot support the target, revise the plan/package scope before
hardware approval. Do not silently drop a test and declare the original batch done.

## Explicit exclusions and review/run boundary

No new FIFO/PBDMA initialization, channel, USERD, runlist, PUT or NOP programming.
The inherited A7 FIFO-reset pair remains in its write inventory. Read-only TOP
routing may be recorded if its read protocol is justified. PBDMA-count discovery
requires writes and belongs to the later scheduler batch unless separately
proposed, reviewed and included in a new explicit scope.
No GR, copy engine, GPU firmware upload, power/fan/voltage controls or host binding
changes. No other GPU, root, Linux --gpu, manual reset, blanket permit or physical
backend claiming hostSimulation. No unsupported host-payload/coherency provider.

Before asking for a run, publish exact commands, stage/driver/kernel/ROM hashes,
all reads/writes/values or source-derived expressions, bounds, resource ledger,
phase gates, evidence scopes, fault rules and guest-end bus-master check. A
combined-package approval must explicitly cover all its substeps. It grants one
launch, including fresh A7, not reuse of A7's consumed approval. ADR 006 applies
after any launcher stop. This design review is not that run approval.

The second batch remains channel/scheduler/NOP plus teardown. Its feasibility
still depends on the first batch's actual results and GR-free scheduling.

## Review inputs and checks

`python3 tools/batch1_review.py --check` verifies the A7 report and exact plan/task
input hashes in `work/S1BATCH1PLAN/review-inputs.json`. It starts no guest. This
bundle binds the planning revision; later source changes need a refreshed review
record. Use make check and git diff --check before the planning commit.
