# ABC1 running findings

- A3 rework now passes full make check and both --check runs. Exact observed
  counts: 598/560/38, 24 names; prescribed presentation inventory 2041 rows,
  1519 distinct listing offsets absent from instruction log. Seven COPY_NV_REG
  starts are split-line display, zero is repeat bookkeeping. This is not a
  complete reachable-opcode proof. No rejected branch/reviewer code read.
- Cross-toolchain rebuild running under session 47057, two jobs, ignored
  build/haiku-cross; source checkout session 95876 was started first.
- B2 freestanding memory ownership/publication boundary implemented, 39 host
  checks pass. Distinct guest-physical/IOVA/VRAM/GPU-VA types, no device addresses
  derived from CPU pointers. GPU mapping and physical backend not yet done.
- Next: executor source/design + bounded safe host subset; load-trace/recipe;
  finish native cross build and cardless backend/tooling.
