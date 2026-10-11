# D5 notes (written by the scaffold, 2026-10-12)

The first session wrote `src/compute/LaunchDesc.h` and `work/D5/PLAN.md`
and was then stopped several times in the middle of a long reply, before
any other file existed.

State: the header exists but does not compile (`#include <vector>` is
missing). `src/compute/LaunchDesc.cpp`, the tests, the Makefile line and
the document are not written.

Write `LaunchDesc.cpp` in small steps, one function at a time with a
compile after each: first `Qmd::set` and `Qmd::get` (then the acceptance
test's `test_bitfield` must pass), then `buildQmd`, then
`setConstantBuffer`, then `encodeLaunch`. Do not write the whole file in
one reply.
