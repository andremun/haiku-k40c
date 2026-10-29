# Findings

Claude accepts A7 and the plan with BAR1/gk104 only, no G2/D1, observational
flush readback and exact run7 A7 source preservation. Review recorded verbatim
in substance in CLAUDE-REVIEW.md. No physical/card run authorized.
The generated a7-freeze.json checks the current phase sources against run7's
launched suite. New code must compose with the original module/client/job;
no old A7 permit/latch/API expansion or rewritten POST.

Selected GK110B uses nv50 instmem, gk104 MMU/VMM and gf100 BAR. INST allocations
resolve via nv50's nvkm_ram_get to VRAM. The two default 128 KiB MMU debug objects
therefore reserve VRAM, not additional host-DMA targets. No GM200 programming.
BAR1 context is 0x1704. Guest PCI resource 1 maps the read-only 8 KiB test prefix;
PCI slot 2 may be its high address word, not NVIDIA BAR2. No BAR2/0x1714 effects.

Pinned Haiku vm.cpp supports explicit UC flags, while default UC is weak and
may be overridden. New mappings request UC explicitly and fail on errors; no
claim of measured PAT/MTRR or host-RAM DMA coherency. This source-supported
candidate is tested only by a scoped positive BAR1 witness. General Q7 stays open.
No extra flush-target read/write/echo test; G1's original readback is observational.

The original A7 API lacks a general state query. A trusted host broker must bind
memory authorization to same-launch checked A7 completion and new phase nonce/
challenge. One open per unchanged A7 child and new memory child; no startup retry.
All memory objects remain retained until reviewed guest/VFIO end. Mapping-update
witness uses A/B pages and remap/restore, not an unmapped or freed-page negative test.
The next tasks implement source-backed fault coverage and all runtime gates;
this contract is not a declaration that the physical path is verified/runnable.
