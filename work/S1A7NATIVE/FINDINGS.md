# Findings

- D0 passed structurally and its guest ended. It does not supply a current A7
  mapping grant, provider publication or physical payload/coherency proof.
- KNOWN / SOURCE_ONLY: GK110 selects the GF100 flush-target hook. FB preinit
  writes the target before nvkm_devinit_post. The source chain is in ESC-002.
  Writing the target is not itself proof that device DMA starts before POST.
- The current host candidate requires a verified address and published buffer
  before preinit. The permanent native owner deliberately installs no provider.
  Thus wiring the physical backend to the current controller would fail closed.
- The requested POST-before-D1 order needs a decision on separating an arm-only
  experimental reference from production DMA publication. I did not replace the
  missing provider with GPA-as-IOVA or a caller-supplied Boolean.
- ESC-002 records the precise software-contract conflict and candidate separation.
  Native binding and the executable A7 package are incomplete. Hardware gates,
  one-shot state and quarantine are unchanged. No write-stage approval was asked.
