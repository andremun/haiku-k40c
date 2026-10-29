# S1BATCH1RUN: one approved combined A7/BAR1 launch

Claude accepted package acb2aca. The user explicitly approved one launch after
current package and host checks passed. Keep all reviewed source/artifact bytes.
Run tools/memstage/run.py --run-approved-batch1-once once, with its independent
600-second watchdog, fixed 04:00.0, current observer/R5 and disposable overlay.
Never remove the consumed marker. Any stop ends launches under ADR 006.

Inspect immutable evidence: A7 result/retention and observational flush readback,
memory grant, owned allocations and BAR1 witnesses, raw fault snapshots, R5 delta
and allowed lines, trace closure and end-of-guest bus mastering. Label only the
observed scope, never S1/channel/DMA publication or Q7/Q11 closure.
Write a result review/README, update STATUS and task work, run make check and
commit on main. No push, root, binding change, manual reset or second run.
