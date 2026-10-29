# Plan

1. Catalog MC reset-safe reads separately from post-A7 FIFO/MMU/privring/TOP.
2. Implement bounded raw snapshots with no clear/ack writes, generation and phase
   order checks, monotonic budgets, and resident buffered diagnostics.
3. Test dirty/missing/partial baselines, pending-unit detail bounds, TOP routing,
   overflow and clock faults. Keep channel/PBDMA discovery writes excluded.
4. Compile native objects, generate source-bound report, check frozen A7 and full
   repository checks; commit task. No VM or card.
