# D5 Plan (5 remaining items)

1. **Source citations** — Add `// reference/mesa/.../cla0c0qmd.h:LINE` or
   `nve4_compute.c:LINE` to every line in `src/compute/LaunchDesc.cpp` with a
   hex constant ≥ 2 digits or `constexpr`. Fix off-by-one on field line numbers.
2. **Own tests** — Write `tests/test_launchdesc.cpp` with 15+ CHECKs:
   cross-word `get` after `set`, max-fit `buildQmd`, all 8 CBs, `encodeLaunch`
   decoded with `k40::fifo::decodeBuffer`.
3. **Makefile** — Add `test_launchdesc:compute+fifo` and
   `d5_accept:compute+fifo` to `CXX_TESTS`.
4. **Documentation** — Write `docs/launch-descriptor.md` (50+ lines): field
   table, values, source lines, launch methods, "Not covered" section.
5. **Handoff** — `make check` passes 0 failures, `tools/provenance.py`
   rewrites `docs/register-provenance.md`, write `RESULT.md`, update `STATUS.md`.
