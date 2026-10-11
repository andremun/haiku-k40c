# D5 Plan: Launch descriptor and compute method encoding

Steps:
1. Write `src/compute/LaunchDesc.h` — constants, Qmd class, ComputeJob struct,
   function declarations (set/get/buildQmd/setConstantBuffer/encodeLaunch).
2. Write `src/compute/LaunchDesc.cpp` — Qmd bitfield ops, buildQmd (23 fields
   from nve4_compute.c:581-617), setConstantBuffer (4 assigns from line 543-546),
   encodeLaunch (3 push-buffer methods: LAUNCH_DESC_ADDRESS, LAUNCH,
   NV50_GRAPH_SERIALIZE).
3. Add `test_launchdesc:compute+fifo` and `d5_accept:compute+fifo` to
   `tests/Makefile` (only CXX_TESTS line).
4. Write `tests/test_launchdesc.cpp` — 15+ checks.
5. Write `docs/launch-descriptor.md` — field table, methods, not-covered.

Checks:
- `make check` passes (acceptance + own tests).
- All bits from cla0c0qmd.h, all field names from source.
