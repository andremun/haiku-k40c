# Result

Implemented owned-token physical-window staging, zeroing and the finite two-page
pattern/complement test. Lock scope covers selector/data/flush/readback. Table
patches are private to the future Mapper. Unknown cache profile or inactive
authority denies effects; all failures retain and stop later writes.

Validation: 20 host cases for window crossing, independent readback, aliasing,
partial writes, read/flush failures, zero-progress/backwards clocks, stale
ownership, locks and profile/authority denial. Native object compilation,
source-bound report --check, A7 freeze, full make check and diff check.
Root make check now includes the new contract/arena/fault/upload reports.

Scope: SOURCE_ONLY protocol and HOST_ONLY tests. No GPU-VA/DMA payload proof.
MMU and combined native/rehearsal package remain. No VM/card was launched.
