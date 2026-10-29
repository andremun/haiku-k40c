# S1CHANSCHED: discover and control the polling-only scheduler

## Why and inputs

After S1CHANMEM. Read S1-CHANNEL-CONTRACT, the new resource interfaces and selected
fifo/gk104.c discovery/init/channel/runlist functions, gk110.c group dispatch,
gf100.c PBDMA count/queue setup, and the existing TOP/fault parser.
Read HAIKU_BUILD_TEST before native code.

## Outputs

- Bounded current TOP/PBDMA/routing validation and phase-specific write policy.
- FIFO/queue/channel/runlist mechanics with raw fault and mask evidence.
- Independent routing, exact-value, policy and timeout tests plus native link.

## Work and checks

Make write-all/readback/restore PBDMA discovery explicit. Reject sparse,
unsupported or conflicting routing. Select the GR-associated runlist from TOP,
not an observed trace ID. Derive runq association. Source RAMFC devm separately from nouveau_chan.c:302-307.
Do not replace devm with an engine, runlist or PBDMA mask.
Preserve unrelated runlist block bits. Do not enable every engine.

Require clean pre-write raw baseline. Keep top-level and leaf interrupts masked
under the contract. Never copy Linux INTREN enables or clear dirty status to pass.
Allow only the selected instance/slot/runlist and derived values. Tests must
reject address/phase/value widening, foreign IDs and stale ownership.
Bound every read/poll/clock failure independently. Keep diagnostics buffered.
Implement bind/start/active-list and empty-list mechanics, but provide no runnable
submission path until the closure and package tasks are complete.

## Shared constraints

Read STATUS and this task only, then the named contract/source inputs.
Do not read tools/check_repo.py, tests/accept/ or unrelated task files.
Write PLAN before large work, update FINDINGS, and write RESULT (at most 40 lines).
Generate JSON with a deterministic tool and no-write --check. Record consulted
Nouveau files in licensing.md. Run make check before one commit on main.
No push, root, hardware run, reset, other card, host binding or consumed-marker change.
A7 phase source/client/helper bytes stay frozen to run7. No BAR2 or host payload DMA.
