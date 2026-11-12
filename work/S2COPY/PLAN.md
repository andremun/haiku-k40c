# S2COPY plan

Goal: milestone S2. One 4096-byte copy between two owned VRAM pages, by the copy
engine, on the S1 channel. Task text: docs/tasks/S2COPY.md. Decision 012.

1. Add two arena roles (CopySource, CopyDest) and two channel pages
   (VA 0x10002000 read-only, VA 0x10003000 writable).
2. Extend the push buffer after the NOP with the kernel copy sequence
   (`nouveau_boa0b5.c:37-71,85`) and add a second GPFIFO entry.
3. Channel phase after the NOP: GP_PUT 2, poll GP_GET, poll the CE0 engine status,
   read the copy-engine interrupt status and launch error, compare the destination
   with the source pattern through the slow window, then the S1 teardown.
4. Policy: the same 24-step script. New permissions only when both copy pages are
   in the owned ledger: one more GP_PUT write (value 2), three status reads.
5. Host test with an independent copy-engine simulation. Mutation checks.
6. Independent validator in tools/memstage/evidence.py. Stage selector
   `K40_MEM_STAGE` for the package tools.
7. T7610 steps: native build, package, cardless rehearsal (not possible in the
   cloud container).
