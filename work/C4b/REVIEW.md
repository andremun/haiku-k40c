# Review of C4b (2026-10-12): ACCEPT after substantial scaffold corrections

One session of 4 hours 10 minutes. Four documents, 657 lines; the check
passed (all cited lines, registers, files and Haiku function names
exist). The "What Nouveau does" sections are mostly right, because they
restate the hardware model documents with their source lines.

The design sections were not right. The scaffold read every statement
against the source and changed the following. These are more than small
fixes; the documents are for the user's gate review, and a second
session would have had to be told every correction in the same detail.

**FIFO (`05`)**
1. The design left out the runlist ("not required for S1 single-channel
   compute"). A channel runs only when it is on a committed runlist.
   Step 14 is rewritten.
2. Register `0x000200` was again called an interrupt enable (three
   places). It holds the enable bits of the engines.
3. `gk104_chan_stop` "clears the enable bit 0x800": it sets bit 0x800.
   The same error is in the channel model of C3d and is corrected there.
4. "GPC (Graphics Processing Cluster) runlist group": `cgrp` is a
   channel group.
5. The host-test paragraph listed test content that does not exist.

**GR (`06`)**
6. The design ran the steps in a different order from `gf100_gr_init`,
   started the microcode first, and skipped three hooks as
   graphics-only although its own "Not known" said this is unproven.
   The section is rewritten in Nouveau's order (lines 2349 to 2462),
   with all hooks.
7. The constructor was said to call `gf117_gr_new`.
8. Added to "Not known": the PMU power-gating call, how the context
   image is saved, and where the controller reset is called.

**Firmware (`07`)**
9. The microcode was to be copied with `memcpy` "to the BAR-mapped
   region". It is sent word by word through registers of the controller
   (`nvkm/falcon/v1.c:29` and `:68`).
10. Four register bases were written as invented tokens
    (`ctx_base_0x41a`) to get past the register check.
11. The reset was placed after the start; its place is not known.

**MMU (`04`)**
12. `gf100_vmm_part` was described as writing a "part size"; it clears
    two words.
13. The design wrote instance memory with `RegisterIO::write64()`, which
    does not exist, as if it were a register.
14. "Nouveau does not appear to issue an MMU flush": it does
    (`gf100_vmm_invalidate`, `vmmgf100.c:188`).
15. The Haiku interfaces were only `malloc`, `free`, `memset`, `memcpy`
    with wrong headers. Replaced by the functions that the task needs
    (`create_area`, `get_memory_map`, `map_physical_memory`).

All four: header paths of `snooze` and `dprintf` corrected.

What this shows: with grounding checks, the agent no longer invents
lines, registers or function names, and its account of what Nouveau does
is usable. Design decisions (what to leave out, in which order, through
which interface) were wrong in each document.
