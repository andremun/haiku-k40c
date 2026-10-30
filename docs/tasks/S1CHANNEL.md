# S1CHANNEL: one host NOP on one CE0 channel (lean batch 2)

Implement the final batch-2 design (docs/S1-BATCH2-REVIEW.md) as one channel
phase after the unchanged A7 and batch-1 memory/BAR1 gates, in the resident
memory owner. Copy the Linux kernel CE channel (mmiotrace 560971-562370):
runlist from TOP, PBDMA from routing, RAMFC as Linux, USERD at BAR1 VA 0,
GP_PUT once through BAR1, poll GP_GET, mandatory teardown, no interrupts.
Policy-check every write. Validate the run from the journal. Rehearse cardless.
Card run only after the user's explicit yes (ADR 008). Review: docs/S1-CHANNEL-REVIEW.md.
