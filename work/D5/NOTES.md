# D5 notes (written by the scaffold, 2026-10-12)

Session 1 wrote the header. Session 2 wrote `src/compute/LaunchDesc.cpp`
and then could not find why the acceptance test aborted. The scaffold
found two defects and fixed them:

1. `setConstantBuffer` stored the size in bits 967 to 975. The field
   `CONSTANT_BUFFER_SIZE(i)` is `MW((991+(i)*64):(975+(i)*64))`: the
   call is `q.set(base_addr + 63, base_addr + 47, size)`.
2. `encodeLaunch` began with `bindObject`. The task asks for the three
   launch methods only; the class is bound once, at channel setup.

The acceptance test now passes: 101 checks, also with the sanitizers.
**Do not change the behaviour of `src/compute/` any more.**

Left to do (nothing else):

1. Source citations. `make check` now also runs the provenance check
   of task C4a: every line of `src/compute/` with a hex number of two
   digits or more or with `constexpr` needs `// path/file.c:LINE` (or
   `file.h:LINE`) on the line or in the comment directly above it, or
   `// no source: reason`. The table in `buildQmd` has "(line 582)":
   write `nve4_compute.c:581` (the line of the assignment in
   `reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c`;
   check each number with `sed -n 'Np'`, several are off by one). For
   the bit positions cite `cla0c0qmd.h:LINE` (`grep -n NAME`). Then run
   `python3 tools/provenance.py` to rewrite
   `docs/register-provenance.md`.
2. `tests/test_launchdesc.cpp`: 15 checks or more of your own
   (`docs/tasks/D5.md` lists useful ones).
3. `tests/Makefile`: add `test_launchdesc:compute+fifo` and
   `d5_accept:compute+fifo` to `CXX_TESTS`. Nothing else.
4. `docs/launch-descriptor.md` (50 lines or more), as `docs/tasks/D5.md`
   describes.
5. `work/D5/RESULT.md` and the handoff.

Write each file in small steps. `make check` must show 0 failures.
