# S1MEMARENA: bounded native VRAM ownership and ledger

## Why and inputs

Depends on the accepted S1MEMCONTRACT outputs. Read STATUS, the first-batch plan,
S1-MEMORY-CONTRACT, MEMORY-CONTRACT, S1-INTEGRATION-CHOICES memory section and
src/memory/Memory.*, ArmedReference.*, src/os/NativeOwner.* and HaikuMemory.*
only where needed for owner lifetime. Recheck selected pinned allocation sources.

## Outputs

- Bounded native VRAM arena/ledger under src/memory/, with distinct address roles.
  Exact filenames are chosen with the contract; a CPU pointer is not an address proof.
- Host tests under tests/ for allocation math, exclusions, ownership and retention.
- Generated source-bound layout/test report with --check under tools/ and work/.
- work/S1MEMARENA/{PLAN,FINDINGS,RESULT}.md; source/licensing notes as needed.

## Work and invariants

Derive usable extents and every reservation from source and this driver's actual
consumers. Include firmware/display exclusions, A7 scratch, tables/instances,
data pages and selected FB/MMU debug objects. Do not copy a captured VRAM address
or treat one passing scratch page as proof of a free arena.
Track token, owner/boot generation, role, physical extent, alignment, CPU view,
BAR VA/GPU VA where applicable, write generation and device-reference state.
Reject overflow, misalignment, overlap, double ownership and unsupported layouts.
Bound metadata storage. Define failure after partial acquisition and quarantined
ownership. No referenced extent can be returned to the free list.

## Checks and limits

Use an independent interval oracle and injected partial-allocation/release failures.
Test boundary extents, every exclusion, stale tokens and repeated detach/reload.
Do not change the general Buffer publication contract to bypass a missing proof.
Native compilation is allowed; no load/run. Keep new tests selected by make's
explicit all default. Run generators --check, make check and diff check. RESULT
<=40 lines; one task commit on main. No card, VM, root, reset or binding change.
If usable ownership cannot be justified, the physical arena remains disabled.
