# Plan

1. Derive a pure uniform-FBP layout from source-backed raw inputs, rejecting mixed layouts.
2. Implement a bounded append-only VRAM ledger: head/tail/A7 scratch exclusions,
   two retained debug objects, role/owner/epoch tokens, dirty/reference state.
3. Test allocation with an independent interval oracle, stale-token and injected
   capacity/partial-layout failures. No live release or proof-flag promotion.
4. Cross-compile, generate deterministic report, verify A7 freeze, full checks, commit.
