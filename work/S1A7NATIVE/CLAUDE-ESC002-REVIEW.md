# User-supplied Claude review of ESC-002, 2026-10-28

Resolution: **separate arm-only contract, arm before POST, D1 stays after POST.
Do not defer arming.** This file records the supplied review's decision and facts.
It is not a new Codex hardware approval.

The supplied source/trace findings are:
- FB preinit and FB init both call the flush-target hook (fb/base.c:227 and 204).
- TRACE_VERIFIED in the Linux capture: mmiotrace.txt.xz:45505 writes 0x7fbff0
  before the first script write at 45511. Line 114450 repeats it after POST.
  The trace contains no read of 0x100c10. That captured address is historical only.
- This ROM's decoded script has no 100c1 operand. Neither arming write is a script write.
- Nouveau allocates a zeroed page, DMA-maps it bidirectionally, installs its
  address, and eventually unmaps/frees it. It does not use the page's payload.

Required implementation:
1. Distinct arm-only memory type, not Buffer publication or submission pinning.
   Never set published, mappingVerified or visible. No DMA payload claim.
2. Owner-allocated zeroed aligned DMA32 page. Validate complete address bounds and
   addr >> 8 encoding. No CPU payload access or reuse after arming. Device writes
   are allowed by the bidirectional mapping.
3. Retain backing until a verified VFIO end/reset or reviewed teardown. Failures
   quarantine without early free. Driver detach must not lose ownership.
4. Fresh structural device-address witness in this same A7 run, before arming.
   Do not reuse D0's ended witness. IOVA=GPA remains INFERRED. No visibility claim.
5. R5 monitoring during A7. A new DMAR, VFIO or AER line stops under ADR 006.
6. Program 0x100c10 before POST. After POST, read it and record the actual value,
   then program it again. Do not assume the script left it unchanged.
7. Package both driver writes, complete script write inventory, exact commands,
   driver hashes, readiness checks and stop rules. Wait for an explicit yes for
   one write-stage run under the amended ADR 008.

D1 follows POST. Q7 stays open. Physical backends never report hostSimulation.
Close ESC-002 as resolved against this review. Building the type, PreStart change,
fresh witness bridge and complete A7 package is the S1A7NATIVE macro task.

## Evidence limit retained by Codex

IOMMU protection does not make every incorrect IOVA harmless. Another valid
mapped IOVA can address other guest RAM without a fault. Validate the full
selected extent and encoding. Do not perform a negative DMA probe. No host-memory
corruption or guest-memory safety guarantee is inferred merely from an empty log.
