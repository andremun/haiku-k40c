# S1CHANCLOSE: implement finite channel detach and retention

## Why and inputs

After S1CHANSCHED, before native submission. Read S1-CHANNEL-CONTRACT and new
scheduler/resource interfaces. Follow fifo/chan.c:135-192, gk110.c:35-58,
gf100.c:42-46,370-373, gk104.c:40-79,190-294,410-447, runl.c:86-100 and
mmu/vmmgf100.c:337-367. Read HAIKU_BUILD_TEST before native code.

## Outputs

- One bounded cleanup controller with separate primary and cleanup results.
- Raw stop/preempt/remove/pending/engine/queue/unbind/mapping closure records.
- Failure-injection tests for every side-effect boundary and native link.

## Work and checks

Use the settled source-backed order. Stop future PUT, stop/preempt the standalone
channel, publish/wait an owned empty list, inspect current engine/queue state,
unbind, detach/invalidate the owned channel PDB and close owned BAR1 as specified.
Keep active and empty lists and all other resources retained through guest end.
Distinguish inactive stale IDs from active references. Incomplete/unknown status
fails closure. A recovery-loop idle sample is not a generic release proof.

Inject partial writes, dirty statuses, failed readbacks, clock stalls, journal
exhaustion and timeout at every step. Verify that primary failures survive cleanup,
no unsafe step follows missing prerequisites, and no allocation is freed/reused.
A successful finite detach never sets the old released Boolean as a shortcut.
A failed detach cannot become S1 PASS even if GET already advanced.

## Shared constraints

Read STATUS and this task only, then the named contract/source inputs.
Do not read tools/check_repo.py, tests/accept/ or unrelated task files.
Write PLAN before large work, update FINDINGS, and write RESULT (at most 40 lines).
Generate JSON with a deterministic tool and no-write --check. Record consulted
Nouveau files in licensing.md. Run make check before one commit on main.
No push, root, hardware run, reset, other card, host binding or consumed-marker change.
A7 phase source/client/helper bytes stay frozen to run7. No BAR2 or host payload DMA.
