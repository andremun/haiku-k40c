# S1C2 findings

- SOURCE_ONLY: selected GK104 VMM + GF100 BAR; mode 17 from GK110 FB default.
  Use 4 KiB mappings with mode-17 directory geometry, not mode-16 geometry.
- SOURCE_ONLY: full PDB-specific invalidation includes free-slot check, target
  encoding, serialized request, and queued status. It is not a quiescence proof.
- Corrected older design: source BAR wait is 2000 ms, not 2 ms.
- Corrected unsupported MMU scratch deferral and GPA-as-DMA substitution.
- SOURCE_ONLY: standalone hw=false group means no hardware group runlist record
  and channel-ID preemption. Native construction must enforce that choice.
- TOP and PBDMA associations must be discovered. PBDMA count discovery writes
  an enable mask and restores it; it is outside read-only B5.
- Conservative release requires stop/preempt/remove/idle/unbind and final faults;
  physical completeness remains UNKNOWN. Keep allocations quarantined on doubt.
- No runtime code or hardware/VM command changed. No new test was needed for
  this source-design task; full existing repository checks remain mandatory.
