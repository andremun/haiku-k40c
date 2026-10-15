# V1 findings

2026-10-16. Base revision: 637c436.

- Purpose explicitly requested by the user: revise possible mistakes by "Local"
  and advance toward machine-dependent implementation. No reviewer code read;
  the rejected A3 branch was not used.
- Independent boundary test reproduces seven failed assertions on original
  sources: four negative-token cases, one crossing command-buffer range, two
  invalid page-shift cases. Corrected without modifying acceptance tests.
- Existing C++ suites pass (583 reported checks). New S1 controller passes 58
  checks; boundary regression passes. The encoder emits the settled NOP words.
- New controller builds freestanding with exceptions/RTTI disabled, and its
  object has no undefined symbols on this Linux host. This is not a Haiku ABI
  or kernel link/load result.
- All five pinned reference links are broken here. Captures remain available;
  hash inventory generated. Full make check reports 220 failures both before
  and after implementation. Do not regenerate prior source-derived outputs in
  this environment merely to make checks agree with empty source trees.
- Standalone R1 Python acceptance: 9/11 checks pass, positive generation/verify
  fail with the absent Mesa header. D4 acceptance: 37/38 pass, missing named
  register lookup with absent envytools. These failure-path tests do not prove
  valid-input behavior while their reference inputs are absent.
- Python pytest and PyYAML unavailable in current interpreter. Recorded
  ~/haiku-cross compiler/header/kernel bundle absent. No kernel build attempted
  against invented substitutes; no VM/card experiment attempted.
- ROM absent, capture identity documented. User will arrange ROM later.
- Plan contradiction corrected: VBIOS is firmware, and no-GR scheduling remains
  unproven. Host flush page can precede POST, coupling B2 and A7.
