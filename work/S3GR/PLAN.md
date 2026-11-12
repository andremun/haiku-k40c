# S3GR plan

Goal: start the GR engine and its two microcode programs under Haiku, checked
against the Linux reference trace before any card run. Task: docs/tasks/S3GR.md.

1. Trace sections (done, FINDINGS): the whole GR bring-up of the reference run is
   6,155 BAR0 accesses in two blocks, plus instance-memory writes.
2. Generator `tools/gr/tables.py` (`--check`): register tables of
   `gk110b_gr_pack_mmio`, the context lists, and the four microcode arrays, each
   row with its Nouveau source line. Output: generated C++ data and a JSON record.
3. Host model `src/gr/` (freestanding C++, shared with the native build): one-time
   set-up, `gf100_gr_init` in source order, Falcon load and start. It emits ordered
   accesses through the same Io interface as the memory stage.
4. Trace oracle `tools/gr/oracle.py`: run the host model against a register
   responder filled from the trace reads, compare the emitted write sequence with
   trace lines 616417-619444. Every difference is listed with a reason or fixed.
5. Policy ranges for PGRAPH, FECS, GPCCS, PMU power gating; arena capacity above 16.
6. Native compile here; link, package and rehearsal on the T7610.
