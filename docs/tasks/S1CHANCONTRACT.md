# S1CHANCONTRACT: fix channel progress and closure contracts

## Why and inputs

First task after the batch-2 design review. Read S1-BATCH2-REVIEW, the current
S1-MEMORY-CONTRACT, and interfaces in memory/VramArena, memnative/NativeOwner,
memstage/Mapper and runtime/S1Experiment. Follow pinned fifo/gk110.c:35-128,
gk104.c:40-118,190-294,379-457,735-808; gf100.c:118-145,351-373,927-943;
base.c:138-160,306-320; chan.c:135-192,350-485; mmu/vmmgf100.c:188-233,337-367;
nouveau_dma.c:35-119; nouveau_chan.c:302-307,447-450; open-gpu-doc cla16f.h.
Follow additional selected dependencies only when a source gate requires them.

## Outputs

- docs/S1-CHANNEL-CONTRACT.md: roles, authority/phase transitions, address domains,
  ordering, interrupt policy, exact progress and finite teardown predicates.
- Deterministic source/trace matrix with omission reasons and unresolved gates.
- A frozen A7 source boundary and the required resident memory-owner ABI changes.

## Work and gates

Resolve USERD source-sized backing and its physical/slot/BAR address relationship.
Define selected channel-ID baseline and BAR0 mapping bounds. Define channel VMM
join/flush and BAR1 USERD handoff after the old memory witness disables BAR1.
Keep GP_GET distinct from payload GET. Define stable high/low reads and whether
payload GET reaches packet end under the exact selected flags. Do not invent a
completion interpretation. Confirm host NOP needs no GR object binding.

List every Linux initialization write kept, changed or omitted. Justify polling
INTREN masks and raw fault coverage. Set source-backed standalone scheduling,
preemption/removal/unbind ordering and a finite detach predicate. Do not equate
retention with release or generic quiescence. Resolve the old controller's
release Boolean with an explicit new result. Unknown mandatory facts block
execution and require an escalation if reference and evidence conflict.

## Shared constraints

Read STATUS and this task only, then the named contract/source inputs.
Do not read tools/check_repo.py, tests/accept/ or unrelated task files.
Write PLAN before large work, update FINDINGS, and write RESULT (at most 40 lines).
Generate JSON with a deterministic tool and no-write --check. Record consulted
Nouveau files in licensing.md. Run make check before one commit on main.
No push, root, hardware run, reset, other card, host binding or consumed-marker change.
A7 phase source/client/helper bytes stay frozen to run7. No BAR2 or host payload DMA.
