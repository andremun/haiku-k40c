# S1CHANSUBMIT: compose one native host-NOP experiment

## Why and inputs

After S1CHANCLOSE. Read S1-CHANNEL-CONTRACT and the new memory/scheduler/closure
interfaces. Inspect runtime/S1Experiment and fifo/PushBuffer for reusable semantics,
not native authority. Reconsult nouveau_dma.c:74-119, nouveau_chan.c:447-450,
open-gpu-doc cla16f.h USERD/GPFIFO/NOP fields and source-selected packet encoding.
Read HAIKU_BUILD_TEST before native code.

## Outputs

- One-shot resident channel experiment and separate role-bound signed grant.
- Native client/module composition and deterministic operation/authority inventory.
- Independent event-order, corruption, replay, progress and failure tests.

## Work and checks

Keep frozen A7, repeat exact memory gates, then require the new broker-attested
same-launch owner/ledger/closure/kernel/artifact/witness binding for channel work.
No caller address/flag/Boolean grants permission. Reject crossed stage keys,
replay, second open, load replay, phase skips and failure recovery into success.

Validate every input and ensure cleanup is ready before bind/start. Stage/read
back the complete zero ring and exact two-word host NOP, with one GPFIFO entry.
Record empty pointers before publishing GP_PUT once. Apply the selected CPU/BAR
ordering independently. Poll raw faults and GP_GET/payload GET with fixed limits.
Do not add GR, object bindings, a semaphore, doorbell or host DMA payload.

Test false progress, prefetched/stale pointers, payload mismatch, out-of-range
indices, double notification, parser truncation and cleanup failure after progress.
Native code cannot identify as hostSimulation. No physical run in this task.

## Shared constraints

Read STATUS and this task only, then the named contract/source inputs.
Do not read tools/check_repo.py, tests/accept/ or unrelated task files.
Write PLAN before large work, update FINDINGS, and write RESULT (at most 40 lines).
Generate JSON with a deterministic tool and no-write --check. Record consulted
Nouveau files in licensing.md. Run make check before one commit on main.
No push, root, hardware run, reset, other card, host binding or consumed-marker change.
A7 phase source/client/helper bytes stay frozen to run7. No BAR2 or host payload DMA.
