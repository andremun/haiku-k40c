# S1CHANMEM: prepare owned channel images and USERD mapping

## Why and inputs

After S1CHANCONTRACT. Read S1-CHANNEL-CONTRACT and the memory contract, then
memory/VramArena, memstage/{Tables,Mapper,Upload} and memnative owner/mapping
interfaces. Read HAIKU_BUILD_TEST before native code. Reconsult only selected
RAMFC/USERD/VMM sources named in the contract.

## Outputs

- Distinct typed channel PDB/SPT/instance, USERD, ring/pushbuffer and runlist roles.
- Freestanding encoders and independent field/address/layout tests.
- Resident same-arena allocation and a checked BAR1 USERD handoff, plus native link.
- Deterministic layout/encoding report, with no hardware verification flags.

## Work and checks

Preserve the old memory witness and its owned-disable result. Reuse its backing
only through reviewed owner transitions, never a second overlapping allocator.
Prepare source-sized USERD storage, both runlists, ring and packet extents.
Check ledger capacity, overflow, alignment, owner/epoch, generation and address
confusion before mutation. Channel VA must not numerically alias physical/BAR VA.
Serialize every RAMFC word and VMM join field from checked owned inputs.

Test raw bytes against independent source-field expectations, all boundary cases,
complete absent entries, alias mistakes and failure retention. Test channel
invalidate selection separately from BAR HUB_ONLY. Add bounded BAR0 mapping and
explicit UC writable selected-USERD view only behind future channel authority.
No runtime scheduler activation. No CPU echo becomes a GPU translation claim.

## Shared constraints

Read STATUS and this task only, then the named contract/source inputs.
Do not read tools/check_repo.py, tests/accept/ or unrelated task files.
Write PLAN before large work, update FINDINGS, and write RESULT (at most 40 lines).
Generate JSON with a deterministic tool and no-write --check. Record consulted
Nouveau files in licensing.md. Run make check before one commit on main.
No push, root, hardware run, reset, other card, host binding or consumed-marker change.
A7 phase source/client/helper bytes stay frozen to run7. No BAR2 or host payload DMA.
